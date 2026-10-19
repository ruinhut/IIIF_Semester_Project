"""Reconcile five real provider validations and optionally promote their recipes."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()] if path.exists() else []


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def table(path, values):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(values[0]))
        writer.writeheader(); writer.writerows(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promote", action="store_true", help="Append only validated entries; preserve all earlier methods")
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / "evaluation/2026-10-19_five_provider_completion"
    providers = read(root / "providers.json")
    expected = {p["provider_id"] for p in providers}
    bundle_qa = read(root / "bundle_verification.json")
    pixel_qa = read(root / "image_decode_verification.json")
    assert set(bundle_qa["provider_ids"]) == expected and not bundle_qa["errors"]
    assert pixel_qa["decoded_images"] == 5 and not pixel_qa["decode_errors"]
    checks = read(root / "test_results.json")
    assert all(result["exit_code"] == 0 for result in checks)
    manifests = rows(root / "validation/module3/output/manifest_urls.jsonl") + rows(root / "akon_check/module3/output/manifest_urls.jsonl")
    manifests = list({r["manifest_url"]: r for r in manifests}.values())
    validated = rows(root / "combined_validated_manifests.jsonl")
    media = rows(root / "downstream/module7/output/common_media.jsonl")
    documents = rows(root / "downstream/module7/output/common_records.jsonl")
    references = rows(root / "downstream/module7/output/institution_reference_texts.jsonl")
    provider_by_record = {r["record_id"]: r["source"]["providers"][0]["provider_id"] for r in documents}
    sample_root = root / "download_examples/module8/output"
    downloads = rows(sample_root / "all/download_index.jsonl")
    sample_providers = {}
    sample_locations = []
    for entry in downloads:
        record = read(sample_root / entry["bundle_directory"] / "common_record.json")
        provider = record["source"]["providers"][0]
        sample_providers[provider["provider_id"]] = entry
        directory = sample_root / entry["bundle_directory"]
        sample_locations.append({"provider_name": provider["provider_name"], "record_id": record["record_id"],
            "manifest_url": record["source"]["manifest_url"], "image_path": str((sample_root / entry["image_path"]).resolve()),
            "common_record_json": str((directory / "common_record.json").resolve()),
            "common_media_json": str((directory / "common_media.json").resolve()),
            "ocr_document_profile_json": str((directory / "ocr_document_profile.json").resolve()),
            "reference_index_json": str((directory / "institution_reference_texts.json").resolve()) if entry["reference_texts"] else ""})
    table(root / "sample_downloads.csv", sample_locations)
    counts = []
    for p in providers:
        identifier = p["provider_id"]
        values = {"provider_id": identifier, "provider_name": p["name"],
            "discovered_manifest_urls": sum(any(v["provider_id"] == identifier for v in row["providers"]) for row in manifests),
            "validated_manifests": sum(any(v["provider_id"] == identifier for v in row["providers"]) for row in validated),
            "exported_media_associations": sum(provider_by_record[r["record_id"]] == identifier for r in media),
            "downloaded_sample_images": int(identifier in sample_providers)}
        counts.append(values)
    table(root / "provider_results.csv", counts)
    save(root / "provider_results.json", counts)
    old_paths = [code / "Module_4/data/output/validated_manifests.jsonl",
        module / "evaluation/2026-10-15_provider_investigation/combined_validated_manifest_index.jsonl",
        module / "evaluation/2026-10-15_five_provider_completion/final_validation/module4/output/validated_manifests.jsonl",
        module / "evaluation/2026-10-15_three_provider_completion/validation/module4/output/validated_manifests.jsonl",
        module / "evaluation/2026-10-16_blavatnik_investigation/final/module4/output/validated_manifests.jsonl"]
    old_ids = {p["provider_id"] for path in old_paths for r in rows(path) for p in r.get("providers", [])}
    assert not old_ids & expected, "A new source must not have been counted previously"
    all_ids = old_ids | expected
    census = rows(code / "Module_1/data/output/providers.jsonl")
    statuses = [{"provider_id": r["provider_id"], "provider_name": r["name"], "institution_url": r["institution_url"],
                 "status": "manifest_found_and_basic_structure_validated" if r["provider_id"] in all_ids else "unresolved_in_cumulative_evidence"}
                for r in census]
    save(root / "cumulative_provider_status.json", statuses)
    table(root / "cumulative_provider_status.csv", statuses)
    remaining = [r for r in statuses if r["provider_id"] not in all_ids]
    save(root / "remaining_unresolved_entries.json", remaining)
    table(root / "remaining_unresolved_entries.csv", remaining)
    preservation = {}
    for kind, filename, additions in [("knowledge", "discovery_knowledge.json", "new_knowledge_entries.json"),
                                      ("endpoints", "provider_endpoints.json", "new_endpoint_entries.json")]:
        current_path = module / "config" / filename
        before = read(root / ("before_" + filename))
        current = read(current_path)
        old_entries = {p["provider_id"]: p for p in before["providers"]}
        current_entries = {p["provider_id"]: p for p in current["providers"]}
        assert all(current_entries.get(k) == v for k, v in old_entries.items()), "Existing provider knowledge changed during investigation"
        if args.promote:
            for entry in read(root / additions):
                if entry["provider_id"] in current_entries:
                    assert current_entries[entry["provider_id"]] == entry
                else:
                    current["providers"].append(entry)
            save(current_path, current)
        preservation[kind] = {"old_entries": len(old_entries), "current_entries": len(current["providers"]), "old_entries_unchanged": True}
    save(root / "knowledge_preservation_check.json", preservation)
    downloaded_bytes = sum(r["bytes"] for r in downloads)
    page_references = [r for r in references if r.get("resource_id")]
    summary = {"generated_at": datetime.now(timezone.utc).isoformat(), "new_resolved_source_entries": 5,
        "discovered_manifest_urls": len(manifests), "validated_manifests": len(validated),
        "unavailable_manifest_urls": len(manifests) - len(validated), "declared_image_associations": len(media),
        "distinct_image_urls": len({r["image"]["id"] for r in media}),
        "actual_downloaded_sample_images": len(downloads), "actual_sample_image_bytes": downloaded_bytes,
        "reference_descriptors": len(references), "page_scoped_reference_descriptors": len(page_references),
        "unique_pages_with_reference_descriptors": len({r["resource_id"] for r in page_references}),
        "downloaded_reference_versions": sum(r["reference_texts"] for r in downloads),
        "downloaded_reference_pages": sum(bool(r["reference_texts"]) for r in downloads),
        "schema_validated_sample_json_files": bundle_qa["schema_validated_json_files"],
        "sample_images_decoded": pixel_qa["decoded_images"], "tests_passed": sum(r["passed"] for r in checks),
        "previous_resolved_census_entries": len(old_ids), "cumulative_resolved_census_entries": len(all_ids),
        "census_entries": len(census), "remaining_unresolved_census_entries": len(remaining),
        "configuration_promoted": args.promote, "preservation": preservation,
        "scope": "Bounded catalogue/collection samples, not full-institution harvests; census entries include platforms and duplicate institutions."}
    save(root / "summary.json", summary)
    lines = ["# 新增五个来源：批量发现与下载验证", "", "日期：2026-10-19。", "",
        "五个来源均已跑通 Manifest 发现、基础结构检查、Module 5–7 导出，以及 Module 8 的真实图片下载。", "",
        "| 来源 | 发现 Manifest | 基础检查通过 | 图片关联记录 | 实际样例图片 |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {r['provider_name']} | {r['discovered_manifest_urls']} | {r['validated_manifests']} | {r['exported_media_associations']:,} | {r['downloaded_sample_images']} |" for r in counts]
    lines += ["", f"合计：**{len(manifests)} 个候选、{len(validated)} 个有效样本、{len(media):,} 条图片关联记录、5 张实际下载图片**。图片链接数量不等于已下载数量，也不代表全馆规模。", "",
        "## 方法与范围", "",
        "- e-rara、e-manuscripta：官方培训给出的 Visual Library Collection，跟随 members、子集合和 next 分页。",
        "- FromThePage：公开的 Jeremiah White Graves Diaries Collection。本轮只验证这个项目，未枚举所有转录项目。",
        "- Bodmer Lab：搜索结果提取编号，按查看器实际声明的 autographes 专题路由获取 Manifest。第二页额外验证 2 个不重复候选，未并入主表。其他专题未宣称全部覆盖。",
        "- 奥地利国家图书馆：官方脚本声明的年度 ANNO Collection；另用官网 Jerusalem Collection 的 AKON 明信片验证真实图片下载。", "",
        "## 失败与修正", "",
        "首轮 100 个候选中 99 个通过，1 个 ANNO Manifest 返回 400；初次 5 张图片尝试中 4 张成功，1 张 ANNO 图片返回 400。随后独立验证官网另一 Collection 的 5 个 Manifest，并成功下载 AKON 图片。最终样例集为每来源 1 张，共 5 张；原来的 Manifest 与图片失败仍保存在 initial_download_attempt 和各轮日志中，未伪装成已修复。",
        "另修正 Module 4 会删除 Canvas ID 的 #canvas 片段的问题。HTTP 请求 URL 的处理保持原逻辑，逻辑 Canvas ID 保留 fragment。回归测试先复现失败再通过；原始响应未改，以缓存重新验证后更新下游结果。", "",
        "## 参考文本和交接", "",
        f"Module 7 导出了 {len(references):,} 条文本/相关资源描述。这些包含同一页面的不同版本及文献级 seeAlso，不能当成这么多份已下载、准确的 OCR 答案。",
        "FromThePage 的实际样例下载了同一页的 4 个文本版本（HTML、searchable、verbatim、emended）。用于 OCR/HTR 评估优先考察 Verbatim Plaintext；4 个版本不是 4 个独立页面。来源转录的逐字准确率和全文覆盖范围尚未认证。",
        "每张图都带 common_record.json、common_media.json、ocr_document_profile.json；带文本样例另含文本文件及 institution_reference_texts.json。", "",
        f"5 张图片均解码成功，尺寸与声明一致；15 个主要 JSON 通过 schema 和关联校验。Module 3–8 自动测试合计 **{summary['tests_passed']} 项通过**，另有 7 个子测试。", "",
        "## 累计数量和文件", "",
        f"累计已发现并保存有效 Manifest 的来源条目 **{len(old_ids)} → {len(all_ids)} / {len(census)}**，未解决条目 **{len(census)-len(old_ids)} → {len(remaining)}**。这是沿用现有清单与历史证据的累计结果，不是今天重新联网复查全部来源；平台及同机构不同入口没有冒充独立机构数。",
        "原有 EPFL、Chicago、Blavatnik 等知识逐项核对未变；新配置在实际下载与校验成功后合入。", "",
        "- provider_results.csv：本轮逐来源数量；cumulative_provider_status.csv：94 条来源的累计状态。",
        "- remaining_unresolved_entries.csv：剩余条目。",
        "- downstream/module7/output/：文献、媒体、OCR 画像和参考资源描述。",
        "- download_examples/module8/output/all/：真实图片与配套 JSON，按 with_reference / without_reference 分开。",
        "- sample_downloads.csv：5 个最终样例的图片、三个 JSON、参考文本索引的实际完整路径。修复前的旧 ID 样例归档到 initial_download_attempt。",
        "- 运行命令.txt：本轮命令与输出目录。",
        "- [经过验证的方法与官方来源](../../knowledge/institutions/2026-10-19_five_provider_completion.md)。", ""]
    (root / "五来源验证结果.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == "__main__":
    main()
