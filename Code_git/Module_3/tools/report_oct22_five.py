"""Write reconciled evidence, ownership checks and Chinese reproduction notes."""
import json
from pathlib import Path

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-22_five_provider_completion"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


before = {p["provider_id"]: p for p in rows(root / "before_provider_census.jsonl")}
after = {p["provider_id"]: p for p in rows(code / "Module_1/data/output/providers.jsonl")}
leuven = "provider-ef2f1cc06db37bc3"
assert len(before) == 102 and len(after) == 106
assert all(after.get(identifier) == provider for identifier, provider in before.items() if identifier != leuven)
old, new = dict(before[leuven]), dict(after[leuven])
old_endpoints, new_endpoints = old.pop("endpoints"), new.pop("endpoints")
old.pop("endpoint_count", None)
new.pop("endpoint_count", None)
assert old == new and all(endpoint in new_endpoints for endpoint in old_endpoints)
assert len(new_endpoints) == len(old_endpoints) + 1
save("census_preservation_check.json", {"before_entries": 102, "after_entries": 106,
     "new_institutions": 4, "restored_old_sources": 1, "unchanged_old_records": 101,
     "ku_leuven_existing_identity_and_fields_preserved": True,
     "ku_leuven_original_endpoints_preserved": True, "ku_leuven_added_catalogue_endpoint": True})
summary = read(root / "summary.json")
production = {p["provider_id"]: p for p in read(module / "config/discovery_knowledge.json")["providers"]}
assert all(production.get(p["provider_id"]) == p for p in read(root / "new_knowledge_entries.json"))
pixels = read(root / "image_decode_verification.json")
assert len(pixels["dimension_mismatches"]) == 3
assert all(p["height"] - p["declared_dimensions"][1] == 50 for p in pixels["dimension_mismatches"])
summary.update(new_institutions=4, restored_old_sources=1, old_census_entries=94,
    configuration_promoted=True,
    old_census_resolved=67, old_census_remaining=27, tests_subtests_passed=7,
    decoded_images_with_dimension_mismatch=3, smaller_than_canvas_declaration=0,
    larger_than_canvas_declaration=3, actual_downloaded_reference_texts=0,
    fallback_recipes_separately_validated=4, distinct_pagination_checks=5,
    final_sample_images=5, total_images_downloaded_including_initial_example=6,
    initial_frankfurt_example_archived="initial_examples/manifest-0e9ab42db5c5903d",
    image_resolution_note="Three VisualLibrary derivatives add 50 pixels of attribution border; retain actual dimensions and do not treat them as raw OCR coordinate space.")
save("summary.json", summary)
failures = [
    {"provider_name": "Lovaniensia / KU Leuven", "url": "https://www.lovaniensia.be/api/items?per_page=6&page=1",
     "observed_status": "HTTP 403", "resolution": "Use explicitly public catalogue and detail links; no API restriction bypassed."},
    {"provider_name": "KU Leuven legacy Jesuitica route", "url": "https://services.libis.be/m2/manifest/GBIB_Jesuitica",
     "observed_status": "HTTP 404", "resolution": "Historical lecture example was not promoted; use the current public Lovaniensia route."},
    {"provider_name": "Digital Commonwealth", "observed_status": "HTTP 403", "counted_as_new_success": False},
    {"provider_name": "Villanova University", "observed_status": "HTTP 403", "counted_as_new_success": False},
    {"provider_name": "Qatar Digital Library", "observed_status": "HTTP 403 on one candidate Manifest", "counted_as_new_success": False},
    {"provider_name": "Georgetown", "observed_status": "HTTP 200 with HTML access challenge, not catalogue JSON", "counted_as_new_success": False},
    {"provider_name": "University College Dublin / Duesseldorf", "observed_status": "URLError; details retained in probe responses", "counted_as_new_success": False},
]
save("unresolved_investigations.json", failures)
summary["unresolved_investigation"] = failures
save("summary.json", summary)

