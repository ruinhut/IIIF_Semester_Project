# Module 7——公共模式与 OCR 交接导出器

Module 7 校验 Module 6 的数据并导出带版本号的数据包。它保留原有对象与媒体输出，同时增加一套面向 Arsha 的 OCR 输出，用于选择 OCR 引擎和规划 ground truth（人工真值）样本。由于团队最终公共字段尚未确定，目前继续使用临时模式 `provisional-0.1`。

输出包含两类关联数据：

1. **对象记录**：每个 IIIF Manifest 一条；
2. **媒体记录**：每个 Canvas/图片一条，通过 `record_id` 关联对象。

Module 5 保留用于研究的全部记录都可以进入 Module 7，包括未知版权和受限制记录。每条对象与媒体记录都会继续保存：

- 版权类别和公开再利用决定；
- `research_status`；
- 学术分析权限；
- 公开传播和商业使用权限；
- `public_reuse_eligible`。

研究专用记录属于有效输出，但其限制字段会阻止它们被误认为可以公开传播或商业使用的数据。

字段不合法、ID 重复或找不到父对象的媒体记录仍会进入 rejection 文件。`dataset_manifest.json` 保存数量、文件大小和 SHA-256。

## OCR 交接内容

每个 Manifest 的 OCR 画像记录元数据中报告的语言、规范化年代和世纪、明确给出的文字书体、文献类型，以及基于元数据判断的载体类别：印刷、手写、混合、视觉/非文本或未知。它同时保留 Manifest URL、机构、媒体数量、研究权限，以及元数据明确提到的 Fraktur、blackletter、long s 或 ligature。

程序不会编造缺失信息。缩微胶卷、透印、破损、模糊、倾斜和低对比度必须检查实际图像像素，因此当前统一标记为 `unknown`，状态为 `not_assessed_no_image_pixels`。

ground truth 候选样本以固定、可复现的方式选择，尽量覆盖不同机构、载体类型、语言、世纪、书体和历史字体特征。`metadata_supported_ocr_candidate` 表示已有元数据支持其为印刷、手写或混合材料；`visual_triage_required` 表示纳入 ground truth 前需要查看页面。这里输出的是候选页面，不是已经转录完成的 ground truth。

## 运行

```powershell
python -m iiif_common_exporter run --config config.example.json
python -m pytest -q
```

原有输出包括 `common_records.jsonl/csv`、`common_media.jsonl/csv`、拒绝记录、数据包清单和运行日志。

新增 OCR 输出包括：

- `ocr_document_profiles.jsonl/csv`：每个 Manifest 的 OCR 画像；
- `ocr_dataset_summary.json`：语言、世纪、书体、印刷/手写类别和字段覆盖率统计；
- `ocr_ground_truth_candidates.jsonl/csv`：候选页面及其 Manifest、Canvas、图片和 Image API 地址。
- `institution_reference_texts.jsonl`：机构提供的 OCR/转录文本，并通过
  `resource_id` 与具体 `common_media` 图片关联。它属于机构参考文本，不能在
  未核实的情况下宣称为人工校对的绝对金标准。

JSONL 是完整、无损的正式输出，CSV 主要用于查看和交换。候选数量由配置中的 `max_ground_truth_records`、`pages_per_record` 和 `max_records_per_provider` 控制。
