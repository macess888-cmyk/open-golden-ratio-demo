from ogr.core import OGRSystem


def build_demo_system():
    system = OGRSystem()

    actor = "adversary_alpha"

    # baseline
    system.run_proposal(
        system.make_proposal("P001", "governance_baseline", "governance", "global", "update policy parameter", 3, True)
    )

    # initial failures
    system.run_proposal(system.make_proposal("A001", actor, "explorer", "global", "unsafe mutation", 3, True))
    system.run_proposal(system.make_proposal("A002", actor, "explorer", "global", "unsafe mutation", 3, True))

    system.actor_state[actor] = "escalated"

    system.run_proposal(system.make_proposal("A003", actor, "explorer", "local", "unsafe mutation", 1, True))
    system.run_proposal(system.make_proposal("A004", actor, "explorer", "local", "unsafe mutation", 1, True))

    # watch 1
    system.start_watch(actor, 2, "manual transition to demo watch 1")
    system.run_proposal(system.make_proposal("A031", actor, "explorer", "global", "watch violation", 4, True))
    system.run_proposal(system.make_proposal("A032", actor, "explorer", "local", "recovery proposal", 4, True))
    system.review_restoration(actor, approve=True)

    # watch 2
    system.run_proposal(system.make_proposal("A041", actor, "explorer", "local", "watch proposal", 4, True))
    system.run_proposal(system.make_proposal("A042", actor, "explorer", "local", "watch proposal", 4, True))
    system.run_proposal(system.make_proposal("A051", actor, "explorer", "global", "watch violation", 4, True))
    system.run_proposal(system.make_proposal("A052", actor, "explorer", "local", "recovery proposal", 4, True))
    system.review_restoration(actor, approve=True)

    # watch 3
    system.run_proposal(system.make_proposal("A061", actor, "explorer", "local", "watch proposal", 4, True))
    system.run_proposal(system.make_proposal("A062", actor, "explorer", "local", "watch proposal", 4, True))
    system.run_proposal(system.make_proposal("A063", actor, "explorer", "local", "watch proposal", 4, True))
    system.run_proposal(system.make_proposal("A064", actor, "explorer", "global", "terminal trigger", 4, True))

    system.show_actor_status(actor)

    # restoration without override (expected fail)
    system.review_restoration(actor, approve=True, oversight_override=False)

    # restoration with override
    system.review_restoration(actor, approve=True, oversight_override=True)

    # watch 4
    system.run_proposal(system.make_proposal("A081", actor, "explorer", "local", "override watch", 4, True))
    system.run_proposal(system.make_proposal("A082", actor, "explorer", "local", "override watch", 4, True))
    system.run_proposal(system.make_proposal("A083", actor, "explorer", "local", "override watch", 4, True))
    system.run_proposal(system.make_proposal("A084", actor, "explorer", "local", "override watch", 4, True))
    system.run_proposal(system.make_proposal("A085", actor, "explorer", "local", "override watch", 4, True))

    system.show_actor_status(actor)

    return system