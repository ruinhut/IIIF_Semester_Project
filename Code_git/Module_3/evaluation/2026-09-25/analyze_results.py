from collections import Counter
import csv
import json
from pathlib import Path
import textwrap

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def load(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def summarize(split):
    base = ROOT / "runs" / split
    reports = load(base / "module3/output/provider_discovery.jsonl")
    checks = load(base / "module2/output/checked_entry_points.jsonl")
    manifests = load(base / "module3/output/manifest_urls.jsonl")
    successful = [
        row for row in reports
        if row["resource_discovery"]["status"] == "manifests_found"
    ]
    reachable_ids = {
        row["provider_id"] for row in checks
        if row["endpoint_check"]["check_result"]
        in {"reachable_json", "reachable_non_json", "invalid_json"}
    }
    json_ids = {
        row["provider_id"] for row in checks
        if row["endpoint_check"]["check_result"] == "reachable_json"
    }
    return {
        "provider_count": len(reports),
        "endpoint_count": len(checks),
        "reachable_provider_count": len(reachable_ids),
        "json_provider_count": len(json_ids),
        "successful_provider_count": len(successful),
        "success_rate": len(successful) / len(reports),
        "reachable_success_rate": (
            len(successful) / len(reachable_ids) if reachable_ids else 0
        ),
        "unique_manifest_count": len(manifests),
        "check_results": dict(sorted(Counter(
            row["endpoint_check"]["check_result"] for row in checks
        ).items())),
        "successful_providers": [
            {
                "name": row["name"],
                "manifest_count": row["resource_discovery"]["manifest_count"],
            }
            for row in sorted(successful, key=lambda item: item["name"].casefold())
        ],
    }


def test_provider_rows():
    path = ROOT / "runs/test/module3/output/provider_discovery.jsonl"
    rows = []
    for report in load(path):
        discovery = report["resource_discovery"]
        routes = report.get("endpoint_checks", [])
        roles = sorted({
            str(route.get("endpoint_candidate", {}).get(
                "endpoint_role", "unclassified"
            ))
            for route in routes
        })
        checks = [
            str(route.get("endpoint_check", {}).get(
                "check_result", "unknown"
            ))
            for route in routes
        ]
        methods = sorted({
            str(item.get("resolution_method", "unknown"))
            for item in discovery.get("resolved_endpoints", [])
        })
        issues = Counter(
            str(item.get("issue_type", "unknown"))
            for item in discovery.get("issues", [])
        )
        row = {
            "provider_id": report["provider_id"],
            "name": report["name"],
            "endpoint_count": len(routes),
            "endpoint_roles": " | ".join(roles),
            "module_2_results": " | ".join(sorted(set(checks))),
            "reachable_endpoint_count": sum(
                value in {"reachable_json", "reachable_non_json", "invalid_json"}
                for value in checks
            ),
            "module_3_status": discovery["status"],
            "manifest_found": discovery["status"] == "manifests_found",
            "manifest_count": int(discovery["manifest_count"]),
            "resolved_methods": " | ".join(methods),
            "issue_count": sum(issues.values()),
            "issue_types": " | ".join(
                f"{key}:{value}" for key, value in sorted(issues.items())
            ),
            "truncated": bool(discovery.get("truncated", False)),
        }
        if row["manifest_found"]:
            row["failure_category"] = "resolved"
        elif row["reachable_endpoint_count"] == 0:
            row["failure_category"] = "no_reachable_endpoint"
        elif row["issue_count"] == 0:
            row["failure_category"] = "reachable_but_no_iiif_candidate"
        else:
            row["failure_category"] = "candidate_not_confirmed_as_manifest"
        rows.append(row)
    return rows


def role_rows():
    split = json.loads(
        (ROOT / "split/split_manifest.json").read_text(encoding="utf-8")
    )
    dev = split["development"]["role_provider_counts"]
    test = split["test"]["role_provider_counts"]
    roles = sorted(
        set(dev) | set(test),
        key=lambda role: (-(dev.get(role, 0) + test.get(role, 0)), role),
    )
    return [{
        "endpoint_role": role,
        "development_providers": dev.get(role, 0),
        "test_providers": test.get(role, 0),
        "all_providers": dev.get(role, 0) + test.get(role, 0),
    } for role in roles]


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def draw_provider_results(rows):
    ordered = sorted(
        rows,
        key=lambda row: (
            not row["manifest_found"],
            row["name"].casefold(),
        ),
    )
    labels = [
        "\n".join(textwrap.wrap(row["name"], width=44))
        for row in ordered
    ]
    values = [1 if row["manifest_found"] else 0 for row in ordered]
    colors = ["#2E8B57" if value else "#C44E52" for value in values]
    y_values = list(range(len(ordered)))
    fig, ax = plt.subplots(figsize=(11.5, 10.5))
    ax.scatter(
        values, y_values, s=115, c=colors,
        edgecolors="black", linewidths=0.5, zorder=3
    )
    for index, row in enumerate(ordered):
        if row["manifest_found"]:
            unit = "Manifest URL" if row["manifest_count"] == 1 else "Manifest URLs"
            ax.text(
                1.04, index, f'{row["manifest_count"]} {unit}',
                va="center", fontsize=9, color="#1E633D"
            )
    ax.set_yticks(y_values, labels)
    ax.set_xticks([0, 1], ["No Manifest found", "Manifest(s) found"])
    ax.set_xlim(-0.18, 1.38)
    ax.set_ylim(-0.8, len(ordered) - 0.2)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    ax.set_title(
        "Held-out Module 3 Generalisation Results",
        loc="left", fontsize=16, fontweight="bold", pad=16
    )
    successful_count = sum(row["manifest_found"] for row in rows)
    success_rate = successful_count / len(rows) if rows else 0
    ax.text(
        0, 1.01,
        f"{len(rows)} providers; frozen generic strategies; "
        f"{successful_count} providers resolved ({success_rate:.1%})",
        transform=ax.transAxes, fontsize=10, color="#444444"
    )
    fig.text(
        0.01, 0.008,
        "Negative means no Manifest was found within the shared limits; it does not prove that the provider has no IIIF resources.",
        fontsize=8.5, color="#555555"
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(RESULTS / "held_out_provider_results.png", dpi=300, bbox_inches="tight")
    fig.savefig(RESULTS / "held_out_provider_results.pdf", bbox_inches="tight")
    plt.close(fig)


def draw_role_counts(rows):
    labels = [row["endpoint_role"].replace("_", " ").title() for row in rows]
    dev = [row["development_providers"] for row in rows]
    test = [row["test_providers"] for row in rows]
    y_values = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.barh(y_values, dev, color="#4C78A8", label="Development set (75)")
    ax.barh(
        y_values, test, left=dev,
        color="#F58518", label="Held-out test set (19)"
    )
    for index, row in enumerate(rows):
        ax.text(
            row["all_providers"] + 0.7, index,
            str(row["all_providers"]), va="center", fontsize=10
        )
    ax.set_yticks(y_values, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Number of providers exposing the endpoint role")
    ax.set_xlim(0, max(row["all_providers"] for row in rows) * 1.13)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title(
        "Endpoint-Role Coverage in the 94-Provider Census",
        loc="left", fontsize=16, fontweight="bold", pad=16
    )
    ax.text(
        0, 1.01,
        "Provider-level multi-label counts: one provider may expose several roles.",
        transform=ax.transAxes, fontsize=10, color="#444444"
    )
    fig.tight_layout()
    fig.savefig(RESULTS / "endpoint_role_provider_counts.png", dpi=300, bbox_inches="tight")
    fig.savefig(RESULTS / "endpoint_role_provider_counts.pdf", bbox_inches="tight")
    plt.close(fig)


def write_report(dev, test, provider_rows):
    failure_counts = Counter(
        row["failure_category"] for row in provider_rows
        if not row["manifest_found"]
    )
    lines = [
        "# Module 3 Generalisation Evaluation",
        "",
        "Date: 25 September 2026",
        "",
        "## Method",
        "",
        "The 94-provider census was split at institutional-domain-group level:",
        "75 development providers and 19 held-out test providers. The split",
        "used only institutional domains and endpoint roles. Network and",
        "Module 3 outcomes were not used. The same implementation and limits",
        "were frozen before the held-out test.",
        "",
        "## Results",
        "",
        "| Metric | Development | Held-out test |",
        "|---|---:|---:|",
        f'| Providers | {dev["provider_count"]} | {test["provider_count"]} |',
        f'| Endpoints checked | {dev["endpoint_count"]} | {test["endpoint_count"]} |',
        f'| Providers with a reachable endpoint | {dev["reachable_provider_count"]} | {test["reachable_provider_count"]} |',
        f'| Providers with a JSON endpoint | {dev["json_provider_count"]} | {test["json_provider_count"]} |',
        f'| Providers with Manifest(s) found | {dev["successful_provider_count"]} | {test["successful_provider_count"]} |',
        f'| Provider success rate | {dev["success_rate"]:.1%} | {test["success_rate"]:.1%} |',
        f'| Unique Manifest URLs | {dev["unique_manifest_count"]} | {test["unique_manifest_count"]} |',
        "",
        "Held-out successes:",
        "",
    ]
    for item in test["successful_providers"]:
        lines.append(f'- {item["name"]}: {item["manifest_count"]} Manifest URL(s)')
    lines.extend([
        "",
        f'The held-out success rate was {test["successful_provider_count"]}/{test["provider_count"]} ({test["success_rate"]:.1%}).',
        f'Among providers with a reachable endpoint it was {test["successful_provider_count"]}/{test["reachable_provider_count"]} ({test["reachable_success_rate"]:.1%}).',
        "",
        "Held-out unresolved diagnostics:",
        "",
        f'- No reachable endpoint in Module 2: {failure_counts["no_reachable_endpoint"]}',
        f'- Reachable page, but no IIIF candidate was exposed within the crawl limits: {failure_counts["reachable_but_no_iiif_candidate"]}',
        f'- Candidate routes were tried, but none was confirmed as a Manifest: {failure_counts["candidate_not_confirmed_as_manifest"]}',
        "",
        "## Interpretation",
        "",
        "The generic implementation transferred to a direct Manifest route and",
        "an HTML-declared Manifest route in previously held-out providers.",
        "The low overall success rate shows that institutional APIs, search",
        "interfaces and URL templates still require reusable adapters.",
        "",
        "A negative result means no Manifest was found within the shared limits.",
        "It does not prove that the institution has no IIIF resources.",
        "",
    ])
    (RESULTS / "generalisation_evaluation.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main():
    providers = test_provider_rows()
    roles = role_rows()
    dev = summarize("development")
    test = summarize("test")
    write_csv(RESULTS / "held_out_provider_results.csv", providers)
    write_csv(RESULTS / "endpoint_role_provider_counts.csv", roles)
    draw_provider_results(providers)
    draw_role_counts(roles)
    write_report(dev, test, providers)
    failure_counts = dict(sorted(Counter(
        row["failure_category"] for row in providers
    ).items()))
    summary = {
        "evaluation_date": "2026-09-25",
        "module_3_code": "frozen before held-out evaluation",
        "development": dev,
        "held_out_test": test,
        "held_out_provider_outcomes": failure_counts,
        "interpretation": (
            "Negative means no Manifest was found under shared limits, "
            "not that the provider lacks IIIF."
        ),
    }
    (RESULTS / "generalisation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
