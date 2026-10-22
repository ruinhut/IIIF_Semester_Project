"""Build and validate documentary knowledge from the official IIIF guides.

The official guides usually describe a human path from an item page to a
Manifest.  This module preserves those instructions as evidence and maps them
to reusable *candidate* skills.  It deliberately does not mark a candidate as
executable until Module 3 has validated a concrete recipe.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping, Optional, Sequence


OFFICIAL_GUIDE_KNOWLEDGE_VERSION = "1.0"
OFFICIAL_GUIDE_INDEX = "https://iiif.io/guides/finding_resources/"
OFFICIAL_GUIDE_REPOSITORY = "https://github.com/IIIF/guides"
NON_PROVIDER_GUIDE_SLUGS = {"personas"}

IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
ANGLE_URL_PATTERN = re.compile(r"<(?P<url>https?://[^>]+)>")
BARE_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
ACTION_WORDS = (
    "iiif",
    "manifest",
    "click",
    "copy",
    "scroll",
    "press",
    "open",
    "select",
    "filter",
    "search",
    "record",
    "item",
    "viewer",
    "api",
    "identifier",
    "url",
)


GENERIC_SKILLS: tuple[dict[str, Any], ...] = (
    {
        "skill_id": "filtered-search-result-enumeration",
        "description": "Traverse a provider's IIIF-filtered result pages and retain item-record URLs.",
        "implementation_status": "candidate",
    },
    {
        "skill_id": "record-page-manifest-link-extraction",
        "description": "Extract declared Manifest URLs from item-page links, data attributes, JSON-LD, metadata fields, and inline configuration.",
        "implementation_status": "partial",
    },
    {
        "skill_id": "viewer-configuration-manifest-extraction",
        "description": "Read Mirador, Universal Viewer, or custom-viewer configuration and request parameters to recover Manifest URLs.",
        "implementation_status": "candidate",
    },
    {
        "skill_id": "record-identifier-to-manifest-template",
        "description": "Transform a documented item identifier into one or more Manifest URL templates and validate every result.",
        "implementation_status": "implemented_as_part_of_paginated_json_identifiers_to_manifest_templates",
    },
    {
        "skill_id": "catalogue-api-identifier-enumeration",
        "description": "Page through a structured catalogue API, extract item identifiers, and hand them to a validated Manifest template.",
        "implementation_status": "implemented_as_paginated_json_identifiers_to_manifest_templates",
    },
    {
        "skill_id": "iiif-collection-traversal",
        "description": "Traverse Presentation 2/3 Collections and their pagination or child collections.",
        "implementation_status": "implemented",
    },
    {
        "skill_id": "wikidata-p6108-query",
        "description": "Query Wikidata property P6108 and validate returned Manifest URLs.",
        "implementation_status": "candidate",
    },
    {
        "skill_id": "image-api-filename-resolution",
        "description": "Resolve documented filename or identifier templates to IIIF Image API info.json resources without misclassifying them as Presentation Manifests.",
        "implementation_status": "candidate",
    },
    {
        "skill_id": "legacy-platform-route-review",
        "description": "Recheck redirects, replacement catalogues, archived documentation, and current APIs before encoding a route for a migrated site.",
        "implementation_status": "investigation_only",
    },
)


@dataclass(frozen=True)
class GuideDocument:
    """One visible provider guide parsed from the official repository."""

    slug: str
    title: str
    homepage: str
    consortium: str
    direct_url: Optional[str]
    action_texts: tuple[str, ...]
    screenshots: tuple[Mapping[str, str], ...]
    links: tuple[Mapping[str, str], ...]
    candidate_skill_ids: tuple[str, ...]


def parse_guide_file(path: Path) -> GuideDocument:
    """Parse one official guide without requiring a YAML or Markdown package."""

    text = path.read_text(encoding="utf-8-sig")
    metadata, body = _split_front_matter(text)
    title = metadata.get("title", "").strip()
    homepage = metadata.get("homepage", "").strip()
    if not title or not homepage:
        raise ValueError(f"Guide {path} requires title and homepage")
    screenshots = tuple(
        {"alt": alt.strip(), "path": target.strip()}
        for alt, target in IMAGE_PATTERN.findall(body)
    )
    links = _deduplicate_mappings(
        {"label": label, "url": url}
        for label, url in extract_markdown_links(body)
    )
    known_urls = {item["url"] for item in links}
    for url in _plain_urls(body):
        if url not in known_urls:
            links += ({"label": "literal URL", "url": url},)
            known_urls.add(url)
    actions = extract_action_texts(body, screenshots)
    skills = classify_candidate_skills(title, body, actions)
    return GuideDocument(
        slug=path.parent.name,
        title=title,
        homepage=homepage,
        consortium=metadata.get("consortium", "unknown").strip() or "unknown",
        direct_url=_optional_string(metadata.get("direct")),
        action_texts=actions,
        screenshots=screenshots,
        links=links,
        candidate_skill_ids=skills,
    )


def visible_provider_guides(repository: Path) -> list[GuideDocument]:
    """Return visible provider guides, excluding non-provider tutorials."""

    guide_root = repository / "guides"
    output: list[GuideDocument] = []
    for path in sorted(guide_root.glob("*/index.md")):
        if path.parent.name in NON_PROVIDER_GUIDE_SLUGS:
            continue
        metadata, _body = _split_front_matter(path.read_text(encoding="utf-8-sig"))
        if metadata.get("visible", "").strip().casefold() == "no":
            continue
        output.append(parse_guide_file(path))
    return output


def build_knowledge_base(
    repository: Path,
    *,
    provider_records: Sequence[Mapping[str, Any]],
    previous_results: Sequence[Mapping[str, Any]],
    executable_provider_ids: Iterable[str],
    checked_date: str,
) -> dict[str, Any]:
    """Build a provider knowledge file from official guides and local evidence."""

    providers_by_slug = _providers_by_guide_slug(provider_records)
    result_by_id = {
        str(item.get("provider_id")): item
        for item in previous_results
        if str(item.get("provider_id", "")).strip()
    }
    executable_ids = {str(value) for value in executable_provider_ids}
    entries: list[dict[str, Any]] = []
    for guide in visible_provider_guides(repository):
        provider = providers_by_slug.get(guide.slug)
        provider_id = str(provider.get("provider_id")) if provider else None
        previous = result_by_id.get(provider_id or "")
        previous_status = None
        if previous:
            previous_status = str(
                (previous.get("resource_discovery") or {}).get("status") or "unknown"
            )
        if provider_id in executable_ids:
            validation_state = "validated_executable_knowledge"
        elif previous_status == "manifests_found":
            validation_state = "previous_baseline_found_manifests"
        else:
            validation_state = "official_documented_candidate"
        evidence_links = list(guide.links)
        if guide.direct_url:
            evidence_links.insert(
                0, {"label": "front-matter direct example", "url": guide.direct_url}
            )
        entries.append(
            {
                "provider_id": provider_id,
                "provider_name": guide.title,
                "guide_slug": guide.slug,
                "guide_url": f"https://iiif.io/guides/{guide.slug}/",
                "homepage": guide.homepage,
                "consortium_status": guide.consortium,
                "official_actions": list(guide.action_texts),
                "official_evidence": {
                    "screenshots": list(guide.screenshots),
                    "links": evidence_links,
                },
                "candidate_skill_ids": list(guide.candidate_skill_ids),
                "validation_state": validation_state,
                "previous_module3_status": previous_status,
                "knowledge_rule": (
                    "Official instructions are documentary evidence. Candidate skills "
                    "must pass live HTTP, JSON, and IIIF validation before execution."
                ),
            }
        )
    return {
        "knowledge_base_version": OFFICIAL_GUIDE_KNOWLEDGE_VERSION,
        "knowledge_kind": "official_iiif_resource_guide_workflows",
        "checked_date": checked_date,
        "source": {
            "index_url": OFFICIAL_GUIDE_INDEX,
            "repository_url": OFFICIAL_GUIDE_REPOSITORY,
            "repository_revision": repository_revision(repository),
        },
        "generic_skills": list(GENERIC_SKILLS),
        "providers": entries,
    }


def validate_knowledge_base(value: Mapping[str, Any]) -> None:
    """Validate the stored documentary knowledge contract."""

    if value.get("knowledge_base_version") != OFFICIAL_GUIDE_KNOWLEDGE_VERSION:
        raise ValueError("official guide knowledge requires version 1.0")
    if value.get("knowledge_kind") != "official_iiif_resource_guide_workflows":
        raise ValueError("unexpected official guide knowledge kind")
    skills = value.get("generic_skills")
    providers = value.get("providers")
    if not isinstance(skills, list) or not skills:
        raise ValueError("generic_skills must be a non-empty array")
    skill_ids = {
        str(item.get("skill_id"))
        for item in skills
        if isinstance(item, Mapping) and str(item.get("skill_id", "")).strip()
    }
    if len(skill_ids) != len(skills):
        raise ValueError("generic skill IDs must be present and unique")
    if not isinstance(providers, list) or not providers:
        raise ValueError("providers must be a non-empty array")
    seen_slugs: set[str] = set()
    for index, provider in enumerate(providers):
        if not isinstance(provider, Mapping):
            raise ValueError(f"providers[{index}] must be an object")
        slug = str(provider.get("guide_slug", "")).strip()
        if not slug or slug in seen_slugs:
            raise ValueError(f"providers[{index}] has a missing or duplicate guide_slug")
        seen_slugs.add(slug)
        actions = provider.get("official_actions")
        candidate_ids = provider.get("candidate_skill_ids")
        if not isinstance(actions, list) or not actions:
            raise ValueError(f"providers[{index}] requires official_actions")
        if not isinstance(candidate_ids, list) or not candidate_ids:
            raise ValueError(f"providers[{index}] requires candidate_skill_ids")
        unknown = {str(item) for item in candidate_ids} - skill_ids
        if unknown:
            raise ValueError(f"providers[{index}] references unknown skills: {unknown}")


def write_knowledge_base(path: Path, value: Mapping[str, Any]) -> None:
    """Validate and write stable UTF-8 JSON."""

    validate_knowledge_base(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def write_markdown_inventory(path: Path, value: Mapping[str, Any]) -> None:
    """Write a human-readable provider-to-skill audit table."""

    validate_knowledge_base(value)
    source = value.get("source") if isinstance(value.get("source"), Mapping) else {}
    lines = [
        "# Official IIIF Provider Workflow and Skill Inventory",
        "",
        (
            f"Checked: `{_markdown_cell(value.get('checked_date'))}`; "
            f"source revision: `{_markdown_cell(source.get('repository_revision'))}`."
        ),
        "",
        (
            "This inventory transcribes official guide instructions into candidate "
            "skills. A candidate is not executable knowledge until its complete "
            "HTTP, JSON, and IIIF chain has been validated."
        ),
        "",
        "## Generic skill catalogue",
        "",
        "| Skill | Meaning | Status |",
        "|---|---|---|",
    ]
    for skill in value["generic_skills"]:
        lines.append(
            "| {skill} | {meaning} | {status} |".format(
                skill=_markdown_cell(skill.get("skill_id")),
                meaning=_markdown_cell(skill.get("description")),
                status=_markdown_cell(skill.get("implementation_status")),
            )
        )
    lines.extend(
        [
            "",
            "## Provider workflows",
            "",
            "| # | Provider | Officially documented operation | Candidate skills | Validation state |",
            "|---:|---|---|---|---|",
        ]
    )
    for index, provider in enumerate(value["providers"], 1):
        actions = provider.get("official_actions") or []
        action = _inventory_action(actions)
        if len(action) > 280:
            action = action[:277].rstrip() + "..."
        guide_url = str(provider.get("guide_url", ""))
        provider_name = _markdown_cell(provider.get("provider_name"))
        provider_cell = f"[{provider_name}]({guide_url})" if guide_url else provider_name
        lines.append(
            "| {index} | {provider} | {action} | {skills} | {state} |".format(
                index=index,
                provider=provider_cell,
                action=_markdown_cell(action),
                skills=_markdown_cell(", ".join(provider.get("candidate_skill_ids") or [])),
                state=_markdown_cell(provider.get("validation_state")),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[Mapping[str, Any]]:
    """Read JSON objects from a JSONL file."""

    rows: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, Mapping):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(dict(value))
    return rows


def executable_provider_ids(path: Optional[Path]) -> set[str]:
    """Read provider IDs already backed by executable Module 3 knowledge."""

    if path is None:
        return set()
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    providers = value.get("providers", []) if isinstance(value, Mapping) else []
    return {
        str(item.get("provider_id"))
        for item in providers
        if isinstance(item, Mapping) and str(item.get("provider_id", "")).strip()
    }


def extract_markdown_links(text: str) -> tuple[tuple[str, str], ...]:
    """Extract Markdown links while preserving balanced parentheses in URLs."""

    output: list[tuple[str, str]] = []
    index = 0
    while index < len(text):
        start = text.find("[", index)
        if start < 0:
            break
        if start > 0 and text[start - 1] == "!":
            index = start + 1
            continue
        label_end = text.find("](", start + 1)
        if label_end < 0:
            break
        label = text[start + 1 : label_end].strip()
        cursor = label_end + 2
        depth = 1
        url_parts: list[str] = []
        while cursor < len(text) and depth:
            char = text[cursor]
            if char == "(":
                depth += 1
                url_parts.append(char)
            elif char == ")":
                depth -= 1
                if depth:
                    url_parts.append(char)
            else:
                url_parts.append(char)
            cursor += 1
        if depth == 0:
            url = "".join(url_parts).strip().split(maxsplit=1)[0]
            if url.startswith(("http://", "https://")):
                output.append((label or "link", url))
        index = max(cursor, start + 1)
    deduplicated: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, url in output:
        if url not in seen:
            deduplicated.append((label, url))
            seen.add(url)
    return tuple(deduplicated)


def extract_action_texts(
    body: str,
    screenshots: Sequence[Mapping[str, str]],
) -> tuple[str, ...]:
    """Keep concise operation-bearing prose and screenshot alt text."""

    candidates: list[str] = [
        str(item.get("alt", "")).strip()
        for item in screenshots
        if str(item.get("alt", "")).strip()
    ]
    without_images = IMAGE_PATTERN.sub("", body)
    for paragraph in re.split(r"\n\s*\n", without_images):
        text = " ".join(line.strip() for line in paragraph.splitlines()).strip()
        text = re.sub(r"^#{1,6}\s+", "", text)
        text = re.sub(r"^(?:[-*]|\d+\.)\s+", "", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        for label, url in extract_markdown_links(text):
            text = text.replace(f"[{label}]({url})", f"{label} ({url})")
        text = re.sub(r"\s+", " ", text).strip()
        if text and any(word in text.casefold() for word in ACTION_WORDS):
            candidates.append(text[:800])
    output: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        normalized = re.sub(r"\s+", " ", value).strip(" -*\t")
        key = normalized.casefold()
        if normalized and key not in seen:
            output.append(normalized)
            seen.add(key)
    if not output:
        output.append("Open an item record and inspect the documented IIIF control.")
    return tuple(output)


def classify_candidate_skills(
    title: str,
    body: str,
    actions: Sequence[str],
) -> tuple[str, ...]:
    """Map official wording to reusable candidate skill identifiers."""

    text = " ".join((title, body, *actions)).casefold()
    output: list[str] = []

    def add(skill_id: str) -> None:
        if skill_id not in output:
            output.append(skill_id)

    image_api_only = (
        ("info.json" in text or "image service" in text)
        and "manifest" not in text
    )

    if "filter" in text and ("search" in text or "result" in text):
        add("filtered-search-result-enumeration")
    if not image_api_only and any(
        term in text
        for term in (
            "mirador",
            "universal viewer",
            "viewer",
            "share button",
            "information panel",
        )
    ):
        add("viewer-configuration-manifest-extraction")
    if any(term in text for term in ("suffix", "url structure", "url template", "add the .json", "place that identifier", "/manifest")):
        add("record-identifier-to-manifest-template")
    if any(
        term in text
        for term in (
            "api documentation",
            "api reference",
            "developer api",
            "developers",
            "catalogue api",
            "catalog api",
        )
    ):
        add("catalogue-api-identifier-enumeration")
    if "iiif collection" in text:
        add("iiif-collection-traversal")
    if "p6108" in text or "wikidata" in title.casefold():
        add("wikidata-p6108-query")
    if image_api_only or "info.json" in text:
        add("image-api-filename-resolution")
    if any(term in title.casefold() for term in ("world digitial library", "wellcome", "british library", "vatican")):
        add("legacy-platform-route-review")
    if any(term in text for term in ("record", "item", "copy", "click", "manifest", "iiif button", "iiif icon")):
        add("record-page-manifest-link-extraction")
    if not output:
        add("record-page-manifest-link-extraction")
    return tuple(output)


def repository_revision(repository: Path) -> str:
    """Return the checked-out Git commit when available."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _split_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}, text
    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, parts[2]


