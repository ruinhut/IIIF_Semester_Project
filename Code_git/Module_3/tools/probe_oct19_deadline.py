"""Record a bounded pre-deadline check without promoting unverified providers."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import ssl
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    root = Path(__file__).resolve().parents[1] / "evaluation/2026-10-19_evening_provider_completion"
    root.mkdir(parents=True, exist_ok=True)
    deadline = datetime(2026, 10, 19, 16, 5, tzinfo=timezone.utc)
    ca = Path("C:/Users/43057/AppData/Local/Programs/Python/Python310/lib/site-packages/certifi/cacert.pem")
    context = ssl.create_default_context(cafile=str(ca))
    targets = [
        ("Princeton University Libraries", "https://figgy.princeton.edu/concern/scanned_resources/3880841a-aaa8-418f-a6cb-dac6b77c9422/manifest"),
        ("University of North Texas Libraries", "https://digital.library.unt.edu/"),
        ("Villanova University", "https://digital.library.villanova.edu/"),
        ("Stanford University", "https://searchworks.stanford.edu/catalog?f%5Biiif_resources%5D%5B%5D=available"),
        ("Harvard University Digital Collections", "https://library.harvard.edu/digital-collections"),
    ]

    def check(target):
        name, url = target
        row = {"provider_name": name, "url": url, "checked_at": datetime.now(timezone.utc).isoformat(), "promoted": False}
        if (deadline - datetime.now(timezone.utc)).total_seconds() < 15:
            row["result"] = "not_started_deadline"
            return row
        start = time.monotonic()
        try:
            request = Request(url, headers={"User-Agent": "EPFL-DHLAB-IIIF-discovery-audit/1.0 (academic research)"})
            try:
                response = urlopen(request, context=context, timeout=6)
            except HTTPError as error:
                response = error
            with response:
                row.update(http_status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"))
                body = response.read(2 * 1024 * 1024 + 1)
            row["bytes"] = len(body)
            row["truncated"] = len(body) > 2 * 1024 * 1024
            row["result"] = "endpoint_checked_only"
            if not row["truncated"]:
                try:
                    value = json.loads(body)
                    row["json_parseable"] = True
                    if isinstance(value, dict):
                        row["declared_type"] = value.get("type", value.get("@type"))
                        row["context"] = value.get("@context")
                        if row["http_status"] == 200 and row["declared_type"] in ("Manifest", "sc:Manifest"):
                            (root / "princeton_candidate_manifest.json").write_bytes(body)
                            row["evidence_file"] = "princeton_candidate_manifest.json"
                            row["result"] = "manifest_candidate_fetched_not_end_to_end_validated"
                except (ValueError, UnicodeError):
                    row["json_parseable"] = False
        except Exception as error:
            row.update(result="request_failed", error_type=type(error).__name__, error=str(error))
        row["elapsed_seconds"] = round(time.monotonic() - start, 3)
        return row

    rows = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        for future in as_completed([pool.submit(check, target) for target in targets]):
            row = future.result()
            rows.append(row)
            (root / "endpoint_checks.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(row, ensure_ascii=True), flush=True)
    summary = {"completed_at": datetime.now(timezone.utc).isoformat(), "deadline_utc": deadline.isoformat(),
               "requested_providers": 5, "new_end_to_end_resolved": 0, "global_configs_modified": False,
               "checks": rows, "cleanup": {"temporary_bodies_written": 0, "deleted_files": [],
               "note": "HTML bodies were inspected in memory and discarded. Retained JSON is final audit evidence, not temporary data."}}
    (root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "README.md").write_text("# 2026-10-19 截止时间记录\n\n本轮目标为新增 5 个来源，按要求于柏林时间 18:05 前停止。本轮未完成任何新增来源的端到端验证，因此新增跑通数量为 0；不得将入口可达或单条 Manifest 候选计作批量发现及图片下载已跑通。\n\n复核了 IIIF 官方指南中的 Princeton、UNT、Villanova、Stanford 和 Harvard 条目，并保存了有超时限制的入口检查结果。具体 HTTP 状态及失败原因见 endpoint_checks.json。下一轮应从这些证据继续，完成可复用发现配置、Module 3–4 验证和图片下载后再纳入累计结果。\n\n未修改全局机构配置或技能库。HTML 响应仅存在内存中，检查后释放，没有产生需要保留的大型临时响应文件。summary.json 记录完成时间、清理情况及明确的未完成状态。\n", encoding="utf-8")


if __name__ == "__main__":
    main()
