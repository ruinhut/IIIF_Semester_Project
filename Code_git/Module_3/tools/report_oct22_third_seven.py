"""Reconcile the 100-source milestone from saved, measured evidence."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-22_third_seven_provider_completion"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


before = {p["provider_id"]: p for p in rows(root / "before_provider_census.jsonl")}
after = {p["provider_id"]: p for p in rows(code / "Module_1/data/output/providers.jsonl")}
assert len(before) == 120 and len(after) == 127
assert all(after.get(k) == v for k, v in before.items())
save("census_preservation_check.json", {"before_entries": 120, "after_entries": 127,
    "new_institutions": 7, "old_entries_unchanged": True})
summary = read(root / "summary.json")
assert summary["configuration_promoted"] and summary["cumulative_resolved_census_entries"] == 100
output = root / "download_examples/module8/output"
downloads = rows(output / "all/download_index.jsonl")
pixels = {x["resource_id"]: x for x in read(root / "image_decode_verification.json")["images"]}
references = rows(root / "downstream/module7/output/institution_reference_texts.jsonl")
media_ids = {x["resource_id"] for x in rows(root / "downstream/module7/output/common_media.jsonl")}
alignments = []
for download in downloads:
    directory = output / download["bundle_directory"]
    reference_file = directory / "institution_reference_texts.json"
    if not reference_file.exists():
        continue
    for reference in read(reference_file)["reference_texts"]:
        source = directory / reference["download"]["source_file"]
        xml = ET.fromstring(source.read_bytes())
        page = next(n for n in xml.iter() if n.tag.rsplit("}", 1)[-1] == "Page")
        words = [n for n in xml.iter() if n.tag.rsplit("}", 1)[-1] == "String"]
        pixel = pixels[download["resource_id"]]
        width, height = int(page.get("WIDTH")), int(page.get("HEIGHT"))
        assert (width, height) == (pixel["width"], pixel["height"])
        inside = all(0 <= float(w.get("HPOS", 0)) and 0 <= float(w.get("VPOS", 0))
            and float(w.get("HPOS", 0)) + float(w.get("WIDTH", 0)) <= width
            and float(w.get("VPOS", 0)) + float(w.get("HEIGHT", 0)) <= height for w in words)
        assert words and inside
        alignments.append({"resource_id": download["resource_id"], "canvas_id": reference["canvas"]["id"],
            "source_url": reference["reference_text"]["id"], "downloaded_source_file": str(source),
            "image_width": width, "image_height": height, "alto_words": len(words),
            "image_and_alto_page_dimensions_match": True, "word_boxes_within_image": inside,
            "manually_corrected_gold_truth_asserted": False})
assert len(alignments) == 1
save("reference_alignment_verification.json", alignments)
investigations = [
    {"provider_name": "Luebeck City Library", "observed_status": "Public Schriftgut.SH Manifest works, but its declared external image URL raised client URLError [Errno 2]. No successful image download established here.", "counted_as_new_success": False},
    {"provider_name": "GWLB Hannover", "observed_status": "Public /oai2/ works and official example /content/00068782/manifest.json is valid. The corresponding template returned 404 for sampled newspaper IDs. ListSets returned noSetHierarchy.", "next_method": "Investigate catalogue-to-content-directory mapping and collection coverage, not blind identifier substitution.", "counted_as_new_success": False},
    {"provider_name": "Weimar / Herzogin Anna Amalia Library", "observed_status": "Candidate public RSS request timed out; not a conclusion that IIIF is absent.", "counted_as_new_success": False},
    {"provider_name": "Berlin Central and Regional Library", "observed_status": "RSS item 019591853_2010 Manifest timed out. Other records succeeded. Guessed YEARPUBLISH search field returned explicit undefined-field HTTP 400 and was not promoted.", "failed_candidate_in_valid_manifest_count": False},
    {"provider_name": "Freiburg / Bielefeld / Halle / Rostock / Gotha", "observed_status": "Raw catalogue/platform/failed-route probes retained locally; no fresh end-to-end success established in this batch.", "counted_as_new_success": False},
]
save("unresolved_investigations.json", investigations)
summary.update(new_institutions=7, restored_old_sources=0, old_census_entries=94,
    old_census_resolved=67, old_census_remaining=27, tests_subtests_passed=7,
    actual_downloaded_reference_texts=1, final_sample_images=7,
    page_aligned_reference_descriptors=sum(x.get("resource_id") in media_ids for x in references),
    manifest_level_reference_descriptors=sum(x.get("resource_id") is None for x in references),
    independently_checked_provenance_records=42, separate_fallback_recipes_validated=7,
    separate_oai_next_page_pairs_checked=1, runtime_modules_changed=False,
    unresolved_investigation=investigations,
    scope_note="Cumulative bounded-run source evidence, not deduplicated institutions or complete catalogues. RSS recipes enumerate capped public feed subsets only.")
save("summary.json", summary)
result = """# 本轮七机构验证结果：累计 100 个来源（2026-10-22）