def _plain_urls(text: str) -> tuple[str, ...]:
    # Markdown targets are already parsed by ``extract_markdown_links``.  Scan
    # only the remaining prose here; otherwise ``[URL](URL)`` is captured a
    # second time as one malformed value containing ``](https://``.
    prose = _remove_markdown_links(text)
    values = [match.group("url") for match in ANGLE_URL_PATTERN.finditer(prose)]
    values.extend(match.group(0) for match in BARE_URL_PATTERN.finditer(prose))
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.rstrip(".,;]")
        while cleaned.endswith(")") and cleaned.count("(") < cleaned.count(")"):
            cleaned = cleaned[:-1]
        if "](" in cleaned:
            continue
        if cleaned not in seen:
            output.append(cleaned)
            seen.add(cleaned)
    return tuple(output)


def _remove_markdown_links(text: str) -> str:
    """Remove Markdown link targets while retaining their visible labels."""

    output: list[str] = []
    index = 0
    while index < len(text):
        start = text.find("[", index)
        if start < 0:
            output.append(text[index:])
            break
        image_start = start > 0 and text[start - 1] == "!"
        segment_start = start - 1 if image_start else start
        label_end = text.find("](", start + 1)
        if label_end < 0:
            output.append(text[index:])
            break
        cursor = label_end + 2
        depth = 1
        while cursor < len(text) and depth:
            if text[cursor] == "(":
                depth += 1
            elif text[cursor] == ")":
                depth -= 1
            cursor += 1
        if depth:
            output.append(text[index:])
            break
        output.append(text[index:segment_start])
        output.append(text[start + 1 : label_end])
        index = cursor
    return "".join(output)


