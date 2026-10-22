"""Reconcile the fourth batch and write Chinese evidence and run instructions."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-21_fourth_five_provider_completion"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


before = {p["provider_id"]: p for p in rows(root / "before_provider_census.jsonl")}
after = {p["provider_id"]: p for p in rows(code / "Module_1/data/output/providers.jsonl")}
assert len(before) == 97 and len(after) == 102
assert all(after.get(identifier) == provider for identifier, provider in before.items())
save("census_preservation_check.json", {"before_entries": 97, "after_entries": 102,
     "new_institutions": 5, "old_entries_unchanged": True})
sample_root = root / "download_examples/module8/output"
reference_sample = next(p for p in rows(sample_root / "all/download_index.jsonl") if p["reference_texts"])
bundle = sample_root / reference_sample["bundle_directory"]
xml = ET.parse(bundle / "institution_reference_001.xml")
namespace = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
page = xml.find(".//a:Page", namespace)
dimensions = [int(page.get("WIDTH")), int(page.get("HEIGHT"))]
pixels = next(p for p in read(root / "image_decode_verification.json")["images"] if p["resource_id"] == reference_sample["resource_id"])
plain = (bundle / "institution_reference_001.txt").read_text(encoding="utf-8")
strings = xml.findall(".//a:String", namespace)
assert plain.strip() and "ocrd-tesserocr-recognize" not in plain and '"segmentation_level"' not in plain
assert dimensions == [pixels["width"], pixels["height"]] == [2221, 3540]
reference = {"provider": "Berlin State Library", "canvas_id": read(bundle / "common_media.json")["canvas"]["id"],
    "image_file": str((bundle / "image.png").resolve()), "alto_file": str((bundle / "institution_reference_001.xml").resolve()),
    "text_file": str((bundle / "institution_reference_001.txt").resolve()), "alto_namespace": "http://www.loc.gov/standards/alto/ns-v4#",
    "alto_dimensions": dimensions, "decoded_image_dimensions": dimensions, "image_alto_dimensions_match": True,
    "measurement_unit": xml.findtext(".//a:MeasurementUnit", namespaces=namespace),
    "word_elements": len(strings), "words_with_declared_confidence": sum("WC" in word.attrib for word in strings),
    "plain_text_characters": len(plain.strip()),
    "institution_ocr_not_manually_corrected_gold": True, "processing_metadata_excluded_from_plain_text": True}
save("reference_sample_validation.json", reference)
summary = read(root / "summary.json")
summary.update(new_institutions=5, restored_old_sources=0, old_census_entries=94,
               old_census_resolved=66, old_census_remaining=28, tests_subtests_passed=7,
               actual_downloaded_reference_texts=1, reference_image_dimensions_match=True)
save("summary.json", summary)
text = """# 本轮新增 5 个机构：结果与样例（2026-10-21）

本轮完成 5 个新机构的入口检查、Manifest 发现与校验、Module5–7 导出、Module8 实际下载。
这 5 家均是原先 97 条清单之外的新机构。累计为 **74/102 个来源条目**；原清单仍有 **28 条未完成**。
原有 97 条记录和入口不变，旧成功来源没有在本轮全部重新请求。

| 新机构 | 校验通过的 Manifest | 图片关联记录 |
|---|---:|---:|
"""
for provider in read(root / "provider_results.json"):
    text += f'| {provider["provider_name"]} | {provider["validated_manifests"]} | {provider["exported_image_associations"]:,} |\n'
text += """
合计 **24 个 Manifest、10,194 条图片关联记录**。这些是有界样本中的关联记录，既不是机构总量，也不是已下载图片数。
本轮实际下载 **5 张图片、15 份配套 JSON、1 份机构 ALTO OCR 与抽取文本**，下载失败为 0。

## 本轮保存的可复用方法

- **曼彻斯特大学**：检查搜索页面使用的 JavaScript，找到公开 `JSONAdvanced` 目录请求。
  从 `item.id[0]` 获取文献 ID，再请求该站原生 IIIF Manifest。增加通用 `{page_end}` 参数，支持 `start/end` 范围分页。
- **宾州州立大学**：公开 CONTENTdm 目录 API 给出馆藏别名，IIIF Collection 给出文献 Manifest。
  本轮验证 Elisha J. Bracken 内战日记：1 个 Manifest 内含 57 条图像关联，而不是 57 个 Manifest。
- **挪威国家图书馆**：公开目录 API 过滤可在线访问、已数字化、出版日期在 1500–1900 年的图书，读取声明的 HAL `presentation` 链接。
- **柏林国家图书馆**：通过 OAI-PMH 获取 PPN 标识符，再使用其官方 Manifest 模板；直接复用上一轮新增的 XML 技能。
- **伯尔尼大学图书馆**：从机构 IIIF 服务器手册给出的 Haller GGA Collection 开始，读取其声明的各卷 Manifest。

5 条机构配置已加入正式知识库：**42 → 47 条**；原 42 条与 19 条预设入口均未改动。
机构和集合、搜索子集与完整馆藏分别记录，不把精选馆藏的成功夸大成全站已经采完。

## 新的图片—参考文本样例

柏林的 3 个样本文献共声明 **97 条页面级 ALTO OCR 链接**。本轮实际下载并检查其中 **1 份**，没有声称全部 97 份均已下载。

- 文献：`https://content.staatsbibliothek-berlin.de/dc/PPN1000056597/manifest`
- 图片对应第 1 个 Canvas；可见 1719 年德文印刷页面及历史字体。
- 图片解码尺寸：**2221×3540**；ALTO Page 也为 **2221×3540 像素**，尺寸吻合。
- ALTO 含 **47 个非空词元素**，原始文本和词坐标保留在 XML 内；本例机构没有提供词级置信度，未补造数值。
- 它是机构提供的 OCR，有识别错误，**不等于经过人工校正的标准答案**。
- 实际 XML 使用 ALTO v4 命名空间；原 Manifest 的 profile 链接提到 v2。保留原始声明，不把本次 JSON 校验称为 ALTO XSD 校验。

