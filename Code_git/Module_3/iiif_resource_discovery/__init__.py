"""Public interface for Module 3 IIIF resource discovery."""

from .discovery import DiscoveryLimits, ProviderDiscovery, ResourceDiscoverer
from .fetch import FetchError, HttpFetcher
from .knowledge import ProviderKnowledge, knowledge_for_provider, read_knowledge_base
from .pipeline import PipelineResult, run_pipeline
from .skills import SkillExecution, ValidatedManifest, execute_skill

__all__ = [
    "DiscoveryLimits",
    "FetchError",
    "HttpFetcher",
    "PipelineResult",
    "ProviderKnowledge",
    "ProviderDiscovery",
    "ResourceDiscoverer",
    "SkillExecution",
    "ValidatedManifest",
    "execute_skill",
    "knowledge_for_provider",
    "read_knowledge_base",
    "run_pipeline",
]

__version__ = "0.3.0"
