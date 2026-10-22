# Module 3 AI泛化与OCR图文训练集改进计划

日期：2026-10-06

## 1. 当前结论

后续工作应沿两条相互关联的路线推进：

1. 为 Module 3 增加可持续的未知机构调查能力，使未来新增机构也能被处理；
2. 保留机构提供的页面文本，将图片和OCR或人工转录准确关联后交给 Arsha。

当前有界全流程测试中，Module 3 只为94家候选机构中的10家发现了
Manifest。已测试的324个 Manifest 产生约5.46万条媒体记录。这说明一旦扩大
机构发现覆盖率，后续模块可以处理更大规模的数据，但目前最主要的上游瓶颈仍然
是 Module 3。

## 2. 路线一：Module 3的AI泛化能力

### 2.1 当前阶段：使用Codex建立初始知识

近期可以使用 Codex 遍历尚未解决的机构，逐家完成以下调查：

```text
读取Module 2的全部入口和访问结果
-> 判断机构网站、平台和公开API
-> 查找官方技术文档
-> 枚举藏品标识符
-> 推导候选Manifest URL
-> 实际请求并验证Manifest
-> 保存调查过程、通用技能和机构配置
```

这一阶段的目标是建立经过验证的初始知识库，并总结不同机构之间可复用的处理
模式。它能够处理目前已知机构，但不能自动保证未来新增机构的泛化性。

### 2.2 最终阶段：在Module 3中接入AI API

Module 3最终应具备运行时调查未知机构的能力。建议分成三层：

1. **调查流程（Investigation Playbook）**\
   规定分析 Module 2 证据、识别平台、查找文档和验证完整链路的步骤。
2. **通用技能（Reusable Generic Skills）**\
   实现 API 分页、标识符提取、记录筛选、URL模板展开和IIIF结构验证。
3. **机构知识与配置（Provider Knowledge and Configuration）**\
   保存机构API地址、JSON路径、分页参数、筛选条件、Manifest模板和证据来源。

未来工作流为：

```text
未知机构
-> AI读取入口并检索技术资料
-> AI提出结构化发现方案
-> 确定性程序验证HTTP、JSON和IIIF结构
-> 只保存验证成功的方法
-> 后续机构复用已有经验
```

AI负责调查和提出候选方案；确定性程序负责最终判定。这样可以避免未经验证的
AI输出直接进入数据集。

\newpage

### 2.3 AI API的结构化输出

AI不应只返回自然语言解释，而应输出可验证的配置，例如：

```json
{
  "provider_id": "provider-example",
  "api_url": "https://example.org/api/items",
  "records_path": "data.items",
  "identifier_path": "id",
  "pagination": {
    "page_parameter": "page",
    "page_size_parameter": "limit"
  },
  "manifest_url_templates": [
    "https://example.org/iiif/{identifier}/manifest"
  ],
  "evidence_urls": [
    "https://example.org/developer-documentation"
  ]
}
```

程序必须对配置产生的每个候选URL执行实际请求，并检查其是否声明有效的IIIF
Presentation Manifest。

## 3. 路线二：为Arsha生成图片-文本训练材料

部分机构在 Manifest 中提供与每个 Canvas 对应的OCR或人工转录，例如：

- Presentation 2 Canvas的 `seeAlso`；
- Presentation 2的 `otherContent`；
- ALTO XML；
- hOCR；
- 纯文本文件；
- Presentation 3中 `motivation: supplementing` 的 Annotation。

当前流水线能够输出图片，但没有把这些页面文本一直传递到 Module 7。因此需要
修改 Modules 4-7。

### 3.1 各模块需要增加的功能

| 模块 | 需要增加的功能 |
|---|---|
| Module 4 | 从 Manifest 和 Canvas 中提取文字资源地址、格式、类型及对应关系；下载或缓存原始文本并保存校验值。 |
| Module 5 | 分别保存图片与文字资源的版权证据，继续区分学术分析、公开传播和商业使用。 |
| Module 6 | 解析和规范化 hOCR、ALTO、纯文本及 Annotation，保留原始内容、语言、版面信息和来源。 |
| Module 7 | 输出页面级图片-文本配对，并生成供 Arsha 使用的训练、验证和测试划分。 |

### 3.2 建议的页面级输出

```json
{
  "record_id": "manifest-example",
  "canvas_id": "https://example.org/canvas/15",
  "image_url": "https://example.org/image/15/full/full/0/default.jpg",
  "image_service_url": "https://example.org/image/15",
  "text_url": "https://example.org/ocr/15.hocr",
  "text_format": "text/vnd.hocr+html",
  "text_source": "institution_provided_ocr",
  "alignment_scope": "canvas",
  "verification_level": "silver_standard",
  "image_rights": {},
  "text_rights": {},
  "provenance": {}
}
```

核心要求是每条文本必须能够追溯到具体 `canvas_id` 和 `image_url`，不能只保存
文献级描述。

### 3.3 文本质量分级

机构提供的文本不应全部自动视为 ground truth：

| 等级 | 含义 | 建议用途 |
|---|---|---|
| `institution_provided_ocr` | 机构OCR，尚未人工校对 | 银标准、预训练或预标注 |
| `institutional_transcription` | 机构提供的人工或学术转录 | Ground-truth候选 |
| `human_verified_ground_truth` | 已确认与页面准确对齐并经过人工校对 | 正式训练、验证和测试 |

训练集、验证集和测试集应优先按机构或文献划分，避免同一文献的相邻页面同时进入
训练集和测试集而造成数据泄漏。

## 4. 建议实施顺序

### 第一阶段：跑通一组真实图片-文本配对

优先选择 BSB。其部分 Manifest 已在 Canvas 的 `seeAlso` 中提供 hOCR 地址，
适合验证：

```text
Canvas
-> 图片URL
-> hOCR URL
-> 下载文本
-> 解析文本
-> 保存图文配对
-> Module 7导出
```

验收条件：至少一份文献的多个页面能够同时下载图片与机构文本，并通过
`record_id`、`canvas_id` 和 `resource_id` 准确关联。

### 第二阶段：扩展文本格式和机构覆盖

在 hOCR 跑通后，依次增加 ALTO、纯文本、Presentation 2 Annotation List和
Presentation 3 supplementing Annotation，并统计各机构可用的图文对数量。

### 第三阶段：建立Module 3初始知识库

使用 Codex 调查当前未解决机构，记录成功方法和失败原因。只有被确定性验证器
确认的方案才能加入知识库。

### 第四阶段：接入OpenAI API

当调查流程、通用技能接口、知识库结构和验证器稳定后，再将 AI API 接入
Module 3。这样API产生的方案具有明确输入、输出和自动验证标准。

### 第五阶段：泛化性评估

将机构划分为开发集和独立测试集，重点统计：

- 机构Manifest发现成功率；
- 每个机构发现的有效Manifest数量；
- AI方案通过确定性验证的比例；
- 仅增加配置、不增加机构专用Python代码时的测试机构成功率；
- 可用图片-文本配对数量及其质量等级分布。

## 5. 最终目标

最终流水线应同时具备两种能力：

1. Module 3能够调查未来新增的未知机构，并将验证成功的方法积累为可复用经验；
2. Modules 4-7能够输出具有清晰来源、版权状态和质量等级的页面级图片-文本
   数据，为 Arsha 的OCR引擎选择、训练和评估提供可靠输入。
