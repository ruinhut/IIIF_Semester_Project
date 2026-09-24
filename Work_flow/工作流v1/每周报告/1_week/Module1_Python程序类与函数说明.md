# Module 1 Python 程序、类与函数说明

本文档对应 `Code_git/Module_1` 的当前代码。它按文件说明每个类和函数的职责、输入和输出。

约定：

- `self` 是实例方法自动接收的当前对象，`cls` 是类方法自动接收的当前类；调用时通常不需要手动传入。
- 名称以 `_` 开头的函数或方法是模块内部实现，不建议下游程序直接调用。
- `None` 表示函数没有业务返回值；它可能完成校验、写文件或修改初始化中的对象状态。
- `Mapping` 可理解为字典型对象，`Sequence` 是有顺序的集合，`Iterable` 是可逐项遍历的对象。

## 1. 文件总览

| 文件 | 主要职责 |
|---|---|
| `iiif_provider_census/models.py` | 定义统一数据模型、URL 规范化和稳定 ID |
| `iiif_provider_census/fetch.py` | 从 HTTP(S)、file URI 或本地路径读取 JSON |
| `iiif_provider_census/registry.py` | 解析 Registry、人工清单和目录快照，生成统一记录 |
| `iiif_provider_census/selector.py` | 根据明确条件筛选本次运行的机构入口 |
| `iiif_provider_census/store.py` | 读写 JSONL、CSV 和 TXT 日志 |
| `iiif_provider_census/pipeline.py` | 编排完整的模块 1 工作流 |
| `iiif_provider_census/cli.py` | 定义命令行参数和执行入口 |
| `iiif_provider_census/__init__.py` | 暴露包的公共类、函数和版本号 |
| `iiif_provider_census/__main__.py` | 支持 `python -m iiif_provider_census` |
| `tools/build_catalog_inputs.py` | 将两份外部目录转换成本地 JSON 输入快照 |
| `tests/test_selector_and_store.py` | 测试筛选和文件存储 |
| `tests/test_registry.py` | 测试 Registry/人工清单解析 |
| `tests/test_pipeline.py` | 测试完整流水线 |
| `tests/test_catalog_builder.py` | 测试外部目录转换工具 |

## 2. `models.py`

### 2.1 普通函数

#### `canonicalize_url(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 校验并规范化 HTTP(S) URL；统一协议和主机名大小写、删除默认端口和 fragment |
| 输入 | `value: str`，待处理 URL |
| 输出 | `str`，规范化后的 URL；非法 URL 或带账号密码时抛出 `ValueError` |

#### `stable_provider_id(discovery_endpoint)`

| 项目 | 说明 |
|---|---|
| 用途 | 根据规范化入口生成可重复的机构记录 ID |
| 输入 | `discovery_endpoint: str` |
| 输出 | `str`，格式为 `provider-` 加 SHA-256 摘要前 16 位 |

#### `_optional_string(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 把可选值转换成去除首尾空白的文本 |
| 输入 | `value: Any` |
| 输出 | 非空时返回 `str`；缺失或空文本返回 `None` |


### 2.2 `SourceProvenance` 类

**用途：**保存一条记录的来源证据。

**构造输入：**

| 字段 | 类型 | 含义 |
|---|---|---|
| `source_type` | `str` | 来源类别，例如 `iiif_registry` |
| `source_url` | `str` | 公开来源 URL 或本地来源路径 |
| `source_page_url` | `Optional[str]` | 具体条目所在页面 |
| `activity_type` | `Optional[str]` | Registry 活动类型，例如 `Update` |
| `observed_at` | `Optional[str]` | 本次观察时间 |

**构造输出：**一个不可变的 `SourceProvenance` 实例。

#### `SourceProvenance.from_mapping(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 从 JSON 解码后的字典重建来源对象 |
| 输入 | `value: Mapping[str, Any]` |
| 输出 | `SourceProvenance` 实例 |


### 2.3 `ProviderRecord` 类

**用途：**表示模块 1 中一条统一的机构或入口记录。

**主要构造输入：**

