"""Tests for the persistent Module 3 knowledge base."""

import json
from pathlib import Path
import tempfile

from iiif_resource_discovery.knowledge import (
    knowledge_for_provider,
    read_knowledge_base,
)


def test_knowledge_base_reads_and_matches_provider_id_first():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "knowledge.json"
        path.write_text(
            json.dumps({
                "knowledge_base_version": "1.0",
                "providers": [{
                    "provider_id": "provider-1",
                    "provider_name": "Example",
                    "investigation_id": "investigation-1",
                    "skills": [{"skill_id": "s1", "type": "example"}],
                }],
            }),
            encoding="utf-8",
        )
        entries = read_knowledge_base(path)

    match = knowledge_for_provider("provider-1", "Renamed Example", entries)
    assert match is not None
    assert match.investigation_id == "investigation-1"
    assert match.skills[0]["skill_id"] == "s1"


def test_knowledge_base_matches_exact_provider_name_as_fallback():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "knowledge.json"
        path.write_text(
            json.dumps({
                "knowledge_base_version": "1.0",
                "providers": [{
                    "provider_name": "Example Library",
                    "investigation_id": "investigation-2",
                    "skills": [{"skill_id": "s2", "type": "example"}],
                }],
            }),
            encoding="utf-8",
        )
        entries = read_knowledge_base(path)

    assert knowledge_for_provider(
        "different-id", "example library", entries
    ) is not None
