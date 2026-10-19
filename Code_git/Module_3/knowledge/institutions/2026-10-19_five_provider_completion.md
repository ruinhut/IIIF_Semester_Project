# 五个来源的批量发现方法（2026-10-19）

本页记录实际调查路线。最终数量与下载结果以同日评估目录的报告为准。
这里的“来源”沿用机构清单的口径，包含跨机构平台，不等于五家独立馆藏机构。

## e-rara 与 e-manuscripta：Visual Library Collection

- 官方指南：[e-rara](https://iiif.io/guides/guides/e-rara.ch/)、[e-manuscripta](https://iiif.io/guides/guides/e-manuscripta.ch/)。指南从单条目录记录出发，提示复制 IIIF 链接。
- IIIF 官方[培训材料的 Collection 示例](https://training.iiif.io/dhsi/day-four/collections.html)另行给出了两个平台的批量 Collection 根入口。
- 当前有效版本是 `v21`；探测的 `v20/collection` 返回 404。
- 完整目录入口分别为 `https://www.e-rara.ch/i3f/v21/collection/all` 和 `https://www.e-manuscripta.ch/i3f/v21/collection/all`。
- 分类入口将 `all` 换成 `top`。保留两个入口，但优先使用 `all`，避免先遍历分类导致重复或偏向单个专题。
- 必须识别 `members` 中的 Manifest 和嵌套 Collection，并跟随服务器给出的 `next`，不能自行假设页大小相同：本轮 e-rara 首批 20 条，e-manuscripta 首批 10 条。
- 直接复用现有 Collection 遍历器，没有机构专用 Python 分支。

## FromThePage：可访问的公开转录项目 Collection

- 从官方[发现指南](https://iiif.io/guides/guides/fromthepage.com/)和上述官方培训材料入手。
- 培训给出的当前可访问入口：`https://fromthepage.com/iiif/collection/jeremiah-white-graves-diaries`。
- 根响应包含 33 个 Manifest 成员，`service` 中保留项目自行报告的转录进度。
- 直接遍历 `manifests`，不把 `pctTranscribed` 或 `pctComplete` 当作文字准确率。
- 此次只证明该公开项目的批量获取，不等于已经枚举 FromThePage 上全部用户或全部项目。
- 同一个 Canvas 声明 HTML、searchable、verbatim、emended 等不同转录版本。下载四个版本不是四个不同页面或四套独立答案；用于字形识别时优先考察标为 `Verbatim Plaintext` 的版本，不把 emended 校订或 searchable 规范化文本混作逐字识别答案。
- 一个任意数字 Collection 探测返回 403，没有尝试绕过；成功路线来自官方材料给出的不同公开项目。

## 奥地利国家图书馆：SACHA 年度报纸 Collection

- [官方 API 文档](https://iiif.onb.ac.at/api/)说明 Presentation 接口，官网示例页为 `https://iiif.onb.ac.at/gui/demo.html`。
- 官网公开脚本 `https://iiif.onb.ac.at/gui/demo.js` 明确拼出 `wrz_` 加年份的年度 Collection 路径；必须保留下划线。
- 已请求 `https://iiif.onb.ac.at/presentation/collection/wrz_1703`（41 个成员）与 `.../wrz_1704`（105 个成员）。这些是指定年度的成员数，不是全馆规模。
- 年度成员给出真实日期 ID，例如 `wrz17030808`，链接到 `https://iiif.onb.ac.at/presentation/ANNO/wrz17030808/manifest/`。
- 另保留官网声明的 `.../presentation/collection/jerusalem` 入口；没有执行创建 Collection 的 POST 请求。
- 本轮使用 ANNO 报纸，按顺序、限速抽样。ABO 的整本批量下载有官网明确限制，不能把相同权限推及其他项目。
- 实测中 1703 年 Collection 的一条 Manifest（`wrz17030808`）返回 400；另一条有效 Manifest（`wrz17030813`）声明的第 8 页图片和第 1 页 info.json 也返回 400。失败原样保留。另经完整 M3–8 链路实际下载了官网 Jerusalem Collection 声明的 AKON 明信片，不能据此声称 ANNO 图片问题已修复。
- 代码仍使用通用 Collection 遍历。本轮不宣称已覆盖所有年份、报刊或 ABO/AKON/REPO 内容。

## Bodmer Lab：搜索结果 → 专题查看器配置 → Manifest

- [官方指南](https://iiif.io/guides/guides/bodmerlab.unige.ch/)提示从藏品查看器取得链接。
- 当前首页搜索 `https://bodmerlab.unige.ch/fr/search?keywords=` 是服务端 HTML，藏品链接包含 `/constellations/<专题>/barcode/<编号>`；分页参数为大写 `Page`。
- 当前藏品页展示的图片已转向 `iiif.hedera.unige.ch`。图片服务根地址不能直接当作 Presentation Manifest。
- 查看器 `https://bodmerlab.unige.ch/fr/constellations/autographes/mirador/1072068450` 的 `manifestUri` 和 `loadedManifest` 明确声明相对地址 `/fr/constellations/autographes/manifest/1072068450`。
- 先根据实际查看器声明确认地址，再配置搜索记录链接的正则与 URL 模板。没有用猜测的 `/manifest/<id>` 或 Hedera 路径充当成功结果。
- 当前可执行范围为 `autographes` 专题。其他专题需要核对自己的查看器声明，不能用一个专题的测试结果冒充全馆覆盖。
- 复用已有 `paginated_html_identifiers_to_manifest_templates`，没有新增机构名称分支。另从第二页独立测试，须得到不与第一页样本重叠的 ID。
- 发现一个通用标识符问题：源 Canvas ID 末尾的 `#canvas` 原先在 Module 4 被删除。现将 Canvas 标识符与 HTTP 请求 URL 分开处理，保留其 fragment。回归测试先复现、修复后通过；保留原始响应，以缓存重验再更新 Module 5–8 输出。

## 通用处理流程与边界

官方单条资源指南 → 官方培训/平台文档 → 检查当前公开页面及查看器配置 →
找到目录或 Collection → 保留分页与子集合 → 验证实际 Manifest →
Module 4 基础结构检查 → 原有 Module 5–7 合同 → Module 8 实际图片与关联 JSON。

Collection 遍历和 HTML 编号模板是已有通用能力；本次主要增加经过验证的配置。
原有 EPFL、Chicago、Blavatnik 等方法必须逐项保留。官方指南、可执行配置与实测结果分别保存。
发现了目录链接、抓取到了 JSON、通过了结构检查、实际下载图片是四个不同指标。
有限样本不能证明全部资源可用，也不能作为全馆下载成功率的无偏估计。

证据位于 `evaluation/2026-10-19_five_provider_completion/`：`live/checks.jsonl`、
`validation/module3/requests.jsonl`、Module 4 原始响应和校验结果、下游日志与下载索引。
候选配置只有在五个来源均具有有效 Manifest 和真实下载后才合并到正式配置。