| 字段 | 类型 | 含义 |
|---|---|---|
| `provider_id` | `str` | 稳定记录 ID |
| `name` | `str` | 机构、馆藏或实现名称 |
| `institution_url` | `Optional[str]` | 面向人的机构页面 |
| `discovery_endpoint` | `str` | 交给下一模块检查的入口 |
| `discovery_type` | `str` | `OrderedCollection`、`InstitutionWebsite` 等入口类型 |
| `stream_label` | `Optional[str]` | 入口说明 |
| `collection_focus` | `Optional[str]` | 馆藏范围 |
| `estimated_size` | `Optional[int]` | 已知时的预计规模 |
| `rights_status` | `str` | `unknown`、`declared` 或 `mixed` |
| `rights_values` | `tuple[str, ...]` | 来源级版权值 |
| `record_status` | `str` | `active` 或 `removed` |
| `last_checked_at` | `Optional[str]` | 最近检查时间 |
| `source` | `SourceProvenance` | 来源证据 |
| `raw_source_record` | `Mapping[str, Any]` | 未丢失的原始来源记录 |
| `schema_version` | `str` | 模块 1 记录模式版本 |

**构造输出：**经过校验、不可变的 `ProviderRecord` 实例。

#### `__post_init__()`

| 项目 | 说明 |
|---|---|
| 用途 | 创建对象后自动规范化 URL，并检查名称、规模和状态 |
| 输入 | 隐式输入当前实例 |
| 输出 | `None`；非法字段抛出 `ValueError` |

#### `to_dict()`

| 项目 | 说明 |
|---|---|
| 用途 | 转换为可被 `json` 写出的普通字典 |
| 输入 | 隐式输入当前实例 |
| 输出 | `dict[str, Any]` |

#### `ProviderRecord.from_mapping(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 从 JSONL 字典校验并重建记录 |
| 输入 | `value: Mapping[str, Any]` |
| 输出 | `ProviderRecord` 实例；缺失或非法字段会报错 |


## 3. `fetch.py`

### 3.1 `FetchError` 类

**用途：**表示 JSON 来源无法读取、下载或解析。它继承 `RuntimeError`。

- 输入：通常是错误说明字符串。
- 输出：`FetchError` 异常对象；被 `raise` 后中断当前读取流程，由上层处理。

### 3.2 `JsonFetcher` 类

**用途：**统一执行本地和远程 JSON 读取，并限制超时与重试。

#### `__init__(timeout_seconds=20.0, retries=2)`

| 项目 | 说明 |
|---|---|
| 用途 | 创建读取器并检查网络参数 |
| 输入 | 正数超时秒数；非负重试次数 |
| 输出 | `JsonFetcher` 实例；参数非法时抛出 `ValueError` |

#### `load(reference)`

| 项目 | 说明 |
|---|---|
| 用途 | 根据地址类型读取 JSON |
| 输入 | `reference: str`，HTTP(S) URL、file URI 或本地路径 |
| 输出 | `Any`，`json` 解码后的字典、数组等对象；失败抛出 `FetchError` |

#### `_load_http(url)`

| 项目 | 说明 |
|---|---|
| 用途 | 发送带请求头的 HTTP GET，并进行有限重试和短暂指数退避 |
| 输入 | `url: str` |
| 输出 | 解码后的 JSON 对象；所有尝试失败后抛出 `FetchError` |


注意：`JsonFetcher` 只证明“某个来源能否作为 JSON 被读取”，并不执行模块 2 所需的完整入口有效性检查。

## 4. `registry.py`

#### `utc_now()`

| 项目 | 说明 |
|---|---|
| 用途 | 生成无微秒的当前 UTC 时间 |
| 输入 | 无 |
| 输出 | `str`，例如 `2026-09-17T10:00:00Z` |

#### `read_registry(source, fetcher, max_pages=100, observed_at=None)`

| 项目 | 说明 |
|---|---|
| 用途 | 读取 Registry Collection/Page，沿 `first/next` 或 `last/prev` 遍历，解析活动并去重 |
| 输入 | 来源地址、`JsonFetcher`、最大分页数、可选观察时间 |
| 输出 | `list[ProviderRecord]`；结构不支持、分页循环或超过限制时抛出错误 |

#### `read_manual_records(source, fetcher, observed_at=None)`

| 项目 | 说明 |
|---|---|
| 用途 | 读取人工清单或生成的目录快照，保留来源信息并统一成记录 |
| 输入 | 来源地址、`JsonFetcher`、可选观察时间 |
| 输出 | 去重后的 `list[ProviderRecord]` |

#### `deduplicate_records(records)`

