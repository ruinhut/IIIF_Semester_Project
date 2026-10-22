"""Build an evidence-linked checkpoint without replacing production outputs."""

from collections import Counter
from datetime import datetime, timezone
import csv
import json
from pathlib import Path


def read_lines(path):
    """Return JSONL rows; an absent optional batch contributes no rows."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []


def main():
    """Join original providers, HTTP evidence, discovery and structural results."""
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-15_provider_investigation"
    baseline = json.loads((root / "baseline_unresolved.json").read_text(encoding="utf-8"))
    checks = read_lines(root / "live/checks.jsonl")
    discovery = []
    manifests = {}
    outcomes = {}
    for batch in ("module3", "additional_module3", "brown_module3"):
        discovery += read_lines(root / batch / "output/provider_discovery.jsonl")
        for row in read_lines(root / batch / "output/manifest_urls.jsonl"):
            manifests[row["manifest_url"]] = row
    for batch in ("module4", "additional_module4", "brown_module4"):
        for filename, status in (("validated_manifests.jsonl", "image_structure_valid"),
                                 ("manual_review.jsonl", "no_image_or_review"),
                                 ("unavailable_manifests.jsonl", "fetch_failed"),
                                 ("invalid_manifests.jsonl", "invalid")):
            for row in read_lines(root / batch / "output" / filename):
                outcomes[row["manifest_url"]] = (status, row)
    resolved = {row["provider_id"]: row for row in discovery
                if row.get("resource_discovery", {}).get("status") == "manifests_found"}
    # Derive resolution from actual output provenance too, rather than trusting labels.
    for row in manifests.values():
        for provider in row.get("providers", []):
            resolved.setdefault(provider["provider_id"], provider)
    partial = {
        "Göttingen University Collections": "Single Manifest verified; top Collection has broken/HTML child routes; corrected children contain no members.",
        "Leiden University": "Official item Manifest verified; current bulk enumerator not established.",
        "National Library of Wales": "Official item Manifest verified; catalogue-wide enumeration not established.",
        "Utrecht University Library": "Item Manifest verified; bulk enumeration and image structure not tested.",
        "Bodmer Lab": "Item HTML exposes Hedera Image API; catalogue listing found; Manifest enumeration not established.",
        "e-rara (digitized rare books from Swiss institutions)": "Browser verification page; official OAI-PMH documentation is a lead, not a validated recipe.",
        "e-manuscripta (Manuscript material from Swiss libraries and archives)": "Browser verification page; no validated catalogue-to-Manifest recipe in this session.",
        "Universitaet Jena": "MyCoRe JSON API lists objects and object/derivates yields derivative IDs; the same candidate Manifest returned HTTP 200 on retry and declared sc:Manifest. Two-stage enumeration is not yet implemented.",
        "Austrian National Library": "SACHA documents project-specific Manifest templates and collection queries. ABO bulk-image download restrictions are explicit; no full-download recipe was enabled.",
    }
    guide_knowledge = json.loads((module / "config/official_guide_knowledge.json").read_text(encoding="utf-8"))
    audit = []
    for provider in baseline:
        pid, name = provider["provider_id"], provider["name"]
        evidence = [c for c in checks if c.get("provider_id") == pid or c.get("provider_name") == name]
        linked = [m for m in manifests.values() if any(p["provider_id"] == pid for p in m.get("providers", []))]
        states = Counter(outcomes[m["manifest_url"]][0] for m in linked if m["manifest_url"] in outcomes)
        guides = sorted({c.get("final_url", c["url"]) for c in evidence if c.get("purpose") == "official_guide" and c.get("status") == 200})
        if linked:
            stage, next_action = "bounded_discovery_verified", "Expand catalogue pagination and coverage in a separately configured run."
        else:
            stage = "route_investigated" if len(evidence) > 2 else "initial_screen_only"
            next_action = "Read item-level guide, identify catalogue/platform, verify an enumerator and a Manifest."
        failures = sorted({str(c.get("status") or c.get("error") or c.get("error_type") or "unknown") for c in evidence if not c.get("json_parseable") and (c.get("status") != 200 or c.get("error"))})
        audit.append({"provider_id": pid, "provider_name": name,
                      "investigation_stage": stage, "http_evidence_count": len(evidence),
                      "official_guides_checked": guides, "discovered_sample_manifests": len(linked),
                      "module4_sample_results": dict(states), "observed_failures": failures,
                      "partial_findings": partial.get(name), "next_action": next_action,
                      "official_guide_instructions": [g.get("official_actions", []) for g in guide_knowledge["providers"] if g.get("provider_id") == pid],
                      "evidence": evidence})
    image_rows = [r for status, r in outcomes.values() if status == "image_structure_valid"]
    historical = {r["manifest_url"] for r in read_lines(module / "data/output/manifest_urls.jsonl")}
    summary = {"generated_at": datetime.now(timezone.utc).isoformat(),
               "baseline_unresolved_entries": len(baseline), "newly_resolved_entries": len(resolved),
               "still_unresolved_entries": len(baseline) - len(resolved),
               "unique_discovered_manifest_urls": len(manifests),
               "overlap_with_production_manifest_urls": len(set(manifests) & historical),
               "module4_outcomes": dict(Counter(s for s, _ in outcomes.values())),
               "validated_canvas_count": sum(r["structural_validation"]["canvas_count"] for r in image_rows),
               "validated_image_body_count": sum(r["structural_validation"]["image_body_count"] for r in image_rows),
               "http_checks_recorded": len(checks),
               "limit_note": "At most five Manifest URLs per candidate provider entry. e-codices occurs twice in the census. No full-catalogue or image-download claim."}
    for filename, obj in (("summary.json", summary), ("provider_route_audit.json", audit)):
        (root / filename).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "combined_manifest_urls.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in manifests.values()), encoding="utf-8")
    # Keep references to each batch: raw_manifest_path is relative to its own batch config.
    (root / "combined_validated_manifest_index.jsonl").write_text("".join(json.dumps({"manifest_url": r["manifest_url"], "manifest_id": r["manifest_id"], "providers": r["providers"], "validation": r["structural_validation"]}, ensure_ascii=False) + "\n" for r in image_rows), encoding="utf-8")
    with (root / "provider_route_audit.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["provider_id", "provider_name", "investigation_stage", "http_evidence_count", "discovered_sample_manifests", "module4_sample_results", "observed_failures", "partial_findings", "next_action"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(r[k], ensure_ascii=False) if isinstance(r[k], (dict, list)) else r[k] for k in fields} for r in audit)
    lines = ["# 2026-10-15 机构入口逐项筛查记录", "", "本轮从旧批次未解决的 83 个候选机构条目开始，先复查主页和匹配到的 IIIF 官方指南，再对有明确线索的机构验证批量发现路线。所有原始响应保存在 live/，旧生产输出未覆盖。", "", "## 已验证结果", "", f"- 新增跑通 {len(resolved)} 个候选清单条目（e-codices 在清单中出现两次，不能当成两个独立机构）。", f"- 合并去重后发现 {len(manifests)} 个 Manifest URL，每个条目最多 5 个样本。", f"- Module 4：{len(image_rows)} 个通过图片资源结构检查；其余结果见 summary.json。", f"- 通过检查的样本声明 {summary['validated_canvas_count']:,} 个 Canvas、{summary['validated_image_body_count']:,} 个图片资源。这是声明数量，未在本轮逐张下载。", "- Northwestern 的两个非图片 Manifest 被分到 review；Lancaster 一个 Manifest 请求超时，不能据此判断该资源永久不可用。", "- Wellcome 与 Northwestern 的 JSON 链接提取技能均经过真实请求验证，迁移仅修改配置。", "", "## 逐机构记录", "", "下表的 initial_screen_only 表示只完成了初筛；不能把所有未成功条目都解释成机构不提供 IIIF。完整 HTTP 证据、官方指南地址和失败分类见 provider_route_audit.json。", ""]
    for row in audit:
        lines += [f"### {row['provider_name']} ({row['provider_id']})", f"- 进度：{row['investigation_stage']}；HTTP 检查 {row['http_evidence_count']} 次；发现样本 {row['discovered_sample_manifests']} 个。", f"- Module 4：{json.dumps(row['module4_sample_results'], ensure_ascii=False)}。"]
        if row["partial_findings"]:
            lines.append("- 已知线索：" + row["partial_findings"])
        for guide in row["official_guides_checked"]:
            lines.append("- 本轮查阅的官方指南：" + guide)
        if row["official_guide_instructions"]:
            lines.append("- 官方操作步骤：见 provider_route_audit.json 的 official_guide_instructions（保留原指南已有结构化记录）。")
        if row["observed_failures"]:
            lines.append("- 本轮失败响应：" + ", ".join(row["observed_failures"]) + "。不等同于机构没有资源。")
        lines.append("- 下一步：" + row["next_action"])
        lines.append("")
    (root / "机构逐项筛查报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
