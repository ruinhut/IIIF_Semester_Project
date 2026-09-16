# 流水线机器 1：IIIF Provider Census and Selector

本模块建立 IIIF 数据提供机构目录，并为一次处理任务选择机构。它读取 IIIF Registry 或手工补充清单，统一字段、按发现入口去重，最后输出完整目录和选中目录。Manifest 抓取、入口可访问性检查及版权判定由后续模块负责。

## 它具体如何工作

可以把模块 1 理解为“机构通讯录生成器”，而不是 Manifest 下载器。一次完整运行分为五步：

```text
config.example.json
        │
        ├── IIIF Registry URL ──> fetch.py ──> registry.py ──┐
        │                                                    │
        └── manual_providers.json ──────────> registry.py ───┤
                                                             ▼
                                             ProviderRecord 统一数据模型
                                                             │
                                                按发现入口去重
                                                             │
                                          selector.py 按配置选择机构
                                                             │
                                              store.py 写入四类输出
```

1. `pipeline.py` 读取 `config.example.json`，确定从哪里获取机构；本次要处理的机构由运行命令中的 `--institution` 明确指定。
2. `fetch.py` 下载 Registry JSON；`registry.py` 遍历分页，并把不同来源的字段转换成统一的 `ProviderRecord`。
3. 程序以 `discovery_endpoint` 为机构数据流的唯一入口进行去重。较新的 Registry 活动覆盖旧活动；同一入口的人工记录可补充 Registry 信息。
4. `selector.py` 根据命令行输入的机构完整名称选择本次要处理的机构；输入 `all` 时选择全部未被标记为移除的已知机构。
5. `store.py` 保存完整目录和选中目录。下一台机器只需逐行读取 `selected_providers.jsonl`，取出其中的 `discovery_endpoint` 进行网络可访问性检查。

例如，Registry 中的一条活动说明 “Bodleian Libraries 发布了一个 Change Discovery 数据流”。模块 1 将它转换为包含机构名、机构网址和发现入口的记录，但不会在这一阶段读取该数据流中的 Manifest。

代码中的英文注释说明每个文件、函数和关键分支的职责。JSON 标准不允许注释，因此配置文件通过本 README 解释，不能直接插入注释。

## 运行环境

- Python 3.10 或更高版本
- 无第三方运行依赖

在本目录执行：

```powershell
python -m iiif_provider_census run --config config.example.json --institution all
```

输出位于 `data/output/`：

- `providers.jsonl`：完整机构/发现入口目录，也是模块的规范化主存储；
- `selected_providers.jsonl`：传给流水线机器 2 的机构子集；
- `providers.csv`：便于人工检查的表格视图，不含完整原始记录；
- `Module1_YYYY-MM-DD_HH-MM-SS_log.txt`：以电脑本地时间命名的本次运行日志。

## 输入

`config.example.json` 中配置两类机构来源：

1. `registry_sources`：IIIF Registry 的 `OrderedCollection` 或 `OrderedCollectionPage` URL/本地 JSON 文件；
2. `manual_sources`：人工维护的提供机构 JSON 文件，用于补充 Registry 尚未收录的机构。

手工记录格式：

```json
{
  "providers": [
    {
      "name": "Institution name",
      "institution_url": "https://institution.example/",
      "discovery_endpoint": "https://institution.example/iiif/activity/all-changes",
      "discovery_type": "OrderedCollection",
      "stream_label": "All changes",
      "collection_focus": null,
      "estimated_size": null,
      "rights_status": "unknown",
      "rights_values": []
    }
  ]
}
```

未知信息使用 JSON `null` 或明确的 `"unknown"`，不由程序猜测。`raw_source_record` 会在 JSONL 中保留来源记录，`source` 会保存来源 URL、页面 URL、活动类型和观察时间，从而可以追溯每条数据。`record_status = active` 只表示 Registry/手工清单没有将该记录标为移除，不代表端点已经通过网络可访问性检查；该检查属于流水线机器 2。

## 筛选规则

每次执行完整流程都必须人为指定机构。机构名称采用不区分大小写的完整名称匹配，拼写错误或已经移除的机构会触发错误，并显示当前可选名称。

选择一个机构：

```powershell
python -m iiif_provider_census run `
  --config config.example.json `
  --institution "Bodleian Libraries, University of Oxford"
```

选择全部当前已知且未被移除的机构：

```powershell
python -m iiif_provider_census run --config config.example.json --institution all
```

选择多个机构时，重复使用 `--institution` 参数。

也可以对现有目录重新筛选，而不重新访问 Registry：

```powershell
python -m iiif_provider_census select `
  --input data/output/providers.jsonl `
  --output data/output/selected_providers.jsonl `
  --criteria config/selection.example.json
```

## 测试

测试全部使用本地样例，不依赖网络：

```powershell
python -m unittest discover -s tests -v
```

实现依据为 [IIIF Change Discovery API 1.0](https://iiif.io/api/discovery/1.0/) 与 [IIIF Registry](https://registry.iiif.io/)。
