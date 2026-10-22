# Module 4：IIIF Manifest 获取与结构校验

Module 4 读取 Module 3 输出的 Manifest URL，下载并缓存原始 JSON，检查其是否符合基本 IIIF Presentation 结构，并输出页面与图片资源清单。

它不继续发现 Manifest，不判断版权是否允许使用，不执行元数据标准化，也不下载完整图片或运行 OCR。

## 输入

默认读取：

~~~text
../Module_3/data/output/manifest_urls.jsonl
~~~

每条记录包含稳定的 manifest_id、manifest_url、机构信息和发现证据。Module 4 会完整保留这些来源信息。

## 处理步骤

1. 如果本地已有缓存且没有指定强制刷新，则读取缓存；
2. 否则发送带超时、重试、大小限制、Accept 和 User-Agent 的网络请求；
3. 解析 JSON，按 manifest_id 保存原始响应，并计算 SHA-256；
4. 检查顶层类型是否为 Manifest，以及是否存在 id 或 @id；
5. 分别检查 Presentation 3 的 items/Canvas 和 Presentation 2 的 sequences/canvases；
6. 统计 Canvas、图片 body、Image Service、辅助文件和顶层 rights/license；
7. 将结果分为 valid、manual_review、invalid 和 unavailable。

缺少 context、没有可用 Canvas 或没有图片时进入 manual_review。不是 Manifest、必要结构错误或 JSON 无法解析时进入 invalid。HTTP 和网络失败进入 unavailable。

## 输出

- data/raw_manifests：可解析原始 JSON 和请求元数据；
- data/output/validated_manifests.jsonl：交给 Module 5；
- data/output/manifest_resource_inventory.jsonl：逐 Canvas/图片资源；
- data/output/manifest_resource_inventory.csv：便于人工查看；
- data/output/manual_review.jsonl：需要人工判断；
- data/output/invalid_manifests.jsonl：JSON 或结构错误；
- data/output/unavailable_manifests.jsonl：网络访问失败；
- data/log/Module4_电脑时间_log.txt：运行摘要。

资源清单包含机构、版权字段、Canvas 顺序与标签、图片地址、格式和 Image Service 地址。正式交给下游使用前，仍需由 Module 5 按团队规则筛选版权。

## 运行

在 Code_git/Module_4 中执行：

~~~powershell
python -m iiif_manifest_validator run --config config.example.json
~~~

只测试前5条：

~~~powershell
python -m iiif_manifest_validator run --config config.example.json --limit 5
~~~

忽略缓存并重新访问：

~~~powershell
python -m iiif_manifest_validator run --config config.example.json --limit 5 --force-refresh
~~~

config.smoke.json 对应5个公开 Manifest 的联网测试样本。

## 自动化测试

Canvas 的标识符保留 `#canvas` 等 fragment，因为它属于逻辑资源的身份。
这与 HTTP 请求 URL 的处理不同；不会修改发布方原始 JSON。

~~~powershell
python -m unittest discover -s tests -v
~~~

测试覆盖 Presentation 2/3、重定向、访问限制、响应过大、错误 JSON、错误资源类型、人工审核分类、资源输出和缓存复用。

## 缺失标识符的透明处理

`normalization.infer_missing_manifest_id` 默认开启：仅当响应明确声明为
IIIF Presentation Manifest、且顶层标识符缺失时，以成功请求的最终 URL
补足 `id` / `@id`。原始 JSON 不改动，另写 `.normalized.json`；输出同时
保留 `source_structural_validation` 原始问题及 `structural_normalization`
补丁依据。设为 `false` 可严格拒绝原始缺失标识符的响应。

校验范围是本项目用于提取图片的基本结构检查，不是全部 IIIF 必填字段
的合规认证。复用 Module 3 当前 HTTP 快照时也会保留来源和原始时间，
不会把缓存命中说成重新联网成功。

## Git

Git 记录程序、测试、README、示例配置和小型样本输入。下载的原始 Manifest、运行输出和日志不会提交。任何 .py 文件都不会被整体忽略。
