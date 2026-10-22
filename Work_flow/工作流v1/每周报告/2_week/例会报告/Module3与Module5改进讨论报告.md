---
title: "Module 3 与 Module 5 改进讨论报告"
subtitle: "指标、版权状态与发现策略"
author: "Boheng Shang"
date: "2026-09-28"
lang: zh-CN
papersize: a4
fontsize: 10.5pt
documentclass: ctexart
geometry:
  - top=1.9cm
  - bottom=1.9cm
  - left=2.05cm
  - right=2.05cm
numbersections: true
colorlinks: true
linkcolor: blue
urlcolor: blue
header-includes:
  - |
    \setCJKmainfont{FandolSong}
    \setCJKsansfont{FandolFang}
    \setmonofont{DejaVu Sans Mono}
    \usepackage{booktabs}
    \usepackage{longtable}
    \usepackage{array}
    \usepackage{xcolor}
    \usepackage{fancyhdr}
    \pagestyle{fancy}
    \fancyhf{}
    \fancyhead[L]{IIIF Document Information Extraction}
    \fancyhead[R]{Module 3 / Module 5 改进讨论}
    \fancyfoot[C]{\thepage}
    \setlength{\headheight}{14pt}
    \setlength{\parindent}{2em}
    \setlength{\parskip}{0.25em}
    \renewcommand{\arraystretch}{1.14}
---

# 结论

当前应把 **Module 3 和 Module 5 设为 P1**。两者已有明确问题和可立即验证的改进方向。Module 7 暂标为 Pending，明天取得公共字段要求后再转为 P1。

三个核心指标的方向基本正确，但需要区分“直接取得的信息”和“经过解析后取得的信息”：

| 指标 | 当前结果 | 用途 |
|---|---:|---|
| 已知入口直接 JSON 机构率 | 6/94，6.38% | 衡量 Module 1 输入中有多少机构直接暴露 JSON |
| 机构 Manifest 发现成功率 | 10/94，10.64% | 衡量 Module 3 的主要能力 |
| 明确开放版权率 | 18/324，5.56% | 衡量可明确再利用的数据 |
| 版权可判定率 | 122/324，37.65% | 衡量 Module 5 是否取得明确版权结论 |
| 研究数据保留率（新策略） | 324/324，100% | 衡量 URL、元数据和学术分析数据的保留规模 |

端到端对象数是结果指标，主要受入口质量、Module 3 发现能力和 Module 5 策略影响；同时也受单机构 Manifest 数量、采集上限以及后续校验率影响。它不能由三个百分比直接相乘得到。

“已知入口直接 JSON 率”主要反映清单和机构发布方式。Module 3 改进后应另外增加“**适配后机器入口解析率**”，避免把 Module 3 的搜索和适配成果错误记入 Module 2。

# Module 5：全部保留用于研究，单独限制公开再利用

## 当前状态

目前 324 个 Manifest 中：

- 18 个具有明确 public domain 或 open license；
- 202 个为 unknown；
- 104 个具有版权保护、限制性条款、机构条款或冲突。

## 已实施状态

Module 5 schema 2.0 已将“研究保留”和“公开再利用”拆分：

- **allow：**保留并进入研究下游，同时进入可公开再利用子集；
- **exclude：**同样保留并进入研究下游，但不得公开传播或商业使用；
- **unknown：**属于 `exclude` 的版权类别，同样保留 URL、元数据、机构和判断证据。

因此，当前 324 个 Manifest 均属于研究保留记录，其中 18 个进入可公开再利用子集，306 个属于研究专用记录。正式下游输入为 `research_manifests.jsonl` 和 `research_resource_inventory.jsonl`；公开再利用子集单独写入 `reuse_eligible_*.jsonl`。

每条记录继续保留 provider_id、provider_name、source_manifest_url、original_rights_values、evidence、policy_version、判断理由和运行时间，并显式记录学术分析、公开传播和商业使用权限。

## 为什么不能把接口公开直接解释为许可

IIIF 接口公开说明服务器允许当前请求访问，但不自动授予下载、传播或再利用许可。IIIF Presentation API 中的 rights 属性是可选的；没有 rights 只表示机器没有取得明确权利信息。

工程上应区分：

1. 保存 URL 和元数据；
2. 内部学术分析；
3. 对外传播或再利用图片。

