# 模块 6：元数据提取与规范化

模块 6 读取模块 5 放行的 Manifest 和图片清单。它保留 IIIF 中的原始元数据，同时把可识别内容映射为稳定字段：标识符、标题、描述、作者、日期、地点、主题、类型、语言、版权和来源。

程序不会猜测缺失内容。无法确定的日期或地点仍保留原文，并把记录标为 `partial`。日期只在能够识别 ISO 日期、年份、年份区间或世纪时进行规范化；地点只清理文本，本模块不负责地理编码。

## 运行

```powershell
cd Code_git/Module_6
python -m pip install -e .
python -m iiif_metadata_normalizer run --config config.example.json
```

小规模样本测试可改用 `config.smoke.json`。

主要输出包括：`normalized_records.jsonl`（每个 Manifest 一条对象记录）、`normalized_resources.jsonl`（每张图片一条资源记录）、两个便于阅读的 CSV、失败记录和带本机时间的 TXT 日志。运行测试使用 `python -m pytest -q`。
