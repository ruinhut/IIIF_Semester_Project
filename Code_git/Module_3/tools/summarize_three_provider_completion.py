"""Summarize three-provider live discovery and actual linked image downloads."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path


def rows(path):
    """Read existing JSONL outputs; never generate substitute records."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(path, value):
    """Save a readable UTF-8 result."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    """Reconcile counts, links, old recipes and the remaining census entries."""
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-15_three_provider_completion"
    providers = json.loads((root / "providers.json").read_text(encoding="utf-8"))
    discovered = {p["provider_id"]: p for p in rows(root / "validation/module3/output/provider_discovery.jsonl")}
    validated = rows(root / "validation/module4/output/validated_manifests.jsonl")
    manifests = {p["manifest_id"]: p for p in validated}
    out = root / "download_examples/module8/output"
    downloads = rows(out / "all/download_index.jsonl")
    assert len(downloads) == 3 and all(p["download_status"] == "downloaded" for p in downloads)
    decoded = {p["record_id"]: p for p in json.loads((root / "image_decode_verification.json").read_text(encoding="utf-8"))}
    verification = json.loads((root / "schema_and_link_verification.json").read_text(encoding="utf-8"))
    tests = json.loads((root / "test_results.json").read_text(encoding="utf-8"))
    preserved = {}
    for filename in ["discovery_knowledge.json", "provider_endpoints.json"]:
        old = json.loads((root / ("before_" + filename)).read_text(encoding="utf-8"))
        current = json.loads((module / "config" / filename).read_text(encoding="utf-8"))
        by_id = {p["provider_id"]: p for p in current["providers"]}
        preserved[filename] = all(by_id.get(p["provider_id"]) == p for p in old["providers"])
    assert all(preserved.values()), "An earlier provider recipe changed unexpectedly"
    summaries, samples = [], []
    for provider in providers:
        pid = provider["provider_id"]
        valid = [m for m in validated if any(p["provider_id"] == pid for p in m["providers"])]
        images = [p for p in downloads if any(x["provider_id"] == pid for x in manifests[p["record_id"]]["providers"])]
        discovery = discovered[pid]["resource_discovery"]
        audit = discovery["knowledge_application"]
        result = {"provider_id": pid, "provider_name": provider["name"],
                  "discovered_manifests": discovery["manifest_count"], "validated_manifests": len(valid),
                  "declared_canvases": sum(p["structural_validation"]["canvas_count"] for p in valid),
                  "declared_image_bodies": sum(p["structural_validation"]["image_body_count"] for p in valid),
                  "downloaded_example_images": len(images),
                  "method": audit[0]["skill_id"] if audit else "native-paginated-IIIF-Collection"}
        assert result["discovered_manifests"] == len(valid) == 20 and len(images) == 1
        summaries.append(result)
        for image in images:
            path = out / image["image_path"]
            sample = {"provider_name": provider["name"], "manifest_url": manifests[image["record_id"]]["manifest_url"],
                      "record_id": image["record_id"], "resource_id": image["resource_id"],
                      "image_path": str(path.resolve()), "bundle_directory": str(path.parent.resolve()),
                      "image_url": image["final_url"], "reference_texts": image["reference_texts"],
                      "decoded_image": decoded[image["record_id"]]}
            samples.append(sample)
    save(root / "provider_results.json", summaries)
    save(root / "sample_downloads.json", samples)
    with (root / "provider_results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    # Reconcile against the same original 83 unresolved entries, not a new census.
    original = json.loads((module / "evaluation/2026-10-15_provider_investigation/baseline_unresolved.json").read_text(encoding="utf-8-sig"))
    first = json.loads((module / "evaluation/2026-10-15_provider_investigation/provider_route_audit.json").read_text(encoding="utf-8"))
    solved = {p["provider_id"] for p in first if p.get("discovered_sample_manifests", 0) > 0}
    five = json.loads((module / "evaluation/2026-10-15_five_provider_completion/provider_results.json").read_text(encoding="utf-8"))
    solved.update(p["provider_id"] for p in five if p["validated_manifests"] > 0)
    solved.update(p["provider_id"] for p in summaries)
    remaining = [{"provider_id": p["provider_id"], "provider_name": p["name"], "institution_url": p["institution_url"]}
                 for p in original if p["provider_id"] not in solved]
    assert len(remaining) == 61
    save(root / "remaining_unresolved_entries.json", remaining)
    with (root / "remaining_unresolved_entries.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(remaining[0]))
        writer.writeheader()
        writer.writerows(remaining)
    summary = {"generated_at": datetime.now(timezone.utc).isoformat(), "new_institutions": len(summaries),
               "manifest_urls": len(manifests), "valid_manifests": len(validated),
               "declared_image_bodies": sum(p["declared_image_bodies"] for p in summaries),
               "actual_downloaded_images": len(downloads), "downloaded_reference_texts": sum(p["reference_texts"] for p in downloads),
               "schema_validated_bundle_json_files": verification["validated_json_files"],
               "module3_tests_passed": tests["module3"]["passed"], "module8_tests_passed": tests["module8"]["passed"],
               "old_recipes_preserved": preserved, "remaining_unresolved_census_entries": len(remaining),
               "scope": "20 Manifests per institution; one actual image download per institution. Not a full harvest."}
    save(root / "summary.json", summary)
    lines = ["# 新增三个机构：批量发现与下载验证", "", "日期：2026-10-15。BSB、David Rumsey、梵蒂冈三家均已具备可执行批量发现配方，并通过 Module 3–8 的真实运行。", "", "| 机构 | 发现 Manifest | Module 4 验证通过 | 样本声明图片资源 | 实际下载图片 |", "|---|---:|---:|---:|---:|"]
    for p in summaries:
        lines.append(f"| {p['provider_name']} | {p['discovered_manifests']} | {p['validated_manifests']} | {p['declared_image_bodies']:,} | {p['downloaded_example_images']} |")
    lines += ["", f"合计：**60 个有效 Manifest、{summary['declared_image_bodies']:,} 条声明图片资源、3 张实际下载图片、1 份机构 OCR。** Module 4、8 均重新联网获取，缓存命中为 0。", "", "## 获取方式", "", "- BSB：官方指南明确给出的原生 IIIF Collection，跟随服务器提供的 `next` 游标。另行请求了实际下一页，确认可用。", "- Rumsey：LUNA 分页搜索 JSON → `results[].iiifManifest` → 逐个验证。本次 20 个样本来自两页各 10 条结果。", "- 梵蒂冈：目录 HTML 声明分库接口 → JSON `fond[].shelfmark` → 标准 Manifest 模板。保存 83 个目录声明的分库入口，本次在 Capp.Giulia 分库验证 20 个 Manifest；未声称所有分库均已测试。", "", "三种方法复用现有解析器，本次没有新增机构专用 Python 分支。旧 EPFL、Chicago 和前两批配方全部保留，且与修改前备份逐项相同。", "", "## 图片及关联文件", "", "每个图片目录均包含 `image.jpg`、`common_record.json`、`common_media.json`、`ocr_document_profile.json`。全部 9 个 JSON 通过 schema 检查，record_id / resource_id / Canvas 关联一致；3 张图片通过实际解码和目视检查。"]
    for p in samples:
        image = Path(p["image_path"]).relative_to(root).as_posix()
        bundle = Path(p["bundle_directory"]).relative_to(root).as_posix()
        size = p["decoded_image"]
        lines += ["", f"### {p['provider_name']}", "", f"- [图片]({image})，{size['width']} × {size['height']}；[图片与 JSON 文件夹]({bundle}/)。", f"- Manifest：<{p['manifest_url']}>。"]
        if p["reference_texts"]:
            lines += [f"- 另含机构 hOCR、纯文本、`institution_reference_texts.json`。hOCR 页面坐标为 `{size['hocr_page_bbox']}`，与本地图片尺寸一致，含 {size['ocr_word_count']} 个 OCR 单词。", "- 它是机构给出的 OCR 参考文本，没有证据证明经过人工校对，不能称为无误的 gold ground truth。"]
        elif "Vatican" in p["provider_name"]:
            lines.append("- 样例是带手写文字的乐谱页；本次未发现该页机构参考文本，保存在 without_reference。")
        else:
            lines.append("- 样例为图集插图；本次未发现该页机构参考文本，保存在 without_reference。Manifest 给出的下载地址是 1024 像素级样例，不代表机构最大原图。")
    lines += ["", "## 范围与失败记录", "", "- 本次每家 20 个 Manifest。12,783 是这些 Manifest 声明的图片资源数，并未逐张下载；真实下载为 3 张。", "- BSB Collection 返回 `total=3213257`，Rumsey 初次搜索返回 `totalResults=151554`。它们是服务器的目录统计，不是本次验证量，亦不是已下载页图数。", "- 梵蒂冈已保存全部 83 个手稿分库路线，但全馆其他材料类别尚未枚举；大分库 Vat.lat 的调查请求发生超时，原始日志保留。", "- Frick 在调查中部分目录 API 可读，但尚未证实有效资源 Manifest 路线；没有将其计入成功三家。", "- 本次未改 Module 5 权限策略；unknown / exclude 仍按项目要求保留作研究，公开传播及商业用途标记没有放宽。Module 6 的三份文献记录标为 partial，表示部分描述元数据缺失，并非下载失败。", "- 当前剩余 **61 个未解决清单条目**（上一批为 64），不等于去重后的 61 家机构。DigiVatLib 与 Vatican 等重复条目没有未经运行就合并计算。", "", "## 文件与复现", "", "- `provider_results.csv`：逐机构数量与方法。", "- `validation/module3/output/manifest_urls.jsonl`：本批 60 个 Manifest URL。", "- `validation/module4/output/`：验证结果和 12,783 条图片资源清单。", "- `sample_downloads.json`：三份样例的绝对路径、实际下载 URL。", "- `download_examples/module8/output/all/`：with_reference / without_reference 两类下载结果。", "- `运行命令.txt`：可直接复制的 PowerShell 命令，运行会写入该隔离验证目录。", "- `live/`、`validation/module3/requests.jsonl`、各模块 `log/`：原始 HTTP 响应、失败记录、运行日志。", "- `remaining_unresolved_entries.csv`：当前剩余 61 条清单。", "", "Module 3 自动测试 **44 项通过**，Module 8 **16 项通过**；Module 5–7 真实运行各接收 3 条样本并导出 3 条，Module 8 下载 3 张、失败 0，同时下载机构参考文本 1 份、失败 0。此次不更改旧生产或历史评估输出。", "", "获取方法详见 [知识库文档](../../knowledge/institutions/2026-10-15_three_provider_completion.md)。"]
    (root / "三机构批量获取与下载结果.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    commands = ['# PowerShell: this file uses ordinary ASCII hyphens.', '$CodeRoot = "E:\\exchange-epfl\\Semester_Project\\Code_git"', '$Python = Join-Path $CodeRoot ".venv\\Scripts\\python.exe"', '$Evaluation = Join-Path $CodeRoot "Module_3\\evaluation\\2026-10-15_three_provider_completion"', 'Set-Location -LiteralPath $CodeRoot', '', '# Module 3: 20 Manifest samples per institution', '& $Python "Module_3\\tools\\prepare_three_provider_completion.py" --sample-limit 20', '& $Python "Module_3\\tools\\run_discovery_with_evidence.py" --config "$Evaluation\\module3_validation.json"', '', '# Module 4: fetch and validate 60 Manifests', '$env:PYTHONPATH = Join-Path $CodeRoot "Module_4"', '& $Python -m iiif_manifest_validator run --config "$Evaluation\\module4_validation.json"', '', '# Choose one object and image per institution', '& $Python "Module_3\\tools\\prepare_three_provider_download_examples.py"']
    for number, package in [(5, "iiif_rights_filter"), (6, "iiif_metadata_normalizer"), (7, "iiif_common_exporter"), (8, "iiif_image_downloader")]:
        commands += ["", f"# Module {number}", f'$env:PYTHONPATH = Join-Path $CodeRoot "Module_{number}"', f'& $Python -m {package} {"download-all" if number == 8 else "run"} --config "$Evaluation\\module{number}_examples.json"']
    commands += ["", "# Open actual downloads", 'Invoke-Item -LiteralPath "$Evaluation\\download_examples\\module8\\output\\all"', "", "# Open per-institution statistics from this verified run", 'Invoke-Item -LiteralPath "$Evaluation\\provider_results.csv"']
    guarded = []
    for command in commands:
        guarded.append(command)
        if command.startswith("& $Python "):
            guarded.append('if ($LASTEXITCODE -ne 0) { throw "Pipeline stage failed; inspect its log before continuing." }')
    guarded.insert(1, '$ErrorActionPreference = "Stop"')
    guarded += ["", "# Existing verified image bundles may be reused on a rerun (overwrite_existing=false).", "# provider_results.csv records the original verified batch; it is not refreshed by these commands."]
    (root / "运行命令.txt").write_text("\n".join(guarded) + "\n", encoding="utf-8-sig")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
