# Module 8：关联图片下载器

图片直链失效或请求格式不被支持时，Module 8 会读取该图片已声明的 IIIF
`info.json`，核验 Image API 上下文和尺寸，再通过该服务取得 JPEG。原始链接、
失败状态和回退尝试都会记录；不会按机构名称硬编码新地址。

下载目录中的 `common_media.json` 使用实际下载成功的 URL 和图片格式，同时通过
`image.source_id` 保留原始标识符。缓存重跑会保留已验证的 URL。Göttingen、Leiden
和 Wales 的真实样例均已验证这一通用处理。

Module 8 使用 Module 7 的 `common_media.jsonl` 作为图片下载清单。每张成功
下载的图片都和三份对应 JSON 放在同一个独立目录中：

1. `common_record.json`：该图片所属 Manifest 的文献主记录；
2. `common_media.json`：该图片对应的 Canvas、URL、顺序和版权字段；
3. `ocr_document_profile.json`：该 Manifest 的语言、年代、文字和 OCR 特征。
4. `institution_reference_texts.json`：机构提供的 OCR/转录文本与本图片的
   精确关联及下载来源；若存在，还会保存原始 hOCR/XML/文本和便于训练读取的
   纯文本版本。

三份文件通过同一个 `record_id` 关联。这样即使单独复制某张图片的目录，
仍然可以知道图片来自哪一份文献、哪一个 Canvas，以及它的 OCR 背景信息。

## 两条命令

在 `Code_git/Module_8` 中运行：

```powershell
python -m iiif_image_downloader download-example --config config.example.json
python -m iiif_image_downloader download-all --config config.example.json
```

- `download-example`：按 Module 7 的顺序尝试，直到成功下载一张图片；
- `download-all`：尝试下载所有允许学术分析并具有图片 URL 的记录。

每次输出自动分入 `with_reference/`、`without_reference/` 和
`reference_failed/`。只有至少成功下载一份机构 OCR/转录文本的图片才进入
`with_reference/`；生成训练集时可将 `require_reference_text` 设为 `true`。

未知版权或限制公开传播的资源，只要 Module 7 明确记录
`academic_analysis_allowed: true`，仍可为研究目的下载；三份 JSON 会继续保留
其不可公开传播、不可商业使用等限制。

## 输出目录

```text
data/output/example/   # 示例模式
data/output/all/       # 全部模式
```

每张图片的目录如下：

```text
<record_id>/<sequence>_<resource_id>/
  image.jpg
  common_record.json
  common_media.json
  ocr_document_profile.json
```

程序还会生成下载索引、失败清单、跳过清单、运行摘要和时间戳日志。
下载器会检查实际文件头，因此不会把 `info.json`、HTML 页面或普通文本错误地
保存为图片。再次运行时，已有且格式有效的图片会直接复用。

## 自动测试

```powershell
python -m pytest -q
```

测试使用本地模拟服务器，不会访问真实机构。
