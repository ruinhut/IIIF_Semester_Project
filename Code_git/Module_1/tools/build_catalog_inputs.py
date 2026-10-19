"""Build reproducible Module 1 inputs without discarding catalogue links."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit


GUIDES_SOURCE_URL = "https://guides.iiif.io/finding_resources/"
AWESOME_SOURCE_URL = "https://github.com/IIIF/awesome-iiif/blob/main/implementations.md"
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)(?:\s+[^)]*)?\)", re.IGNORECASE)
HTML_LINK = re.compile(r"<a\s+[^>]*href=[\"'](https?://[^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE)
RAW_URL = re.compile(r"""https?://[^\s<>\"']+""", re.IGNORECASE)


def _front_matter(path: Path) -> dict[str, str]:
    """Read the scalar subset of YAML used by the guide pages."""

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


def _document_links(path: Path) -> list[tuple[str, str]]:
    """Return every explicit absolute HTTP(S) link in source order."""

    text = path.read_text(encoding="utf-8-sig")
    matches: list[tuple[int, str, str]] = []
    for match in MARKDOWN_LINK.finditer(text):
        matches.append((match.start(), match.group(1).strip(), match.group(2).strip()))
    for match in HTML_LINK.finditer(text):
        label = re.sub(r"<[^>]+>", " ", match.group(2))
        matches.append((match.start(), " ".join(label.split()), match.group(1).strip()))
    for match in RAW_URL.finditer(text):
        url = match.group(0).rstrip(").,;:]}" + chr(96))
        matches.append((match.start(), "Literal source URL", url))
    matches.sort(key=lambda item: item[0])
    output: list[tuple[str, str]] = []
    seen: set[str] = set()
    for _, label, url in matches:
        if url not in seen:
            output.append((label or url, url))
            seen.add(url)
    return output


def _git_revision(repository: Path) -> str | None:
    """Return the exact source revision when input is a Git checkout."""

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


def _endpoint_role(label: str, url: str, *, is_homepage: bool = False) -> str:
    """Classify a route conservatively while keeping the role open-ended."""

    text = f"{label} {url}".casefold()
    if "change discovery" in text or "activity stream" in text or "/activity" in text:
        return "change_discovery"
    if "manifest" in text and ("{" in url or "}" in url):
        return "manifest_url_template"
    if "manifest" in text:
        return "manifest"
    if "collection" in text or "/iiif/presentation" in text:
        return "presentation_collection"
    if "api" in text:
        return "provider_api"
    if is_homepage:
        return "institution_website"
    return "related_resource"


def _discovery_type(role: str) -> str:
    return {
        "change_discovery": "OrderedCollection",
        "presentation_collection": "Collection",
        "manifest": "Manifest",
        "institution_website": "InstitutionWebsite",
        "provider_api": "ProviderAPI",
        "manifest_url_template": "ManifestURLTemplate",
    }.get(role, "RelatedResource")


def _endpoint_rows(
    links: Iterable[tuple[str, str]], *, homepage: str
) -> list[dict[str, object]]:
    """Create endpoint objects, retaining one row for every unique source URL."""

    ordered: list[tuple[str, str]] = [("Institution homepage", homepage)]
    ordered.extend(links)
    output: list[dict[str, object]] = []
    seen: set[str] = set()
    for label, url in ordered:
        if url in seen:
            continue
        parts = urlsplit(url)
        if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
            continue
        role = _endpoint_role(label, url, is_homepage=(url == homepage))
        output.append(
            {
                "url": url,
                "endpoint_role": role,
                "discovery_type": _discovery_type(role),
                "label": label,
                "verification_status": "pending_module_2",
            }
        )
        seen.add(url)
    return output


def build_guides_records(repository: Path) -> list[dict[str, object]]:
    """Extract visible official guide entries and every link in each entry."""

    guide_root = repository / "guides"
    records: list[dict[str, object]] = []
    for index_path in sorted(guide_root.glob("*/index.md")):
        metadata = _front_matter(index_path)
        title = metadata.get("title", "").strip()
        homepage = metadata.get("homepage", "").strip()
        if not title or not homepage or metadata.get("visible", "").casefold() == "no":
            continue
        slug = index_path.parent.name
        endpoints = _endpoint_rows(_document_links(index_path), homepage=homepage)
        records.append(
            {
                "name": title,
                "institution_url": homepage,
                "discovery_endpoint": endpoints[0]["url"],
                "discovery_type": endpoints[0]["discovery_type"],
                "endpoints": endpoints,
                "stream_label": "Official IIIF resource-guide entry",
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
    """Extract each Awesome IIIF entry and all links on its bullet line."""

    source_path = repository / "implementations.md"
    records: list[dict[str, object]] = []
    for line in source_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.lstrip().startswith("-"):
            continue
        links = [
            (match.group(1).strip(), match.group(2).strip())
            for match in MARKDOWN_LINK.finditer(line)
        ]
        if not links:
            continue
        name, homepage = links[0]
        endpoints = _endpoint_rows(links[1:], homepage=homepage)
        records.append(
            {
                "name": name,
                "institution_url": homepage,
                "discovery_endpoint": endpoints[0]["url"],
                "discovery_type": endpoints[0]["discovery_type"],
                "endpoints": endpoints,
                "stream_label": "Community-maintained IIIF Catalogue entry",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guides-repository", type=Path, required=True)
    parser.add_argument("--awesome-repository", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    return parser


def main() -> int:
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
