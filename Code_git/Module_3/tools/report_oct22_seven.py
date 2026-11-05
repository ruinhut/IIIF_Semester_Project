"""Reconcile the 86-source milestone and write its Chinese evidence report."""
import json
from pathlib import Path

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-22_seven_provider_completion"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


before = {p["provider_id"]: p for p in rows(root / "before_provider_census.jsonl")}
after = {p["provider_id"]: p for p in rows(code / "Module_1/data/output/providers.jsonl")}
assert len(before) == 106 and len(after) == 113
assert all(after.get(key) == value for key, value in before.items())
save("census_preservation_check.json", {"before_entries": 106, "after_entries": 113,
    "new_institutions": 7, "old_entries_unchanged": True})
ownership = read(root / "institution_ownership_verification.json")
scope = read(root / "collection_scope_verification.json")
assert len(ownership["sample_manifest_ownership_checks"]) == 23
assert len(scope) == 4 and all(v["all_requests_keep_institution_scope"] for v in scope)
summary = read(root / "summary.json")
assert summary["cumulative_resolved_census_entries"] == 86 and summary["configuration_promoted"]
summary.update(new_institutions=7, restored_old_sources=0, old_census_entries=94,
    old_census_resolved=67, old_census_remaining=27, tests_subtests_passed=7,
    actual_downloaded_reference_texts=0, total_images_downloaded_including_initial_examples=9,
    final_sample_images=7, separately_validated_fallback_recipes=7,
    separately_checked_pagination_pairs=7, institution_scoped_24_url_runs=4,
    independently_verified_holder_metadata_records=23,
    all_final_sample_dimensions_match_declared_image_body=True,
    scope_note="79 historical successes plus seven additional libraries. Cumulative source entries are not a deduplicated institution count; earlier successes were not all re-fetched today.")
failures = [
    {"provider_name": "Finna", "observed_status": "HTTP 403 on the public API search", "counted_as_new_success": False},
    {"provider_name": "University of Illinois", "observed_status": "HTTP 403 on catalogue JSON", "counted_as_new_success": False},
    {"provider_name": "North Carolina State University", "observed_status": "HTTP 401 on catalogue JSON", "counted_as_new_success": False},
    {"provider_name": "Hamburg", "observed_status": "HTML CAPTCHA / browser challenge", "counted_as_new_success": False},
    {"provider_name": "Halle", "observed_status": "HTTP 404 on guessed Collection routes", "counted_as_new_success": False},
    {"provider_name": "Folger / Bremen / Wuppertal / Luebeck", "observed_status": "URLError; exact errors retained in probe checks", "counted_as_new_success": False},
    {"provider_name": "Dilibri partner HTML history pages", "observed_status": "HTTP 200 browser verification page, not a catalogue", "resolution": "Native public IIIF Collections work; do not run the challenge or count the HTML response as discovery."},
    {"provider_name": "Trier City Library", "manifest_url": "https://www.dilibri.de/i3f/v21/2799234/manifest",
     "observed_status": "M4 HTTP 404", "included_in_valid_manifest_count": False},
]
save("unresolved_investigations.json", failures)
summary["unresolved_investigation"] = failures
save("summary.json", summary)
report = """# 已达到 86 个成功来源：本轮 7 家机构验证（2026-10-22）

累计成功来源从 **79 增至 86 / 113 条**。本轮新增 7 家此前不在清单中的图书馆，原始 94 条清单仍有 **27 条未完成**。
旧清单中的部分入口本次重试仍被限制；未将它们包装为成功。累计是保留历史证据的来源条目数，不是去重后的机构数，
也不表示今天重新检查了全部 113 条。

| 本轮机构 | 发现 Manifest URL | M4 有效 Manifest | 图片关联记录 |
|---|---:|---:|---:|
"""
for p in read(root / "provider_results.json"):
    report += f'| {p["provider_name"]} | {p["discovered_manifest_urls"]} | {p["validated_manifests"]} | {p["exported_image_associations"]:,} |\n'
