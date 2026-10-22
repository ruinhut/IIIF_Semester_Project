# Module 5——IIIF 版权识别与研究数据保留

Module 5 读取 Module 4 已通过结构校验的 Manifest，提取并规范化版权证据，然后执行带版本号的自动策略。

schema 2.0 将两个问题分开处理：

1. URL、元数据和相关记录能否被项目保存并用于学术分析；
2. 资源能否被公开传播或用于商业用途。

**所有处理过的记录都会保留并送入 Module 6。**
`allow` 和 `exclude` 只表示是否进入“可公开再利用”子集，不再决定记录是否继续进入流水线。

## 自动状态

| 版权类别 | 公开再利用 | 研究下游 |
|---|---|---|
| `public_domain` | `allow` | 保留 |
| `open_license` | `allow` | 保留 |
| `noncommercial_or_limited` | `exclude` | 保留 |
| `in_copyright` | `exclude` | 保留 |
| `no_known_copyright` | `exclude` | 保留 |
| `institutional_terms` | `exclude` | 保留 |
| `unknown` | `exclude` | 保留 |
| `conflicting` | `exclude` | 保留 |

因此，`exclude` 的准确含义是“不得进入公开再利用数据集”，并不是“从流水线删除”。

每条版权判断都会保存：

- 原始版权声明及规范化值；
- JSON 路径、资源层级和匹配规则；
- 机构名称、Manifest URL 和来源证据；
- `decision_scope: public_reuse`；
- `research_status: retained`；
- URL/元数据保存、学术分析、公开传播和商业使用权限；
- 策略版本、判断理由和运行时间。

## 输入

- `../Module_4/data/output/validated_manifests.jsonl`
- `../Module_4/data/output/manifest_resource_inventory.jsonl`
- Module 4 缓存的原始 Manifest JSON

## 输出

- `research_manifests.jsonl`：全部 Manifest 和完整版权判断；Module 6 的正式输入。
- `research_only_manifests.jsonl`：可以保存和研究，但不能公开再利用的记录。
- `reuse_eligible_manifests.jsonl`：可以公开再利用的记录。
- `research_resource_inventory.jsonl/csv`：全部研究资源行；Module 6 的正式输入。
- `reuse_eligible_resource_inventory.jsonl/csv`：可公开再利用的资源子集。
- `rights_summary.csv`：每个 Manifest 一行的审计表。
- `data/log/Module5_电脑时间_log.txt`：输入、策略、数量和输出路径。

即使原始 JSON 缺失或解析失败，记录的 URL、机构、元数据和失败原因仍会保存在研究输出中，但不会获得公开再利用资格。

## 运行

```powershell
python -m iiif_rights_filter run --config config.example.json
python -m iiif_rights_filter run --config config.smoke.json
python -m iiif_rights_filter run --config config.example.json --limit 20
```

## 测试

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```
