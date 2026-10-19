"""Allow python -m iiif_metadata_normalizer execution."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
