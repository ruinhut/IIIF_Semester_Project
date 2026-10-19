"""Public interface for the IIIF provider census and selection package.

Importing from this file gives callers the main data models and orchestration
functions without requiring knowledge of the package's internal file layout.
"""

# Re-export the small set of names that downstream modules are expected to use.
from .models import EndpointCandidate, ProviderRecord, SourceProvenance
from .pipeline import PipelineResult, run_pipeline
from .selector import SelectionCriteria, select_providers

__all__ = [
    "EndpointCandidate",
    "PipelineResult",
    "ProviderRecord",
    "SelectionCriteria",
    "SourceProvenance",
    "run_pipeline",
    "select_providers",
]

__version__ = "0.2.0"
