"""Allow ``python -m iiif_rights_filter`` execution."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
