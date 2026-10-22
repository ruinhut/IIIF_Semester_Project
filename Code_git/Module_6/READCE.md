# Module 6——元数据提取与规范化

Module 6 读取 Module 5 输出的全部研究保留记录，包括可公开再利用、未知版权和受限制记录。

本模块保存 IIIF 中的原始元数据，并将可识别内容映射为稳定字段：标识符、标题、描述、作者、日期、地点、主题、类型、语言、版权和来源。Module 5 给出的版权限制会继续附着在每条记录和资源上，使 Module 7 能够区分研究数据与可公开再利用数据。

## 输入

- `research_manifests.jsonl`：全部 `research_status = retained` 的 Manifest；
- `research_resource_inventory.jsonl`：全部可用于学术分析的资源行；
- Module 4 缓存的当前原始 Manifest JSON。

## 输出

- `normalized_records.jsonl`
- `normalized_resources.jsonl`
- `normalized_reference_texts.jsonl`：机构在 Manifest 中声明的 OCR/转录文本，
  保留其 Manifest、Canvas、机构、格式与对齐范围

- `metadata_summary.csv`
- `normalized_resources.csv`
- `failed_records.jsonl`
- `data/log/Module6_电脑时间_log.txt`

程序不会猜测缺失内容。无法确定的字段仍保留原文，并将记录标为 `partial`。

## 可选的机构目录原文补充

有些机构把原始转录放在自己的公开藏品 API 中，Manifest 只给图片。
`provider_reference_sources` 可以指定经过核验的目录配置；程序读取
指定字段，并保留源 JSON、字段路径和语言信息。

当前只在“一个 Canvas、一个图片主体、一个目录页面，且图片标识相同”
时自动建立配对。不把英文翻译当作俄文图片的 OCR 答案，也不把多页全文
随便配给其中一张图。无法配对时记明原因，图片和文献记录仍继续输出。

`catalogue_reference_cache_directory` 可指定保存的目录快照。配置中的
`cache_only=true` 表示只使用这份快照；没采集到的目录记录属于未检查，
不代表机构没有转录。`catalogue_reference_audit.jsonl` 可查看实际结果。

## 运行与测试

```powershell
python -m iiif_metadata_normalizer run --config config.example.json
python -m pytest -q
```
