# 模块 3：IIIF 入口解析与资源发现

模块 3 将模块 2 检查过的机构候选入口转换为去重后的 IIIF Manifest URL。
它包含两个内部阶段：

1. **机器入口解析**：使用已确认 JSON、项目人工维护映射、HTML 明确链接、
   JSON-LD，以及受控的同站点网页爬取寻找机器入口。
2. **资源发现**：遍历 Change Discovery Activity Stream、Presentation
   Collection，或者接收网页直接声明的 Manifest。

模块 3 只发现 Manifest URL。Manifest 下载与结构校验属于模块 4。

## 输入

默认读取：

```text
../Module_2/data/output/checked_entry_points.jsonl
```

人工确认的机器入口保存在：

```text
config/provider_endpoints.json
```

示例：

```json
{
  "provider_id": "provider-example",
  "provider_name": "Example Library",
  "entry_points": ["https://example.org/iiif/activity/all-changes"],
  "html_seeds": ["https://example.org/digital-collections"]
}
```

程序优先通过 `provider_id` 匹配；缺少 ID 时使用不区分大小写的机构全名。
人工配置的 URL 仍然必须经过访问和 IIIF 类型检查。

## 支持的发现方式

- `OrderedCollection`：优先从 `last` 开始，通过 `prev` 反向遍历；
- `OrderedCollectionPage`：读取 `orderedItems` 中的资源；
- `Collection`：支持 Presentation API 3 的 `items`，以及 API 2 的
  `manifests`、`collections` 和 `members`；
- `Manifest`：直接记录 URL；
- HTML：识别明确的 Manifest 属性、JSON 类型链接、JSON-LD，以及少量
  具有 IIIF、馆藏、对象或查看器特征的同站点页面。

`Delete` 和 `Remove` 活动不会生成待采集 Manifest。所有分页、递归、
HTML 页面、候选 URL、响应大小和 Manifest 数量均有配置上限。

## 输出

`data/output/` 中包含：

- `provider_discovery.jsonl`：每个机构的完整发现报告；
- `resolved_endpoints.jsonl`：确认的机器可读 IIIF 入口；
- `manifest_urls.jsonl`：去重后的 Manifest URL，是模块 4 的主要输入；
- `unresolved_providers.jsonl`：没有发现 Manifest 的机构；
- `provider_discovery.csv`：便于人工检查的机构级汇总表。

日志位于：

```text
data/log/Module3_YYYY-MM-DD_HH-MM-SS_log.txt
```

## 运行

```powershell
cd E:\exchange-epfl\Semester_Project\Code_git\Module_3
python -m iiif_resource_discovery run --config config.example.json
```

只处理前 5 个机构：

```powershell
python -m iiif_resource_discovery run --config config.example.json --limit 5
```

## 测试

```powershell
python -m unittest discover -s tests -v
```

自动测试使用本地 HTTP 站点，不依赖外部机构当时是否在线。

