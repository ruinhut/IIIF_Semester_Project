"""Tests for importing documentary knowledge from the official IIIF guides."""

import json
from pathlib import Path
import tempfile

from iiif_resource_discovery.official_guide_knowledge import (
    build_knowledge_base,
    extract_markdown_links,
    parse_guide_file,
    validate_knowledge_base,
)


def test_markdown_link_parser_preserves_parentheses_in_url():
    links = extract_markdown_links(
        "[Example](https://commons.wikimedia.org/wiki/File:Example_(Test).jpg)"
    )
    assert links == (
        (
            "Example",
            "https://commons.wikimedia.org/wiki/File:Example_(Test).jpg",
        ),
    )


def test_guide_parser_does_not_duplicate_markdown_target_as_malformed_url():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "wikipedia.org" / "index.md"
        path.parent.mkdir()
        path.write_text(
            """---
title: Wikipedia
homepage: https://www.wikipedia.org/
layout: guide
---

[https://commons.wikimedia.org/wiki/File:Example_(Test).jpg](https://commons.wikimedia.org/wiki/File:Example_(Test).jpg)
""",
            encoding="utf-8",
        )
        guide = parse_guide_file(path)

    urls = [item["url"] for item in guide.links]
    assert urls == ["https://commons.wikimedia.org/wiki/File:Example_(Test).jpg"]
    assert all("](" not in url for url in urls)


def test_image_api_only_guide_is_not_classified_as_manifest_viewer_skill():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "wikipedia.org" / "index.md"
        path.parent.mkdir()
        path.write_text(
            """---
title: Wikipedia
homepage: https://www.wikipedia.org/
layout: guide
---

Open the zoomviewer Image API URL and create its info.json from the filename.
""",
            encoding="utf-8",
        )
        guide = parse_guide_file(path)

    assert "image-api-filename-resolution" in guide.candidate_skill_ids
    assert "viewer-configuration-manifest-extraction" not in guide.candidate_skill_ids


def test_guide_parser_collects_actions_evidence_and_skills():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "plume.epfl.ch" / "index.md"
        path.parent.mkdir()
        path.write_text(
            """---
title: EPFL Plume
consortium: full
homepage: https://plume.example/
layout: guide
---

![Copy the IIIF link towards the bottom of the item page](epfl.png)
""",
            encoding="utf-8",
        )
        guide = parse_guide_file(path)

    assert guide.title == "EPFL Plume"
    assert guide.action_texts == (
        "Copy the IIIF link towards the bottom of the item page",
    )
    assert "record-page-manifest-link-extraction" in guide.candidate_skill_ids
    assert guide.screenshots[0]["path"] == "epfl.png"


def test_build_knowledge_excludes_tutorial_and_preserves_validation_state():
    with tempfile.TemporaryDirectory() as directory:
        repository = Path(directory)
        guide = repository / "guides" / "example.org" / "index.md"
        guide.parent.mkdir(parents=True)
        guide.write_text(
            """---
title: Example Library
consortium: no
homepage: https://example.org/
layout: guide
---
Copy the IIIF Manifest link from an item record.
""",
            encoding="utf-8",
        )
        tutorial = repository / "guides" / "personas" / "index.md"
        tutorial.parent.mkdir(parents=True)
        tutorial.write_text(
            """---
title: Guide to personas
homepage: https://example.org/personas
layout: guide
---
Tutorial.
""",
            encoding="utf-8",
        )
        value = build_knowledge_base(
            repository,
            provider_records=[
                {
                    "provider_id": "provider-1",
                    "name": "Example Library",
                    "source": {
                        "source_page_url": "https://iiif.io/guides/example.org/"
                    },
                }
            ],
            previous_results=[
                {
                    "provider_id": "provider-1",
                    "resource_discovery": {"status": "unresolved"},
                }
            ],
            executable_provider_ids={"provider-1"},
            checked_date="2026-10-08",
        )

    validate_knowledge_base(value)
    assert len(value["providers"]) == 1
    assert value["providers"][0]["provider_id"] == "provider-1"
    assert value["providers"][0]["validation_state"] == "validated_executable_knowledge"
    assert json.loads(json.dumps(value))["checked_date"] == "2026-10-08"
