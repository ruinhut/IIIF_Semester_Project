"""Allow Module 3 to run with ``python -m iiif_resource_discovery``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
