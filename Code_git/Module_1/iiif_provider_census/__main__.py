"""Allow the package to be executed with ``python -m iiif_provider_census``."""

from .cli import main

# Keep process exit codes consistent with the command-line interface.
raise SystemExit(main())
