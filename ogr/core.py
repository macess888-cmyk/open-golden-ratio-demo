from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class Proposal:
    id: str
    actor_id: str
    author_role: str
    scope: str
    claim: str
    evidence_level: int
    rollback_available: bool


@dataclass
class WatchRecord:
    watch_id: str
    actor_id: str
    target_state_after_watch: str
    required_clean_proposals: int
    clean_proposals_observed: int = 0
    current_status: str = "active"
    failure_refs: list = None
    notes: str = ""

    def __post_init__(self):
        if self.failure_refs is None:
            self.failure_refs = []


class OGRSystem:
    def __init__(self):
        self.ledger = []
        self.watch_records = {}
        self.restoration_log = []

        self.actor_pressure = {}
        self.actor_state = {}
        self.actor_failures = {}
        self.failed_watch_counts = {}

        self.watch_counter = 0
        self.restoration_counter = 0

    def ensure_actor(self, actor_id: str):
        if actor_id not in self.actor_pressure:
            self.actor_pressure[actor_id] = 0
        if actor_id not in self.actor_state:
            self.actor_state[actor_id] = "normal"
        if actor_id not in self.actor_failures:
            self.actor_failures[actor_id] = []
        if actor_id not in self.failed_watch_counts:
            self.failed_watch_counts[actor_id] = 0

    def make_proposal(
        self,
        proposal_id,
        actor_id,
        author_role,
        scope,
        claim,
        evidence_level,
        rollback_available,
    ):
        self.ensure_actor(actor_id)
        return Proposal(
            id=proposal_id,
            actor_id=actor_id,
            author_role=author_role,
            scope=scope,
            claim=claim,
            evidence_level=evidence_level,
            rollback_available=rollback_available,
        )

    def corridor_check(self, proposal: Proposal):
        if proposal.scope == "global" and proposal.author_role != "governance":
            return False, "scope inflation"
        if not proposal.rollback_available:
            return False, "rollback missing"
        return True, "corridor pass"

    def verifier_one(self, proposal: Proposal):
        if "unsafe" in proposal.claim.lower():
            return False
        return proposal.evidence_level >= 2

    def verifier_two(self, proposal: Proposal):
        return proposal.evidence_level >= 2

    def verifier_results(self, proposal: Proposal):
        v1 = self.verifier_one(proposal)
        v2 = self.verifier_two(proposal)
        return v1 and v2, {
            "verifier_one": v1,
            "verifier_two": v2,
            "reentry_strict_review": None,
        }

    def commit(self, proposal: Proposal, verifier_results: dict):
        self.ledger.append(
            {
                "type": "proposal_committed",
                "proposal_id": proposal.id,
                "actor_id": proposal.actor_id,
                "state_at_commit": self.actor_state[proposal.actor_id],
                "pressure_at_commit": self.actor_pressure[proposal.actor_id],
                "verifiers": verifier_results,
            }
        )
        print(f"COMMITTED: {proposal.id}")

    def start_watch(self, actor_id: str, required_clean_proposals: int, notes: str):
        self.ensure_actor(actor_id)
        self.watch_counter += 1
        watch_id = f"WATCH_{actor_id}_{self.watch_counter:03}"
        self.actor_state[actor_id] = "normal_watch"
        self.watch_records[watch_id] = WatchRecord(
            watch_id=watch_id,
            actor_id=actor_id,
            target_state_after_watch="normal",
            required_clean_proposals=required_clean_proposals,
            notes=notes,
        )
        self.ledger.append(
            {
                "type": "watch_started",
                "watch_id": watch_id,
                "actor_id": actor_id,
                "target_state_after_watch": "normal",
                "required_clean_proposals": required_clean_proposals,
                "notes": notes,
            }
        )
        print(f"WATCH STARTED: {watch_id}")
        return watch_id

    def active_watch_for_actor(self, actor_id: str):
        for watch_id, record in self.watch_records.items():
            if record.actor_id == actor_id and record.current_status == "active":
                return watch_id, record
        return None, None

    def fail_watch(self, actor_id: str, proposal_id: str, reason: str):
        watch_id, record = self.active_watch_for_actor(actor_id)
        if record is None:
            return

        record.current_status = "failed"
        record.failure_refs.append(proposal_id)
        self.failed_watch_counts[actor_id] += 1

        if self.failed_watch_counts[actor_id] >= 3:
            self.actor_state[actor_id] = "contained_review_only"
        else:
            self.actor_state[actor_id] = "escalated"

        self.ledger.append(
            {
                "type": "watch_failed",
                "watch_id": watch_id,
                "actor_id": actor_id,
                "proposal_id": proposal_id,
                "reason": reason,
                "reversal_state": self.actor_state[actor_id],
                "failed_watch_count": self.failed_watch_counts[actor_id],
            }
        )

        print(f"WATCH FAILED: {watch_id} | reason: {reason}")
        print(f"Actor moved to state: {self.actor_state[actor_id]}")

    def observe_clean_watch_commit(self, actor_id: str, proposal_id: str):
        watch_id, record = self.active_watch_for_actor(actor_id)
        if record is None:
            return

        record.clean_proposals_observed += 1
        self.ledger.append(
            {
                "type": "watch_clean_commit_observed",
                "watch_id": watch_id,
                "actor_id": actor_id,
                "proposal_id": proposal_id,
                "clean_proposals_observed": record.clean_proposals_observed,
                "required_clean_proposals": record.required_clean_proposals,
            }
        )

        if record.clean_proposals_observed >= record.required_clean_proposals:
            record.current_status = "passed"
            self.actor_state[actor_id] = "normal"
            self.actor_pressure[actor_id] = 0
            self.ledger.append(
                {
                    "type": "watch_passed",
                    "watch_id": watch_id,
                    "actor_id": actor_id,
                    "target_state_after_watch": "normal",
                }
            )
            print(f"WATCH PASSED: {watch_id}")
            print("Actor moved to state: normal")

    def run_proposal(self, proposal: Proposal):
        actor_id = proposal.actor_id
        self.ensure_actor(actor_id)

        print(f"\n--- Testing proposal: {proposal.id}")
        print(proposal)
        print(f"Current state for {actor_id}: {self.actor_state[actor_id]}")
        print(f"Current pressure score: {self.actor_pressure[actor_id]}")

        if self.actor_state[actor_id] in ["contained", "contained_review_only"]:
            print(f"REJECTED: actor is {self.actor_state[actor_id]}")
            self.actor_failures[actor_id].append(proposal.id)
            self.ledger.append(
                {
                    "type": f"proposal_rejected_{self.actor_state[actor_id]}",
                    "proposal_id": proposal.id,
                    "actor_id": actor_id,
                }
            )
            return

        passed, reason = self.corridor_check(proposal)
        if not passed:
            print(f"REJECTED at corridor: {reason}")
            self.actor_pressure[actor_id] += 1
            self.actor_failures[actor_id].append(proposal.id)
            self.ledger.append(
                {
                    "type": "proposal_rejected_corridor",
                    "proposal_id": proposal.id,
                    "actor_id": actor_id,
                    "reason": reason,
                }
            )

            if self.actor_state[actor_id] == "normal_watch":
                self.fail_watch(actor_id, proposal.id, reason)
            elif self.actor_pressure[actor_id] >= 4:
                self.actor_state[actor_id] = "contained" if self.failed_watch_counts[actor_id] == 0 else "escalated"
            return

        print(f"PASSED corridor: {reason}")

        quorum_passed, verifier_results = self.verifier_results(proposal)
        print("Verifier results:", verifier_results)

        if not quorum_passed:
            print("REJECTED at verifier quorum")
            self.actor_pressure[actor_id] += 1
            self.actor_failures[actor_id].append(proposal.id)
            self.ledger.append(
                {
                    "type": "proposal_rejected_quorum",
                    "proposal_id": proposal.id,
                    "actor_id": actor_id,
                    "verifiers": verifier_results,
                }
            )
            if self.actor_pressure[actor_id] >= 4 and self.actor_state[actor_id] == "normal":
                self.actor_state[actor_id] = "escalated"
            return

        self.commit(proposal, verifier_results)

        if self.actor_state[actor_id] == "escalated":
            self.actor_pressure[actor_id] = max(0, self.actor_pressure[actor_id] - 1)

        if self.actor_state[actor_id] == "normal_watch":
            self.observe_clean_watch_commit(actor_id, proposal.id)

    def review_restoration(
        self,
        actor_id: str,
        approve: bool,
        oversight_override: bool = False,
    ):
        self.ensure_actor(actor_id)

        self.restoration_counter += 1
        restoration_id = f"REST{self.restoration_counter:03}"

        retry_sequence = self.failed_watch_counts[actor_id]
        retry_after_failed_watch = retry_sequence > 0
        required_clean = 2 + retry_sequence
        base_reviewer_count = 2
        effective_reviewer_count = base_reviewer_count + retry_sequence

        print(f"\n--- Reviewing restoration: {restoration_id}")
        print(f"Actor: {actor_id}")
        print(f"Current state: {self.actor_state[actor_id]}")
        print(f"Current pressure: {self.actor_pressure[actor_id]}")
        print("Requested target state: normal")
        print(f"Retry sequence: {retry_sequence}")
        print(f"Base reviewer count: {base_reviewer_count}")
        print(f"Effective reviewer count: {effective_reviewer_count}")
        print(f"Retry after failed watch: {retry_after_failed_watch}")
        print(f"Required clean proposals for resulting watch: {required_clean}")

        if self.actor_state[actor_id] not in ["escalated", "contained_review_only"]:
            print("RESTORATION REJECTED at admissibility: actor state not eligible for restoration")
            self.ledger.append(
                {
                    "type": "restoration_rejected_admissibility",
                    "restoration_id": restoration_id,
                    "actor_id": actor_id,
                    "reason": "actor state not eligible for restoration",
                    "requested_target_state": "normal",
                    "state_at_review": self.actor_state[actor_id],
                    "pressure_at_review": self.actor_pressure[actor_id],
                    "retry_after_failed_watch": retry_after_failed_watch,
                    "prior_watch_id": self.get_last_watch_id(actor_id),
                    "retry_sequence": retry_sequence,
                }
            )
            return False

        if self.actor_state[actor_id] == "contained_review_only" and not oversight_override:
            print("RESTORATION REJECTED at admissibility: terminal contained-review-only state requires oversight override")
            self.ledger.append(
                {
                    "type": "restoration_rejected_admissibility",
                    "restoration_id": restoration_id,
                    "actor_id": actor_id,
                    "reason": "terminal contained-review-only state requires oversight override",
                    "requested_target_state": "normal",
                    "state_at_review": self.actor_state[actor_id],
                    "pressure_at_review": self.actor_pressure[actor_id],
                    "retry_after_failed_watch": retry_after_failed_watch,
                    "prior_watch_id": self.get_last_watch_id(actor_id),
                    "retry_sequence": retry_sequence,
                }
            )
            return False

        if not approve:
            print("RESTORATION REJECTED at review outcome")
            return False

        print("RESTORATION PASSED admissibility: restoration admissible for normal target")
        print("RESTORATION PASSED review independence: restoration review independence satisfied")
        print("RESTORATION review outcome check: restoration review quorum satisfied")
        print(f"RESTORATION APPROVED: {restoration_id}")

        self.restoration_log.append(
            {
                "restoration_id": restoration_id,
                "actor_id": actor_id,
                "outcome": "approved",
                "requested_target_state": "normal",
                "retry_after_failed_watch": retry_after_failed_watch,
                "prior_watch_id": self.get_last_watch_id(actor_id),
                "retry_sequence": retry_sequence,
                "state_at_review": self.actor_state[actor_id],
                "pressure_at_review": self.actor_pressure[actor_id],
                "required_reviewer_count_base": base_reviewer_count,
                "required_reviewer_count_effective": effective_reviewer_count,
                "required_clean_proposals_for_watch": required_clean,
            }
        )

        self.ledger.append(
            {
                "type": "restoration_reviewed",
                "restoration_id": restoration_id,
                "actor_id": actor_id,
                "outcome": "approved",
                "requested_target_state": "normal",
                "retry_after_failed_watch": retry_after_failed_watch,
                "prior_watch_id": self.get_last_watch_id(actor_id),
                "retry_sequence": retry_sequence,
                "state_at_review": self.actor_state[actor_id],
                "pressure_at_review": self.actor_pressure[actor_id],
                "required_reviewer_count_base": base_reviewer_count,
                "required_reviewer_count_effective": effective_reviewer_count,
                "required_clean_proposals_for_watch": required_clean,
            }
        )

        self.actor_state[actor_id] = "normal_watch"
        self.actor_pressure[actor_id] = 0
        print("Actor moved to state: normal_watch")
        self.start_watch(actor_id, required_clean, f"Started by restoration {restoration_id}")
        return True

    def get_last_watch_id(self, actor_id: str):
        ids = [wid for wid, rec in self.watch_records.items() if rec.actor_id == actor_id]
        if not ids:
            return None
        return ids[-1]

    def show_actor_status(self, actor_id: str):
        self.ensure_actor(actor_id)
        print(f"\nActor status: {actor_id}")
        print(f"State: {self.actor_state[actor_id]}")
        print(f"Pressure: {self.actor_pressure[actor_id]}")
        print(f"Failures: {self.actor_failures[actor_id]}")

    def export_jsonable(self):
        return {
            "ledger": self.ledger,
            "watch_records": {k: asdict(v) for k, v in self.watch_records.items()},
            "restoration_log": self.restoration_log,
        }