# Module 3：LLM 接口与知识复用

2026-11-05。UI 暂不开发；这里通过统一命令行或 Module 3 的 JSON 配置使用。

## 它如何工作

1. 先执行原有的入口解析、Collection/Change Discovery 遍历、HTML 发现和已审核机构配置。
2. 对仍未找到 Manifest 的机构，先重试独立学习库中属于该机构的方法。每次都重新请求并验证响应。
3. 用户显式开启 LLM 后，仍未解决的机构才进入模型调查。模型读取机构名称、候选 URL、失败原因和公开页面摘录；可请求查看其他公开页面，或通过支持的 Responses 服务使用网页搜索。
4. 模型给出 JSON 格式的方法配置，而不是可执行 Python。程序运行配置中的分页、ID 提取、URL 模板展开或 IIIF 入口遍历。
5. 实际请求得到声明标准 IIIF Presentation context、Manifest 类型且包含 Canvas 的 JSON 后，才输出 Manifest 并保存方法。完整结构和图片资源仍由 Module 4 检查。
6. Module 3 继续输出原有的 `manifest_urls.jsonl`，因此 Modules 4–8 无需了解 LLM 或机构平台。

“记住经验”指保存可复用的方法配置和验证证据，没有重新训练模型。它能组合已有执行技能；需要全新程序算法、登录、密钥保护的机构 API 或复杂脚本时，仍可能失败。不能声称已自动覆盖所有未知机构。

## 开始使用

在仓库根目录运行，机构名换成清单中需要调查的机构，模型 ID 换成自己 API 账户可用的模型：

```text
python pipeline.py --modules 1-3 --institution "机构名称" --llm --llm-model "自己的模型ID" --llm-key-prompt
```

随后出现隐藏的 token 输入提示。它只放在本次进程环境中，不写入配置和日志，也不作为命令行参数传给子进程。模型服务可能计费；ChatGPT/Codex 登录不自动提供 API 凭据。

也可将 token 单独放在仓库根目录 `.secrets/llm-token.txt`，只写一行令牌，然后使用：

```text
python pipeline.py --modules 1-3 --institution "机构名称" --llm --llm-model "自己的模型ID" --llm-key-file .secrets/llm-token.txt
```

`.secrets/` 已被 Git 忽略。共享配置只保存文件路径，不复制文件内容。文件也支持 `{"api_key":"自己的令牌"}`。环境变量 `IIIF_LLM_API_KEY` 也可使用；未设置时回退到 `OPENAI_API_KEY`。`IIIF_LLM_MODEL` 可代替模型参数。不要将密钥写到公共 JSON 配置、报告、截图或版本库。

## API 类型与搜索

默认：OpenAI Responses，`https://api.openai.com/v1`。支持相应工具的模型可加 `--llm-web-search`，由服务端进行网页搜索。不开搜索时，模型仍可请求公开 URL，但不会自动获得一个搜索引擎。

兼容其他服务：

```text
python pipeline.py --modules 1-3 --institution "机构名称" --llm --llm-model "模型ID" --llm-mode chat_completions --llm-base-url https://自己的服务/v1 --llm-key-prompt
```

该模式要求兼容 Chat Completions 的 JSON 请求/响应，不支持本程序的服务端网页搜索开关。若服务只接受 `max_tokens`，在 Module 3 配置的 `llm_discovery` 中设置 `"chat_token_parameter":"max_tokens"`；默认使用 `max_completion_tokens`。远程服务必须使用 HTTPS；用户自行选择的本机模型服务允许 loopback HTTP。

## 配置与预算

`config.example.json` 中 `llm_discovery.enabled` 默认为 `false`。独立运行 Module 3 时，在自己的配置中开启并提供模型、环境变量名或本地令牌路径即可；旧的 Module 3 命令仍有效。

默认每次最多调查 3 家未解决机构；每家最多 6 次模型调用、16 次公开请求、最多接受 3 个验证样例。配置限制与原有 `max_manifests_per_provider` 共同生效，取较小值。它验证方法样例，不能算作全馆采集。

```text
python pipeline.py --modules 3 --run-dir "已有运行目录" --resume --llm --llm-model "模型ID" --llm-key-prompt --llm-max-providers 2 --llm-max-rounds 6 --llm-max-fetches 16
python pipeline.py --modules 3 --run-dir "已有运行目录" --resume --no-llm
```

每家最多可设置 30 轮、200 次公开请求；不自动重试付费模型请求。支持的模型配置只生成公开 GET 请求，不执行模型生成的代码或附带认证头，不访问内网、localhost 和保留地址，并检查重定向目标。已有人工审核的机构方法不受这套生成配置白名单替换。

模型服务返回认证失败、配置错误或限额错误（HTTP 400/401/403/404/429）会让 Module 3 报错停止，避免反复调用或把 API 配置失败伪装成机构无法解析。普通候选失败则保留为未解决记录。

## 保存什么、去哪里看

- 原审核库：`config/discovery_knowledge.json`，原有内容保留。
- 新学习库：`config/learned_discovery_knowledge.json`，包含机构 ID/名称、执行技能、配置参数、验证时间、证据 URL、实际成功的 Manifest URL 和样例范围说明。文件使用临时文件替换和写锁保护。
- 机构结果：运行目录 `module_3/output/provider_discovery.jsonl`，保存成功状态、方法记录和失败原因。
- 下游输入：`module_3/output/manifest_urls.jsonl`，格式保持兼容。
- 调查日志：`module_3/log/llm_investigation.jsonl`，记录模型动作、公开请求结果、候选拒绝原因、成功方法、模型调用数与服务返回的 usage。没有价格模型，不将 token 用量伪装成实际费用。
- 普通摘要：`module_3/log/Module3_电脑时间_log.txt`，增加调查机构数、调用数和学习库位置。

后续不提供 API key，也会重试已学方法；若网站变动导致失效，会保留失败记录。不能因为过去成功就跳过当前 HTTP 和 JSON 验证。新学习文件可在审阅后纳入 Git，不包含 token；本次验证不会把模拟服务器的方法写入正式学习库。

## 本次验证的边界

测试使用本机模拟模型服务，验证 Responses/Chat Completions 协议和实际执行引擎；机构 HTTP 服务也通过真实请求交互。测试覆盖错误认证响应、无效模型 JSON、无证据候选、非 IIIF/空 Manifest、请求预算和无密钥重用。

没有用户提供的真实模型凭据，因此未进行付费模型端到端效果评测。接口测试通过不等于证明模型对所有机构都有泛化能力。

另外，用模拟 Responses 服务给出预先指定的 EPFL 方法，实际请求 EPFL 的公开 API 提取 `o:id`，并成功验证 item 44 的真实 Manifest；随后关闭模型、移除测试 token 再次执行，复用成功且模型调用为0。结果在 `Pipeline_Runner/data/cli_validation_20261105/llm_public_recipe_replay/verification.json`。这验证了真实网站与学习库的连接，不应表述为真实 AI 独立调查成功。

接口参考：[OpenAI Responses](https://developers.openai.com/api/reference/resources/responses/methods/create)、[Web search](https://developers.openai.com/api/docs/guides/tools-web-search)。
