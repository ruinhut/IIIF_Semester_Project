"""Small deterministic fixtures shared by Module 5 tests."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


def write_json(path: Path, value: Any) -> bytes:
    body = json.dumps(value, ensure_ascii=False).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def module4_record(
    manifest_id: str,
    raw_relative_path: str,
    body: bytes,
    *,
    provider_name: str = "Test Provider",
) -> dict[str, Any]:
    return {
        "manifest_id": manifest_id,
        "manifest_url": f"https://example.org/{manifest_id}/manifest",
        "resource_type": "Manifest",
        "providers": [
            {"provider_id": "provider-test", "provider_name": provider_name}
        ],
        "module_4_schema_version": "1.0",
        "raw_manifest": {
            "raw_manifest_path": raw_relative_path,
            "sha256": sha256(body).hexdigest(),
        },
        "structural_validation": {
            "status": "valid",
            "presentation_version": "3",
        },
    }


def write_jsonl(path: Path, records: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            json.dump(dict(record), handle, ensure_ascii=False)
            handle.write("\n")
