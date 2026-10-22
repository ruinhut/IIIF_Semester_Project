# 2026-10-19：恢复筛查后验证的五条发现路线

证据目录：`evaluation/2026-10-19_resumed_five_provider_completion/`。
本轮在 18:05 截止后收到新的“继续跑”指令才恢复；先前截止记录不改写。
所有路线先在隔离配置中验证，经过 M3–8 和实际图片解码后才合入正式知识库。

## Princeton University Libraries

- [IIIF 官方单条资源指南](https://guides.iiif.io/guides/dpul.princeton.edu/)。
- 公开搜索 JSON：`https://dpul.princeton.edu/papyri/catalog.json?q=papyrus&search_field=all_fields`。
- 真实分页字段为 `page`、`per_page`；返回 `data[].links.self` 和 `links.next`。
- 从 `links.self` 取目录记录编号，请求相应的 `<编号>.json`。
- 详情的 `response.document.content_metadata_iiif_manifest_field_ssi` 明确声明 Figgy Manifest；目录编号与 Figgy UUID 不相同，不能直接互换。
- 从这个声明链接提取 UUID，再请求同一 Figgy 路由，并验证 IIIF 类型。实测跨两页取得 6 个有效 Manifest。
- 范围为 papyri 的公开搜索，不代表 Princeton 全馆目录。HTML 搜索可能返回浏览器挑战；本轮使用的是公开结构化 JSON 接口，没有破解挑战。

## University of North Texas Libraries

- [官方 API 文档](https://digital.library.unt.edu/api/)说明每个馆藏有自己的 API 页面，文献地址后加 `manifest/` 可返回 IIIF。
- 沿目录实际链接进入 `https://digital.library.unt.edu/explore/collections/UNTPC/api/`，其中的 `../top` 指向原生 Collection。
- `https://digital.library.unt.edu/explore/collections/UNTPC/top` 声明 `first`、`last`、`total`。另保存 `UNTSW/top` 入口；本轮不声称已实测所有馆藏。
- 复用已有 Collection 遍历，保留分页，随后由 M4 获取真实 Manifest。配置中的 6 个是样本上限，不是 UNT 总量。
- UNT 的 `metadata.untl.xml` 和 Dublin Core XML 是描述性元数据，不是图片的 OCR 答案。本轮纠正 M6 将通用 `text/xml` 误当参考文本的判断；原始链接仍保留在 Manifest 中。

## Harvard University Digital Collections

- 指南的旧首页 `https://library.harvard.edu/digital-collections` 本次返回 404。
- [Harvard 官方 IIIF 说明](https://library.harvard.edu/services-tools/iiif-manifests-digital-objects)及 [LibraryCloud 介绍](https://iiif.harvard.edu/collaborators/harvard-library/)指向现存服务。
- 公开目录：`https://api.lib.harvard.edu/v2/items.json?q=iiif.lib.harvard.edu`。
- `items.mods[]` 中的 `location[].url` 既有对象形式又有数组形式；用两个明确 JSON 路径保留这两类声明链接。`start` 是偏移量，配合 `limit`，不是普通页码。
- 一些旧 `https://iiif.lib.harvard.edu/manifests/drs:<编号>` 请求返回 HTTP 200，但内容为迁移提示 HTML，不能计作有效 JSON。
- 只跟随该页面 `meta http-equiv="refresh"` 明确声明的新地址，并限制允许域名、跳数与循环；NRS 再以 HTTP 重定向提供真实 Manifest。
- 例如 `https://nrs.lib.harvard.edu/URN-3:VIT.BB:37265343:MANIFEST:2` 实际返回 IIIF Manifest。
- 没有凭空猜新编号，也没有将迁移 HTML 当作解析成功。

## Stanford University

- [官方 IIIF API 文档](https://api.library.stanford.edu/docs/iiif/api/)给出 `https://purl.stanford.edu/{id}/iiif/manifest`。
- 本次 SearchWorks / exhibits 搜索请求可能返回 HTTP 200 的脚本挑战页；200 不能视为有效目录结果。
- 书籍元数据可指向父 Collection，但本次 `nb786jb6054/iiif/manifest` 返回的 Collection 没有列出成员，不能据此宣称已实现全馆枚举。
- 可用替代发现入口为公开贡献索引 `https://fromthepage.com/iiif/contributions/stanford.edu`。
- 索引 `manifests[].metadata[].value` 中的 `dc:source` 明确列出 Stanford 原始 PURL Manifest。只接受 Stanford PURL 命名空间并实际验证响应；输出原馆 Manifest，而不是将第三方 Manifest 冒充原馆资源。
- 此路线覆盖索引列出的 Stanford 原始资源，不覆盖 Stanford 全部馆藏，也不代表本轮已下载对应转录文本。

## Biblissima

- [官方指南](https://guides.iiif.io/guides/biblissima.fr/)和 [Biblissima 公开检索目录](https://iiif.biblissima.fr/collections/search)提供发现线索。
- 旧原生 top Collection 可以访问，但主要指向 Gallica；不能把它等同于现行聚合目录的全部内容。
- 现行搜索结果直接声明原馆 Manifest。本轮配置覆盖 `https://api.irht.cnrs.fr/ark:/63955/<编号>/manifest.json` 命名空间，其他原馆待分别核对。
- 翻页使用 `from=0`、`from=20` 等偏移量，不是 `page`。第二页独立取得 2 个不与主样本重叠的有效候选。
- Biblissima 是聚合平台，应计为一个来源条目；不能将它当作新增独立收藏机构，也不能重复累加其原馆资源规模。

## 未解决来源与共通教训

- Villanova：首页、公开 VuFind API 根地址和已发表的 top Collection 本次均返回 403；已记录失败，未绕过限制，未计入本轮五个成功来源。
- Windows 本机 CA 环境曾导致 TLS 失败。本轮显式使用本机已安装 certifi 的 CA 文件，保持证书链和主机名校验；没有禁用 TLS 验证。重跑需要同样有效的 CA 配置。
- 新增通用能力为：详情对象取值及编号提取、目录链接模式筛选、有界的明确 HTML 迁移处理。机构差异保存在 JSON 配置，未增加按机构名称分支的代码。
- 保留已验证的 EPFL、Chicago 等旧方法；不要把新机构未知的编号硬套入旧 Manifest URL。
- 已验证的 Manifest 数、导出的媒体关联数、实际下载图片数和全馆规模分别统计。
- 一张图片可成功解码，不代表它是最高分辨率。本轮应同时查看实际像素、请求的尺寸参数与 Canvas 声明；缩放图的坐标不能直接充当原尺寸 OCR 坐标。
