# Blavatnik Archive：可复用的公共搜索 API 发现方法

核验日期：2026-10-16。机构 ID：`provider-4ef10065e633729c`。

## 从哪里入手

IIIF 官方指南 <https://iiif.io/guides/guides/blavatnikarchive.org/> 指示：
打开藏品的 IIIF 查看器，再复制 Manifest 地址。指南截图中的旧地址
`/manifest/view/9411` 当前返回 404，不能直接当作可执行的批量入口。

调查当前网站的公开前端脚本和查看器配置，找到了公开搜索请求与目前
真正使用的 Manifest 路由。这里没有登录、创建收藏夹、提交资料或修改远端数据。

## 可执行链路

1. 只读搜索：`POST https://www.blavatnikarchive.org/api/data/es/search?size=60`。
2. 请求头：`Content-Type: application/json`、`N-Belonging-To: BAF`。
3. JSON 请求体：`{"query":"","filters":[],"from":0}`。
4. 从 `es_hits.data[].generalInfo.itemId` 读取 ID；`from` 每页增加 60。
5. 展开候选地址：
   `https://www.blavatnikarchive.org/api/data/es/iiif-manifest/{identifier}?type=mirador&site=BAF`。
6. 对每个响应检查 HTTP、JSON、IIIF Presentation context 和 Manifest 类型。
   Module 4 再进行基本结构检查及图片清点。

搜索使用 POST，但其用途是读取公开目录；配置必须明确标注 `read_only=true`。
这些请求头只发送给目录接口，Manifest 仍使用普通 GET。

## 本次发现的两个覆盖问题

- 请求 `size=100` 实际只返回 60 条。如果把短页直接当末页，就会误报全量完成。
  当前使用已核验的 `size=60`、`page_step=60`，并与 `es_hits.total` 对照。
- 按 30 个顶层集合分别枚举得到 20,162 个唯一 ID；不加集合过滤的完整分页
  得到 20,199 个，补回 37 个。集合之间还存在重复，不能直接相加。

20,199 是本次公开搜索快照的目录 ID 数，并非图片数，也不是历史永久总量。
执行配置保存完整目录方法，另外保留 30 个集合查询作为定向采集方法。
原先 EPFL、Chicago 等机构的配置和方法不被替换。

## 发布方结构缺陷与透明修复

当前已核验的 Manifest 响应缺少顶层 `@id`。严格检查原始 JSON 会报告
`missing_id`，不能声称原始响应完全符合 IIIF。

Module 4 的通用可选策略只把成功请求的最终 URL 作为缺失标识符，写入
独立的 `.normalized.json`；原始响应、原始失败原因和补丁依据都保留。
它不会虚构图片、Canvas、标题或文本。将
`normalization.infer_missing_manifest_id` 设为 `false` 可恢复严格拒绝行为。
这里的“可用”仅指通过本项目基本结构检查，不代表通过完整 IIIF 合规认证。
抽查的原始响应也没有顶层 `label`，标题存在于 `metadata` 中。当前基本检查
不覆盖全部必填展示字段，Module 6 从真实标题元数据提取文献名称；本次没有
把补入 `@id` 后的 JSON 宣称为完全符合 IIIF 的发布版本。

不要混淆另一种接口：
`/api/data/es/iiif-manifest/{image_hash}?type=IIIF&site=BAF` 返回图片服务描述，
不是文献 Manifest。缺少参数或换成 `type=Manifest` 也不能替代已核验的路由。

## 图片与机构参考文本

图片由 Manifest 自己声明的 Image API 地址提供，例如：
`https://iiiflb.blavatnikarchive.org/iiif/3/baf__{image_hash}/full/max/0/default.jpg`。
下载器优先读取声明，不能把服务根地址当成 JPEG。

机构原始转录另见 `GET https://www.blavatnikarchive.org/api/data/es/item/{identifier}`：
`data.originalTranscript`，语言见 `data.originalTranscriptLanguages`。
`englishTranscript` 是另一字段，可能是翻译，不能自动当作俄文图片的 OCR 答案。
Manifest 本身不一定声明这些文本，因此 Module 6 使用可选的目录补充配置。

