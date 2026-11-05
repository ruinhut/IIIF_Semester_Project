"""Write the measured 93-source milestone and its copyable run commands."""
import json
from pathlib import Path

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-22_second_seven_provider_completion"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


before = {p["provider_id"]: p for p in rows(root / "before_provider_census.jsonl")}
after = {p["provider_id"]: p for p in rows(code / "Module_1/data/output/providers.jsonl")}
assert len(before) == 113 and len(after) == 120
assert all(after.get(key) == value for key, value in before.items())
save("census_preservation_check.json", {"before_entries": 113, "after_entries": 120,
    "new_institutions": 7, "old_entries_unchanged": True})
summary = read(root / "summary.json")
assert summary["configuration_promoted"] and summary["cumulative_resolved_census_entries"] == 93
owners = read(root / "institution_ownership_verification.json")
assert owners["records_checked"] == 41 and not owners["manifest_urls_overlap_between_sources"]
summary.update(new_institutions=7, restored_old_sources=0, old_census_entries=94,
    old_census_resolved=67, old_census_remaining=27, tests_subtests_passed=7,
    actual_downloaded_reference_texts=0, final_sample_images=7,
    total_images_downloaded_including_initial_examples=8,
    independently_checked_provenance_records=41, separate_fallback_recipes_validated=7,
    separate_next_page_pairs_checked=5, runtime_modules_changed=False,
    scope_note="Historical bounded-run evidence, not a deduplicated institution count or a full reharvest of 120 sources.")
investigations = [
    {"provider_name": "Rijksmuseum", "observed_status": "Public Change Discovery root/page work; events also label non-Presentation metadata serializations as Manifest.",
     "next_method": "Official documentation describes a Linked Art object-to-VisualItem-to-DigitalObject chain and native Micrio Manifest. This chain was not executed end to end in this batch.",
     "counted_as_new_success": False},
    {"provider_name": "Freiburg University Library / SLUB Dresden", "observed_status": "Public OAI-PMH METS catalogue responses saved; Manifest/image chain not validated in this batch.", "counted_as_new_success": False},
    {"provider_name": "Leipzig old UBLab guide", "observed_status": "Old documentation URL redirects to the library homepage; native top Collection still returns valid JSON.", "resolution": "Use the actual root's declared Greek manuscript Collection; do not treat an old guide redirect as loss of the IIIF server."},
    {"provider_name": "Mannheim / Salzburg / Stuttgart / Duesseldorf / Bremen / Dortmund / Duisburg-Essen", "observed_status": "Probed routes raised URLError; details saved locally. This does not prove the institutions lack IIIF.", "counted_as_new_success": False},
    {"provider_name": "Kassel", "observed_status": "HTTP 404 on a candidate index route", "counted_as_new_success": False},
    {"provider_name": "Trier Seminary Library", "manifest_url": "https://www.dilibri.de/i3f/v21/1937135/manifest", "observed_status": "M4 HTTP 404", "included_in_valid_manifest_count": False},
]
save("unresolved_investigations.json", investigations)
summary["unresolved_investigation"] = investigations
save("summary.json", summary)
report = """# 93 个已验证来源：本轮结果（2026-10-22）

累计来源验证从 **86 增至 93 / 120 条清单记录**。本轮是 7 家新增图书馆，原始清单仍有 **27 条未完成**。
这是累计历史有界测试的来源条目数，不是去重后的独立机构数；也不是今天重新跑过全部 120 条，更不是已完成全馆下载。

| 本轮来源 | 发现 URL | M4 有效 Manifest | M7 图片关联 |
|---|---:|---:|---:|
"""
for p in read(root / "provider_results.json"):
    report += f'| {p["provider_name"]} | {p["discovered_manifest_urls"]} | {p["validated_manifests"]} | {p["exported_image_associations"]:,} |\n'
