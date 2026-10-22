"""Conservative, auditable repairs of transport-identifiable Manifest fields."""

from copy import deepcopy
from typing import Any, Mapping

from .models import canonicalize_url


def infer_missing_manifest_id(document: Any, retrieved_url: str):
    """Fill only an absent top-level identifier, never overwrite a declared one.

    A successfully retrieved document already has a transport URL. Using that
    URL as its effective identifier does not invent content or page mappings.
    The caller must retain the original bytes and its strict validation result.
    Non-IIIF objects, malformed identifiers and unrelated errors are not repaired.
    """
    if not isinstance(document, Mapping):
        return document, []
    kind = document.get("type", document.get("@type"))
    if not isinstance(kind, str) or kind not in {"Manifest", "sc:Manifest"}:
        return document, []
    if any(key in document and document[key] not in (None, "") for key in ("id", "@id")):
        return document, []
    contexts = str(document.get("@context", ""))
    if "/presentation/2/" not in contexts and "/presentation/3/" not in contexts:
        return document, []
    identifier = canonicalize_url(retrieved_url)
    field = "id" if "/presentation/3/" in contexts else "@id"
    repaired = deepcopy(dict(document))
    repaired[field] = identifier
    patches = [{"operation": "infer_missing_manifest_id", "path": field,
                "value": identifier, "evidence": "successful_retrieval_final_url"}]
    return repaired, patches
