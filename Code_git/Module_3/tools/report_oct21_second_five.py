"""Write the Chinese source-completion report and copy-safe PowerShell steps."""

import json
from pathlib import Path


def main():
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / "evaluation/2026-10-21_second_five_provider_completion"
    read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    counts = read("provider_results.json")
    summary = read("summary.json")
    pixels = read("image_decode_verification.json")
    references = read("reference_alignment_verification.json")
    output = root / "download_examples/module8/output"
    bundles = [json.loads(line) for line in (output / "all/download_index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    by_provider = {}
    for bundle in bundles:
        directory = output / bundle["bundle_directory"]
        record = json.loads((directory / "common_record.json").read_text(encoding="utf-8"))
        by_provider[record["source"]["providers"][0]["provider_id"]] = directory
    image_by_resource = {p["resource_id"]: p for p in pixels["images"]}
    for reference in references:
        image = image_by_resource[reference["resource_id"]]
        reference["actual_image_dimensions"] = [image["width"], image["height"]]
        reference["bbox_matches_image"] = reference["hocr_page_bbox"] == f"bbox 0 0 {image['width']} {image['height']}"
        assert reference["bbox_matches_image"] and reference["hocr_words"] > 0
    (root / "reference_alignment_verification.json").write_text(json.dumps(references, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# 本轮新增五条来源：验证结果", "", "日期：2026-10-21（本日第二批）。", "",
             "已完成 **5 条原先未完成的来源**，累计由 **59/94 增至 64/94**，还有 **30 条**未完成。这里按既有清单的来源条目计数，包含馆藏子集和聚合来源，不等于 64 家独立机构；历史成功来源没有全部在今天重跑。", "",
             "## 实测结果", "", "| 来源 | 有效 Manifest | 图片记录 | 实际下载样例 |", "|---|---:|---:|---:|"]
    labels = ["BSB 东亚馆藏", "Cardiff University", "University of Leeds", "vHMML / DREAMSEA", "Yale University Library"]
    for label, row in zip(labels, counts):
        directory = by_provider[row["provider_id"]]
        link = (directory / "image.jpg").relative_to(root).as_posix()
        lines.append(f"| {label} | {row['validated_manifests']} | {row['exported_image_associations']:,} | [1 张：{row['actual_width']}×{row['actual_height']}]({link}) |")
    lines += ["", "合计 **26 个 Manifest、7,918 条图片记录、5 张已下载图片及 15 份配套 JSON**。26 个 Manifest 均由模块 4 重新联网获取，缓存命中为 0；模块 7 无记录或图片被拒绝；5 张图片均通过完整解码，尺寸与样例声明一致。", "",
              "这是受数量限制的样本验证，**7,918 条图片链接没有全部下载，也不是各馆总量**。Leeds 下载的是机构声明的 762×1024 衍生图，不代表原始扫描分辨率。", "",
              "## 已保存的获取方法", "",
              "- **BSB 东亚馆藏**：搜索结果中的 `data-manifest` 属性。使用 China 查询；该查询显示 108 个结果，分页参数 start 是从 0 开始的页码。它属于 BSB 的馆藏子集。",
              "- **Cardiff**：Primo 公开目录 → 筛选有数字资源的记录 → 提取 MMS ID → 原生 Alma Manifest。Ellor 查询中验证了 2 个数字文献，其他目录命中不是可用 Manifest。图片原始 body 链接返回 404，已有模块 8 通过其声明的 Image API 服务成功下载。",
              "- **Leeds**：公开的 IMC 中世纪手稿专题 Collection → 原生 Manifest。覆盖专题选集；主目录搜索仍返回 403。",
              "- **vHMML**：DREAMSEA 公开老挝目录 → 文献详情页 → 读取页面直接写出的 vHMML Manifest URL。两套系统的编号不同，不能直接互换。未绕过受限的 Reading Room 搜索。",
              "- **Yale 图书馆**：LUX 搜索 → Linked Art 条目 → 提取明确声明的图书馆 Manifest 链接。同一条目录记录可能包含多卷 Manifest；搜索估计数不能当成 Manifest 总数。", "",
              "已向本地知识库追加 4 个执行配置和 1 个 Collection 入口；旧有 33 个知识条目、18 个入口配置全部保留不变。具体证据与方法见 [机构调查笔记](../../knowledge/institutions/2026-10-21_second_five_provider_completion.md)。", "",
              "## 机构参考文本样例", "",
              "本轮 BSB 的六本文献声明了 **5,256 条页级 hOCR 链接**。这些是参考文本描述，不是 5,256 份已下载、已证明非空的训练标签。抽查第 10、20、50、100 页均有识别正文；最终下载包选择第 10 页。", "",
              "另发现封面页的 hOCR 只有文件名标题、没有正文；已修正模块 8，排除 HTML 的 head/title/script/style，空正文按参考文本失败处理，避免把文件名当成 OCR。", ""]
    reference_dir = by_provider[counts[0]["provider_id"]]
    for name, filename in [("中文古籍图片", "image.jpg"), ("机构原始 hOCR", "institution_reference_001.hocr.html"),
                           ("提取后的文本", "institution_reference_001.txt"), ("页级图片—文本关联", "institution_reference_texts.json"),
                           ("文献主记录", "common_record.json"), ("图片记录", "common_media.json"),
                           ("OCR 文献特征", "ocr_document_profile.json")]:
        lines.append(f"- [{name}]({(reference_dir / filename).relative_to(root).as_posix()})")
    lines += ["", "该页包含 **157 个 hOCR 词片段、373 个提取字符**；Canvas 为第 10 页，图片与 hOCR 坐标范围均为 **1731×2996**。这是机构给出的机器 OCR，仍可能有识别错误，不能直接称为人工校正的标准答案。", "",
              "当前结果分为 `with_reference`（1 组）和 `without_reference`（4 组）。参考文本下载失败时进入 `reference_failed`，不会混入有参考文本的训练样例。最初发现问题的旧样例只作错误证据保留，不是最终输出。", "",
              "## 检查与使用", "",
              f"模块 3–8 自动测试共 **{summary['tests_passed']} 项通过，另有 7 个子测试通过**。新增测试覆盖 HTML 详情页解析、URL 编码和空 hOCR 分类。模块 6 的 26 条文献记录为部分元数据完整状态，失败数为 0；来源缺少部分描述字段仍会如实保留。", "",
              "本轮版权策略下 26 个文献均保留用于既定学术分析流程，公开复用合格数为 0。原版权声明和限制保留在 JSON 中。", "",
              "- [复跑命令及查看输出的方法](运行命令.txt)",
              "- [分来源统计 CSV](provider_results.csv)", "- [每组图片与 JSON 的绝对路径](sample_downloads.csv)",
              "- [自动测试结果](test_results.json)", "- [图片解码结果](image_decode_verification.json)",
              "- [三份 JSON 的结构与关联核验](bundle_verification.json)",
              "- [图片—hOCR 对齐检查](reference_alignment_verification.json)",
              "- [尚未完成的 30 条来源](remaining_unresolved_entries.csv)", "",
              "这些是本地修改，本轮没有自动推送 GitHub，也未接入运行时 AI API。"]
    (root / "本轮五来源验证结果.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    commands = r'''# PowerShell：在新终端中从第一段开始运行。以下所有连字符均为 ASCII。
# 这次演示每个来源最多验证 6 个 Manifest、最终只下载每个来源的一张图片。
$ErrorActionPreference = 'Stop'
$ProjectRoot = 'E:\exchange-epfl\Semester_Project'
$CodeRoot = Join-Path $ProjectRoot 'Code_git'
$PipelinePython = Join-Path $CodeRoot '.venv\Scripts\python.exe'
$ImageCheckPython = 'C:\Users\43057\AppData\Local\Programs\Python\Python310\python.exe'
$RunRoot = Join-Path $CodeRoot 'Module_3\evaluation\2026-10-21_second_five_provider_completion'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:SSL_CERT_FILE = 'C:\Users\43057\AppData\Local\Programs\Python\Python310\lib\site-packages\certifi\cacert.pem'
if (-not (Test-Path -LiteralPath $PipelinePython)) { throw 'Project virtual environment not found' }
Set-Location $ProjectRoot

# 1. 从 Module 1 的既有清单选择本轮五条来源；保留其来源信息。
& $PipelinePython "$CodeRoot\Module_3\tools\prepare_oct21_second_five.py"
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
# 输入/配置：$RunRoot\selected_providers.jsonl 和 module2_validation.json 等。

# 2. Module 2：检查清单里的原始入口。
& $PipelinePython -m iiif_entry_validator run --config "$RunRoot\module2_validation.json"
if ($LASTEXITCODE -ne 0) { throw 'Module 2 failed' }
# 查看：$RunRoot\validation\module2\output 和 log。
# 原首页失败不代表不存在 IIIF；Module 3 还执行已经核验、保存的发现配置。

# 3. Module 3：运行本轮保存的四个发现配置和一个 Collection 入口。
& $PipelinePython "$CodeRoot\Module_3\tools\run_discovery_with_evidence.py" --config "$RunRoot\module3_validation.json" --network-delay 0.5
if ($LASTEXITCODE -ne 0) { throw 'Module 3 failed' }
# 查看：$RunRoot\validation\module3\output\manifest_urls.jsonl。

# 4. Module 4：独立获取并校验 Manifest。
& $PipelinePython -m iiif_manifest_validator run --config "$RunRoot\module4_validation.json"
if ($LASTEXITCODE -ne 0) { throw 'Module 4 failed' }
# 查看：$RunRoot\validation\module4\output 和 raw_manifests。

# 5. 依次执行 Module 5、6、7、8；末步只给五个样例下载图片和配套 JSON。
& $PipelinePython "$CodeRoot\Module_3\tools\complete_oct19_provider_completion.py" --evaluation-root $RunRoot
if ($LASTEXITCODE -ne 0) { throw 'Downstream execution failed' }
# 查看版权：$RunRoot\downstream\module5\output。
# 查看规范化记录：$RunRoot\downstream\module6\output。
# 查看最终 JSONL：$RunRoot\downstream\module7\output。
# 查看样例：$RunRoot\download_examples\module8\output\all\with_reference 和 without_reference。
# 各样例含 image.jpg、common_record.json、common_media.json、ocr_document_profile.json。
# 有参考文本的还含 hOCR、txt、institution_reference_texts.json。
# 还要查看 Module 8 运行摘要中的 failed_images/reference_text_failures，不能只看退出码。

# 6. 校验五个下载包的三份 JSON 和关联。
& $PipelinePython "$CodeRoot\Module_3\tools\verify_linked_download_bundles.py" --output-root "$RunRoot\download_examples\module8\output" --mode all --report "$RunRoot\bundle_verification.json"
if ($LASTEXITCODE -ne 0) { throw 'Bundle verification failed' }

# 7. 完整解码图片。此 Python 已安装 Pillow，仅用于额外核验。
& $ImageCheckPython "$CodeRoot\Module_3\tools\verify_downloaded_pixels.py" --module8-output "$RunRoot\download_examples\module8\output" --raw-manifest-directory "$RunRoot\validation\module4\raw_manifests" --mode all --report "$RunRoot\image_decode_verification.json"
if ($LASTEXITCODE -ne 0) { throw 'Image verification failed' }

# 8. 运行 Module 3-8 自动测试，结果写入 test_results.json。
& $PipelinePython "$CodeRoot\Module_3\tools\run_completion_test_suites.py" --evaluation-root $RunRoot
if ($LASTEXITCODE -ne 0) { throw 'Regression tests failed' }

# 9. 打开本轮输出文件夹。
Invoke-Item "$RunRoot\download_examples\module8\output\all"
Invoke-Item "$RunRoot\downstream\module7\output"

# 不要删除 Module 1 的输入清单、配置和知识库。网络结果可能随机构变化。
'''
    (root / "运行命令.txt").write_text(commands, encoding="utf-8-sig")
    print("Report and PowerShell instructions written:", root)


if __name__ == "__main__":
    main()
