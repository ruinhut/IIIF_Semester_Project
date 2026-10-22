# 30 分钟机构入口筛查：2026-10-15

本轮工作从 19:48 左右开始，按“官方 guide → 当前网站/平台文档 → 候选批量路线 → Module 3 → Module 4”进行。最终统计请以同目录 `summary.json` 为准。

- 原先未解决：83 个候选机构条目；每条均已重新请求主页，匹配的 63 个官方指南已查阅。
- 新增跑通：14 个清单条目，对应 13 个不同的机构/平台名称实体；e-codices 原清单有重复身份。
- 实际发现：65 个去重 Manifest URL，与旧生产输出的 URL 没有重叠。
- Module 4：62 个通过图片资源结构检查；2 个是无图片内容的 Manifest；1 个请求超时。
- 62 个样本共声明 8,985 个 Canvas、8,985 个图片资源。本轮未下载这 8,985 张图片，也没有进行机构全量采集。
- 剩余 69 个条目尚未跑通。并非全部经过深入调查，部分仅完成主页和指南初筛。

## 这轮具体改了什么

1. 保留 EPFL/Chicago 原有方法，增加已验证的机构入口和配置。
2. IIIF Collection 同时遍历 `first`、`next`，避免漏掉 CONTENTdm 的分页入口。
3. 增加嵌套 JSON 数组中的显式 Manifest URL 提取；Wellcome、Northwestern 均验证成功。
4. 增加定向 HTML 目录的标识符提取；e-codices 已验证首个列表页。
5. 标识符模板技能支持从零开始的 offset 分页；Brown 已通过 Module 3–4 验证。
6. 所有网络失败、猜错的入口、限额和未解决线索保留，不把 HTTP 200 直接当成成功。

## 文件怎么看

- `机构逐项筛查报告.md`：83 个原始条目的逐项进度。
- `provider_route_audit.csv`：可直接用 Excel 打开的机构筛查表。
- `provider_route_audit.json`：每条目的 HTTP 证据、官方操作记录、下一步。
- `combined_manifest_urls.jsonl`：三批去重合并的 65 个 Manifest URL，供审阅。
- `combined_validated_manifest_index.jsonl`：62 个通过结构验证的 Manifest 索引。
- `live/checks.jsonl`、`live/responses/`：HTTP 原始证据。
- `module3/`、`additional_module3/`、`brown_module3/`：三次真实 Module 3 输出与日志。
- 对应 `module4/`、`additional_module4/`、`brown_module4/`：真实验证输出、原始 Manifest 与日志。
- `northwestern_skill_transfer.json`：JSON 链接提取方法的迁移验证。
- `brown_skill_execution.json`：offset 搜索 API 与 URL 模板的执行记录。
- `baseline_*`：本轮修改前的未解决清单与配置备份。

完整方法与边界：`../../knowledge/institutions/2026-10-15_provider_routes.md`。
可复用技能说明：`../../knowledge/skills/2026-10-15_catalogue_link_skills.md`。

原有生产 `data/output` 未被这些批次覆盖。保留原来 Module 3 输出契约；本轮没有要求 Module 4–8 增加机构专用解析。

## 接下来继续处理的优先线索

1. Jena/MyCoRe：已枚举对象与 derivative ID；重试同一 Manifest 成功。下一步将两阶段枚举接入通用技能。
2. Göttingen、Leiden、Wales、Utrecht：已有单条 Manifest 线索，重点补齐目录枚举。
3. e-codices：验证目录分页；Washington：替换当前只覆盖一个集合的超时兜底入口。
4. Bodmer/Hedera：区分直接 Image API 与 Presentation Manifest，寻找目录到 Manifest 的公开映射。
5. 对 403、TLS 证书链、浏览器验证和旧站迁移分别诊断。访问失败不代表没有 IIIF。

另见 `verified_partial_manifest_examples.json`：保存 5 个未完成批量枚举的机构的单条 Manifest 成功证据，未混入上述 65 个集成测试样本。
