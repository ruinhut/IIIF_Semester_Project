# BSB、David Rumsey、梵蒂冈：批量发现方法

日期：2026-10-15。执行配置：`config/provider_endpoints.json`、`config/discovery_knowledge.json`。
实际结果与原始请求：`evaluation/2026-10-15_three_provider_completion/`。

## 可复用的调查过程

1. 先读官方 IIIF guide：区分它给的是网站、单件 Manifest，还是可枚举的 Collection。
2. 如果已有 Collection，优先使用它，并检查 `first` / `next`，不要再从首页盲爬。
3. 如果目录由 JavaScript 加载，读公开页面声明的脚本和请求路径，寻找实际目录数据接口。不要把 Image API 地址当成 Manifest。
4. 优先读取目录 JSON 中明确的 Manifest URL；否则提取真实对象编号，依照经过验证的 URL 规则生成候选。
5. 检查真实分页是否改变记录；检查候选 HTTP、JSON、IIIF context 和类型，再通过 Module 4 独立下载验证。
6. 用相同的 Module 5–8 契约导出一张图片和关联 JSON；任何失败均保留日志，不把目录数量或声明图片数当成实际下载数。

这些步骤是调查思路，当前由 Codex 辅助执行，并非已接入无人值守的 LLM API。已确认路线存为配置，日常运行使用确定性程序。

## 1. Bavarian State Library / Munich Digitization Centre

- 清单条目 ID：`provider-9dd288533f853f26`。
- [IIIF 官方指南](https://iiif.io/guides/guides/digitale-sammlungen.de/)直接列出全馆 Collection：
  `https://api.digitale-sammlungen.de/iiif/presentation/v2/collection/top`。
- 响应为 Presentation 2 `sc:Collection`，每页有 `manifests`，`next` 是不透明游标。保持服务器给出的完整 URL，不自行拼接页码。
- 本次实际请求首页及其 `next`，均返回 Collection；运行时复用现有原生 Collection 遍历器。
- 首页声明 `total = 3213257`，这是服务器目录声明的资源规模，不是本次验证或下载数量，也不能直接换算为页图数量。
- 这一入口本来就在官方指南里；此前漏接属于入口收集不完整，不能解释成机构不支持通用 IIIF。
- 本次仅处理清单中的该条目；同属 BSB 的东亚专题条目没有自动记为已解决。

## 2. David Rumsey Map Collection / LUNA

- 清单条目 ID：`provider-0a19a8e5992b5a87`。
- [IIIF 官方指南](https://iiif.io/guides/guides/davidrumsey.com/)说明从分享菜单复制 Manifest。
- 实际批量入口：`https://www.davidrumsey.com/luna/servlet/as/search?q=&os=0&bs=10`。
- JSON `results` 是记录数组，`results[].iiifManifest` 直接给出标准 Manifest，不需要猜 ID。
- `os` 是结果偏移量，`bs` 是页大小。本次以 `os=0`、`os=10` 两页生成 20 个样本。
- JSON 也声明 `iiifCollection`，对应 Collection 使用 `first` 分页；本次将分页搜索 API 作为执行配方，保留 Collection 响应作为证据。
- 初次查询返回 `totalResults = 151554`，仅表示这次查询的目录总数，不能等同于本次验证 Manifest 或下载图片数量。
- 技能类型：`paginated_json_manifest_links`。网址、JSON 路径、分页参数均为配置；没有新增 Rumsey 专用 Python 分支。

## 3. Vatican Library / DigiVatLib / AMLAD

- 本次清单条目 ID：`provider-9087fc100047c3b2`。清单另有 DigiVatLib 同机构条目，本次未将它重复记为新增机构。
- [IIIF 官方指南](https://iiif.io/guides/guides/vatlib.it/)说明目录记录、查看器的 IIIF 入口。
- 手稿目录 `https://digi.vatlib.it/mss/` 的 HTML 明确给出 `data-item-url` 分库请求，共提取 83 个不同分库路径，并全部保存到配置。
- 已验证分库：`https://digi.vatlib.it/mss/ajax/category/Capp.Giulia`。
- JSON 的 `fond[].shelfmark` 是真实馆藏编号，例如 `Capp.Giulia.II.1.pt.bis`。
- 候选模板：`https://digi.vatlib.it/iiif/MSS_{identifier}/manifest.json`。每个候选仍须联网验证，不把模板本身当成有效资源。
- 单个分库接口一次返回其记录数组，不向其注入未经验证的分页参数。分库顺序以已验证的 Capp.Giulia 开始，随后保留其余目录公开的分库。
- 技能类型：`paginated_json_identifiers_to_manifest_templates`。本次无需改通用解析器。
- 83 个入口来自目录声明，只有样本用到的分库及候选经过此次验证；不能声称 83 个分库都已完整跑完。当前覆盖手稿，不代表其他材料类别均已枚举。
- `Vat.lat` 目录/分库请求在初次调查中发生超时；失败记录保留。不存在的 `/iiif/collection` 返回 404，没有将其加入执行配置。

## 额外调查但未计入成功：Frick

- 首页是 JavaScript 目录；公开脚本声明目录 API 和查看器逻辑。
- 跨目录搜索返回 401；匿名会话后的 Books、Archives、Photoarchive 分目录搜索能返回记录。
- 脚本中的 `/compare/{id}/manifest` 使用的是保存比较会话的书签 ID，并非普通目录记录 ID。尝试用记录 ID 套用该路线失败，不能作为已证实配方。
- 因此本次没有将 Frick 计入三个成功机构，也没有保存未经验证的 Manifest 模板。后续需继续确认其单条资源如何进入 IIIF；不得通过写入远程书签来冒充只读发现。

## 扩大采集

执行 `tools/prepare_three_provider_completion.py --sample-limit N` 可以增大本次隔离运行的 Manifest 输出预算，源目录配方无需重写。应保留新批次输出，明确源目录耗尽、达到预算、网络失败三种停止原因。全量采集可能很大，应使用适当磁盘和运行时间；本次 20 个/机构是验证样本。

旧 EPFL、Chicago 及前两批机构配方保留；与此次修改前备份逐项对比，旧配方内容不变。Module 3–8 输出结构不变。