| 项目 | 说明 |
|---|---|
| 用途 | 按规范化 `discovery_endpoint` 去重并按名称、入口排序 |
| 输入 | `Iterable[ProviderRecord]` |
| 输出 | `list[ProviderRecord]`；同一入口保留最后出现的记录 |

#### `_record_from_activity(activity, source_url, page_url, observed_at)`

| 项目 | 说明 |
|---|---|
| 用途 | 把一条 Add/Create/Update/Delete/Remove 活动转换成记录 |
| 输入 | 活动字典及来源上下文 |
| 输出 | 有效时返回 `ProviderRecord`；无关或缺少必要信息时返回 `None` |

#### `_parse_legacy_registry_record(document, source, observed_at)`

| 项目 | 说明 |
|---|---|
| 用途 | 兼容旧式带 `streams` 数组的 Registry 文件 |
| 输入 | Registry 字典、来源地址、观察时间 |
| 输出 | `list[ProviderRecord]` |

#### `_extract_label(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 从 `label`、`name`、`nameMap`、`summary` 或语言映射中找名称 |
| 输入 | `Mapping[str, Any]` |
| 输出 | `str` 或 `None` |

#### `_language_value(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 递归提取字符串、数组或语言映射中的第一个非空文本 |
| 输入 | `Any` |
| 输出 | `str` 或 `None` |

#### `_rights_values(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 统一单个或多个版权值 |
| 输入 | `Any` |
| 输出 | `tuple[str, ...]` |

#### `_as_mapping_list(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 把一个字典或字典数组统一为列表 |
| 输入 | `Any` |
| 输出 | `list[Mapping[str, Any]]` |

#### `_link_id(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 从 URI 字符串或含 `id/@id` 的对象读取链接 |
| 输入 | `Any` |
| 输出 | `str` 或 `None` |

#### `_resolve_reference(base, reference)`

| 项目 | 说明 |
|---|---|
| 用途 | 解析远程或本地相对链接 |
| 输入 | 基准地址与引用地址 |
| 输出 | `str`，解析后的绝对 URL 或绝对本地路径 |

#### `_host_name(url)`

| 项目 | 说明 |
|---|---|
| 用途 | 从 URL 提取主机名作为后备名称 |
| 输入 | `url: str` |
| 输出 | `str`，主机名；无法解析时返回原 URL |

#### `_optional_text(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 转换可选文本并去除空白 |
| 输入 | `Any` |
| 输出 | `str` 或 `None` |


## 5. `selector.py`

### 5.1 `SelectionCriteria` 类

**用途：**保存筛选规则。

**构造输入：**`include_provider_ids`、`include_exact_names`、`include_name_keywords`、`include_hosts`、`exclude_name_keywords`、`exclude_hosts`、`record_statuses` 等字符串元组，以及可选正整数 `limit`。

**构造输出：**不可变的 `SelectionCriteria` 实例。

#### `__post_init__()`

| 项目 | 说明 |
|---|---|
| 用途 | 确保 `limit` 为 `None` 或正数 |
| 输入 | 隐式输入当前实例 |
| 输出 | `None`；0 或负数抛出 `ValueError` |

#### `SelectionCriteria.from_mapping(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 从 JSON 配置字典创建筛选条件 |
| 输入 | `value: Mapping[str, Any]` |
| 输出 | `SelectionCriteria` 实例 |


### 5.2 普通函数

#### `select_providers(records, criteria)`

| 项目 | 说明 |
|---|---|
| 用途 | 筛选、稳定排序，并应用数量上限 |
| 输入 | 记录可迭代对象和 `SelectionCriteria` |
| 输出 | `list[ProviderRecord]` |

#### `_matches(record, criteria)`

| 项目 | 说明 |
|---|---|
| 用途 | 判断单条记录是否满足所有包含、排除和状态条件 |
| 输入 | 一个 `ProviderRecord` 和筛选条件 |
| 输出 | `bool` |

#### `_host_matches(host, rule)`

| 项目 | 说明 |
|---|---|
| 用途 | 匹配指定域名本身或其子域名 |
| 输入 | 实际主机名和域名规则 |
| 输出 | `bool` |

#### `_strings(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 校验选择配置中的数组并清理空元素 |
| 输入 | `Any`，必须为列表或 `None` |
| 输出 | `tuple[str, ...]`；类型错误抛出 `ValueError` |


## 6. `store.py`

