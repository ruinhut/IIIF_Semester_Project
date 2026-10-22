"""Write precise Chinese results and copy-safe reproduction commands."""
import csv
import json
from pathlib import Path

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-21_third_five_provider_completion"
read = lambda path: json.loads(path.read_text(encoding="utf-8"))
summary = read(root / "summary.json")
counts = read(root / "provider_results.json")
before = {json.loads(s)["provider_id"]: json.loads(s) for s in (root / "before_provider_census.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()}
after = {json.loads(s)["provider_id"]: json.loads(s) for s in (code / "Module_1/data/output/providers.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()}
assert set(before) <= set(after)
for identifier, provider in before.items():
    for endpoint in provider["endpoints"]:
        assert endpoint in after[identifier]["endpoints"]
    if identifier not in {"provider-acb86cbbcb639914", "provider-3acece25cdf777e4"}:
        assert provider == after[identifier]
registration = {"old_entries": len(before), "new_entries": len(after) - len(before),
                "current_entries": len(after), "old_ids_and_endpoints_preserved": True,
                "restored_old_entries": 2, "added_new_institutions": 3,
                "old_census_resolved": 66, "old_census_remaining": 28}
(root / "census_preservation_check.json").write_text(json.dumps(registration, indent=2) + "\n", encoding="utf-8")
summary.update(registration)
summary["tests_subtests_passed"] = 7
(root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
text = """# 本轮 5 个来源更新结果（2026-10-21）

本轮已完成 5 个来源的 Manifest 发现、结构校验、Module5–7 导出与 Module8 实际图片下载。
其中 **2 个是原清单恢复的来源，3 个是新增机构**。当前累计为 **69/97 个来源条目**；
原来 94 条中有 66 条已有成功证据，28 条仍未完成。此前成功来源未在本轮全部重新请求。

| 来源 | 本轮变化 | 校验通过的 Manifest | 图片关联记录 |
|---|---|---:|---:|
"""
for p in counts:
    kind = "恢复旧来源" if p["provider_id"] in before else "新增机构"
    text += f'| {p["provider_name"]} | {kind} | {p["validated_manifests"]} | {p["exported_image_associations"]:,} |\n'
text += """
合计 **25 个 Manifest、3,635 条图片关联记录**。实际下载 **5 张样例图片**，每张均附带
`common_record.json`、`common_media.json`、`ocr_document_profile.json`。
15 份 JSON 通过结构和关联校验，5 张图片均能解码。**关联记录数不是实际已下载图片数，也不是机构总量。**

## 本轮保存的方法

- **英国图书馆**：从官方数字化精选页面的查看器链接读取原生 Manifest URL；范围是精选目录，不是全部馆藏。
- **Indigenous Digital Archive / DigiTreaties**：从公开条约目录提取条约 ID，访问该条约的 Manifest；图片来自其声明的美国国家档案馆服务。
  机构官方公告证明项目关联，但这不代表旧寄宿学校档案网站已全部恢复。
- **海德堡大学图书馆**：读取公开 OAI-PMH XML 的 `dc:hasFormat` 链接；保存 XML 命名空间与续页 token 的处理方法。
- **日本国会图书馆**：OpenSearch RSS 返回数字馆藏 PID，再使用官方 Manifest 模板；已验证翻页。
- **V&A**：公开馆藏 API 提供对象标识符，使用官方 `systemNumber` 模板；整条流水线本轮保留 1 个 Manifest。
  单独测试配置化方法另通过 6 个 Manifest，结果在 `vam_recipe_validation.json`，未重复计入上表。

Module3 新增通用 XML 目录技能，支持数值分页、命名空间、属性取值及 OAI-PMH 续页。
正式知识库由 37 条增加至 42 条；原 37 条和 19 条预设入口全部保留不变。
Module1 的手工维护来源已更新；原有 ID 和入口保留，新增机构由 Module1 自身生成规范记录。

## 失败与边界没有被隐藏

- 日本目录中的一个候选 Manifest 返回 404，程序继续下一条和下一页，最终保留 6 个有效 Manifest。
- DigiTreaties 的首选样例仍引用旧域名，图片返回 403。没有绕过限制；失败记录保存在
  `initial_failed_downloads.jsonl`，最终选择明确声明公共 NARA 图片的条约 81147473。
  因此不能声称所有发现的图片链接均能下载。
- 日本样例按已有图片服务降级逻辑取得 3340×2203 图片；Canvas 标注为 6680×4406，不能称为原始分辨率。
- 本批样例没有声明关联的机构参考文本，输出全部进入 `without_reference`。
  不把 OCR 候选提示、普通描述或元数据 XML 当成已验证参考文本。
- 本轮每来源最多保留 6 个 Manifest。英国精选、DigiTreaties 条约、海德堡更新日期、日本历史标题、V&A 手稿查询均有明确范围。
- 日本 OpenSearch 只能访问前 500 条匹配结果；大规模采集应分割查询，或使用官方 OAI-PMH 采集接口。
- 本次没有新增运行时 AI API，也没有将其描述为已经实现。

## 验证与文件位置

- Module2：5 个来源、9 个入口，5 个来源均有可访问入口；旧失效入口仍保留检查结果。
- Module4：25 个 Manifest 全部重新下载校验，通过 25，缓存命中 0。
- Module5–7：25 条文献记录、3,635 条图片关联、25 份 OCR 画像。
- Module8：5 张图片与 15 份配套 JSON；参考文本样例 0。
- Module3–8：**182 项测试全部通过，另有 7 个子测试通过**；其中新增 XML 测试 3 项。

查看结果：

- [机构统计表](provider_results.csv)
- [图片及三份 JSON 的完整位置](sample_downloads.csv)
- [实际样例目录](download_examples/module8/output/all/without_reference/)
- [Module7 全量样本输出](downstream/module7/output/)
- [累计来源状态](cumulative_provider_status.csv)
- [剩余 28 条](remaining_unresolved_entries.csv)
- [运行命令](运行命令.txt)
- [知识库中的调查记录](../../knowledge/institutions/2026-10-21_third_five_provider_completion.md)
- [通用 XML 方法](../../knowledge/skills/xml_catalogue_discovery.md)

报告中的“累计成功”表示各次有界样本的历史证据，不能视为对整个机构或全部资源的完整认证。
"""
(root / "本轮五来源验证结果.md").write_text(text, encoding="utf-8")
relative = "Code_git/Module_3/evaluation/2026-10-21_third_five_provider_completion"
commands = f'''# PowerShell; ASCII command punctuation. Existing five-source input is retained.
Set-Location -LiteralPath 'E:\\exchange-epfl\\Semester_Project'
$PipelinePython = 'E:\\exchange-epfl\\Semester_Project\\Code_git\\.venv\\Scripts\\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath $PipelinePython)) {{ throw 'Python executable not found' }}

# Module 1 registration outputs: {relative}/registration/module1/output
# The production manual source already includes the additions and recovered endpoints.
# Rebuild the complete census only when desired, with normal Module 1 configuration.

# Module 2; output: {relative}/validation/module2/output
& $PipelinePython -m iiif_entry_validator run --config '{relative}/module2_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 2 failed' }}

# Module 3; omit --resume to request fresh discovery responses.
# Output: {relative}/validation/module3/output
& $PipelinePython Code_git/Module_3/tools/run_discovery_with_evidence.py --config '{relative}/module3_validation.json' --network-delay 0.6
if ($LASTEXITCODE -ne 0) {{ throw 'Module 3 failed' }}

# Module 4; output: {relative}/validation/module4/output
& $PipelinePython -m iiif_manifest_validator run --config '{relative}/module4_validation.json'
if ($LASTEXITCODE -ne 0) {{ throw 'Module 4 failed' }}

# Modules 5, 6, 7 then five selected images through Module 8.
# Outputs: {relative}/downstream/module5/output (and module6, module7)
# Images and linked JSON: {relative}/download_examples/module8/output/all/without_reference
& $PipelinePython Code_git/Module_3/tools/complete_oct19_provider_completion.py --evaluation-root '{relative}'
if ($LASTEXITCODE -ne 0) {{ throw 'Downstream execution failed' }}

# Verify five successful bundles; inspect failed_downloads.jsonl if any are absent.
& $PipelinePython Code_git/Module_3/tools/verify_linked_download_bundles.py --output-root '{relative}/download_examples/module8/output' --mode all --report '{relative}/bundle_verification.json'
& $PipelinePython Code_git/Module_3/tools/run_completion_test_suites.py --evaluation-root '{relative}'

# Open the image/JSON path index.
Invoke-Item -LiteralPath '{relative}/sample_downloads.csv'
'''
assert '\u2010' not in commands and '\u2011' not in commands
(root / "运行命令.txt").write_text(commands, encoding="utf-8-sig")
print("Report, commands and census preservation checks written.")
