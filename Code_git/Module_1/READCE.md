# 流水线机器 1：IIIF Provider Census and Selector

模块 1 建立 IIIF 机构及入口目录，并按照命令行参数选择本次需要处理的机构。它不下载 Manifest，也不判断入口是否有效；网络访问检查由模块 2 负责。

## 工作方式

```text
IIIF Registry ───────────────┐
IIIF 官方资源指南 ────────────┤
Awesome IIIF 实现清单 ────────┼─> 统一 ProviderRecord ─> 按入口去重 ─> 人工选择
项目人工补充清单 ──────────────┘                                  │
                                                                 ├─> providers.jsonl
                                                                 ├─> selected_providers.jsonl
                                                                 ├─> providers.csv
                                                                 └─> 秒级 TXT 日志
```

必须区分两类入口：

- `OrderedCollection` 等值表示已经登记的机器可读 IIIF 发现入口。
- `InstitutionWebsite` 或 `ImplementationWebsite` 表示可信目录提供的候选网页，尚未证明是机器可读 API，必须交给模块 2 检查。

因此，Registry 当前只有一条记录，只表示它目前只有一个自愿登记的活动流，并不表示世界上只有一家机构使用 IIIF。

## 输入

`config.example.json` 配置以下来源：

- `https://registry.iiif.io/index.json`：IIIF Registry 的机器入口；
- `config/iiif_guides_providers.json`：IIIF 官方资源指南快照；
- `config/awesome_iiif_providers.json`：IIIF GitHub 社区实现清单快照；
- `config/manual_providers.json`：项目自行维护的补充记录。

官方指南和 Awesome IIIF 的生成文件保留公开来源 URL、来源 Git 提交版本及每条记录的来源页面。Awesome IIIF 是“实现清单”，其中包含机构、项目、演示和工具；这些条目均作为候选入口保存，不能在模块 2 验证前统称为有效机构 API。

人工记录格式：

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

未知信息使用 JSON `null` 或明确的 `"unknown"`，不能猜测。`raw_source_record` 保存输入原文，`source` 保存来源类型、公开来源 URL、单条记录来源页和观察时间。

## 运行

环境要求：Python 3.10 或更高版本；无第三方运行依赖。

在本目录中选择全部已知活动入口：

```powershell
python -m iiif_provider_census run --config config.example.json --institution all
```

选择一个机构：

```powershell
python -m iiif_provider_census run `
  --config config.example.json `
  --institution "Bodleian Libraries, University of Oxford"
```

选择多个机构时重复使用 `--institution`。名称采用不区分大小写的完整匹配；未知名称会报错并列出可用名称。

## 输出

交换数据位于 `data/output/`：

- `providers.jsonl`：去重后的完整入口目录；
- `selected_providers.jsonl`：传给模块 2 的本次选择；
- `providers.csv`：便于人工检查的扁平表格。

运行日志位于 `data/log/Module1_YYYY-MM-DD_HH-MM-SS_log.txt`。日志记录本机时间、选择参数、各来源记录数、去重前后数量及输出路径。

## 更新两份公开清单

先取得 `IIIF/guides` 和 `IIIF/awesome-iiif` 的本地仓库，再执行：

```powershell
python tools/build_catalog_inputs.py `
  --guides-repository <IIIF-guides目录> `
  --awesome-repository <awesome-iiif目录> `
  --output-directory config
```

该脚本只转换公开清单，不验证网站或 API。生成后应运行测试和完整目录构建。

## 测试

```powershell
python -m unittest discover -s tests -v
```

实现依据：[IIIF Change Discovery API 1.0](https://iiif.io/api/discovery/1.0/)、[IIIF Registry](https://registry.iiif.io/)、[IIIF Guides](https://guides.iiif.io/finding_resources/) 和 [Awesome IIIF](https://github.com/IIIF/awesome-iiif/blob/main/implementations.md)。

## 2.0 版多入口数据结构

每个 JSONL 对象代表一个机构，`endpoints` 是长度不固定的入口数组。每个入口分别保存 URL、`endpoint_role`、资源类型、验证状态和来源。机构只在 provider ID、机构 URL 或共同入口等证据一致时合并；名称相同本身不作为合并依据。
