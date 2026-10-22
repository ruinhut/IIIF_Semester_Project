# 2026-10-19：第三批五个来源的发现与交接

证据目录：`evaluation/2026-10-19_third_five_provider_completion/`。
沿用现有 Module 1–2 输入，仅对本轮路线进行联网验证，不将历史清单当作已重新全量检查。

## Digital Repository of Ireland

- [IIIF 官方指南](https://guides.iiif.io/guides/repository.dri.ie/)说明从条目的 Object Tools 取得 IIIF 链接。
- 实测公开搜索 JSON 返回 403，但公开原生 Collection `https://repository.dri.ie/iiif/collection/b564jg065.json` 正常返回。
- 根 Collection 声明子 Collection，例如 `b851kb90q.json`，再进入 `bc38m774v.json` 等叶集合即可枚举 Manifest。
- 使用现有的嵌套 Collection 遍历，未破解受限搜索页，也未推测连续编号。
- 当前范围为 Major Richard William George Hingston 的档案集合，不是 DRI 全部机构和馆藏。
- 原文版权声明限制公开发布与传播；本轮仅保存学术研究样例，保留原始权利信息，不能因链接公开就宣称可自由传播。

## Princeton University Art Museum

- [IIIF 官方指南](https://guides.iiif.io/guides/artmuseum.princeton.edu/)给出单条资源的查看器操作。
- [机构官方 API 文档](https://github.com/Princeton-University-Art-Museum/puam-api-docs)声明无须认证的对象 API、过滤字段、`from` 偏移量和 `size` 页长。
- `/objects?limit=5&page=1` 及没有受支持筛选条件的请求返回 400，不代表机构没有 API。
- 可用实例为 `https://data.artmuseum.princeton.edu/objects?maker=5560&size=3&from=0`，从 `hits.hits[]._source.objectid` 提取对象编号，并要求 `primaryimage` 非空。
- 根据实际已验证的原馆路由 `https://data.artmuseum.princeton.edu/iiif/objects/<编号>` 获取 Manifest；与 Princeton 大学图书馆 Figgy 路线分开配置。
- 主验证样本跨两个 API 页，共 6 个 Manifest。配置目前使用 Edgar Degas 的 maker ID 5560；其他 maker / department 等官方过滤方式可通过配置复用，但未在本轮逐一穷尽验证。
- API 的 `texts` 多为馆方作品解说，不等同于图片上的文字转录。Manifest 的普通藏品 HTML seeAlso 页面也不能当作 OCR 答案。

## UCLA Library Digital Collections

- [IIIF 官方指南](https://guides.iiif.io/guides/digital.library.ucla.edu/)及 [UCLA 自有指南](https://guides.library.ucla.edu/digital-collections/iiif)提供 IIIF 链接使用说明。
- 公开 JSON 目录 `https://digital.library.ucla.edu/catalog.json?q=map` 返回 `data[]`、`links.next` 及分页信息。
- 从 `type == Work` 的条目提取完整 `id`，例如 `ark:/21198/z1nt173p`；完整 ARK 需 URL 编码，不能只取最后一段后拼到另一命名空间。
- 对应真实 Manifest 为 `https://iiif.library.ucla.edu/ark%3A%2F21198%2Fz1nt173p/manifest`。
- 复用通用 JSON 编号与模板技能，跨两页验证 6 个。范围为公开 map 查询，不代表全馆总数。
- 本次实际样例使用原 Manifest 提供的缩放图片，像素小于 Canvas 声明；没有把它称为原始分辨率，也未用其直接构造原尺寸 OCR 坐标。

## The SCTA Reading Room

- 项目公开根 Collection 为 `https://scta.info/iiif/scta/collection`；作者及文本子集合均由这个目录声明。
- 已保存的执行入口为 `https://scta.info/iiif/plaoulcommentary/collection` 和 `https://scta.info/iiif/PetrusGracilis/collection`，经嵌套遍历发现 6 个 Manifest。
- [项目作者的 IIIF 讲解](https://jeffreycwitt.com/slides/2018-10-18-munster2/)同样明确链接项目 Collection、示例 Manifest 及转录 layer。
- Collection 有些使用早期声明形式，实际条目 Manifest 则声明 IIIF Presentation context；原始内容保留，不凭空补造 context。
- 图片资源和其声明的 Image API 服务需分别处理；本轮样例的真实下载可在 Module 8 索引中追溯。
- 一些 Manifest 声明 external AnnotationList / 转录 layer，这是后续文本配对的调查线索。本次未完成这些外部转录的抓取和页级验证，不计作已交付的训练参考文本。
- SCTA 是文本研究平台，来源中的图像可能来自其他图书馆；计为来源条目，不能重复计作独立原藏机构规模。

## Smithsonian Institution

- [IIIF 官方指南](https://guides.iiif.io/guides/collections.si.edu/)指向机构资源；[机构专题页](https://iiif.si.edu/featured/index.html)直接列出多份 Manifest 链接。
- 使用专题页中的直接 `https://iiif.si.edu/manifests/<名称>.json` 链接，未依赖受限的总目录搜索，也未猜测藏品编号。
- 这些资源的实际 context 为 `http://www.shared-canvas.org/ns/context.json`，而不是现代 Presentation 2/3 context。旧技能因版本检查拒绝，首次为 0；不能将此误解释为机构没有 Manifest。
- 只对经过核查的技能配置开启 `allow_legacy_shared_canvas: true`：精确匹配已知 context、要求 Manifest 类型和 sequences 数组，再交给 M4 检查真实 Canvas 与图片结构。
- M4 不改写源 JSON，记录 `source_format: legacy_shared_canvas` 和 `legacy_shared_canvas_context` 警告；`presentation_version: 2` 在此表示使用兼容的 sequences 读取器，不是断言源文件符合现代 Presentation 2。
- 当前覆盖机构官方专题页所列 Manifest，未声称覆盖整个 Smithsonian 的机构目录、所有藏品或每个单件对象。

## 被保留的失败与边界

- Folger 新站返回浏览器验证页，旧站请求发生网络错误；未处理挑战或计入成功。
- Illinois 的目录 JSON 与 API 探测返回 403；未认定该机构没有 IIIF。
- Getty 根地址返回迁移 HTML，但该迁移文档地址返回 404；仅说明本次这条路线未完成。
- Parliamentary Archives 的一条公开 Manifest 可以请求，但目录入口被拒绝，尚未完成批量枚举，不计入本轮成功。
- Cultural Japan 的旧示例 Manifest 返回 404；未据此否定其所有资源。
- 本轮 5 个来源各取 6 个 Manifest，经 M4 独立联网获取和基础结构检查，再经过 M5–8 下载每来源一张图片。样本上限不是全馆数量，也不是全部资源的成功率估计。
