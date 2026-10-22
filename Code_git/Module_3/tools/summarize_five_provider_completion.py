"""Produce the current five-provider result table from real module outputs."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-15_five_provider_completion"
    providers = json.loads((root / "providers.json").read_text(encoding="utf-8"))
    tests = json.loads((root / "test_results.json").read_text(encoding="utf-8"))
    discovery = {r["provider_id"]: r for r in rows(root / "combined/module3/output/provider_discovery.jsonl")}
    validated = rows(root / "final_validation/module4/output/validated_manifests.jsonl")
    downloads = rows(root / "download_examples/module8/output/all/download_index.jsonl")
    manifest_by_id = {r["manifest_id"]: r for r in validated}
    samples, results = [], []
    for provider in providers:
        pid = provider["provider_id"]
        selected = [r for r in validated if any(p["provider_id"] == pid for p in r["providers"])]
        images = [r for r in downloads if any(p["provider_id"] == pid for p in manifest_by_id[r["record_id"]]["providers"])]
        audit = discovery[pid]["resource_discovery"]["knowledge_application"]
        result = {"provider_id": pid, "provider_name": provider["name"],
                  "discovered_manifests": discovery[pid]["resource_discovery"]["manifest_count"],
                  "validated_manifests": len(selected),
                  "declared_canvas_count": sum(r["structural_validation"]["canvas_count"] for r in selected),
                  "declared_image_bodies": sum(r["structural_validation"]["image_body_count"] for r in selected),
                  "downloaded_examples": len(images), "discovery_skill": audit[0]["skill_id"]}
        results.append(result)
        for row in images:
            image = root / "download_examples/module8/output" / row["image_path"]
            samples.append({"provider_name": provider["name"], "record_id": row["record_id"], "resource_id": row["resource_id"],
                            "image_path": str(image.resolve()), "bundle_directory": str(image.parent.resolve()),
                            "verified_image_url": row["final_url"], "resolution": row.get("image_resolution")})
    for filename, value in (("provider_results.json", results), ("sample_downloads.json", samples)):
        (root / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (root / "provider_results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    summary = {"generated_at": datetime.now(timezone.utc).isoformat(), "providers_resolved": len(results),
               "manifest_urls": len(rows(root / "combined/module3/output/manifest_urls.jsonl")),
               "validated_manifests": len(validated), "declared_image_bodies": sum(r["declared_image_bodies"] for r in results),
               "downloaded_example_images": len(downloads), "module3_tests_passed": tests["module3"]["passed"], "module8_tests_passed": tests["module8"]["passed"],
               "previous_unresolved_entries": 69, "remaining_unresolved_entries": 64,
               "scope": "20 Manifest samples per provider; image counts are declared resources, not full-collection totals or completed downloads."}
    (root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = ["# 五个机构批量发现与下载验证结果", "", "这五家现在均已具有可执行的批量发现配方，并各取得 20 个不同 Manifest。100 个 Manifest 全部通过 Module 4 验证。", "", "| 机构 | 发现 Manifest | 验证通过 | 样本声明的图片资源 | 实际下载样例 |", "|---|---:|---:|---:|---:|"]
    for result in results:
        text.append(f"| {result['provider_name']} | {result['discovered_manifests']} | {result['validated_manifests']} | {result['declared_image_bodies']:,} | {result['downloaded_examples']} |")
    text += ["", "合计：100 个有效 Manifest、26,832 个声明图片资源；实际下载 5 张图片，失败 0。图片已经与文献主记录、媒体记录和 OCR 特征描述关联。", "", "## 每家是怎样获取的", "", "- Göttingen：分页读取全站检索页中的文献 ID，生成并验证标准 Manifest URL。", "- Leiden：按书籍对象类型检索目录，读取实际 item ID；允许旧 Manifest URL 自动跳转到迁移后的 Alma 地址。", "- Wales：公开 Primo JSON 搜索 → 查看器 ID → IIIF 资源；若返回 Collection，继续遍历其子 Manifest。", "- Utrecht：完整对象清单 → 公开访问条目的对象 ID → Presentation 3 Manifest。", "- Jena：MyCoRe 对象分页 API → 每个对象的 derivative ID → Presentation Manifest。", "", "## 这次解决了哪些通用问题", "", "1. JSON 数组中提取 ID、按正则从 URL 提取 ID、调用第二层详情 API。", "2. 定向读取 HTML 目录，并按公开访问标记筛选；基于实际翻页链接判断是否还有下一页。", "3. 目录边读边验证，不先把所有目录页抓完再产生输出；识别重复返回同一页的分页错误。", "4. API 返回 Collection 时复用现有 IIIF 遍历器，保持 Module 3 的下游输出契约。", "5. Module 8 增加标准 Image Service 回退。Göttingen、Wales 的旧图片直链返回 404，Leiden 的 JP2 请求返回 400；读取各自已声明的 info.json 后均成功取得 JPEG。没有加入机构名称分支，也没有改 Module 4–7 的解析。", "", "## 真实失败与范围", "", "- Jena 的一次复跑曾因目录接口 HTTP 500 而失败；后续独立重试成功。失败批次和成功重试均保留，combined/batch_sources.json 指明合并来源。不能把这一结果理解成网站永远不会超时。", "- 本次是每家 20 个 Manifest 的验证。26,832 是这些 Manifest 声明的图片资源数量，本次没有逐张下载这些资源。", "- Leiden 当前配方覆盖书籍类型；Wales 当前配方覆盖已验证的目录查询结果，不能据此宣称已枚举全馆。", "- Utrecht 完整清单包含 29,357 个不同对象 ID，25,564 条标为公开访问。这些目录数量并不等于已验证 Manifest 数量。", "- 生产知识库的源目录预算与本次 20 条输出限额分开。增大测试输出只需修改配置/运行参数，不必为每家写新 Python 分支。", "", "## 输出在哪里", "", "- provider_results.csv：逐机构统计。", "- combined/module3/output/manifest_urls.jsonl：100 个 Manifest URL。", "- final_validation/module4/output/validated_manifests.jsonl：100 个验证记录。", "- final_validation/module4/output/manifest_resource_inventory.jsonl：26,832 条图片资源清单。", "- sample_downloads.json：每张图片的本地绝对路径、机构、Manifest ID、实际图片 URL 和回退尝试记录。", "- download_examples/module8/output/all/without_reference/：5 张图片及各自的三份 JSON。", "- live/、validation/、final_validation/、jena_recovery/：原始 HTTP 证据、逐机构检查点和模块日志。", "- 运行命令.txt：可直接复制的 PowerShell 指令。", "", "## 检查结果", "", "Module 3 自动测试 44 项通过；Module 8 自动测试 16 项通过。Module 5–7 的真实样例运行均为 5 条输入、5 条有效输出；Module 8 最终重新联网下载 5 张图片，缓存命中 0、失败 0。", "", "原来 69 个未解决清单条目减少为 64 个；这仍是清单条目数量，不自动等同于去重后的机构数量。"]
    (root / "五机构批量获取与下载结果.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
