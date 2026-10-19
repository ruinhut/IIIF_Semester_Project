"""Deterministic readers and atomic output writers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number} is not a JSON object")
            rows.append(value)
    return rows


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    content = json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    atomic_write_text(path, content)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    content = "".join(
        json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )
    atomic_write_text(path, content)


def write_linked_json(
    directory: Path,
    *,
    record: Mapping[str, Any],
    media: Mapping[str, Any],
    profile: Mapping[str, Any],
    reference_texts: Iterable[Mapping[str, Any]] = (),
) -> None:
    write_json(directory / "common_record.json", record)
    write_json(directory / "common_media.json", media)
    write_json(directory / "ocr_document_profile.json", profile)
    references = list(reference_texts)
    if references:
        write_json(
            directory / "institution_reference_texts.json",
            {"reference_texts": references},
        )


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8", newline="\n")
    temp.replace(path)


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
