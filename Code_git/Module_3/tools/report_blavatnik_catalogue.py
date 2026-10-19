"""Produce count tables and a concise report from saved pipeline evidence."""

from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

from build_reference_delivery_index import main as build_reference_delivery_index

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Module_6"))
from iiif_metadata_normalizer.reference_text import clean_text


def rows(path):
    return [json.loads(line) for line in path.open(encoding="utf-8")] if path.exists() else []


def read(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main():
    build_reference_delivery_index()
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-16_blavatnik_investigation"
    final = root / "final"
    summary = read(root / "summary.json")
    catalogue = {r["identifier"]: r["record"]["generalInfo"] for r in rows(root / "entire_catalogue_snapshot_v2/catalogue_records.jsonl")}
    by_type = defaultdict(Counter)
    for item in catalogue.values():
        by_type[item["itemType"]]["catalogue_ids"] += 1
    record_type, record_rights = {}, {}
    image_urls = defaultdict(set)
    for record in rows(final / "module7/output/common_records.jsonl"):
        identifier = re.search(r"/iiif-manifest/(\d+)", record["source"]["manifest_url"]).group(1)
        kind = catalogue[identifier]["itemType"]
        record_type[record["record_id"]] = kind
        record_rights[record["record_id"]] = record["rights"]
        by_type[kind]["exported_documents"] += 1
    for media in rows(final / "module7/output/common_media.jsonl"):
        kind = record_type[media["record_id"]]
        by_type[kind]["image_associations"] += 1
        image_urls[kind].add(media["image"]["id"])
    paired_pages = defaultdict(list)
    for reference in rows(final / "module7/output/institution_reference_texts.jsonl"):
        by_type[record_type[reference["record_id"]]]["aligned_original_references"] += 1
        if reference.get("resource_id"):
            paired_pages[reference["record_id"]].append(reference["resource_id"])
    type_rows = [{"item_type": kind, **{field: counts[field] for field in ["catalogue_ids", "exported_documents", "image_associations", "aligned_original_references"]},
                  "distinct_image_urls_within_type": len(image_urls[kind])} for kind, counts in sorted(by_type.items())]
    with (root / "catalogue_type_counts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(type_rows[0])); writer.writeheader(); writer.writerows(type_rows)
    snapshot_events = {}
    for event in rows(root / "item_snapshot/requests.jsonl"):
        snapshot_events[event["identifier"]] = event
    availability, language_counts, document_language_counts = Counter(), Counter(), Counter()
    manifest_by_identifier = {re.search(r"/iiif-manifest/(\d+)", row["manifest_url"]).group(1): row
                              for row in rows(final / "module3/output/manifest_urls.jsonl")}
    document_texts = []
    item_identity_differences = []
    for event in snapshot_events.values():
        availability["item_ids_checked"] += 1
        if event.get("status") == "record_received":
            availability["item_json_received"] += 1
            item = read(Path(event["raw_json_path"]), {}).get("data", {})
            returned_id = item.get("generalInfo", {}).get("itemId")
            if str(returned_id) == event["identifier"]:
                availability["item_record_identity_matches"] += 1
            else:
                item_identity_differences.append({"requested_id": event["identifier"], "returned_id": returned_id,
                                                  "source_url": event["url"]})
            declared = item.get("generalInfo", {}).get("languages") or []
            if isinstance(declared, str):
                declared = [declared]
            values = sorted({value.strip() for value in declared if isinstance(value, str) and value.strip()}) if isinstance(declared, list) else []
            document_language_counts[";".join(values) or "unknown"] += 1
            original = item.get("originalTranscript")
            text = clean_text(original) if isinstance(original, str) else ""
            if text.strip():
                manifest = manifest_by_identifier[event["identifier"]]
                page_ids = paired_pages[manifest["manifest_id"]]
                document_texts.append({"record_id": manifest["manifest_id"], "manifest_url": manifest["manifest_url"],
                    "institution_item_id": event["identifier"], "institution_item_url": event["url"],
                    "source_json_path": event["raw_json_path"], "source_field": "data.originalTranscript",
                    "source_language": event.get("original_language"), "source_catalogue_page_count": event.get("catalogue_page_count"),
                    "plain_text": text, "alignment_scope": "manifest",
                    "page_alignment_status": "single_page_pair_exported" if page_ids else "not_page_aligned",
                    "paired_page_resource_ids": page_ids, "rights": record_rights.get(manifest["manifest_id"]),
                    "note": "Document text only. It is not an image training pair unless the separately validated page linkage is present."})
        if event.get("has_original_transcript"):
            availability["nonempty_original_transcript"] += 1
            language_counts[str(event.get("original_language") or "unknown")] += 1
            if event.get("catalogue_page_count") == 1:
                availability["single_page_text_candidates"] += 1
    (root / "reference_availability.json").write_text(json.dumps({"counts": dict(availability),
        "reported_language_values": dict(language_counts),
        "item_identity_differences": item_identity_differences,
        "note": "Counts are over unique checked item IDs; not all text is page-aligned or independently corrected."}, indent=2), encoding="utf-8")
    with (root / "catalogue_document_transcripts.jsonl").open("w", encoding="utf-8") as handle:
        for row in document_texts:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (root / "document_transcript_summary.json").write_text(json.dumps({"nonempty_cleaned_document_transcripts": len(document_texts),
        "with_exported_single_page_link": sum(bool(r["paired_page_resource_ids"]) for r in document_texts),
        "not_page_aligned": sum(not r["paired_page_resource_ids"] for r in document_texts),
        "scope": "Supplementary document-level text. Only separately validated page links are eligible as image-reference pairs."}, indent=2), encoding="utf-8")
    with (root / "catalogue_declared_language_counts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_field", "institution_reported_language_combination", "checked_catalogue_item_ids"])
        writer.writeheader()
        for value, count in document_language_counts.most_common():
            writer.writerow({"source_field": "data.generalInfo.languages", "institution_reported_language_combination": value, "checked_catalogue_item_ids": count})
    downloads = {}
    for phase in ["reference_batch", "diverse_downloads", "additional_references"]:
        output = root / phase / "module8/output"
        result = read(output / "all/download_summary.json")
        if result:
            downloads[phase] = result
    download_type_counts = defaultdict(Counter)
    diverse_selection = read(root / "diverse_downloads/selection.json", {}).get("records", [])
    sample_types = {r["resource_id"]: r["item_type"] for r in diverse_selection}
    for row in rows(root / "diverse_downloads/module8/output/all/download_index.jsonl"):
        download_type_counts[sample_types[row["resource_id"]]]["downloaded_or_cached"] += 1
    for row in rows(root / "diverse_downloads/module8/output/all/failed_downloads.jsonl"):
        download_type_counts[sample_types[row["resource_id"]]]["failed"] += 1
    if download_type_counts:
        with (root / "diverse_download_results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["item_type", "attempted", "downloaded_or_cached", "failed"])
            writer.writeheader()
            for kind, counts in sorted(download_type_counts.items()):
                writer.writerow({"item_type": kind, "attempted": sum(counts.values()),
                                 "downloaded_or_cached": counts["downloaded_or_cached"], "failed": counts["failed"]})
    matched = read(root / "identity_audit/summary.json", {}).get("counts", {})
    reference_link_qa = read(root / "reference_batch_link_verification.json", {})
    image_qa = read(root / "reference_batch_image_verification.json", {})
    diverse_qa = read(root / "diverse_image_verification.json", {})
    diverse_link_qa = read(root / "diverse_bundle_verification.json", {})
    delivery = read(root / "reference_delivery_summary.json", {})
    additional_link_qa = read(root / "additional_reference_bundle_verification.json", {})
    additional_pixel_qa = read(root / "additional_reference_image_verification.json", {})
    full_input_download = read(final / "module8/output/example/download_summary.json", {})
    full_input_link_qa = read(root / "full_input_bundle_verification.json", {})
    full_input_pixel_qa = read(root / "full_input_image_verification.json", {})
    stop = read(root / "item_snapshot/summary.json", {}).get("stop_reason")
    lines = ["# Blavatnik Archive 机构攻克与全目录验证", "", f"更新：{datetime.now().astimezone().isoformat(timespec='seconds')}。范围为本次公开目录快照。", "",
        "已从 IIIF 官方指南入手，调查当前查看器和公共前端请求，保存了可执行的批量发现配方。指南截图的 `/manifest/view/9411` 地址在本轮请求中返回 404；当前验证路线是只读 POST 搜索 → 目录 ID → 带完整参数的 Manifest URL。", "",
        "## 已验证数量", "", "| 阶段 | 结果 |", "|---|---:|",
        f"| 公开目录唯一 ID | {summary['public_catalogue_ids']:,} |",
        f"| Module 3：返回声明为 Manifest 的 JSON | {summary['module3_manifest_urls']:,} |",
        f"| Module 4：通过本项目基本检查、可用于图片提取 | {summary['module4_usable_after_explicit_normalization']:,} |",
        f"| 无 Canvas/图片的 Video 条目 | {summary['module4_without_usable_structure']:,} |",
        f"| Module 7：文献主记录 / OCR 文献画像 | {summary['exported_documents']:,} / {summary['exported_documents']:,} |",
        f"| Module 7：图片关联行 | {summary['exported_media_records']:,} |",
        f"| 全库不同图片 URL | {summary['globally_distinct_image_urls']:,} |",
        f"| Module 7 已导出的对齐机构原文 | {summary['exported_aligned_original_references']:,} |", "",
        f"另有文献级原文补充资料 **{len(document_texts):,} 份**（清理后非空，来源与配页状态均保留），其中未明确配页的全文不能当作图片训练配对。", "",
        "Module 5 保留全部研究用途记录；Module 6、7 本次没有记录或媒体导出失败。`partial` 表示部分描述字段缺失，不是流程失败。", "",
        "这不是纯古籍语料：目录包含 11,212 条明信片、3,270 条照片和 1,333 条信件等。不能把全部图片链接都称为古籍文字页或 OCR 训练页，具体类型见 CSV。", "",
        f"{summary['exported_media_records']:,} 是文献—页面—图片关联次数；同一图片可属于相册与单件记录。Module 4 在每份 Manifest 内按图片 URL 去重后相加为 {summary['per_manifest_distinct_image_urls_sum']:,}；全库按 URL 去重为 {summary['globally_distinct_image_urls']:,}。这些都是声明的链接，不是已下载总量。", "",
        "## 实际图片与原始转录", ""]
    for phase, title in [("reference_batch", "单页参考文本样例"), ("diverse_downloads", "35 种文献类型的异质性样例"),
                         ("additional_references", "补充的单页参考文本")]:
        result = downloads.get(phase)
        if result:
            success = result["downloaded_images"] + result["cached_images"]
            rate = success / result["attempted_images"] if result["attempted_images"] else 0
            lines.append(f"- {title}：{result['attempted_images']} 次尝试，{success} 张成功，{result['failed_images']} 张失败（{rate:.2%}）；机构文本 {result['downloaded_reference_texts']} 份。")
    lines += [f"- 合并下载记录并按 resource_id 对照当前 Module 7 清单：{delivery.get('unique_aligned_page_candidates', 0)} 个对齐页面候选中，{delivery.get('delivery_statuses', {}).get('downloaded_with_reference', 0)} 个已下载图片和原文，{delivery.get('delivery_statuses', {}).get('image_failed', 0)} 个图片失败，{delivery.get('delivery_statuses', {}).get('not_yet_attempted', 0)} 个尚未尝试。",
        f"- 首批参考样例中，{reference_link_qa.get('schema_validated_json_files', 0)} 个主要 JSON 通过 schema，{reference_link_qa.get('exact_original_text_and_image_matches', 0)} 份原文与源字段、Canvas、图片哈希一致；{image_qa.get('decoded_images', 0)} 张图片可实际解码且与机构声明尺寸相符。",
        f"- 类型样例中，{diverse_qa.get('decoded_images', 0)} 张图片实际解码成功，{diverse_link_qa.get('schema_validated_json_files', 0)} 个主要 JSON 通过 schema；item 13642 有一张图片的源宽高声明颠倒，已记录，未旋转原图来掩盖差异。",
        f"- 补充参考文本批次：{additional_link_qa.get('schema_validated_json_files', 0)} 个主要 JSON 通过 schema，{additional_pixel_qa.get('decoded_images', 0)} 张图片解码成功。",
        "- 已确认的一张失败图片属于 item 19634：图片正文、标准信息地址和官网缩略图均返回 404，保留失败证据，不用别的图片替代。",
        "- 机构原文来自 `originalTranscript`，不使用 `englishTranscript` 翻译代替。配对条件为单 Canvas、单图片、单目录页面且图片 ID 相同；多页全文与编号含糊的分段不随意配页。机构原文不保证经过人工校对。",
        "- 类型平衡抽样是功能与异质性检查，不是全库可下载率的无偏估计。", "",
        "## 全量输入的下载接口检查", "",
        f"Module 8 另以完整 Module 7 输入执行 download-example：读入 {full_input_download.get('inputs', {}).get('common_records', 0):,} 条主记录、{full_input_download.get('inputs', {}).get('common_media', 0):,} 条媒体记录；成功下载 {full_input_download.get('downloaded_images', 0) + full_input_download.get('cached_images', 0)} 张样例，{full_input_link_qa.get('schema_validated_json_files', 0)} 个配套 JSON 通过 schema、{full_input_pixel_qa.get('decoded_images', 0)} 张图片解码通过。这验证完整输入可由下载器加载，没有启动五万张图片的全量下载。", "",
        "## 本次修正与边界", "",
        "- 全目录用真实返回的 60 条/页；按 30 个集合查询只有 20,162 个唯一 ID，完整无过滤查询补回 37 个。程序会检查接口总数，避免把服务器限制的短页误当作末页。",
        f"- 目录—Manifest 身份核对 {matched.get('checked', 0):,} 条；标题一致 {matched.get('title_match', 0):,} 条，馆藏编号一致 {matched.get('asset_code_match', 0):,} 条。",
        "- 发布方 20,199 个原始响应均缺少顶层 `@id` 和 `label`。Module 4 仅以实际最终请求 URL 补足缺失标识符，保留原始 JSON、原始错误和独立补丁文件。标题由 Module 6 从机构 `metadata` 提取；这不代表原始或补丁后的描述已经通过完整 IIIF 合规认证。",
        "- Module 3 增加通用只读 POST、JSON 请求体分页和目录头配置；大目录去重改为集合索引。旧 14 条机构配方逐项比对未变，新方法另行保存。",
        "- 修复 Module 8 复用图片时索引漏掉 all/example 目录前缀的问题；图片文件本身未丢失。两种模式的回归测试均先复现失败、修复后通过，交付索引重新生成并逐个检查实际路径。",
        f"- Module 3–8 共 {summary['unit_tests_passed']} 项测试通过，另有 7 项子测试；20,000 条去重插入的纯内存基准约 0.23 秒，不是网络吞吐量。",
        "- 此次使用 AI 辅助调查并留存经验证的配方；运行时尚未接入自动调查未知机构的 LLM API。",
        "- 沿用 10 月 15 日同一份机构清单，未跑通条目由 61 减至 60；这是累计记录，不是本次重新联网检查全部 94 条，也不等于去重后的机构数。", "",
        "## 参考文本检查范围", "",
        f"公共 item JSON 已检查 {availability['item_ids_checked']:,} 个不同 ID，收到 JSON {availability['item_json_received']:,} 份；其中 {availability['nonempty_original_transcript']:,} 份的 originalTranscript 字段非空，{availability['single_page_text_candidates']:,} 份为单页候选。该数与已通过 Module 6 配图的文本数不同。",
        f"本轮 item 检查停止状态：`{stop or '仍在继续'}`。未检查的 ID 不能算作没有文本。详情见 `reference_availability.json`；语言值保留机构原文，多语标签不强行拆成页面比例。", "",
        "## 文件与重跑", "",
        "- `stage_counts.csv`：模块输入/输出数量及单位；`catalogue_type_counts.csv`：各文献类型统计。",
        "- `catalogue_declared_language_counts.csv`：已检查 item JSON 中 data.generalInfo.languages 的机构语言标签，按条目统计，不按图片页数统计；不是 OCR 自动识别结果，也没有用翻译语言或英文目录标题补值。",
        "- `final/module3/output/manifest_urls.jsonl`：完整候选列表。",
        "- `final/module4/output/`：结构结果、原始问题与图片清单；原文及补丁在 `final/module4/raw_manifests/`。",
        "- `final/module7/output/`：主记录、图片关联、OCR 画像、机构参考文本。",
        "- `reference_batch/module8/output/all/with_reference/`：实际图片、三个主要 JSON、机构转录索引和 TXT。",
        "- `additional_references/module8/output/all/with_reference/`：新增参考页；`reference_delivery_index.csv` 将所有对齐候选与真实本地文件、失败原因逐一对应。",
        "- `catalogue_document_transcripts.jsonl`：另存目录中清理后非空的文献级原文，保留来源、权限和配页状态；未配页的全文没有混入图片训练样例。数量见 `document_transcript_summary.json`。",
        "- `diverse_downloads/module8/output/all/`：按 with_reference / without_reference 保存的类型样例。",
        "- `final/module8/output/example/`：使用完整 Module 7 输入的单图下载接口检查。",
        "- `identity_audit/`、`missing_image_diagnosis/`、各模块日志：身份核对与失败证据。",
        "- `reproduce_commands.txt`：可复制的 PowerShell 命令；默认明确重放快照，新增 URL 仍会联网。Module 4 的全量核验复用了 Module 3 当次真实 HTTP 原文，没有谎报成第二轮独立联网请求。",
        "- [官方指南](https://iiif.io/guides/guides/blavatnikarchive.org/)；[留存的方法与边界](../../knowledge/institutions/2026-10-16_blavatnik.md)。", ""]
    report = "\n".join(lines)
    (root / "Blavatnik_验证结果.md").write_text(report, encoding="utf-8")
    project = module.parents[1]
    weekly = next((project / "Work_flow").glob("*/每周报告/5_week"))
    weekly_report = report.replace("../../knowledge/institutions/2026-10-16_blavatnik.md",
        (module / "knowledge/institutions/2026-10-16_blavatnik.md").as_posix())
    (weekly / "Blavatnik_机构攻克结果_2026-10-16.md").write_text(weekly_report + "\n以上相对文件路径的完整证据目录：\n\n`" + str(root.resolve()) + "`\n", encoding="utf-8")
    print(json.dumps({"report": str(root / "Blavatnik_验证结果.md"), "snapshot_checked_unique_ids": availability["item_ids_checked"],
                      "exported_references": summary["exported_aligned_original_references"], "download_batches_complete": list(downloads)}), flush=True)


if __name__ == "__main__":
    main()
