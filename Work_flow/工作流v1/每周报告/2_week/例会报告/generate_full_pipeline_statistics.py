"""Generate reproducible statistics and charts for the 2026-09-28 full pipeline run."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[5]
CODE_ROOT = PROJECT_ROOT / "Code_git"

BLUE = "#3976B8"
LIGHT_BLUE = "#80ADD8"
ORANGE = "#E9832E"
GREEN = "#4D9A73"
RED = "#C94C4C"
GREY = "#7B8794"
PURPLE = "#8064A2"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_csv(path: Path, headers: list[str], rows: Iterable[Iterable[Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def percentage(numerator: int | float, denominator: int | float) -> float:
    return round(100.0 * numerator / denominator, 2) if denominator else 0.0


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def finish_axes(ax: plt.Axes, title: str, ylabel: str = "Count") -> None:
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D9E1E8", linewidth=0.7, alpha=0.75)
    ax.set_axisbelow(True)


def label_bars(ax: plt.Axes, bars: Any, *, suffix: str = "", decimals: int = 0) -> None:
    for bar in bars:
        value = bar.get_height()
        if decimals:
            text = f"{value:.{decimals}f}{suffix}"
        else:
            text = f"{int(round(value)):,}{suffix}"
        ax.annotate(
            text,
            (bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.savefig(REPORT_DIR / name, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlecolor": "#17324D",
            "axes.labelcolor": "#34495E",
            "xtick.color": "#34495E",
            "ytick.color": "#34495E",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )

    m1_dir = CODE_ROOT / "Module_1" / "data" / "output"
    m2_dir = CODE_ROOT / "Module_2" / "data" / "output"
    m3_dir = CODE_ROOT / "Module_3" / "data" / "output"
    m4_dir = CODE_ROOT / "Module_4" / "data" / "output"
    m5_dir = CODE_ROOT / "Module_5" / "data" / "output"
    m6_dir = CODE_ROOT / "Module_6" / "data" / "output"
    m7_dir = CODE_ROOT / "Module_7" / "data" / "output"

    providers = read_jsonl(m1_dir / "providers.jsonl")
    selected_providers = read_jsonl(m1_dir / "selected_providers.jsonl")
    m2_checked = read_jsonl(m2_dir / "checked_entry_points.jsonl")
    m3_provider_discovery = read_jsonl(m3_dir / "provider_discovery.jsonl")
    m3_resolved = read_jsonl(m3_dir / "resolved_endpoints.jsonl")
    manifest_urls = read_jsonl(m3_dir / "manifest_urls.jsonl")
    m4_valid = read_jsonl(m4_dir / "validated_manifests.jsonl")
    m4_inventory = read_jsonl(m4_dir / "manifest_resource_inventory.jsonl")
    m4_manual = read_jsonl(m4_dir / "manual_review.jsonl")
    m4_invalid = read_jsonl(m4_dir / "invalid_manifests.jsonl")
    m4_unavailable = read_jsonl(m4_dir / "unavailable_manifests.jsonl")
    m5_assessed = read_jsonl(m5_dir / "rights_assessed_manifests.jsonl")
    m5_allowed = read_jsonl(m5_dir / "allowed_manifests.jsonl")
    m5_excluded = read_jsonl(m5_dir / "excluded_manifests.jsonl")
    m5_allowed_resources = read_jsonl(m5_dir / "allowed_resource_inventory.jsonl")
    m6_records = read_jsonl(m6_dir / "normalized_records.jsonl")
    m6_resources = read_jsonl(m6_dir / "normalized_resources.jsonl")
    m6_failed = read_jsonl(m6_dir / "failed_records.jsonl")
    m7_records = read_jsonl(m7_dir / "common_records.jsonl")
    m7_media = read_jsonl(m7_dir / "common_media.jsonl")
    m7_rejected_records = read_jsonl(m7_dir / "rejected_records.jsonl")
    m7_rejected_media = read_jsonl(m7_dir / "rejected_media.jsonl")
    dataset_manifest = read_json(m7_dir / "dataset_manifest.json")

    pipeline_logs = sorted((CODE_ROOT / "Pipeline_Runner" / "data" / "log").glob("Pipeline_*.json"))
    if not pipeline_logs:
        raise FileNotFoundError("No pipeline execution log found")
    pipeline_log_path = pipeline_logs[-1]
    pipeline = read_json(pipeline_log_path)

    # Core counts and distributions.
    endpoint_count = sum(len(row.get("endpoints") or []) for row in selected_providers)
    m2_results = Counter(
        (row.get("endpoint_check") or {}).get("check_result", "unknown") for row in m2_checked
    )
    reachable_results = {"reachable_json", "reachable_non_json"}
    reachable_rows = [
        row for row in m2_checked
        if (row.get("endpoint_check") or {}).get("check_result") in reachable_results
    ]
    reachable_provider_ids = {row.get("provider_id") for row in reachable_rows if row.get("provider_id")}
    json_provider_ids = {
        row.get("provider_id")
        for row in m2_checked
        if (row.get("endpoint_check") or {}).get("check_result") == "reachable_json" and row.get("provider_id")
    }
    response_times = [
        float((row.get("endpoint_check") or {}).get("response_time_ms"))
        for row in m2_checked
        if isinstance((row.get("endpoint_check") or {}).get("response_time_ms"), (int, float))
    ]

    m3_statuses = Counter(
        (row.get("resource_discovery") or {}).get("status", "unknown")
        for row in m3_provider_discovery
    )
    resolved_provider_ids = {
        row.get("provider_id")
        for row in m3_provider_discovery
        if (row.get("resource_discovery") or {}).get("status") == "manifests_found"
    }
    method_counts = Counter(row.get("resolution_method", "unknown") for row in m3_resolved)
    issue_counts: Counter[str] = Counter()
    truncated_providers = 0
    for row in m3_provider_discovery:
        discovery = row.get("resource_discovery") or {}
        if discovery.get("truncated"):
            truncated_providers += 1
        issue_counts.update(issue.get("issue_type", "unknown") for issue in discovery.get("issues") or [])

    manifest_provider_counts: Counter[str] = Counter()
    manifest_provider_ids: defaultdict[str, set[str]] = defaultdict(set)
    for row in manifest_urls:
        for provider in row.get("providers") or []:
            name = provider.get("provider_name") or provider.get("provider_id") or "Unknown provider"
            manifest_provider_counts[name] += 1
            if provider.get("provider_id"):
                manifest_provider_ids[name].add(provider["provider_id"])

    m4_versions = Counter(
        str((row.get("structural_validation") or {}).get("presentation_version", "unknown"))
        for row in m4_valid
    )
    m4_canvas_count = sum(int((row.get("structural_validation") or {}).get("canvas_count") or 0) for row in m4_valid)
    m4_image_count = sum(int((row.get("structural_validation") or {}).get("image_body_count") or 0) for row in m4_valid)
    m4_service_count = sum(int((row.get("structural_validation") or {}).get("image_service_count") or 0) for row in m4_valid)
    m4_bytes = sum(int((row.get("raw_manifest") or {}).get("response_bytes") or 0) for row in m4_valid)
    m4_response_times = [
        float((row.get("raw_manifest") or {}).get("response_time_ms"))
        for row in m4_valid
        if isinstance((row.get("raw_manifest") or {}).get("response_time_ms"), (int, float))
    ]

    rights_categories = Counter(
        (row.get("rights_assessment") or {}).get("category", "unknown") for row in m5_assessed
    )
    rights_decisions = Counter(
        (row.get("rights_assessment") or {}).get("decision", "unknown") for row in m5_assessed
    )

    quality_counts = Counter((row.get("quality") or {}).get("status", "unknown") for row in m6_records)
    normalized_field_presence = Counter()
    normalized_field_names = ["title", "description", "creators", "dates", "places", "languages", "subjects", "types"]
    for row in m6_records:
        metadata = row.get("normalized_metadata") or {}
        for field in normalized_field_names:
            value = metadata.get(field)
            if field in {"title", "description"}:
                present = bool((value or {}).get("preferred")) if isinstance(value, dict) else bool(value)
            else:
                present = bool(value)
            if present:
                normalized_field_presence[field] += 1

    final_rights = Counter((row.get("rights") or {}).get("category", "unknown") for row in m7_records)
    final_versions = Counter(
        str((row.get("source") or {}).get("presentation_version", "unknown")) for row in m7_records
    )
    final_provider_records: Counter[str] = Counter()
    final_provider_media: Counter[str] = Counter()
    record_provider_names: dict[str, set[str]] = defaultdict(set)
    for row in m7_records:
        record_id = row.get("record_id")
        for provider in (row.get("source") or {}).get("providers") or []:
            name = provider.get("provider_name") or provider.get("provider_id") or "Unknown provider"
            final_provider_records[name] += 1
            if record_id:
                record_provider_names[record_id].add(name)
    for row in m7_media:
        names = record_provider_names.get(row.get("record_id"), {"Unknown provider"})
        for name in names:
            final_provider_media[name] += 1
    media_per_record = Counter(row.get("record_id") for row in m7_media)
    media_counts = list(media_per_record.values())

    module_durations: list[tuple[int, str, float]] = []
    for result in pipeline["module_results"]:
        start = datetime.fromisoformat(result["started_at"])
        end = datetime.fromisoformat(result["finished_at"])
        module_durations.append((result["number"], result["name"], (end - start).total_seconds()))

    io_rows = [
        [1, "Providers / endpoints", len(providers), endpoint_count, len(selected_providers), endpoint_count, "providers.jsonl; selected_providers.jsonl"],
        [2, "Endpoints", len(m2_checked), len(m2_checked), len(reachable_rows), len(reachable_provider_ids), "checked_entry_points.jsonl; discovery_ready.jsonl"],
        [3, "Providers / Manifests", len(m3_provider_discovery), len(m2_checked), len(manifest_urls), len(resolved_provider_ids), "manifest_urls.jsonl; provider_discovery.jsonl"],
        [4, "Manifests / media inventory", len(manifest_urls), len(manifest_urls), len(m4_valid), len(m4_inventory), "validated_manifests.jsonl; manifest_resource_inventory.jsonl"],
        [5, "Valid Manifests / allowed media", len(m4_valid), len(m4_inventory), len(m5_allowed), len(m5_allowed_resources), "allowed_manifests.jsonl; allowed_resource_inventory.jsonl"],
        [6, "Allowed Manifests / media", len(m5_allowed), len(m5_allowed_resources), len(m6_records), len(m6_resources), "normalized_records.jsonl; normalized_resources.jsonl"],
        [7, "Normalized records / media", len(m6_records), len(m6_resources), len(m7_records), len(m7_media), "common_records.jsonl; common_media.jsonl; CSV; schemas"],
    ]
    write_csv(
        REPORT_DIR / "module_input_output_counts.csv",
        ["module", "entity_basis", "primary_input_count", "secondary_input_count", "primary_usable_output_count", "secondary_usable_output_count", "main_outputs"],
        io_rows,
    )

    rates = [
        ["Endpoint HTTP success", len(reachable_rows), len(m2_checked), percentage(len(reachable_rows), len(m2_checked)), "reachable JSON or non-JSON endpoints / checked endpoints"],
        ["Provider reachability", len(reachable_provider_ids), len(selected_providers), percentage(len(reachable_provider_ids), len(selected_providers)), "providers with >=1 reachable endpoint / selected providers"],
        ["Provider JSON availability", len(json_provider_ids), len(selected_providers), percentage(len(json_provider_ids), len(selected_providers)), "providers with >=1 parseable JSON endpoint / selected providers"],
        ["Provider discovery success", len(resolved_provider_ids), len(m3_provider_discovery), percentage(len(resolved_provider_ids), len(m3_provider_discovery)), "providers yielding >=1 Manifest / processed providers"],
        ["Manifest structural validity", len(m4_valid), len(manifest_urls), percentage(len(m4_valid), len(manifest_urls)), "valid Manifests / discovered Manifest URLs"],
        ["Rights retention", len(m5_allowed), len(m5_assessed), percentage(len(m5_allowed), len(m5_assessed)), "allowed Manifests / rights-assessed Manifests"],
        ["Normalization success", len(m6_records), len(m5_allowed), percentage(len(m6_records), len(m5_allowed)), "normalized records / allowed Manifests"],
        ["Complete normalized records", quality_counts.get("complete", 0), len(m6_records), percentage(quality_counts.get("complete", 0), len(m6_records)), "complete normalized records / normalized records"],
        ["Final record acceptance", len(m7_records), len(m6_records), percentage(len(m7_records), len(m6_records)), "schema-valid final records / normalized records"],
        ["Final media acceptance", len(m7_media), len(m6_resources), percentage(len(m7_media), len(m6_resources)), "schema-valid final media / normalized media"],
        ["End-to-end object yield", len(m7_records), len(manifest_urls), percentage(len(m7_records), len(manifest_urls)), "final records / discovered Manifest URLs"],
    ]
    write_csv(REPORT_DIR / "pipeline_success_metrics.csv", ["metric", "numerator", "denominator", "rate_percent", "definition"], rates)
    write_csv(
        REPORT_DIR / "module3_manifest_yield_by_provider.csv",
        ["provider", "manifest_count"],
        manifest_provider_counts.most_common(),
    )
    write_csv(
        REPORT_DIR / "module5_rights_categories.csv",
        ["category", "manifest_count", "share_percent"],
        [[key, value, percentage(value, len(m5_assessed))] for key, value in rights_categories.most_common()],
    )
    write_csv(
        REPORT_DIR / "module6_field_completeness.csv",
        ["field", "present_count", "record_count", "completeness_percent"],
        [[field, normalized_field_presence[field], len(m6_records), percentage(normalized_field_presence[field], len(m6_records))] for field in normalized_field_names],
    )
    write_csv(
        REPORT_DIR / "module7_provider_statistics.csv",
        ["provider", "object_records", "media_records"],
        [[name, final_provider_records[name], final_provider_media[name]] for name in sorted(final_provider_records, key=lambda n: (-final_provider_records[n], n))],
    )

    # 01: Comparable stage counts in two panels.
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    left_labels = ["Selected\nproviders", "Candidate\nendpoints", "Reachable\nproviders", "Manifest-yielding\nproviders"]
    left_values = [len(selected_providers), endpoint_count, len(reachable_provider_ids), len(resolved_provider_ids)]
    bars = axes[0].bar(left_labels, left_values, color=[BLUE, LIGHT_BLUE, GREEN, ORANGE], width=0.62)
    finish_axes(axes[0], "Provider and endpoint throughput")
    label_bars(axes[0], bars)
    axes[0].set_ylim(0, max(left_values) * 1.2)

    right_labels = ["Discovered", "Structurally\nvalid", "Rights\nallowed", "Normalized", "Final\naccepted"]
    right_values = [len(manifest_urls), len(m4_valid), len(m5_allowed), len(m6_records), len(m7_records)]
    bars = axes[1].bar(right_labels, right_values, color=[BLUE, GREEN, ORANGE, PURPLE, GREEN], width=0.62)
    finish_axes(axes[1], "Manifest/object throughput")
    label_bars(axes[1], bars)
    axes[1].set_ylim(0, max(right_values) * 1.2)
    fig.suptitle("Full pipeline throughput (2026-09-28)", fontsize=16, fontweight="bold", color="#17324D")
    fig.tight_layout()
    save_figure(fig, "01_pipeline_throughput.png")

    # 02: Success rates.
    chart_rates = rates[:10]
    labels = [row[0] for row in chart_rates]
    values = [row[3] for row in chart_rates]
    colors = [GREEN if value >= 80 else ORANGE if value >= 50 else RED for value in values]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1])
    ax.set_xlim(0, 108)
    ax.set_xlabel("Rate (%)")
    ax.set_title("Pipeline success and retention metrics", loc="left", fontsize=15, fontweight="bold", pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#D9E1E8", linewidth=0.7)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values[::-1]):
        ax.text(value + 1.2, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%", va="center", fontsize=9, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, "02_success_and_retention_rates.png")

    # 03: Module 2 outcomes.
    m2_order = ["reachable_non_json", "reachable_json", "restricted", "unreachable", "temporary_failure", "response_too_large", "invalid_json"]
    m2_labels = ["Reachable HTML/other", "Reachable JSON", "Restricted", "Unreachable", "Temporary failure", "Too large", "Invalid JSON"]
    m2_values = [m2_results.get(key, 0) for key in m2_order]
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    bars = ax.bar(m2_labels, m2_values, color=[GREEN, BLUE, ORANGE, RED, GREY, PURPLE, RED])
    finish_axes(ax, "Module 2 endpoint check outcomes")
    label_bars(ax, bars)
    ax.tick_params(axis="x", rotation=25)
    ax.set_ylim(0, max(m2_values) * 1.18)
    fig.tight_layout()
    save_figure(fig, "03_module2_endpoint_outcomes.png")

    # 04: Module 3 provider yield.
    provider_items = manifest_provider_counts.most_common()
    provider_labels = [name if len(name) <= 38 else name[:35] + "..." for name, _ in provider_items]
    provider_values = [count for _, count in provider_items]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={"width_ratios": [1, 2.25]})
    status_values = [m3_statuses.get("manifests_found", 0), m3_statuses.get("unresolved", 0)]
    bars = axes[0].bar(["Manifests found", "Unresolved"], status_values, color=[GREEN, RED], width=0.6)
    finish_axes(axes[0], "Provider outcomes")
    label_bars(axes[0], bars)
    axes[0].tick_params(axis="x", rotation=15)
    y = np.arange(len(provider_labels))
    bars = axes[1].barh(y, provider_values, color=BLUE)
    axes[1].set_yticks(y, provider_labels)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Unique Manifest URLs")
    axes[1].set_title("Manifest yield by successful provider", loc="left", fontsize=13, fontweight="bold", pad=12)
    axes[1].spines[["top", "right", "left"]].set_visible(False)
    axes[1].grid(axis="x", color="#D9E1E8", linewidth=0.7)
    axes[1].set_axisbelow(True)
    for bar, value in zip(bars, provider_values):
        axes[1].text(value + max(provider_values or [1]) * 0.012, bar.get_y() + bar.get_height() / 2, f"{value:,}", va="center", fontsize=8.5)
    fig.suptitle("Module 3 discovery performance", fontsize=16, fontweight="bold", color="#17324D")
    fig.tight_layout()
    save_figure(fig, "04_module3_discovery_performance.png")

    # 05: Module 4 resource inventory.
    fig, ax = plt.subplots(figsize=(10, 5.4))
    labels = ["Valid\nManifests", "Canvases", "Image\nbodies", "Image\nservices"]
    values = [len(m4_valid), m4_canvas_count, m4_image_count, m4_service_count]
    bars = ax.bar(labels, values, color=[BLUE, LIGHT_BLUE, GREEN, PURPLE], width=0.6)
    finish_axes(ax, "Module 4 validated resource inventory")
    label_bars(ax, bars)
    ax.set_yscale("log")
    ax.set_ylabel("Count (log scale)")
    ax.set_ylim(100, max(values) * 2.2)
    fig.tight_layout()
    save_figure(fig, "05_module4_resource_inventory.png")

    # 06: Module 5 decisions and categories.
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    decision_labels = ["Allowed", "Excluded"]
    decision_values = [rights_decisions.get("allow", 0), rights_decisions.get("exclude", 0)]
    bars = axes[0].bar(decision_labels, decision_values, color=[GREEN, RED], width=0.6)
    finish_axes(axes[0], "Policy decision")
    label_bars(axes[0], bars)
    cat_items = rights_categories.most_common()
    cat_labels = [key.replace("_", " ").title() for key, _ in cat_items]
    cat_values = [value for _, value in cat_items]
    bars = axes[1].bar(cat_labels, cat_values, color=[GREY, ORANGE, GREEN, BLUE, RED, PURPLE, LIGHT_BLUE][: len(cat_values)])
    finish_axes(axes[1], "Detected rights category")
    label_bars(axes[1], bars)
    axes[1].tick_params(axis="x", rotation=30)
    fig.suptitle("Module 5 rights assessment", fontsize=16, fontweight="bold", color="#17324D")
    fig.tight_layout()
    save_figure(fig, "06_module5_rights_statistics.png")

    # 07: Module 6 field completeness.
    completeness = [percentage(normalized_field_presence[field], len(m6_records)) for field in normalized_field_names]
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    bars = ax.bar([field.title() for field in normalized_field_names], completeness, color=BLUE)
    finish_axes(ax, "Module 6 normalized-field completeness", "Records with field (%)")
    label_bars(ax, bars, suffix="%", decimals=1)
    ax.set_ylim(0, 112)
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    save_figure(fig, "07_module6_field_completeness.png")

    # 08: Module 7 final output and media distribution.
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    final_labels = ["Valid objects", "Rejected objects", "Valid media", "Rejected media"]
    final_values = [len(m7_records), len(m7_rejected_records), len(m7_media), len(m7_rejected_media)]
    bars = axes[0].bar(final_labels, final_values, color=[GREEN, RED, BLUE, RED], width=0.62)
    finish_axes(axes[0], "Schema-validation result")
    label_bars(axes[0], bars)
    axes[0].tick_params(axis="x", rotation=18)
    if media_counts:
        bins = np.arange(0.5, max(media_counts) + 1.5, 1)
        axes[1].hist(media_counts, bins=bins, color=BLUE, edgecolor="white")
    finish_axes(axes[1], "Media records per object", "Object records")
    axes[1].set_xlabel("Media records linked to one object")
    fig.suptitle("Module 7 final dataset statistics", fontsize=16, fontweight="bold", color="#17324D")
    fig.tight_layout()
    save_figure(fig, "08_module7_final_dataset.png")

    # 09: Runtime.
    duration_labels = [f"M{number}" for number, _, _ in module_durations]
    duration_values = [seconds for _, _, seconds in module_durations]
    plotted_durations = [seconds if seconds >= 1 else 0.5 for seconds in duration_values]
    fig, ax = plt.subplots(figsize=(10, 5.3))
    bars = ax.bar(duration_labels, plotted_durations, color=[BLUE, LIGHT_BLUE, ORANGE, PURPLE, GREEN, GREY, BLUE])
    finish_axes(ax, "Execution time by module", "Seconds")
    for bar, seconds in zip(bars, duration_values):
        label = f"{int(seconds):,}" if seconds >= 1 else "<1"
        ax.annotate(label, (bar.get_x() + bar.get_width() / 2, bar.get_height()), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylabel("Seconds (log scale)")
    ax.set_ylim(0.5, max(duration_values) * 2.5)
    fig.tight_layout()
    save_figure(fig, "09_module_execution_time.png")

    # Machine-readable consolidated metrics.
    metrics = {
        "run": {
            "status": pipeline["status"],
            "started_at": pipeline["started_at"],
            "finished_at": pipeline["finished_at"],
            "elapsed_seconds": (
                datetime.fromisoformat(pipeline["finished_at"]) - datetime.fromisoformat(pipeline["started_at"])
            ).total_seconds(),
            "pipeline_log": str(pipeline_log_path),
            "module_return_codes": {str(item["number"]): item["return_code"] for item in pipeline["module_results"]},
            "module_durations_seconds": {str(number): seconds for number, _, seconds in module_durations},
        },
        "module_1": {"providers": len(providers), "selected_providers": len(selected_providers), "endpoints": endpoint_count},
        "module_2": {
            "checked_endpoints": len(m2_checked),
            "result_counts": dict(m2_results),
            "reachable_endpoints": len(reachable_rows),
            "reachable_providers": len(reachable_provider_ids),
            "json_providers": len(json_provider_ids),
            "response_time_ms": {
                "median": round(statistics.median(response_times), 2) if response_times else None,
                "p90": round(percentile(response_times, 0.9) or 0, 2) if response_times else None,
                "max": round(max(response_times), 2) if response_times else None,
            },
        },
        "module_3": {
            "processed_providers": len(m3_provider_discovery),
            "status_counts": dict(m3_statuses),
            "resolved_endpoints": len(m3_resolved),
            "resolution_methods": dict(method_counts),
            "unique_manifests": len(manifest_urls),
            "manifest_yield_by_provider": dict(manifest_provider_counts),
            "truncated_provider_runs": truncated_providers,
            "top_issue_types": dict(issue_counts.most_common(15)),
        },
        "module_4": {
            "input_manifests": len(manifest_urls),
            "valid_manifests": len(m4_valid),
            "manual_review": len(m4_manual),
            "invalid": len(m4_invalid),
            "unavailable": len(m4_unavailable),
            "presentation_versions": dict(m4_versions),
            "canvases": m4_canvas_count,
            "image_bodies": m4_image_count,
            "image_services": m4_service_count,
            "inventory_rows": len(m4_inventory),
            "downloaded_bytes": m4_bytes,
            "response_time_ms": {
                "median": round(statistics.median(m4_response_times), 2) if m4_response_times else None,
                "p90": round(percentile(m4_response_times, 0.9) or 0, 2) if m4_response_times else None,
                "max": round(max(m4_response_times), 2) if m4_response_times else None,
            },
        },
        "module_5": {
            "assessed": len(m5_assessed),
            "decisions": dict(rights_decisions),
            "categories": dict(rights_categories),
            "allowed_resources": len(m5_allowed_resources),
        },
        "module_6": {
            "normalized_records": len(m6_records),
            "normalized_resources": len(m6_resources),
            "failed_records": len(m6_failed),
            "quality": dict(quality_counts),
            "field_presence": dict(normalized_field_presence),
        },
        "module_7": {
            "valid_records": len(m7_records),
            "rejected_records": len(m7_rejected_records),
            "valid_media": len(m7_media),
            "rejected_media": len(m7_rejected_media),
            "rights_categories": dict(final_rights),
            "presentation_versions": dict(final_versions),
            "provider_object_counts": dict(final_provider_records),
            "provider_media_counts": dict(final_provider_media),
            "media_per_record": {
                "mean": round(statistics.mean(media_counts), 2) if media_counts else 0,
                "median": round(statistics.median(media_counts), 2) if media_counts else 0,
                "min": min(media_counts) if media_counts else 0,
                "max": max(media_counts) if media_counts else 0,
            },
            "dataset_manifest": dataset_manifest,
        },
        "success_metrics": [
            {"metric": row[0], "numerator": row[1], "denominator": row[2], "rate_percent": row[3], "definition": row[4]}
            for row in rates
        ],
    }
    with (REPORT_DIR / "full_pipeline_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, ensure_ascii=False, indent=2)

    print(json.dumps({
        "report_directory": str(REPORT_DIR),
        "pipeline_log": str(pipeline_log_path),
        "counts": {
            "providers": len(selected_providers),
            "endpoints": len(m2_checked),
            "reachable_providers": len(reachable_provider_ids),
            "manifest_providers": len(resolved_provider_ids),
            "manifests": len(manifest_urls),
            "valid_manifests": len(m4_valid),
            "allowed_manifests": len(m5_allowed),
            "final_records": len(m7_records),
            "final_media": len(m7_media),
        },
        "charts": 9,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
