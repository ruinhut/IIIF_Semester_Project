# 模块 7：公共模式校验与导出

模块 7 把模块 6 的结果映射为带版本号、经过校验的交付数据包。目前团队的最终公共模式尚未给出，因此这里使用 `provisional-0.1` 临时模式；映射逻辑集中在本模块，周二取得最终字段后只需替换模式和映射，不必修改模块 1–6。

输出采用两张相互关联的表：

1. `common_records`：每个 Manifest 一条对象记录，包含标识符、描述元数据、日期、地点、版权、来源、质量和处理来源。
2. `common_media`：每个 Canvas/图片一条媒体记录，通过 `record_id` 连接对象，并保留图片地址和 IIIF Image API 服务地址。

模块会自动拒绝字段不合法、ID 重复或找不到父对象的媒体记录，并把原因写入 rejection 文件。`dataset_manifest.json` 记录全部交付文件的数量、字节数和 SHA-256，便于验证数据包完整性。

运行：

```powershell
cd Code_git/Module_7
python -m pip install -e .
python -m iiif_common_exporter run --config config.example.json
python -m pytest -q
```