unknown 和受限制记录都进入前两类研究数据，但不能自动标记为第三类的开放数据。这样既保留资源，也避免把“可访问”错误转换成“有许可”。

# Module 3 当前具备的能力

Module 3 已经处理 Module 2 给出的全部 158 个入口，并按 provider_id 合并同一机构的多条入口。它目前支持：

1. **直接 Manifest：**确认 JSON 类型后直接输出；
2. **Presentation Collection：**支持 IIIF Presentation 2/3、嵌套 Collection 和 next 分页；
3. **Change Discovery：**支持 OrderedCollection、OrderedCollectionPage 和活动记录；
4. **HTML 声明：**解析 data 属性、link、正文 URL 和 JSON-LD；
5. **通用机构 JSON：**递归寻找已经显式出现的 IIIF、Manifest 或 Collection URL；
6. **人工维护入口：**能够读取 provider_endpoints.json，但当前该文件为空。

本次 324 个 Manifest 的发现来源为：

- Presentation Collection：200；
- Change Discovery：100；
- HTML 声明链接：21；
- Module 2 直接 Manifest：2；
- 机构 API 中的显式 IIIF URL：1。

因此，当前代码并非只会一两种 IIIF 结构。它能够处理标准资源，但缺少“从未知机构业务系统定位标准资源”的知识。

# Module 3 的主要问题与解决方向

## 机构 API

很多机构 API 只返回对象 ID、记录 URL 或图片 ID，不直接给出 Manifest。当前程序只会提取 JSON 中已经出现且明确带有 iiif、manifest 或 collection 特征的 URL。

**解决方向：**建立声明式 API 适配器，记录请求模板、分页方式、记录数组路径、ID 路径、Manifest 字段或 URL 模板、限速和停止条件。优先采用平台级适配器，减少机构专用代码。

## 搜索 API 与标识符枚举

有些机构必须先调用站内搜索，再从结果中取得对象 ID，随后访问详情 API 或构造 Manifest。当前程序不会识别搜索表单、生成查询参数，也不会把普通 UUID、数字 ID 或馆藏编号解释为后续入口。

**解决方向：**增加 search adapter 和 identifier iterator，支持无关键词浏览、分页、ID 提取、详情请求、断点续跑和去重。

## Manifest URL 模板

机构可能使用稳定的“基础地址 + 对象 ID + manifest”格式，但完整 URL 不会出现在当前页面中。

**解决方向：**从官方文档、查看器配置或已验证样本中提取模板。每条模板保存适用域名、平台指纹、ID 来源、证据页面、验证时间、成功率和失效状态。模板生成的 URL 必须实际请求并通过 IIIF 类型验证。

## HTML 检查范围

当前每个机构最多读取 3 个页面，深度为 1，默认只在同一主机内继续，并依赖有限关键词。Manifest 可能位于更深对象页、不同子域、CDN、非英文页面或 JavaScript 配置中。

**解决方向：**先使用资料搜索和本地知识库，再对未解决机构增加 sitemap、站内搜索、相关子域白名单、多语言关键词和查看器配置提取。不要首先扩大无差别抓取范围。

## 动态网页

部分网站在浏览器执行 JavaScript 后才请求 API 或 Manifest。当前 HTTP 客户端不执行 JavaScript。

**解决方向：**优先读取页面源码、脚本配置和官方 API 文档；这些方法失败后，才使用受限无头浏览器捕获网络请求。

## 访问限制与分页差异

本次有 29 个 restricted、19 个 unreachable 和 9 个 temporary failure。普通机构 API 还可能使用 offset、cursor、token 或 Link header，而当前主要支持 IIIF Collection 和 Change Discovery 的标准分页。

**解决方向：**增加按主机限速、缓存、分时重试和清晰的学术 User-Agent；不绕过访问控制。把 API 分页设计成可声明组件，并保存 checkpoint。

# 低发现率的根源

94 个机构的结果可以归为：

| 结果 | 机构数 |
|---|---:|
| 已发现 Manifest | 10 |
| 本次没有可访问入口 | 27 |
| 入口可访问，但没有发现 IIIF 候选 | 13 |
| 尝试候选，但无法确认 Manifest | 44 |

在 67 个至少存在一个可访问入口的机构中，只有 10 个成功，成功率为 14.93%。因此，低发现率不能主要归因于网络。更大的问题是 57 个“可访问但未解析”的机构。

根源可以概括为：