text = """# 本轮 5 家机构验证结果（2026-10-22）

完成 **1 家旧来源恢复（KU Leuven）及 4 家新机构扩充**。累计成功 **74 → 79 / 106 个来源条目**；
原始 94 条清单中，成功 **66 → 67**，尚未完成 **28 → 27**。
累计数沿用已有历史验证证据，不表示今天重新检查了全部来源；来源条目中也包含聚合平台。

| 机构 | 发现的 Manifest | M4 校验通过 | M7 图片关联记录 | 最终实际下载样例 |
|---|---:|---:|---:|---:|
"""
for provider in read(root / "provider_results.json"):
    text += f'| {provider["provider_name"]} | {provider["discovered_manifest_urls"]} | {provider["validated_manifests"]} | {provider["exported_image_associations"]:,} | 1 |\n'
text += """
合计发现 **30 个 Manifest URL**，其中 **29 个**通过独立结构校验；导出 **29 条文献主记录、6,539 条图片关联及 29 份 OCR 画像**。
每家本次最多取 6 个 Manifest，这是有界样本，不是全馆资源总量。图片关联不等于图片全部已下载。

## 逐家保存的方法

1. **KU Leuven（恢复旧来源）**：`Lovaniensia /items/browse` 分页 → `/items/show/{id}` 藏品页 →
   页面明确声明的 `data.lovaniensia.be/IE…/manifest` → Manifest 声明的 `lib.is` 图像。
   6 条样本文献的 Location 均明确写出 KU Leuven Libraries Special Collections。
   目录的 Omeka API 返回 403，使用其公开网页提供的入口，不绕过限制，也不猜测 IE 标识符。
   保留原 provider_id、旧 Limo 入口和来源信息，仅追加公开目录入口。
2. **卡尔斯鲁厄州立图书馆**：VisualLibrary 原生 Collection `178827`（摇篮本）→ `members[].@id`。
3. **波恩大学暨州立图书馆**：原生 Collection `10250864`（中世纪手稿）→ `members[].@id`。
4. **法兰克福大学图书馆**：原生 Collection `all` → `members[].@id`；当前只测试首批样本。
5. **帕德博恩大学图书馆**：原生 Collection `8437472`（Zugschwerdt 历史借阅馆藏）→ `members[].@id`。

后 4 家直接复用已有 Collection 遍历能力；无需修改 Module4–8 的机构逻辑。
它们的 `next` 链接也已逐家请求，确认下一页成员不同；KU 公开目录第 1、2 页也不同。
另将 4 条首页面 Manifest 链接提取配置分别执行验证，额外结果没有重复计入上表。

## 输出和检查

- **Module1**：登记 4 家新机构；原 102 条中的 101 条完全不变，KU 原信息和旧入口均保留，只新增 1 个入口。
- **Module2**：5 家共 6 个入口均可达，4 个为 JSON，2 个为 HTML；HTML 可达不等于直接返回 IIIF。
- **Module3–4**：发现 30 个，独立联网重取 30 个，缓存命中 0。法兰克福的 `8929677` 虽声明 Manifest，
  却没有有效 `sequences` 和 Canvas，保留于 `invalid_manifests.jsonl`，没有伪装为可用图片。
- **Module5–7**：29 个有效文献全部保留到研究输出；28 个按策略只进入研究用途，1 个进入允许复用类别。
  未确认任何机构页面级参考文本，故本批不新增 `with_reference` 样例。`ground_truth_candidates` 的 60 条候选
  也不能当作 60 份机构正确转录；已验证参考文本数仍是 0。原有参考文本功能和之前的样例保持不变。
- **Module8**：最终 5 个样例包分别有 1 张真实图片和 3 份关联 JSON，全部通过解码、schema 和 ID 关联检查。
  首轮额外下载的法兰克福样例是空白页，已改选有文字的页面；初始样例及下载证据保留在 `initial_examples` 和
  `initial_download_index.jsonl`。本次共下载过 6 张不同图片，最终展示目录为 5 个样例。
- **图像尺寸**：KU 样例 3672×4527，波恩 1000×1379，与声明一致。
  卡尔斯鲁厄、法兰克福、帕德博恩的预览图带附加署名边栏，实际高度比声明大 50 像素。
  原始图片未裁剪，实际尺寸记录于核验文件；这些预览图不能直接当作原始 OCR 坐标空间。
- **自动测试**：Module3–8 共 **187 项通过，另 7 个子测试通过**。本轮没有修改流水线运行时代码。
- **知识保存**：正式知识库 **47 → 52 条**；旧 47 条与原 19 条预设入口均保持一致。
  这次保存的是可执行发现配置与调查证据，没有新增运行时大语言模型 API。
- 其他调查遇到的 403、访问挑战和连接错误均保留，未计入成功。详见 `unresolved_investigations.json`。

## 文件位置

- [逐机构数量 CSV](provider_results.csv)
- [5 张图片及各自三个 JSON 的完整路径](sample_downloads.csv)
- [最终图片和 JSON 文件夹](download_examples/module8/output/all/without_reference/)
- [Module7 完整样本输出](downstream/module7/output/)
- [实际像素核验](image_decode_verification.json)
- [KU 六条样本的机构归属](ku_leuven_ownership_validation.json)
- [分页实测证据](pagination_validation.json)
- [剩余 27 条来源](remaining_unresolved_entries.csv)
- [可复制的运行命令](运行命令.txt)
- [详细调查与复用方法](../../knowledge/institutions/2026-10-22_five_provider_completion.md)
"""
(root / "本轮五机构验证结果.md").write_text(text, encoding="utf-8")
rel = "Code_git/Module_3/evaluation/2026-10-22_five_provider_completion"
commands = f'''# PowerShell; copy commands from this TXT, not PDF.
Set-Location -LiteralPath 'E:\\exchange-epfl\\Semester_Project'
$PipelinePython = 'E:\\exchange-epfl\\Semester_Project\\Code_git\\.venv\\Scripts\\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath $PipelinePython)) {{ throw 'Python not found' }}

# Module 1 registration was completed; four additions are in manual_providers.json.
# Registration output: {rel}/registration/module1/output
# KU keeps its existing provider ID and old endpoint, plus the new catalogue.
# Use the isolated five-provider selection below, not all historical providers.

# Module 2 output: {rel}/validation/module2/output
& $PipelinePython -m iiif_entry_validator run --config '{rel}/module2_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 2 failed' }}

# Module 3 output: {rel}/validation/module3/output
& $PipelinePython Code_git/Module_3/tools/run_discovery_with_evidence.py --config '{rel}/module3_validation.json' --network-delay 0.6
if ($LASTEXITCODE -ne 0) {{ throw 'Module 3 failed' }}

# Module 4 output: {rel}/validation/module4/output
& $PipelinePython -m iiif_manifest_validator run --config '{rel}/module4_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 4 failed' }}

# Modules 5-7: {rel}/downstream/module5/output (and module6, module7)
# Module 8: {rel}/download_examples/module8/output/all/without_reference
# One selected image per provider, not all 6539 image links.
& $PipelinePython Code_git/Module_3/tools/complete_oct19_provider_completion.py --evaluation-root '{rel}'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 5-8 failed' }}

& $PipelinePython Code_git/Module_3/tools/verify_linked_download_bundles.py --output-root '{rel}/download_examples/module8/output' --mode all --report '{rel}/bundle_verification.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Bundle validation failed' }}

# Separate supplementary checks; not added to the downstream sample counts.
& $PipelinePython Code_git/Module_3/tools/validate_oct22_recipes.py
if ($LASTEXITCODE -ne 0) {{ throw 'Recipe validation failed' }}
& $PipelinePython Code_git/Module_3/tools/run_completion_test_suites.py --evaluation-root '{rel}'
if ($LASTEXITCODE -ne 0) {{ throw 'Tests failed' }}

Import-Csv -LiteralPath '{rel}/provider_results.csv' | Format-Table -AutoSize
Import-Csv -LiteralPath '{rel}/sample_downloads.csv' | Format-List
Invoke-Item -LiteralPath '{rel}/download_examples/module8/output/all/without_reference'
'''
(root / "运行命令.txt").write_text(commands, encoding="utf-8-sig")
print("Report, commands and census preservation checks written.")
