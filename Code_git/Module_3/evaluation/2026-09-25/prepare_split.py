"""Prepare a reproducible provider-level development/test split.

The split is stratified only by Module 1 endpoint roles. Network outcomes and
Module 3 results are never consulted, so the held-out set remains independent.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import random
from typing import Any
from urllib.parse import urlsplit


SEED = 20260925
TEST_SIZE = 19
SEARCH_ITERATIONS = 60000


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def provider_roles(row: dict[str, Any]) -> set[str]:
    roles = {
        str(endpoint.get("endpoint_role", "unclassified"))
        for endpoint in row.get("endpoints", [])
        if isinstance(endpoint, dict)
    }
    return roles or {"unclassified"}


def organisation_key(row: dict[str, Any]) -> str:
    """Approximate an institution using its canonical institutional domain."""

    value = str(row.get("institution_url") or "").strip()
    if not value:
        endpoints = row.get("endpoints", [])
        if endpoints and isinstance(endpoints[0], dict):
            value = str(endpoints[0].get("url", ""))
    parts = urlsplit(value)
    host = (parts.hostname or "").casefold().removeprefix("www.")
    labels = host.split(".")
    if host.endswith(".s3.amazonaws.com") and len(labels) >= 4:
        domain = ".".join(labels[-4:])
    elif host in {"github.com", "gitlab.com"}:
        first_path = next(
            (part for part in parts.path.split("/") if part),
            "",
        )
        domain = f"{host}/{first_path.casefold()}"
    elif len(labels) >= 3 and ".".join(labels[-2:]) in {
        "ac.uk",
        "co.uk",
        "org.uk",
        "com.au",
        "edu.au",
        "go.jp",
    }:
        domain = ".".join(labels[-3:])
    elif len(labels) >= 2:
        domain = ".".join(labels[-2:])
    else:
        domain = host
    return domain or str(row["provider_id"])


def choose_test_ids(rows: list[dict[str, Any]]) -> set[str]:
    """Choose whole organisation clusters using role-stratified search."""

    role_totals = Counter(
        role for row in rows for role in provider_roles(row)
    )
    clusters: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        clusters.setdefault(organisation_key(row), []).append(row)

    singleton_roles = {role for role, count in role_totals.items() if count == 1}
    mandatory_development_clusters = {
        organisation_key(row)
        for row in rows
        if provider_roles(row) & singleton_roles
    }
    candidate_clusters = [
        (key, cluster_rows)
        for key, cluster_rows in sorted(clusters.items())
        if key not in mandatory_development_clusters
    ]
    target = {
        role: count * TEST_SIZE / len(rows)
        for role, count in role_totals.items()
    }

    sizes = [len(cluster_rows) for _, cluster_rows in candidate_clusters]
    possible: dict[tuple[int, int], bool] = {}

    def can_fill(index: int, remaining: int) -> bool:
        key = (index, remaining)
        if key in possible:
            return possible[key]
        if remaining == 0:
            return True
        if remaining < 0 or index >= len(sizes):
            return False
        result = can_fill(index + 1, remaining) or can_fill(
            index + 1, remaining - sizes[index]
        )
        possible[key] = result
        return result

    if not can_fill(0, TEST_SIZE):
        raise RuntimeError("Organisation clusters cannot form the requested test size")

    rng = random.Random(SEED)
    best_ids: set[str] | None = None
    best_score = float("inf")
    for _ in range(SEARCH_ITERATIONS):
        remaining = TEST_SIZE
        chosen_rows: list[dict[str, Any]] = []
        for index, (_, cluster_rows) in enumerate(candidate_clusters):
            include_ok = can_fill(index + 1, remaining - len(cluster_rows))
            exclude_ok = can_fill(index + 1, remaining)
            if include_ok and exclude_ok:
                include = bool(rng.getrandbits(1))
            else:
                include = include_ok
            if include:
                chosen_rows.extend(cluster_rows)
                remaining -= len(cluster_rows)
        if remaining != 0:
            continue

        counts = Counter(
            role for row in chosen_rows for role in provider_roles(row)
        )
        score = 0.0
        for role, total in role_totals.items():
            observed = counts.get(role, 0)
            score += ((observed - target[role]) ** 2) / max(target[role], 1.0)
            if total >= 2 and observed == 0:
                score += 100.0
            if total >= 2 and observed == total:
                score += 100.0
        ids = {str(row["provider_id"]) for row in chosen_rows}
        tie_key = tuple(sorted(ids))
        current_tie = tuple(sorted(best_ids)) if best_ids else ()
        if score < best_score or (score == best_score and tie_key < current_tie):
            best_score = score
            best_ids = ids

    if best_ids is None or len(best_ids) != TEST_SIZE:
        raise RuntimeError("Could not construct the held-out split")
    return best_ids


def role_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(role for row in rows for role in provider_roles(row))
    return dict(sorted(counts.items()))


def endpoint_count(rows: list[dict[str, Any]]) -> int:
    return sum(len(row.get("endpoints", [])) for row in rows)


def module2_config(input_path: Path, run_root: Path) -> dict[str, Any]:
    return {
        "input_jsonl": str(input_path.resolve()),
        "output_directory": str((run_root / "module2" / "output").resolve()),
        "log_directory": str((run_root / "module2" / "log").resolve()),
        "network": {
            "timeout_seconds": 8,
            "retries": 0,
            "backoff_seconds": 0.25,
            "max_redirects": 10,
            "max_response_bytes": 4194304,
            "user_agent": "iiif-entry-validator/0.2 (+EPFL DHLAB academic research)",
        },
        "run": {
            "delay_between_requests_seconds": 0.1,
            "max_records": None,
        },
    }


def module3_config(run_root: Path) -> dict[str, Any]:
    return {
        "input_jsonl": str(
            (run_root / "module2" / "output" / "checked_entry_points.jsonl").resolve()
        ),
        "curated_endpoints": "",
        "output_directory": str((run_root / "module3" / "output").resolve()),
        "log_directory": str((run_root / "module3" / "log").resolve()),
        "network": {
            "timeout_seconds": 10,
            "retries": 0,
            "backoff_seconds": 0.25,
            "max_response_bytes": 4194304,
            "user_agent": "iiif-resource-discovery/0.2 (+EPFL DHLAB academic research)",
        },
        "limits": {
            "max_providers": None,
            "max_stream_pages_per_provider": 5,
            "max_collections_per_provider": 20,
            "max_html_pages_per_provider": 2,
            "max_html_depth": 1,
            "max_candidates_per_html_page": 25,
            "max_machine_candidates_per_provider": 20,
            "max_manifests_per_provider": 100,
        },
        "html_discovery": {
            "enabled": True,
            "same_host_only": True,
            "delay_between_pages_seconds": 0.1,
        },
    }


def main() -> int:
    root = Path(__file__).resolve().parent
    project_root = root.parents[2]
    source = (
        project_root
        / "Module_1"
        / "data"
        / "output"
        / "selected_providers.jsonl"
    )
    rows = sorted(
        read_jsonl(source),
        key=lambda row: str(row["provider_id"]),
    )
    if len(rows) != 94:
        raise ValueError(f"Expected the current 94-provider census, got {len(rows)}")

    test_ids = choose_test_ids(rows)
    development = [row for row in rows if str(row["provider_id"]) not in test_ids]
    test = [row for row in rows if str(row["provider_id"]) in test_ids]
    if len(development) != 75 or len(test) != 19:
        raise AssertionError("Split must contain 75 development and 19 test providers")

    split_root = root / "split"
    run_root = root / "runs"
    development_path = split_root / "development_providers.jsonl"
    test_path = split_root / "test_providers.jsonl"
    write_jsonl(development_path, development)
    write_jsonl(test_path, test)

    manifest = {
        "created_date": "2026-09-25",
        "method": "provider-level multi-label endpoint-role stratification",
        "seed": SEED,
        "search_iterations": SEARCH_ITERATIONS,
        "leakage_rule": "All provider records sharing an institutional domain, and all of their endpoints, remain in one split",
        "selection_inputs": "Module 1 institutional domains and endpoint roles only; no network or Module 3 outcomes",
        "development": {
            "provider_count": len(development),
            "endpoint_count": endpoint_count(development),
            "role_provider_counts": role_counts(development),
            "organisation_keys": sorted({organisation_key(row) for row in development}),
            "provider_ids": [row["provider_id"] for row in development],
        },
        "test": {
            "provider_count": len(test),
            "endpoint_count": endpoint_count(test),
            "role_provider_counts": role_counts(test),
            "organisation_keys": sorted({organisation_key(row) for row in test}),
            "provider_ids": [row["provider_id"] for row in test],
        },
    }
    (split_root / "split_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    configs = root / "configs"
    configs.mkdir(parents=True, exist_ok=True)
    for label, input_path in (
        ("development", development_path),
        ("test", test_path),
    ):
        current_run_root = run_root / label
        (configs / f"module2_{label}.json").write_text(
            json.dumps(
                module2_config(input_path, current_run_root),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (configs / f"module3_{label}.json").write_text(
            json.dumps(
                module3_config(current_run_root),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "development_providers": len(development),
                "development_endpoints": endpoint_count(development),
                "test_providers": len(test),
                "test_endpoints": endpoint_count(test),
                "development_roles": role_counts(development),
                "test_roles": role_counts(test),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
