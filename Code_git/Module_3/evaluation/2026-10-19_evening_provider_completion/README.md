# 2026-10-19 截止时间记录

本轮目标为新增 5 个来源，按要求于柏林时间 18:05 前停止。本轮未完成任何新增来源的端到端验证，因此新增跑通数量为 0；不得将入口可达或单条 Manifest 候选计作批量发现及图片下载已跑通。

复核了 IIIF 官方指南中的 Princeton、UNT、Villanova、Stanford 和 Harvard 条目，并保存了有超时限制的入口检查结果。具体 HTTP 状态及失败原因见 endpoint_checks.json。下一轮应从这些证据继续，完成可复用发现配置、Module 3–4 验证和图片下载后再纳入累计结果。

未修改全局机构配置或技能库。HTML 响应仅存在内存中，检查后释放，没有产生需要保留的大型临时响应文件。summary.json 记录完成时间、清理情况及明确的未完成状态。

## 本轮实际结果

| 来源 | 实际响应 | 可以确认的内容 | 尚未完成 |
| --- | --- | --- | --- |
| Princeton University Libraries | 单条 Manifest HTTP 200，JSON 声明 Presentation 2 context 和 sc:Manifest | 单条真实 Manifest 可获取，原始 JSON 已保存 | 从目录批量发现、Module 4 验证和图片下载 |
| University of North Texas Libraries | 首页 HTTP 200 | 本次入口可达 | 记录枚举、Manifest 发现与下游验证 |
| Villanova University | 首页 HTTP 403 | 本次请求被拒绝 | 查找官方文档允许的替代入口；不将 403 解释为没有 IIIF |
| Stanford University | 搜索入口 HTTP 200，HTML | 收到了 HTML 响应，尚未认定是有效结果列表 | 检查页面内容和具体记录的 Manifest 链接 |
| Harvard University Digital Collections | 指南链接 HTTP 404 | 指南中的这个地址本次不可用 | 查找目前的官方入口；不将旧链接失效解释为整个机构不可用 |

五份指南均从 https://guides.iiif.io/finding_resources/ 中复核。指南分别为 /guides/dpul.princeton.edu/、/guides/digital.library.unt.edu/、/guides/digital.library.villanova.edu/、/guides/searchworks.stanford.edu/、/guides/library.harvard.edu/。指南说明不能代替实际批量验证。

## 留给下一轮的技术线索

本次 HTTPS 请求使用本机 Python 已安装 certifi 的 CA 文件，并保持证书链和主机名校验。Princeton 的旧默认 CA 验证失败不能视为接口不可用，本次使用有效 CA 后其单条 Manifest 请求成功。应在后续运行中显式记录 CA 配置，避免把本机证书环境问题误计为机构失败。

累计统计仍沿用上一轮已经保存的 39/94 个来源条目，未新增。94 是当前项目清单条目数，并非全球 IIIF 机构总量；其中可能包含平台及同机构不同来源。本轮没有进行全量下载或新增端到端测试。
