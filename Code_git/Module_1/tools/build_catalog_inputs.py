"""Build reproducible Module 1 inputs from two IIIF community catalogues.

The script reads local checkouts of the official IIIF Guides repository and
the community-maintained Awesome IIIF repository. It deliberately records the
catalogue landing page as an unverified entry point unless a catalogue itself
provides a confirmed machine discovery endpoint. Network and IIIF validation
belong to Module 2.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable


GUIDES_SOURCE_URL = "https://guides.iiif.io/finding_resources/"
AWESOME_SOURCE_URL = (
    "https://github.com/IIIF/awesome-iiif/blob/main/implementations.md"
)
MARKDOWN_LINK = re.compile(r"^- \[([^]]+)\]\(([^)]+)\)")


def _front_matter(path: Path) -> dict[str, str]:
    """Read the small scalar subset of YAML used by IIIF guide pages."""

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _git_revision(repository: Path) -> str | None:
    """Return the exact source revision when the input is a Git checkout."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def build_guides_records(repository: Path) -> list[dict[str, object]]:
    """Extract every visible resource entry from the official IIIF Guides."""

    guide_root = repository / "guides"
    records: list[dict[str, object]] = []
    for index_path in sorted(guide_root.glob("*/index.md")):
        metadata = _front_matter(index_path)
        title = metadata.get("title", "").strip()
        homepage = metadata.get("homepage", "").strip()
        if not title or not homepage or metadata.get("visible", "").casefold() == "no":
            continue

        slug = index_path.parent.name
        records.append(
            {
                "name": title,
                "institution_url": homepage,
                "discovery_endpoint": homepage,
                "discovery_type": "InstitutionWebsite",
                "stream_label": "IIIF resource entry; machine endpoint not yet verified",
                "collection_focus": None,
                "estimated_size": None,
                "rights_status": "unknown",
                "rights_values": [],
                "record_status": "active",
                "source_page_url": f"https://guides.iiif.io/guides/{slug}/",
                "catalog_entry_kind": "iiif_resource_guide",
                "endpoint_verification": "pending_module_2",
                "iiif_consortium_status": metadata.get("consortium") or None,
            }
        )
    return sorted(records, key=lambda item: str(item["name"]).casefold())


def build_awesome_records(repository: Path) -> list[dict[str, object]]:
    """Extract every implementation entry, including projects and tools.

    Awesome IIIF describes implementations rather than a strict institution
    registry. Keeping every entry avoids silently imposing a classification;
    downstream validation can identify which entries expose harvestable data.
    """

    source_path = repository / "implementations.md"
    records: list[dict[str, object]] = []
    for line in source_path.read_text(encoding="utf-8-sig").splitlines():
        match = MARKDOWN_LINK.match(line)
        if not match:
            continue
        name, homepage = (part.strip() for part in match.groups())
        records.append(
            {
                "name": name,
                "institution_url": homepage,
                "discovery_endpoint": homepage,
                "discovery_type": "ImplementationWebsite",
                "stream_label": "IIIF implementation entry; machine endpoint not yet verified",
                "collection_focus": None,
                "estimated_size": None,
                "rights_status": "unknown",
                "rights_values": [],
                "record_status": "active",
                "source_page_url": AWESOME_SOURCE_URL,
                "catalog_entry_kind": "awesome_iiif_implementation",
                "endpoint_verification": "pending_module_2",
            }
        )
    return sorted(records, key=lambda item: str(item["name"]).casefold())


def _write_catalog(
    path: Path,
    *,
    source_type: str,
    source_url: str,
    source_revision: str | None,
    providers: Iterable[dict[str, object]],
) -> int:
    """Write one UTF-8 catalogue snapshot and return its entry count."""

    provider_list = list(providers)
    document = {
        "source": {
            "source_type": source_type,
            "source_url": source_url,
            "source_revision": source_revision,
        },
        "providers": provider_list,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(provider_list)


def build_parser() -> argparse.ArgumentParser:
    """Define the local snapshot-builder command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guides-repository", type=Path, required=True)
    parser.add_argument("--awesome-repository", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    return parser


def main() -> int:
    """Generate both source snapshots and print auditable entry counts."""

    args = build_parser().parse_args()
    guide_records = build_guides_records(args.guides_repository)
    awesome_records = build_awesome_records(args.awesome_repository)
    guide_count = _write_catalog(
        args.output_directory / "iiif_guides_providers.json",
        source_type="iiif_official_resource_guide",
        source_url=GUIDES_SOURCE_URL,
        source_revision=_git_revision(args.guides_repository),
        providers=guide_records,
    )
    awesome_count = _write_catalog(
        args.output_directory / "awesome_iiif_providers.json",
        source_type="iiif_community_implementation_list",
        source_url=AWESOME_SOURCE_URL,
        source_revision=_git_revision(args.awesome_repository),
        providers=awesome_records,
    )
    print(json.dumps({"iiif_guides": guide_count, "awesome_iiif": awesome_count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