report += """
本轮发现 **42 个 URL**，其中 **41 个 Manifest**经独立联网重取和结构校验通过，共导出 **2,303 条图片关联记录**。
每家本次最多取 6 个 Manifest；这些不是机构总量，也不是 2,303 张图片已经全部下载。

## 已完成的链路

- Module1：登记 7 家新机构；原 106 条记录及入口保持不变。Dilibri 平台本身没有另算第 8 家。
- Module2：7 个入口全部可达，均返回原生 IIIF Collection JSON。
- Module3–4：发现 42 个，重取 42 个，缓存命中 0；Trier 市图书馆的一条目录成员链接返回 404，已排除并保留记录。
- Module5–7：导出 41 条文献主记录、2,303 条图片关联、41 份 OCR 画像。
  其中 35 个 unknown 权利文献按现有策略保留为研究用途，6 个标为公共领域；没有将 unknown 改成无版权。
- Module8：最终每家有 1 张真实图片及 3 份配套 JSON，合计 **7 张图片、21 份 JSON**。
  全部能解码，JSON 结构与文献/页面 ID 关联检查通过，7 张图片的实际尺寸均与声明的图像尺寸相符。
  这些多数是宽 1000 像素的原站预览图，尺寸相符不代表已取得最高分辨率。
- 本轮没有机构页面级参考文本，故最终样例位于 **without_reference**。59 条 ground-truth 候选不等于机构正确转录，
  不新增训练集承诺。已有 with_reference 功能和旧配对样例保留。
- 初始 Detmold 和 Rheinland-Pfalz 样例是空白页，已改选有内容的页面。两个初始样例与下载证据保存在
  `initial_examples/` 和 `initial_download_index.jsonl`；本次总共下载过 9 张不同图片，最终展示目录保留 7 个样例包。

## 本轮修复的泛化问题

维也纳、Detmold、科隆直接使用其原生 Collection。其余 4 家在 Dilibri 上是独立的馆藏持有机构，
分别使用 `rlb`、`ubtr`、`stbtr`、`stbmz` 路径。虽然首个 Collection 按机构筛选，服务器返回的子 Collection 和
`next` 链接却丢失这一机构路径；直接跟随会混入整个聚合平台的其他机构。

本轮为 Module3 增加**经审核、同站点、仅作用于 Collection 链接的路径映射配置**。它保留机构范围，
不改写 Manifest 或图片链接，不改变 Module4–8 的输出合同。原声明链接和实际请求链接都进入审计记录。
未配置的旧来源行为不变；跨站、过宽及错误类型的配置会记录问题并拒绝使用。

- 7 家的第二页均已实际读取，成员与第一页不同。
- 4 家 Dilibri 来源各做了 **24 个唯一 URL**的额外发现实验，所有 Collection 请求均保持机构路径。
  Mainz 的 24 个 URL 包含子馆藏，达到上限前尚未访问根目录 next；其 next 另有独立请求证据。
  这些额外发现 URL 未全部重取为 Manifest，没有加入上面的 41 个有效文献数量。
- 4 家的 **23 个有效样本文献**逐条核对了机构 attribution 和 Online-Ausgabe；跨馆 Manifest URL 无重复。
- 7 条补充发现配置各独立验证 2 个 Manifest；这些额外验证没有重复计数。
- Module3–8 自动测试 **193 项通过，另 7 个子测试通过**；包含新增的 6 项机构范围/错误配置测试。
- 正式知识库 **52 → 59 条**，旧 52 条及 19 条预设入口保持一致。未增加运行时 AI API。

## 查看文件

- [机构数量 CSV](provider_results.csv)
- [7 张图片及配套 JSON 的完整路径](sample_downloads.csv)
- [最终样例文件夹](download_examples/module8/output/all/without_reference/)
- [Module7 完整样本输出](downstream/module7/output/)
- [4 家机构归属核验](institution_ownership_verification.json)
- [实际跨页/子馆藏请求与范围审计](collection_scope_verification.json)
- [分页检查](pagination_validation.json)
- [仍未完成的 27 条旧来源](remaining_unresolved_entries.csv)
- [运行命令](运行命令.txt)
- [调查过程及复用规则](../../knowledge/institutions/2026-10-22_seven_provider_completion.md)
"""
(root / "本轮七机构验证结果.md").write_text(report, encoding="utf-8")
relative = "Code_git/Module_3/evaluation/2026-10-22_seven_provider_completion"
commands = f'''# PowerShell. Copy from TXT, not PDF.
Set-Location -LiteralPath 'E:\\exchange-epfl\\Semester_Project'
$PipelinePython = 'E:\\exchange-epfl\\Semester_Project\\Code_git\\.venv\\Scripts\\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath $PipelinePython)) {{ throw 'Python not found' }}

# Module 1 registration already ran: {relative}/registration/module1/output
# Native endpoints and institution scope rules are saved in configuration.
# Module 2 output: {relative}/validation/module2/output
& $PipelinePython -m iiif_entry_validator run --config '{relative}/module2_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 2 failed' }}

# Module 3 output: {relative}/validation/module3/output
& $PipelinePython Code_git/Module_3/tools/run_discovery_with_evidence.py --config '{relative}/module3_validation.json' --network-delay 0.6
if ($LASTEXITCODE -ne 0) {{ throw 'Module 3 failed' }}

# Module 4 output: {relative}/validation/module4/output
& $PipelinePython -m iiif_manifest_validator run --config '{relative}/module4_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 4 failed' }}

# Module 5-7: {relative}/downstream/module5/output (and module6/module7)
# Module 8: {relative}/download_examples/module8/output/all/without_reference
# Downloads one reviewed page per provider, not the complete 2303-image inventory.
& $PipelinePython Code_git/Module_3/tools/complete_oct19_provider_completion.py --evaluation-root '{relative}'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 5-8 failed' }}
& $PipelinePython Code_git/Module_3/tools/verify_linked_download_bundles.py --output-root '{relative}/download_examples/module8/output' --mode all --report '{relative}/bundle_verification.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Bundle verification failed' }}

# Supplementary checks are separate from the end-to-end sample count.
& $PipelinePython Code_git/Module_3/tools/validate_oct22_seven.py
if ($LASTEXITCODE -ne 0) {{ throw 'Scope/recipe verification failed' }}
& $PipelinePython Code_git/Module_3/tools/run_completion_test_suites.py --evaluation-root '{relative}'
if ($LASTEXITCODE -ne 0) {{ throw 'Tests failed' }}

Import-Csv -LiteralPath '{relative}/provider_results.csv' | Format-Table -AutoSize
Import-Csv -LiteralPath '{relative}/sample_downloads.csv' | Format-List
Invoke-Item -LiteralPath '{relative}/download_examples/module8/output/all/without_reference'
'''
(root / "运行命令.txt").write_text(commands, encoding="utf-8-sig")
print("86-source milestone report, commands and census preservation verified.")