report += """
本轮发现 42 个 URL，**41 个 Manifest**经独立联网重取和结构校验通过，导出 **8,564 条图片关联记录**。
每家本次最多取 6 个 Manifest，不能将这些样本数量推成机构总量。

## 做完的内容与证据

- Module1 登记 7 家新来源，原 113 条记录和入口逐项不变。
- Module2 的 7 个选定入口全部可达，均返回 IIIF Collection JSON。
- Module3 复用现有 Collection、分页和机构范围配置；**没有修改运行时代码，也没有新增运行时 AI API**。
- Module4 重新联网获取 42 个，缓存命中 0。Trier 神学院的 `1937135` 返回 404，未算入有效文献，失败记录保留。
- Module5–7 导出 41 条文献主记录、8,564 条图片关联及 41 份 OCR 画像。
  29 个 unknown 权利文献按策略保留为研究用途；11 个公共领域、1 个开放许可。没有把 unknown 改成无版权。
- Module8 最终下载并验证 **7 张图片、21 份关联 JSON**，各图都能解码，JSON 结构与关联 ID 校验通过。
  Oldenburg 初选页为空白，已改为同文献第 26 个 Canvas；原样例保留在 `initial_examples/`。
  本轮实际下载过 8 张不同图片，最终展示目录有 7 套。莱比锡样图为 3840×5760，其余主要为宽 1000 像素的原站预览图。
- Oldenburg 图像含机构附加署名栏，实际为 1000×1254，Manifest 图像声明为 1000×1204。
  原图未裁剪，已记录这 50 像素差异；不能直接套用原始 OCR 坐标。其余 6 张与声明尺寸相符。
- 本批没有机构页面级参考文本，样例均在 **without_reference**；72 条 ground-truth 候选不是 72 份机构正确转录。
  之前的参考文本输出及配对样例没有删除或变更。
- 自动测试 **193 项全部通过，另有 7 个子测试通过**。

## 保存了哪些方法

1. Oldenburg：原生手稿 Collection `785124` → `members` → Manifest。
2. 莱比锡：原生顶层目录 → 希腊手稿 Collection → `manifests`。旧 UBLab 文档虽然跳转，原生 IIIF 服务仍可用。
3. Graz：Digi SCRIPT 手稿子站 → 原生 Collection；直接复用上一轮的机构路径保持配置，避免翻页进入整个 UniPub 平台。
4. Potsdam：Digitales Brandenburg 门户 → 原生 Collection。逐条保留数字版出版机构与原件持有方的区别，不能将合作方藏品统一归为 Potsdam 所有。
5. Koblenz 市图书馆、Worms 市图书馆、Trier 神学院图书馆：Dilibri 各自子站 → 原生 Collection。
   它们与前批的 Trier 大学、市图书馆等是不同来源，Dilibri 平台没有额外算一次。

7 条补充配置分别独立验证了 2 个 Manifest。另有 5 组 next 分页请求确认第二页不同；莱比锡目录和神学院这一级没有声明 next。
4 个带子站范围的来源另跑了较大预算：Koblenz、Worms、Graz 各发现 24 个唯一 URL，神学院目录发现 12 个。
全部 Collection 请求保持正确子站路径。这些额外 URL 不是全部经过 M4 的文献，没有重复加入本轮 41 个有效 Manifest。
本轮 **41 条有效文献**逐条检查了机构标签或数字版出版信息，7 个样本来源之间没有重复 Manifest URL。

正式知识库 **59 → 66 条**，旧 59 条和原 19 条预设入口完全保留。
新增通用审计命令 `verify_native_collection_recipes.py` 接收测试目录和机构核验配置，复现时不需要聊天上下文。
它验证配置和证据，尚不是自动调查陌生网站的 AI 系统；这一架构问题仍是后续任务。

## 中期汇报可使用的准确表述

> 目前已在累计有界测试中，为 93 个来源条目发现并验证了有效 IIIF Manifest。
> 本轮新增 7 家图书馆，以每家最多 6 个 Manifest 的样本测试，验证了 41 个文献、8,564 条图像关联，
> 并逐家实际下载图片与关联 JSON。现有方法以通用遍历代码和机构配置复用为主，未知机构的自动调查仍有待完善。

## 文件位置

- [逐来源统计](provider_results.csv)
- [图片和各自三份 JSON 的完整位置](sample_downloads.csv)
- [7 套最终样例](download_examples/module8/output/all/without_reference/)
- [Module7 样本输出](downstream/module7/output/)
- [分页检查](pagination_validation.json)
- [子站范围审计](collection_scope_verification.json)
- [41 条文献来源核验](institution_ownership_verification.json)
- [真实图像尺寸](image_decode_verification.json)
- [仍未完成的 27 条旧来源](remaining_unresolved_entries.csv)
- [可复制的运行命令](运行命令.txt)
- [方法、来源与边界](../../knowledge/institutions/2026-10-22_second_seven_provider_completion.md)
"""
(root / "本轮七机构验证结果_93来源.md").write_text(report, encoding="utf-8")
relative = "Code_git/Module_3/evaluation/2026-10-22_second_seven_provider_completion"
commands = f'''# PowerShell. Copy from this TXT, not PDF.
Set-Location -LiteralPath 'E:\\exchange-epfl\\Semester_Project'
$PipelinePython = 'E:\\exchange-epfl\\Semester_Project\\Code_git\\.venv\\Scripts\\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath $PipelinePython)) {{ throw 'Python not found' }}

# Module 1 registration already ran: {relative}/registration/module1/output
# Module 2 output: {relative}/validation/module2/output
& $PipelinePython -m iiif_entry_validator run --config '{relative}/module2_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 2 failed' }}

# Module 3 output: {relative}/validation/module3/output
& $PipelinePython Code_git/Module_3/tools/run_discovery_with_evidence.py --config '{relative}/module3_validation.json' --network-delay 0.6
if ($LASTEXITCODE -ne 0) {{ throw 'Module 3 failed' }}

# Module 4 output: {relative}/validation/module4/output
& $PipelinePython -m iiif_manifest_validator run --config '{relative}/module4_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 4 failed' }}

# Modules 5-7: {relative}/downstream/module5/output (and module6/module7)
# Module 8: {relative}/download_examples/module8/output/all/without_reference
# One reviewed image per source, not all 8564 image links.
& $PipelinePython Code_git/Module_3/tools/complete_oct19_provider_completion.py --evaluation-root '{relative}'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 5-8 failed' }}
& $PipelinePython Code_git/Module_3/tools/verify_linked_download_bundles.py --output-root '{relative}/download_examples/module8/output' --mode all --report '{relative}/bundle_verification.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Bundle verification failed' }}

# Reusable independent scope, recipe and source-metadata audit.
& $PipelinePython Code_git/Module_3/tools/verify_native_collection_recipes.py --evaluation-root '{relative}' --ownership-profile '{relative}/institution_ownership_rules.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Recipe verification failed' }}
& $PipelinePython Code_git/Module_3/tools/run_completion_test_suites.py --evaluation-root '{relative}'
if ($LASTEXITCODE -ne 0) {{ throw 'Tests failed' }}

Import-Csv -LiteralPath '{relative}/provider_results.csv' | Format-Table -AutoSize
Import-Csv -LiteralPath '{relative}/sample_downloads.csv' | Format-List
Invoke-Item -LiteralPath '{relative}/download_examples/module8/output/all/without_reference'
'''
(root / "运行命令.txt").write_text(commands, encoding="utf-8-sig")
print("93-source report and commands written; all 113 old census records preserved.")