def _providers_by_guide_slug(
    provider_records: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    output: dict[str, Mapping[str, Any]] = {}
    for provider in provider_records:
        source = provider.get("source")
        if not isinstance(source, Mapping):
            continue
        page_url = str(source.get("source_page_url", "")).rstrip("/")
        if "/guides/" not in page_url:
            continue
        output[page_url.rsplit("/", 1)[-1]] = provider
    return output


def _deduplicate_mappings(
    values: Iterable[Mapping[str, str]],
) -> tuple[Mapping[str, str], ...]:
    output: list[Mapping[str, str]] = []
    seen: set[str] = set()
    for value in values:
        url = str(value.get("url", ""))
        if url and url not in seen:
            output.append(dict(value))
            seen.add(url)
    return tuple(output)


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _markdown_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().replace("|", "\\|")


def _inventory_action(actions: Sequence[Any]) -> str:
    """Choose the most operational official sentence for the compact table."""

    values = [re.sub(r"\s+", " ", str(value)).strip() for value in actions]
    values = [value for value in values if value]
    if not values:
        return "No operation extracted"

    def score(value: str) -> tuple[int, int]:
        lower = value.casefold()
        points = 0
        points += 100 if "manifest" in lower else 0
        points += 60 if "iiif collection" in lower else 0
        points += 40 if "info.json" in lower else 0
        points += 20 * sum(
            term in lower
            for term in ("copy", "click", "scroll", "filter", "search", "identifier")
        )
        points += 15 if "api" in lower else 0
        points -= 40 if lower.startswith("screenshot") else 0
        points -= 20 if len(value.split()) < 4 else 0
        return points, min(len(value), 300)

    return max(values, key=score)
