"""Public interface for the Module 2 IIIF entry-point validator."""

from .checker import EndpointChecker
from .models import CheckedProviderRecord, EndpointCheck, ProviderInputRecord, RedirectHop
from .pipeline import PipelineResult, run_pipeline

__all__ = [
    "CheckedProviderRecord",
    "EndpointCheck",
    "EndpointChecker",
    "PipelineResult",
    "ProviderInputRecord",
    "RedirectHop",
    "run_pipeline",
]

__version__ = "0.1.0"

