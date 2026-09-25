# Module 5——IIIF 版权识别与筛选

Module 5 是完全自动化模块。它读取 Module 4 的有效 Manifest，提取和分类版权证据，执行带版本号的“允许/排除”策略，只把版权明确允许的资源交给下游。模块不再产生任何人工审核队列。

必须区分两个概念：

- 没写版权信息：`unknown`，界面显示“未知版权”；
- 明确声明公共领域：`public_domain`，界面显示“公共领域”。

缺失版权信息不能推断为“无版权”。未知版权记录会被完整保存，但自动排除出版权已明确的数据集。

## 功能

本模块会：

- 读取 Module 4 的有效 Manifest、资源清单和缓存的原始 JSON；
- 在启用时核对 Module 4 保存的 SHA-256；
- 提取 Manifest、Canvas、Annotation 和 Body 层级的 `rights` 与 `license`；
- 保留版权相关 metadata、`requiredStatement` 和旧版 `attribution`；
- 保存原始值、规范化值、JSON 路径、资源层级、类别和分类规则；
- 区分决定性版权证据与仅说明署名的文字；
- 输出中英文版权显示名称；
- 自动给出 `allow` 或 `exclude`；
- 只导出允许 Manifest 的页面和图像资源。

## 输入

默认读取：

- `../Module_4/data/output/validated_manifests.jsonl`
- `../Module_4/data/output/manifest_resource_inventory.jsonl`
- Module 4 保存的原始 Manifest JSON

只有 Module 4 schema 1.0 且结构状态为 `valid` 的记录可以进入本模块。

## 自动策略

策略文件为 `policies/automatic-2026-09-25.json`。

| 类别 | 显示含义 | 自动决策 |
|---|---|---|
| `public_domain` | 公共领域 | 允许 |
| `open_license` | CC BY 或 CC BY-SA | 允许 |
| `noncommercial_or_limited` | 限制性使用 | 排除 |
| `in_copyright` | 版权保护中 | 排除 |
| `no_known_copyright` | 无已知版权限制 | 排除 |
| `institutional_terms` | 机构使用条款 | 排除 |
| `unknown` | 未知版权 | 排除 |
| `conflicting` | 版权信息冲突 | 排除 |

原始 JSON 缺失、无法解析或 SHA-256 不一致时也会自动排除，不会等待人工。

## 运行

在 `Code_git/Module_5` 中执行：

```powershell
python -m iiif_rights_filter run --config config.example.json
python -m iiif_rights_filter run --config config.smoke.json
python -m iiif_rights_filter run --config config.example.json --limit 20
```

## 输出

- `rights_assessed_manifests.jsonl`：全部 Manifest，包括被排除的记录和完整证据；
- `allowed_manifests.jsonl`：自动允许的 Manifest；
- `excluded_manifests.jsonl`：自动排除的 Manifest 及原因；
- `allowed_resource_inventory.jsonl/csv`：允许 Manifest 的页面和图像资源；
- `rights_summary.csv`：每个 Manifest 一行，并包含中英文显示名称；
- `data/log/Module5_电脑时间_log.txt`：策略、数量和输出路径。

## 测试

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```

五个真实 Manifest 的预期结果为：1 个允许、4 个自动排除。Fragmentarium 因 CC BY 被允许，输出 3 条图像资源；BSB 的 NoC-NC、Digital Commonwealth 的无已知版权限制、Gallica 的机构条款和 Harvard 的未知版权都会保留分类信息，但不进入下游版权已明确的数据集。