累计有界测试由 **93 增至 100 / 127 个来源条目**。本轮增加的是 7 家不同机构；原始 94 条清单中仍有 **27 条未完成**。
累计清单包含同机构不同项目和聚合门户，因此 100 不能直接称为去重后的 100 家机构，也不代表完成全馆下载。

| 本轮机构 | 有效 Manifest | 图像关联记录 | 最终样图尺寸 |
|---|---:|---:|---|
"""
for p in read(root / "provider_results.json"):
    result += f'| {p["provider_name"]} | {p["validated_manifests"]} | {p["exported_image_associations"]:,} | {p["actual_width"]}×{p["actual_height"]} |\n'
result += """
共 **42 个有效 Manifest、7,123 条图像关联**。每家仅验证 6 个 Manifest；这些不是机构总量。

## 已实际验证

- M1 登记 7 家，原 120 条记录及入口逐项不变。
- M2：7 个入口全部可达，6 个返回 XML、1 个返回原生 Collection JSON。**XML 可作为有效目录，不能把非 JSON 等同不可用。**
- M3：通用 XML→标识符→Manifest 模板、原生 Collection 方法取得 42 个 URL。
- M4：42 次重新联网获取，42 个有效，缓存命中 0。ZLB 年刊 `019591853_2010` 在 M3 超时，失败保留，没有计入 42 个。
- M5–7：42 条文献、7,123 条图像关联、42 份 OCR 画像。权利 allow 14、exclude 28；研究输出保留全部 42 条，限制公开再利用。
  分类为公共领域 8、开放许可 6、机构条款 4、冲突 6、未知 18；没有把 unknown 当成无版权。
- M8：**7 张最终图片、21 份配套 JSON**，全部可解码且 schema、关联 ID、尺寸检查通过。
  原站多给 300–400 像素预览；评估辅助脚本读取其明确声明的 info.json，再请求服务支持的 full 图像。
  三份 JSON 保留原始 image ID/source ID，download_url 记录实际请求的版本。德累斯顿服务本身只声明 1000×1509，未声称得到更大原图。
  此辅助步骤没有修改生产 M7/M8 默认行为：默认下载仍可能是原 Manifest 的预览，需要显式运行高清样例步骤。
- 初次 7 套低清/封面样例归档在 `initial_examples/`；最终基尔样图换为正文，林茨换为正文及对应 ALTO。未删除其他批次结果。
- M3–8 自动测试 **193 项及 7 个子测试全部通过**。

## 机构参考文本

林茨的 6 个 Manifest 声明 **3,504 条参考文本描述**：3,498 条能关联到具体图像，另 6 条是文献整体 ALTO 入口，没有强行配给一张图。
这些主要是尚未逐条下载的地址，不能当成已验证的 3,504 份正确转录。

本轮实际下载了 **1 份正文 ALTO 和抽取纯文本**，与 Canvas 21 的图片通过 resource_id 关联。
图片及 ALTO 页面均为 **2882×4629**，159 个词的坐标均在页面范围内。
这是机构 OCR，尚未确认人工校正，不能直接称为严格的 ground truth。

- [图片、三份 JSON、ALTO 和纯文本](download_examples/module8/output/all/with_reference/manifest-0e0173792b2ca81e/000020_resource-5a1740085010f7233fd1/)
- [其余六家无参考文本样例](download_examples/module8/output/all/without_reference/)
- [图文坐标配对检查](reference_alignment_verification.json)

## 方法与范围

1. 卡塞尔、柏林中央与州立图书馆、柏林洪堡大学图书馆：公开 Goobi RSS→条目 link 中的 ID→原生 Manifest。
2. 基尔大学图书馆、市档案馆：共享 Schriftgut.SH 门户，按 **MD_DV_OWNER** 分别筛选；逐条检查 Manifest 的持有机构字段，没有把门户另外算一次。
3. 德累斯顿：公开 OAI-PMH→header identifier→原生 Manifest；另验证了一次服务器声明的 resumptionToken，第二页确实不同。
4. 林茨：原生 Presentation 3 Collection 的 `items[].id`→Manifest；该层声明 466 个成员，未声明 next，本轮只取 6 个。

**5 家 RSS 配置只覆盖最多 50 条公开 feed 记录，没有已验证的全目录分页。**
不能据此声称“全馆批量枚举已完成”。后续可继续研究各站原生 Collection、OAI 或公开搜索分页。
7 条配置各独立验证另 2 个 Manifest；这些检查不额外计入 42 个对象。
42 条文献无跨来源重复 URL；基尔两个机构的原始 holder 字段全部符合各自筛选。

知识库 **66→73 条**，原 66 条知识和 19 条预设入口完全保留。
新增的是配置、可重放审计和高清样例辅助步骤；**没有新增运行时 AI API，也没有完成未知机构的自动调查系统**。
失败和待研究的候选见 `unresolved_investigations.json`，不计入新增成功。

