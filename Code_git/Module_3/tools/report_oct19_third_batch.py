"""Write concise human-readable evidence and reproducible commands for batch 3."""
import json
from pathlib import Path


def main():
    module = Path(__file__).resolve().parents[1]
    root = module / 'evaluation/2026-10-19_third_five_provider_completion'
    summary = json.loads((root / 'summary.json').read_text(encoding='utf-8'))
    counts = json.loads((root / 'provider_results.json').read_text(encoding='utf-8'))
    lines = ['# 第三批五个来源：验证结果', '', '日期：2026-10-19。', '',
             '| 来源 | 有效 Manifest | 图片关联记录 | 去重图片 URL | 实际图片 |', '|---|---:|---:|---:|---:|']
    lines += [f"| {p['provider_name']} | {p['validated_manifests']} | {p['exported_image_associations']:,} | {p['distinct_image_urls']:,} | 1 |" for p in counts]
    lines += ['', f"合计 **{summary['validated_manifests']} 个 Manifest、{summary['exported_image_associations']:,} 条图片关联记录、{summary['distinct_image_urls']:,} 个去重图片 URL**。实际下载 **5 张图片和 15 份主要 JSON**，不是下载了所有图片。", '',
              '## 方法与范围', '',
              '- DRI：原生嵌套 Collection，当前验证 Hingston 档案集合。',
              '- Princeton 艺术馆：官方对象 API 的 maker 筛选及 from/size 分页，再以对象 ID 获取原馆 Manifest；当前样本为 Edgar Degas。',
              '- UCLA：Blacklight JSON 目录，提取完整 ARK 并编码为 Manifest 路由；当前为 map 查询。',
              '- SCTA：作者/文本 Collection → Manifest → 已声明的图片服务。它是文本研究平台，不能冒充一个独立原藏图书馆。',
              '- Smithsonian：官方专题页的直接 Manifest 链接；当前为精选专题，不是机构全量目录。', '',
              '原有 EPFL、Princeton 图书馆等配置未被替换；Princeton 艺术馆与大学图书馆是两条不同发现路线。',
              '[详细方法、原始链接和限制](../../knowledge/institutions/2026-10-19_third_provider_completion.md)。', '',
              '## 修正与验证', '',
              '- Smithsonian 首次被拒绝的原因是历史 Shared Canvas context。现在仅在明确开启兼容选项时接受精确的旧 context 和相应结构；M4 保留原始 JSON、source_format 与警告。6 个旧格式样本通过的是兼容结构检查，不是现代 Presentation 2/3 合规认证。',
              '- 修正了 M6 将普通藏品 HTML seeAlso 页面误标为 OCR 的问题；明确的转录、ALTO、hOCR 和页面 supplementing 文本继续支持。',
              f"- 30/30 Manifest 由 M4 独立联网请求并检查，未用旧缓存冒充本轮抓取。M3–8 自动测试 **{summary['tests_passed']} 项全部通过**，另有 7 个子测试。",
              '- 5 张图片全部真实解码成功；15 份 JSON 通过 schema、ID、路径及图片关联校验。M6 分类修正后的重跑复用了本轮已经下载的图片，原始下载日志仍保留。', '',
              '## 输出的实际限制', '',
              '- 本轮没有交付已核对的图片—机构 OCR 参考文本对；普通目录说明不能当作训练答案。SCTA 的 external AnnotationList 是后续调查线索，本轮未抓取和验证其页级文本。',
              '- UCLA 和 Smithsonian 的样例图片像素小于 Canvas 声明；实际尺寸见下表和 image_decode_verification.json。没有把这些图片当作原始分辨率，OCR 坐标匹配需另行核对。',
              '- DRI 的原文权限限制仍保留；学术研究样例可用不意味着可公开发布或商业再利用。',
              '- Folger、Illinois、Getty、Parliamentary Archives 和 Cultural Japan 的本轮未完成路线保留在 unresolved_investigations.json，未计入成功。', '',
              '| 来源 | 实际样例像素 | Canvas/图片声明像素 |', '|---|---|---|']
    lines += [f"| {p['provider_name']} | {p['actual_width']} × {p['actual_height']} | {p['canvas_width']} × {p['canvas_height']} |" for p in counts]
    lines += ['', '## 累计与查看文件', '',
              f"累计 **{summary['previous_resolved_census_entries']} → {summary['cumulative_resolved_census_entries']} / {summary['census_entries']} 个来源条目**，剩余 **{summary['remaining_unresolved_census_entries']}**。累计沿用历史实测证据，不是本轮重新联网检查全部 94 条；来源数量不等于独立原藏机构数量。",
              '- provider_results.csv：逐来源 Manifest、媒体和像素数量。',
              '- sample_downloads.csv：每张图片及三个配套 JSON 的完整路径。',
              '- downstream/module7/output：本轮完整文献、图片关联及 OCR 画像 JSONL。',
              '- download_examples/module8/output/all/without_reference：真实图片和 JSON 文件包。',
              '- 运行命令.txt：可直接复制的 PowerShell 命令；仅重跑本轮样本。',
              '- knowledge_preservation_check.json：旧知识未被覆盖的核查。',
              '- cleanup_manifest.json：临时探测响应清理记录；正式代码、可执行方法、原始 Manifest、日志和最终样例保留。', '']
    (root / '本轮五来源验证结果.md').write_text('\n'.join(lines), encoding='utf-8')
    commands = [
        "$CodeRoot = 'E:\\exchange-epfl\\Semester_Project\\Code_git'",
        "$PipelinePython = Join-Path $CodeRoot '.venv\\Scripts\\python.exe'",
        "$EvaluationRoot = Join-Path $CodeRoot 'Module_3\\evaluation\\2026-10-19_third_five_provider_completion'",
        "$env:PYTHONIOENCODING = 'utf-8'",
        "# Valid CA bundle on this computer. Keep certificate/hostname verification enabled.",
        "$env:SSL_CERT_FILE = 'C:\\Users\\43057\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\certifi\\cacert.pem'",
        'Set-Location -LiteralPath $CodeRoot', '',
        '& $PipelinePython Module_3\\tools\\run_discovery_with_evidence.py --config "$EvaluationRoot\\module3_validation.json"',
        'if ($LASTEXITCODE -ne 0) { throw "Module 3 failed" }',
        '& $PipelinePython -m iiif_manifest_validator run --config "$EvaluationRoot\\module4_validation.json"',
        'if ($LASTEXITCODE -ne 0) { throw "Module 4 failed" }',
        '& $PipelinePython Module_3\\tools\\complete_oct19_provider_completion.py --evaluation-root $EvaluationRoot',
        'if ($LASTEXITCODE -ne 0) { throw "Module 5-8 failed" }',
        '& $PipelinePython Module_3\\tools\\verify_linked_download_bundles.py --output-root "$EvaluationRoot\\download_examples\\module8\\output" --report "$EvaluationRoot\\bundle_verification.json"',
        'Import-Csv -LiteralPath "$EvaluationRoot\\provider_results.csv" | Format-Table -AutoSize',
        'Import-Csv -LiteralPath "$EvaluationRoot\\sample_downloads.csv" | Format-List', '',
    ]
    (root / '运行命令.txt').write_text('\n'.join(commands), encoding='utf-8')


if __name__ == '__main__':
    main()