#### `write_jsonl(path, records)`

| 项目 | 说明 |
|---|---|
| 用途 | 每行写入一条完整 JSON 机构记录 |
| 输入 | 输出 `Path`；记录可迭代对象 |
| 输出 | `int`，实际写入条数 |

#### `read_jsonl(path)`

| 项目 | 说明 |
|---|---|
| 用途 | 逐行解析并校验 JSONL |
| 输入 | 输入 `Path` |
| 输出 | `list[ProviderRecord]`；某行非法时报告文件与行号 |

#### `write_csv(path, records)`

| 项目 | 说明 |
|---|---|
| 用途 | 写入带 UTF-8 BOM 的人工查看表 |
| 输入 | 输出 `Path`；记录可迭代对象 |
| 输出 | `int`，实际写入条数 |

#### `write_text(path, value)`

| 项目 | 说明 |
|---|---|
| 用途 | 写入 UTF-8 文本并保证末尾有换行 |
| 输入 | 输出 `Path`；文本字符串 |
| 输出 | `None` |

#### `_csv_row(record)`

| 项目 | 说明 |
|---|---|
| 用途 | 将嵌套记录压平为 CSV 字段字典 |
| 输入 | `ProviderRecord` |
| 输出 | `dict[str, Any]` |


`CSV_COLUMNS` 是常量，不是函数；它规定 CSV 列名及顺序。

## 7. `pipeline.py`

### 7.1 `PipelineResult` 类

**用途：**表示一次成功完成的模块 1 运行结果。

**构造输入：**

- `all_provider_count: int`
- `selected_provider_count: int`
- `output_directory: Path`
- `all_providers_jsonl: Path`
- `selected_providers_jsonl: Path`
- `providers_csv: Path`
- `log_txt: Path`

**构造输出：**不可变的 `PipelineResult` 实例。它表示运行统计与文件位置，不代表模块 2 已经验证这些入口。

### 7.2 函数

#### `run_pipeline(config_path, institution_selection, run_time=None)`

| 项目 | 说明 |
|---|---|
| 用途 | 执行配置读取、来源加载、统一去重、人工选择、文件写出和日志生成 |
| 输入 | 配置路径；机构名称序列；可选运行时间 |
| 输出 | `PipelineResult` |

#### `_local_run_time(value)`

| 项目 | 说明 |
|---|---|
| 用途 | 确保运行时间带本机时区 |
| 输入 | `Optional[datetime]` |
| 输出 | 带时区的 `datetime` |

#### `_selection_for_run(institution_selection)`

| 项目 | 说明 |
|---|---|
| 用途 | 将 `--institution` 值转换成正式筛选规则 |
| 输入 | `Sequence[str]` |
| 输出 | 三元组：`SelectionCriteria`、日志标签、需验证的名称元组 |

#### `_validate_requested_names(requested_names, all_records, selected_records)`

| 项目 | 说明 |
|---|---|
| 用途 | 防止拼写错误或 inactive 名称被静默忽略 |
| 输入 | 请求名称、完整记录、选中记录 |
| 输出 | `None`；有缺失名称时抛出 `ValueError` |

#### `_format_run_log(...)`

| 项目 | 说明 |
|---|---|
| 用途 | 组合人类可读的运行日志 |
| 输入 | 时间、选择标签、来源报告、计数和三个输出路径 |
| 输出 | `str` |

#### `_read_config(path)`

| 项目 | 说明 |
|---|---|
| 用途 | 读取配置 JSON 并检查顶层对象 |
| 输入 | `Path` |
| 输出 | `Mapping[str, Any]`；读取或解析失败时抛出 `ValueError` |

#### `_mapping(value, name)`

| 项目 | 说明 |
|---|---|
| 用途 | 校验一个值是否为字典型对象 |
| 输入 | 任意值及其错误提示名称 |
| 输出 | `Mapping[str, Any]`；类型错误时抛出 `ValueError` |

#### `_source_list(value, name)`

| 项目 | 说明 |
|---|---|
| 用途 | 校验来源配置是否为数组 |
| 输入 | 任意值及配置项名称 |
| 输出 | `list[str]` |

#### `_resolve_local_source(source, base_directory)`

| 项目 | 说明 |
|---|---|
| 用途 | 远程 URL 保持不变；本地相对路径转为绝对路径 |
| 输入 | 来源字符串和配置目录 |
| 输出 | `str` |

