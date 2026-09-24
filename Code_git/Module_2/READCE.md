# 模块 2：IIIF 入口可访问性与响应检查器

模块 2 读取模块 1 输出的 `selected_providers.jsonl`，逐一访问其中的候选入口，
记录网络和响应证据，并判断成功响应中的 JSON 能否解析。

模块 2 不遍历 Activity Stream 分页、不发现 Manifest URL，也不校验 Manifest
结构。这些工作分别属于模块 3 和模块 4。

## 处理流程

对于每个 `discovery_endpoint`，程序会：

1. 发送带超时限制的 HTTP GET 请求；
2. 跟随并记录重定向；
3. 对临时错误进行有限次数的重试；
4. 记录原始 URL、最终 URL、HTTP 状态码、响应类型、耗时和响应大小；
5. 在安全大小限制内读取响应；
6. 对 JSON 响应进行解析；
7. 保留全部模块 1 字段，并追加 `endpoint_check` 检查结果。

## 结果分类

| 分类 | 含义 |
|---|---|
| `reachable_json` | 可以访问，且 JSON 能够解析；交给模块 3 |
| `reachable_non_json` | 可以访问，但返回 HTML 或其他内容；人工复核 |
| `invalid_json` | 返回内容像 JSON，但无法解析；人工复核 |
| `response_too_large` | 响应超过配置的读取上限；人工复核 |
| `restricted` | 返回 401 或 403；人工复核 |
| `temporary_failure` | 超时、限流或可重试的服务器错误；以后重试 |
| `unreachable` | 地址或网络错误，或者不可恢复的 HTTP 错误 |

HTTP 200 只代表服务器成功响应，不代表该地址一定是合规的 IIIF API。

## 输出

`data/output/`：

- `checked_entry_points.jsonl`：全部检查结果；
- `discovery_ready.jsonl`：可以解析 JSON 的入口，作为模块 3 输入；
- `manual_review.jsonl`：需要人工复核的入口；
- `unavailable_entry_points.jsonl`：临时或永久无法访问的入口；
- `checked_entry_points.csv`：便于人工查看的表格。

日志存放在：

```text
data/log/Module2_YYYY-MM-DD_HH-MM-SS_log.txt
```

## 运行

在 `Module_2` 目录执行：

```powershell
python -m iiif_entry_validator run --config config.example.json
```

只检查前 5 条记录进行小规模测试：

```powershell
python -m iiif_entry_validator run --config config.example.json --limit 5
```

## 自动测试

```powershell
python -m unittest discover -s tests -v
```

测试使用本地 HTTP 服务器，不依赖外部机构当时是否在线。

## 2.0 版逐入口检查

Module 2 会检查每个机构的全部入口，并为每个“机构—入口”组合输出一条结果。日志分别记录机构数、候选入口数、实际检查数、可访问机构数和可解析 JSON 的机构数。