## 查看与复现

- [机构统计 CSV](provider_results.csv)
- [每张图片及三份 JSON 的路径](sample_downloads.csv)
- [可直接复制的 PowerShell 命令](运行命令.txt)
- [仍未完成的 27 条旧来源](remaining_unresolved_entries.csv)
- [方法与官方来源](../../knowledge/institutions/2026-10-22_third_seven_provider_completion.md)

中期汇报可说：累计已有 100 个来源条目在有界测试中提供有效 Manifest；本轮新增 7 家机构，
验证 42 个 Manifest、7,123 条图像关联，并逐家下载样例，其中一例包含图像及机构 OCR。
这证明所保存的路线可执行，尚不代表全目录覆盖或对未知机构的自动泛化。
"""
(root / "本轮七机构验证结果_100来源.md").write_text(result, encoding="utf-8")
relative = "Code_git/Module_3/evaluation/2026-10-22_third_seven_provider_completion"
commands = f"""# PowerShell. Copy from this TXT, not PDF.
Set-Location -LiteralPath 'E:\\exchange-epfl\\Semester_Project'
$ProjectRoot = (Get-Location).Path
$PipelinePython = Join-Path $ProjectRoot 'Code_git\\.venv\\Scripts\\python.exe'
$EvaluationRoot = Join-Path $ProjectRoot '{relative}'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath $PipelinePython)) {{ throw 'Python not found' }}

# M1 registration already exists at $EvaluationRoot/registration/module1/output
# M2 output: $EvaluationRoot/validation/module2/output
Set-Location -LiteralPath (Join-Path $ProjectRoot 'Code_git\\Module_2')
& $PipelinePython -m iiif_entry_validator run --config "$EvaluationRoot/module2_validation.json"
if ($LASTEXITCODE -ne 0) {{ throw 'Module 2 failed' }}

Set-Location -LiteralPath $ProjectRoot
# M3 output: $EvaluationRoot/validation/module3/output
& $PipelinePython Code_git/Module_3/tools/run_discovery_with_evidence.py --config "$EvaluationRoot/module3_validation.json" --network-delay 0.6
if ($LASTEXITCODE -ne 0) {{ throw 'Module 3 failed' }}

# M4 output: $EvaluationRoot/validation/module4/output
Set-Location -LiteralPath (Join-Path $ProjectRoot 'Code_git\\Module_4')
& $PipelinePython -m iiif_manifest_validator run --config "$EvaluationRoot/module4_validation.json"
if ($LASTEXITCODE -ne 0) {{ throw 'Module 4 failed' }}

Set-Location -LiteralPath $ProjectRoot
# M5-7 output: $EvaluationRoot/downstream/module5/output (and module6/module7)
# M8 first sample: $EvaluationRoot/download_examples/module8/output/all
& $PipelinePython Code_git/Module_3/tools/complete_oct19_provider_completion.py --evaluation-root $EvaluationRoot
if ($LASTEXITCODE -ne 0) {{ throw 'Modules 5-8 failed' }}

# Read only explicitly declared Image services; retain original image/source IDs.
# Archive the first previews and prepare the reviewed pages at service resolution.
& $PipelinePython Code_git/Module_3/tools/prepare_full_resolution_examples.py --evaluation-root $EvaluationRoot
if ($LASTEXITCODE -ne 0) {{ throw 'Image-service verification failed' }}
Set-Location -LiteralPath (Join-Path $ProjectRoot 'Code_git\\Module_8')
& $PipelinePython -m iiif_image_downloader download-all --config "$EvaluationRoot/module8_full_resolution_examples.json"
if ($LASTEXITCODE -ne 0) {{ throw 'Module 8 failed' }}

Set-Location -LiteralPath $ProjectRoot
& $PipelinePython Code_git/Module_3/tools/verify_linked_download_bundles.py --output-root "$EvaluationRoot/download_examples/module8/output" --mode all --report "$EvaluationRoot/bundle_verification.json"
if ($LASTEXITCODE -ne 0) {{ throw 'Bundle verification failed' }}
& $PipelinePython Code_git/Module_3/tools/verify_catalogue_feed_recipes.py --evaluation-root $EvaluationRoot
if ($LASTEXITCODE -ne 0) {{ throw 'Recipe verification failed' }}

# Statistics refer to this recorded run; network contents can change on a rerun.
Import-Csv -LiteralPath "$EvaluationRoot/provider_results.csv" | Format-Table -AutoSize
Import-Csv -LiteralPath "$EvaluationRoot/sample_downloads.csv" | Format-List
Invoke-Item -LiteralPath "$EvaluationRoot/download_examples/module8/output/all"
"""
(root / "运行命令.txt").write_text(commands, encoding="utf-8-sig")
print("100-source report, reference alignment, preservation evidence and commands written.")