#### `_resolve_directory(value, base_directory)`

| 项目 | 说明 |
|---|---|
| 用途 | 解析输出或日志目录 |
| 输入 | 路径字符串和配置目录 |
| 输出 | 绝对 `Path` |


## 8. `cli.py`

#### `build_parser()`

| 项目 | 说明 |
|---|---|
| 用途 | 定义 `run`、`select` 以及所有命令行参数 |
| 输入 | 无 |
| 输出 | `argparse.ArgumentParser` |

#### `main(argv=None)`

| 项目 | 说明 |
|---|---|
| 用途 | 解析命令；执行完整流水线或已有目录的再次筛选；输出 JSON 摘要 |
| 输入 | 可选字符串参数列表；`None` 时使用真实命令行 |
| 输出 | 成功返回 `0`；已处理错误打印到 stderr 并返回 `1` |


`run` 子命令需要 `--config` 和一个或多个 `--institution`。`select` 子命令需要已有 JSONL、输出路径和筛选条件 JSON。

## 9. `__init__.py` 与 `__main__.py`

这两个文件没有自定义函数或类：

- `__init__.py` 重新导出 `ProviderRecord`、`SourceProvenance`、`PipelineResult`、`SelectionCriteria`、`run_pipeline` 和 `select_providers`，并定义版本 `0.1.0`。
- `__main__.py` 导入并执行 `cli.main()`，把返回值作为进程退出码。因此可以运行 `python -m iiif_provider_census ...`。

## 10. `tools/build_catalog_inputs.py`

#### `_front_matter(path)`

| 项目 | 说明 |
|---|---|
| 用途 | 读取 Guide 页面开头简单 YAML 中的标量字段 |
| 输入 | Markdown 文件 `Path` |
| 输出 | `dict[str, str]`；无合法 front matter 时为空字典 |

#### `_git_revision(repository)`

| 项目 | 说明 |
|---|---|
| 用途 | 调用本机 Git 获取来源仓库当前提交 |
| 输入 | 仓库 `Path` |
| 输出 | 提交哈希 `str`；失败返回 `None` |

#### `build_guides_records(repository)`

| 项目 | 说明 |
|---|---|
| 用途 | 提取所有可见且有 homepage 的官方 Guide 条目 |
| 输入 | IIIF Guides 仓库路径 |
| 输出 | 按名称排序的 `list[dict[str, object]]` |

#### `build_awesome_records(repository)`

| 项目 | 说明 |
|---|---|
| 用途 | 提取 `implementations.md` 每个一级 Markdown 条目 |
| 输入 | Awesome IIIF 仓库路径 |
| 输出 | 按名称排序的候选字典列表 |

#### `_write_catalog(path, source_type, source_url, source_revision, providers)`

| 项目 | 说明 |
|---|---|
| 用途 | 保存来源元数据和候选记录 |
| 输入 | 输出路径、来源字段、记录可迭代对象 |
| 输出 | `int`，写入的记录数量 |

#### `build_parser()`

| 项目 | 说明 |
|---|---|
| 用途 | 定义两个来源仓库路径和输出目录参数 |
| 输入 | 无 |
| 输出 | `argparse.ArgumentParser` |

#### `main()`

| 项目 | 说明 |
|---|---|
| 用途 | 构建两份目录快照并打印数量 JSON |
| 输入 | 参数来自命令行 |
| 输出 | 成功返回整数退出码 `0` |


这个工具只准备输入文件，不进行网络可访问性或 IIIF 合规性检查。

## 11. 测试文件中的类和函数

所有测试方法都由 `unittest` 调用：显式业务输入为空，隐式输入为 `self`；正常输出为 `None`，断言失败时抛出 `AssertionError`。

### 11.1 `tests/test_selector_and_store.py`

#### `provider(name, endpoint, status="active")`

| 项目 | 说明 |
|---|---|
| 用途 | 为测试快速创建最小机构记录 |
| 输入 | 名称、入口、可选状态 |
| 输出 | `ProviderRecord` |

#### `SelectorAndStoreTests`

| 项目 | 说明 |
|---|---|
| 用途 | 汇集筛选和存储测试 |
| 输入 | 由 `unittest` 创建 |
| 输出 | 测试用例实例 |