- Module 1 的很多入口只是机构主页、项目页或查看器，不是机器采集接口；
- 当前程序擅长读取已经找到的标准 IIIF 资源，却不擅长识别机构使用的平台和业务 API；
- 当前没有搜索引擎、机构文档、GitHub 或资料库查询阶段；
- provider_endpoints.json 为空，没有可积累的机构或平台知识；
- HTML 方法经过关键词排序，并非完全盲目，但范围太浅；
- 每机构 100 个 Manifest 的上限影响产量，不是 84 个机构完全未发现的主要原因。

最核心的问题是：

> 对于可访问但不是标准 IIIF JSON 的入口，程序不知道该机构使用什么 API、搜索方式、标识符规则或 Manifest URL 模板。

# 建议采用“搜索优先、验证闭环”

你的“先搜索如何取得 Manifest，再执行解析”的方向正确，比单纯扩大网页遍历更有效。

建议执行顺序如下：

1. **标准入口直读：**先处理已经确认的 Manifest、Collection、Change Discovery 和 JSON；
2. **本地策略知识库：**查找过去已验证的平台与机构规则；
3. **官方资料定向搜索：**只对未解决机构检索官网、API 文档、GitHub、IIIF 社区资料和数据目录；
4. **策略提取：**将资料转换成 API、分页、ID 或 URL 模板候选；
5. **确定性验证：**实际请求候选并检查 IIIF 类型和结构；
6. **站内搜索或 sitemap：**仍未解决时枚举对象页和 ID；
7. **受限 HTML 抓取：**作为没有文档时的后备方法；
8. **动态浏览器：**最后使用。

搜索结果只能提供候选，不能直接作为成功结论。搜索页面可能过时、指向演示站点或非官方镜像，最终仍必须经过网络检查和结构校验。

每次成功研究一种平台或机构后，应把以下知识保存为版本化记录：

- 适用域名或平台指纹；
- 资料来源；
- endpoint 类型；
- API 请求与分页模板；
- ID 路径；
- Manifest URL 模板；
- 首次和最近验证时间；
- 成功率与失效状态。

下一次运行优先复用本地知识，只有没有匹配规则时才调用外部搜索。这可以减少重复搜索、搜索 API 成本和无效网站请求。

大语言模型可以帮助阅读 API 文档、提出模板候选和生成适配器草稿，但不能直接认定 Manifest 有效，也不能决定版权。URL 和版权结论仍需由确定性校验与证据确认。

# 建议的内部结构

以后可以把 Module 3 分为四个内部阶段：

- **3A Standard Resolver：**处理现有的 Manifest、Collection、Change Discovery、HTML 声明和显式 JSON URL；
- **3B Knowledge Resolver：**应用版本化的平台与机构策略；
- **3C Evidence Search：**只为未解决机构查询外部资料并生成候选规则；
- **3D Candidate Validator：**统一请求、验证、去重并保存来源证据。

这种设计保留自动化，也避免让搜索引擎或大语言模型直接控制最终数据。

# 修改程序前需要确认的方案

1. Module 3 与 Module 5 作为立即 P1；Module 7 暂列 Pending。
2. Module 5 已采用“研究保留状态 + 公开再利用决定”两层语义。
3. allow、unknown 和其他受限制类别全部进入研究下游；只有 allow 设置 public_reuse_eligible=true。
4. 分别报告版权可判定率、明确开放率和研究数据保留率。
5. Module 3 新增“适配后机器入口解析率”。
6. Module 3 使用“本地知识库 → 定向搜索 → 验证 → 受限抓取”的顺序。
7. 适配器以平台和 API 类型为主，机构规则作为必要补充。
8. 搜索获得的规则必须持久化、版本化和定期重新验证。
9. 继续使用 development/held-out provider 分割，避免测试机构专用规则造成虚假泛化提升。

# 官方依据

- IIIF Presentation API 3.0：<https://iiif.io/api/presentation/3.0/>
- IIIF Cookbook — Rights statement：<https://iiif.io/api/cookbook/recipe/0008-rights/>
- IIIF Rights Registry：<https://iiif.io/api/registry/rights/>
- IIIF Change Discovery API 1.0：<https://iiif.io/api/discovery/1.0/>

IIIF Presentation API 将 rights 定义为许可或权利声明，并允许 Manifest 不包含该属性。因此，缺少 rights 不能自动转换为开放许可。