"""Allow Module 2 to run with ``python -m iiif_entry_validator``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