#### `test_filters_by_name_host_status_and_limit_deterministically()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证域名、排除词、状态和 limit 的组合 |
| 输入 | 仅隐式 `self` |
| 输出 | `None` |

#### `test_exact_name_matching_is_case_insensitive()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证完整名称匹配不区分大小写 |
| 输入 | 仅隐式 `self` |
| 输出 | `None` |

#### `test_jsonl_round_trip_preserves_raw_record_and_csv_is_flat()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证 JSONL 保留嵌套来源而 CSV 为扁平视图 |
| 输入 | 仅隐式 `self` |
| 输出 | `None` |


### 11.2 `tests/test_registry.py`

#### `RegistryReaderTests`

| 项目 | 说明 |
|---|---|
| 用途 | 汇集 Registry 解析测试 |
| 输入 | 由 `unittest` 创建 |
| 输出 | 测试用例实例 |

#### `setUp()`

| 项目 | 说明 |
|---|---|
| 用途 | 每个测试前建立读取器和固定时间 |
| 输入 | 隐式 `self` |
| 输出 | `None`，设置两个实例属性 |

#### `test_follows_pages_and_keeps_latest_activity_per_endpoint()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证正向分页和较新活动覆盖旧活动 |
| 输入 | 隐式 `self` |
| 输出 | `None` |

#### `test_live_registry_actor_shape_and_declared_rights_are_parsed()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证当前 Registry actor 与 rights 结构 |
| 输入 | 隐式 `self` |
| 输出 | `None` |

#### `test_can_traverse_backwards_when_registry_omits_first_page()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证只有 `last/prev` 时可反向读取并恢复时间顺序 |
| 输入 | 隐式 `self` |
| 输出 | `None` |

#### `test_reads_manual_provider_list()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证人工清单可被统一 |
| 输入 | 隐式 `self` |
| 输出 | `None` |

#### `test_manual_catalog_preserves_external_provenance()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证生成目录的公开来源和条目页不会丢失 |
| 输入 | 隐式 `self` |
| 输出 | `None` |


### 11.3 `tests/test_pipeline.py`

#### `PipelineTests`

| 项目 | 说明 |
|---|---|
| 用途 | 汇集完整流水线测试 |
| 输入 | 由 `unittest` 创建 |
| 输出 | 测试用例实例 |

#### `test_local_end_to_end_run_writes_contract_outputs()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证本地完整执行会写出 JSONL、CSV 和秒级日志 |
| 输入 | 隐式 `self` |
| 输出 | `None` |

#### `test_all_selects_every_active_known_provider()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证 `all` 选择所有 active 记录 |
| 输入 | 隐式 `self` |
| 输出 | `None` |

#### `test_unknown_explicit_institution_fails_with_available_names()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证未知机构会明确报错并显示可用名称 |
| 输入 | 隐式 `self` |
| 输出 | `None` |


### 11.4 `tests/test_catalog_builder.py`

#### `CatalogBuilderTests`

| 项目 | 说明 |
|---|---|
| 用途 | 汇集外部目录转换测试 |
| 输入 | 由 `unittest` 创建 |
| 输出 | 测试用例实例 |

#### `test_guides_excludes_hidden_and_non_resource_pages()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证隐藏或没有 homepage 的 Guide 页面不会成为候选记录 |
| 输入 | 隐式 `self` |
| 输出 | `None` |

#### `test_awesome_keeps_every_list_entry()`

| 项目 | 说明 |
|---|---|
| 用途 | 验证 Awesome IIIF 的项目或工具条目不会被静默删除 |
| 输入 | 隐式 `self` |
| 输出 | `None` |


## 12. 一次实际运行中的调用关系

```text
__main__.py
  -> cli.main()
     -> cli.build_parser()
     -> pipeline.run_pipeline()
        -> pipeline._read_config()
        -> JsonFetcher(...)
        -> registry.read_registry()
           -> JsonFetcher.load()
           -> registry._record_from_activity()
        -> registry.read_manual_records()
        -> registry.deduplicate_records()
        -> pipeline._selection_for_run()
        -> selector.select_providers()
           -> selector._matches()
        -> pipeline._validate_requested_names()
        -> store.write_jsonl()
        -> store.write_csv()
        -> pipeline._format_run_log()
        -> store.write_text()
        -> PipelineResult
```

这条调用链说明：`pipeline.py` 负责编排，实际读取、解析、筛选和保存分别由专门文件完成。
