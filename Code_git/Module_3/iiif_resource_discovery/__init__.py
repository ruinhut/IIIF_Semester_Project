"""Public interface for Module 3 IIIF resource discovery."""

from .discovery import DiscoveryLimits, ProviderDiscovery, ResourceDiscoverer
from .fetch import FetchError, HttpFetcher
from .pipeline import PipelineResult, run_pipeline

__all__ = [
    "DiscoveryLimits",
    "FetchError",
    "HttpFetcher",
    "PipelineResult",
    "ProviderDiscovery",
    "ResourceDiscoverer",
    "run_pipeline",
]

__version__ = "0.1.0"

