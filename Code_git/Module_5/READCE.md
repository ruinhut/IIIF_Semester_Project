# Module 5——IIIF 版权识别与筛选

Module 5 读取 Module 4 已通过结构校验的 IIIF Manifest，从原始 JSON 中提取版权证据，映射为统一类别，再应用带版本号的项目策略。只有决策为 `allow` 的 Manifest 及其图像资源会进入下一模块。结果是可追溯的项目筛选决策，不是法律结论。

## 功能范围

本模块会：

- 读取 Module 4 的有效 Manifest、资源清单和缓存的原始 JSON；
- 在启用时核对 Module 4 保存的 SHA-256；
- 提取 Manifest、Canvas、Annotation 和 Body 层级的 `rights` 与 `license`；
- 保留版权相关 metadata、`requiredStatement` 和旧版 `attribution`；
- 保存原始值、规范化值、JSON 路径、资源层级、类别和命中的规则；
- 区分决定性版权证据与仅说明署名的文本；
- 按版本化策略决策，并把不明确的记录送入人工复核；
- 只导出属于允许 Manifest 的页面和图像资源。

它不负责资源发现、联网获取 Manifest、IIIF 结构校验、图像下载、OCR 或描述性元数据规范化。

## 输入

默认读取：

- `../Module_4/data/output/validated_manifests.jsonl`
- `../Module_4/data/output/manifest_resource_inventory.jsonl`
- Module 4 记录的原始 Manifest JSON 路径

只有 Module 4 schema 1.0 且结构状态为 `valid` 的记录可以进入本模块。

## 当前策略

策略文件为 `policies/baseline-2026-09-25.json`。

| 类别 | 典型内容 | 决策 |
|---|---|---|
| `public_domain` | CC0、Public Domain Mark | 允许 |
| `open_license` | CC BY、CC BY-SA | 允许 |
| `noncommercial_or_limited` | CC BY-NC、CC BY-ND、NoC-NC 等限制性声明 | 人工复核 |
| `in_copyright` | InC 系列、明确的“保留所有权利” | 拒绝 |
| `no_known_copyright` | NKC 或等价文字 | 人工复核 |
| `institutional_terms` | 未识别的机构条款 | 人工复核 |
| `unknown` | 没有决定性证据或原始证据无法可信读取 | 人工复核 |
| `conflicting` | 多个决定性类别相互不一致 | 人工复核 |

当前是保守基线，最终允许清单仍需老师确认。规则改变时应新增带版本号的策略文件，不能静默改写已经用于历史运行的策略。

## 运行

先完成 Module 4，然后在 `Code_git/Module_5` 中执行：

```powershell
python -m iiif_rights_filter run --config config.example.json
python -m iiif_rights_filter run --config config.smoke.json
python -m iiif_rights_filter run --config config.example.json --limit 20
```

## 输出

`data/output` 中生成：

- `rights_assessed_manifests.jsonl`：全部 Manifest 和完整证据；
- `allowed_manifests.jsonl`：策略允许的 Manifest；
- `denied_manifests.jsonl`：策略明确拒绝的 Manifest；
- `manual_review.jsonl`：需要人工检查的记录；
- `allowed_resource_inventory.jsonl/csv`：允许 Manifest 的页面和图像资源；
- `rights_summary.csv`：每个 Manifest 一行的简明结果。

日志为 `data/log/Module5_电脑时间_log.txt`，精确到秒。每项证据都会保留来源字段、JSON 路径、原始值、规范化值、分类规则、是否参与最终判断以及所在资源层级。

## 测试

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```

2026 年 9 月 25 日验证结果：

- 14 个自动化测试全部通过；
- 成功处理 BSB、Gallica、Harvard Art Museums、Digital Commonwealth 和 Fragmentarium 的 5 个真实缓存 Manifest，SHA-256 全部通过；
- 1 个允许，4 个进入人工复核；
- Fragmentarium 的 CC BY Manifest 被允许，导出 3 条页面/图像资源；
- BSB 的 NoC-NC、Digital Commonwealth 的无已知版权限制、Gallica 的机构条款和 Harvard 的版权缺失均按保守策略进入人工复核。
