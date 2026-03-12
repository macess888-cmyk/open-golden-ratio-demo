from ogr.scenarios import build_demo_system
from ogr.export import export_artifacts


def main():
    system = build_demo_system()

    # export artifacts into the artifacts folder
    export_artifacts(system, "artifacts")


if __name__ == "__main__":
    main()