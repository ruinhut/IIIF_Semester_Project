"""Allow Module 4 to run with python -m iiif_manifest_validator."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