检查发现，旧的通用 XML 文本抽取会把 ALTO 的软件参数和文件名混入 TXT。本轮修正 Module8：
只提取 ALTO 页面 `String/@CONTENT`，保留行顺序，正确解码 XML 实体；原始 XML 不变。
只有软件元数据而没有识别词的 ALTO 会进入 `reference_failed`，不能混入参考文本样例。

查看 [柏林图片与参考文本文件夹](download_examples/module8/output/all/with_reference/manifest-5c24009d6db3c363/000000_resource-f42d1791ce42f606f84a/)。
其中包含 `image.png`、三份关联 JSON、`institution_reference_texts.json`、原始 XML 和纯文本。
其余 4 个不带参考文本的样例位于 `without_reference`。

## 验证与边界

- Module1 完成新增机构登记，原 97 条记录逐项保持一致。
- Module2：5 个入口全部可达；4 个返回 JSON，柏林返回 XML。XML 不可解析为 JSON，并不代表接口不可用。
- Module4：24 个 Manifest 全部重新请求并校验，通过 24，缓存命中 0。
- Module5–7：24 条文献、10,194 条图像关联、24 份 OCR 画像、97 条参考文本描述。
  当前版权策略将本批保留为学术分析用途，没有将其标为可不受限制传播的资源。
- Module8：5 张真实图片全部能解码；15 份配套 JSON 的结构和关联校验通过。
  首次下载证据保存在 `initial_download_index.jsonl`；修正文本文档后重新运行时复用了这 5 张图片，并重新获取参考文本。
- 曼彻斯特样例实际为 **1543×2000**，小于 Canvas 的 **4243×5500**；不能称为原始分辨率。
- **187 项自动测试全部通过，另有 7 个子测试通过**。本轮新增 1 项范围分页测试和 4 项 ALTO 抽取/失败分流测试。
- Trinity 返回验证码、Cornell 返回 403 等调查没有被记为成功；RBGE 的标本接口虽可用，本轮未纳入统计。
- 本轮没有增加运行时 AI API。

## 文件索引

- [机构统计 CSV](provider_results.csv)
- [所有样例图片和三份 JSON 的完整位置](sample_downloads.csv)
- [Module7 样本输出](downstream/module7/output/)
- [有参考文本的实际样例](download_examples/module8/output/all/with_reference/)
- [不带参考文本的实际样例](download_examples/module8/output/all/without_reference/)
- [参考文本与图像尺寸核验](reference_sample_validation.json)
- [累计来源状态](cumulative_provider_status.csv)
- [剩余 28 条来源](remaining_unresolved_entries.csv)
- [可复制的 PowerShell 命令](运行命令.txt)
- [调查方法与官方资料](../../knowledge/institutions/2026-10-21_fourth_five_provider_completion.md)
"""
(root / "本轮五机构验证结果.md").write_text(text, encoding="utf-8")
rel = "Code_git/Module_3/evaluation/2026-10-21_fourth_five_provider_completion"
commands = f'''# PowerShell. All punctuation in command lines is ASCII.
Set-Location -LiteralPath 'E:\\exchange-epfl\\Semester_Project'
$PipelinePython = 'E:\\exchange-epfl\\Semester_Project\\Code_git\\.venv\\Scripts\\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath $PipelinePython)) {{ throw 'Python not found' }}

# Module 1 registration already ran; output: {rel}/registration/module1/output
# Its source additions are retained in Module_1/config/manual_providers.json.
# The commands below reuse this batch's selected_providers.jsonl.

# Module 2 output: {rel}/validation/module2/output
& $PipelinePython -m iiif_entry_validator run --config '{rel}/module2_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 2 failed' }}

# Module 3 output: {rel}/validation/module3/output
& $PipelinePython Code_git/Module_3/tools/run_discovery_with_evidence.py --config '{rel}/module3_validation.json' --network-delay 0.6
if ($LASTEXITCODE -ne 0) {{ throw 'Module 3 failed' }}

# Module 4 output: {rel}/validation/module4/output
& $PipelinePython -m iiif_manifest_validator run --config '{rel}/module4_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 4 failed' }}

# Modules 5, 6, 7, 8; M8 downloads one selected image per provider.
# M5-7 output: {rel}/downstream/module5/output (and module6, module7)
# M8 output: {rel}/download_examples/module8/output/all
# Reference text pairs: with_reference; other examples: without_reference
& $PipelinePython Code_git/Module_3/tools/complete_oct19_provider_completion.py --evaluation-root '{rel}'
if ($LASTEXITCODE -ne 0) {{ throw 'Downstream run failed' }}

& $PipelinePython Code_git/Module_3/tools/verify_linked_download_bundles.py --output-root '{rel}/download_examples/module8/output' --mode all --report '{rel}/bundle_verification.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Bundle check failed' }}
& $PipelinePython Code_git/Module_3/tools/run_completion_test_suites.py --evaluation-root '{rel}'
if ($LASTEXITCODE -ne 0) {{ throw 'Tests failed' }}

Invoke-Item -LiteralPath '{rel}/sample_downloads.csv'
Invoke-Item -LiteralPath '{rel}/download_examples/module8/output/all/with_reference'
'''
(root / "运行命令.txt").write_text(commands, encoding="utf-8-sig")
print("Report, commands, preservation and clean reference checks written.")
