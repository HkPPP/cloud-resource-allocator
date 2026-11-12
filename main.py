"""Repository convenience entry point; run after editable installation."""
from cloud_scheduler.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
