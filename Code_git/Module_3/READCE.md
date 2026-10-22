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

对于不能由上述通用 IIIF 入口直接解析的机构，机器可读知识库存放在：

```text
config/discovery_knowledge.json
```

知识库保存已核实的机构事实，例如列表 API、记录数组路径、标识符字段、
分页参数、筛选条件和 Manifest URL 模板；真正的解析算法保存在通用技能中，
不会为每个机构在 Python 代码里堆叠分支。

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

## 2.0 版多路线发现

Module 3 先按 `provider_id` 合并 Module 2 的多条入口结果，再依次处理 JSON、HTML、Change Discovery、IIIF Collection 及 API 中明确暴露的 IIIF 链接。Collection 的 `next` 分页会在上限内继续遍历。只要至少一条路线发现 Manifest，该机构即视为发现成功。

## 2.1 版知识与技能层

2.1 版把未知机构的“做题思路”保存为两层知识：

1. `knowledge/discovery_playbook.md` 记录人类调查流程：分析 Module 2
   证据、识别站点软件或官方 API、寻找记录枚举方式、验证 Manifest 规律、
   再做限量测试；
2. `config/discovery_knowledge.json` 记录程序可执行的机构事实，并调用
   `skills.py` 中的通用技能。

目前的通用技能 `paginated_json_identifiers_to_manifest_templates` 能够遍历
JSON 列表 API、从配置路径提取记录与 ID、应用筛选条件、生成候选 Manifest
URL，并验证其是否为 IIIF Presentation 2/3 Manifest。技能运行情况会写入
`provider_discovery.jsonl` 的 `knowledge_application`，日志另外统计技能运行次数
及借助知识成功解决的机构数。

2026-10-01 的限量迁移测试先突破 EPFL Plume，再把同一通用技能应用到结构
不同的 Art Institute of Chicago API。两个机构均成功发现 10 个 Manifest，
共 20 个；Module 4 随后验证 20/20，并识别 5,570 个 Canvas、图像主体和
Image Service。这里每个机构最多取 10 个，只用于验证方法迁移，不能视为机构
完整资源总量。

## 2026-10-16：公共 POST 搜索与全目录核对

通用技能现在支持只读 POST、JSON 请求体里的分页偏移、目录请求头和
接口声明总数的核对。请求体与请求头放在机构配置里，Manifest 仍用普通 GET；
程序不按机构名称添加分支。去重改为集合索引，保留各个来源的证据，
避免大目录逐条加入时反复扫描全部旧记录。

本次 Blavatnik 的方法、旧地址失效、实际返回页大小、目录遗漏与源图片
坏链证据均见 `knowledge/institutions/2026-10-16_blavatnik.md`。
原 EPFL、Chicago 等配方保留；没有把这次成功宣称为所有未知机构都已解决。