目前自动关联的保守条件：Manifest 只有一个 Canvas、Canvas 只有一个图片 body、
目录只有一个 page，而且目录 `iIIFID` 与真实图片或图片服务地址匹配。
多页文献的整篇转录暂不随意分配给某一页；跳过原因写入审计文件。

已跑通示例：item `6897`，1943 年俄文信件。实际下载一张 3699 × 5154
JPEG，并导出原文转录、文献记录、图片记录、OCR 特征记录及关联依据。
机构转录是参考文本，不保证是人工校对的 gold ground truth。

99 份单页参考候选的首批实际下载为 98 成功、1 失败。item `19634` 的
Manifest 和原文都可读，但图片正文、标准 `info.json` 与官网缩略图均返回
404。错误分类为源图不可用；不能用“发现了 Manifest”替代“图片已下载”。
详情见本次评估的 `missing_image_diagnosis/README.md`。

另一次按 35 种目录类型平衡选取的 100 张图片测试全部下载、解码成功，
300 个主要 JSON 通过 schema。item `13642` 的一张勋章照片实际为
3072 × 2304，源 Manifest 声明为 2304 × 3072，JPEG 没有 EXIF 旋转标记。
这是保留的源尺寸差异，不是下载失败；不要旋转原图来掩盖差异。
这组类型平衡测试不是全馆下载可用率的无偏估计。

### 已调查但尚未启用的分段方法

部分记录还提供 `itemSegments[].originalTranscript` 与 `startPoint` / `endPoint`。
当前公开查看器脚本在切换图片时使用数组下标加一来匹配这些范围；某些
记录的 `pages[].pageNo` 却从 2 或 3 开始，不能把这两个编号体系直接混用。
例如 item `13736` 的两张图片页码是 2、3，而两个文本分段均声明范围 1–1。
这提示分段可能对应第一张图片，但尚不足以承诺页面全文、文本完整性或
坐标范围。当前自动输出仍采用上面的单页规则；没有把这些多页分段混入
已经验证的单页参考样例。后续可在独立测试中核验查看器实际行为，再增加
“配置的数组位置 → 图片哈希 → 唯一 Canvas”的通用映射，并标注文本覆盖范围。
原始 API JSON 和查看器脚本已保留，避免下次重新调查。

## 证据与重跑

全部运行隔离在 `evaluation/2026-10-16_blavatnik_investigation/`：

- `live/`：官网、脚本、接口探测及失败证据。
- `entire_catalogue_snapshot_v2/`：337 页目录响应、20,199 个唯一 ID。
- `catalogue_snapshot/`：30 个集合查询及去重结果。
- `catalogue_reconciliation.json`：37 个补回 ID 的清单。
- `expanded/`：集合方法的完整 Manifest 调用轨迹。
- `reference_examples/`：真实图片与原始转录的 Module 5–8 输出。
- `final/`：全目录方法的最终核验与汇总（以实际生成文件为准）。

先运行 `tools/prepare_blavatnik_investigation.py --limit 25000 --batch final`，
再使用生成的配置运行各模块。`run_discovery_with_evidence.py --resume-from`
可以明确复用已保存 HTTP 响应；这属于重放当前快照，不是再次独立请求。
后续报告必须分别列出网络请求、缓存重放、严格原始检查、补丁后检查和实际下载。
大目录运行还发现原先每次加入发现记录都会重建全部去重键，造成二次复杂度。
现在在发现状态中维护集合索引，重复证据合并、不同证据保留；20,000 条纯内存
插入实测约 0.23 秒。这不是网络吞吐量。重叠配方的集成回归已确认统计仍按唯一
Manifest URL 计数。

## 留存的通用解题经验

官方指南 → 当前查看器 → 公开前端请求 → 目录分页与总数交叉核对 →
提取真实 ID → 参数完整的 Manifest 路由 → 确定性验证 → 图片/原文关联验证。

可复用的代码能力是只读 POST、JSON body 分页、路径提取、模板展开、
短页异常检测、审计缓存和确定性验证。域名、请求头、JSON 路径、参数与模板
放在机构配置中，不在 Python 里新增机构名称分支。尚未对另一个新机构验证
这次 POST 扩展的迁移效果，因此不能宣称它已经解决所有未知机构。
