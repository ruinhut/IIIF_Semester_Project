# Blavatnik Archive 机构攻克与全目录验证

更新：2026-10-16T20:57:10+02:00。范围为本次公开目录快照。

已从 IIIF 官方指南入手，调查当前查看器和公共前端请求，保存了可执行的批量发现配方。旧的 `/manifest/view/...` 路由已失效；当前路线是只读 POST 搜索 → 目录 ID → 带完整参数的 Manifest URL。

## 已验证数量

| 阶段 | 结果 |
|---|---:|
| 公开目录唯一 ID | 20,199 |
| Module 3：返回声明为 Manifest 的 JSON | 20,199 |
| Module 4：通过本项目基本检查、可用于图片提取 | 19,625 |
| 无 Canvas/图片的 Video 条目 | 574 |
| Module 7：文献主记录 / OCR 文献画像 | 19,625 / 19,625 |
| Module 7：图片关联行 | 50,600 |
| 全库不同图片 URL | 50,188 |
| Module 7 已导出的对齐机构原文 | 174 |

Module 5 保留全部研究用途记录；Module 6、7 本次没有记录或媒体导出失败。`partial` 表示部分描述字段缺失，不是流程失败。

这不是纯古籍语料：目录包含 11,212 条明信片、3,270 条照片和 1,333 条信件等。不能把全部图片链接都称为古籍文字页或 OCR 训练页，具体类型见 CSV。

50,600 是文献—页面—图片关联次数；同一图片可属于相册与单件记录。Module 4 在每份 Manifest 内按图片 URL 去重后相加为 50,599；全库按 URL 去重为 50,188。这些都是声明的链接，不是已下载总量。

## 实际图片与原始转录

- 单页参考文本样例：99 次尝试，98 张成功，1 张失败（98.99%）；机构文本 98 份。
- 35 种文献类型的异质性样例：100 次尝试，100 张成功，0 张失败（100.00%）；机构文本 1 份。
- 补充的单页参考文本：74 次尝试，74 张成功，0 张失败（100.00%）；机构文本 74 份。
- 合并下载记录并按 resource_id 对照当前 Module 7 清单：174 个对齐页面候选中，173 个已下载图片和原文，1 个图片失败，0 个尚未尝试。
- 首批参考样例中，294 个主要 JSON 通过 schema，98 份原文与源字段、Canvas、图片哈希一致；98 张图片可实际解码且与机构声明尺寸相符。
- 类型样例中，100 张图片实际解码成功，300 个主要 JSON 通过 schema；item 13642 有一张图片的源宽高声明颠倒，已记录，未旋转原图来掩盖差异。
- 补充参考文本批次：222 个主要 JSON 通过 schema，74 张图片解码成功。
- 已确认的一张失败图片属于 item 19634：图片正文、标准信息地址和官网缩略图均返回 404，保留失败证据，不用别的图片替代。
- 机构原文来自 `originalTranscript`，不使用 `englishTranscript` 翻译代替。配对条件为单 Canvas、单图片、单目录页面且图片 ID 相同；多页全文与编号含糊的分段不随意配页。机构原文不保证经过人工校对。
- 类型平衡抽样是功能与异质性检查，不是全库可下载率的无偏估计。

## 本次修正与边界

- 全目录用真实返回的 60 条/页；按 30 个集合查询只有 20,162 个唯一 ID，完整无过滤查询补回 37 个。程序会检查接口总数，避免把服务器限制的短页误当作末页。
- 目录—Manifest 身份核对 20,199 条；标题一致 20,199 条，馆藏编号一致 20,199 条。
- 发布方 20,199 个原始响应均缺少顶层 `@id` 和 `label`。Module 4 仅以实际最终请求 URL 补足缺失标识符，保留原始 JSON、原始错误和独立补丁文件。标题由 Module 6 从机构 `metadata` 提取；这不代表原始或补丁后的描述已经通过完整 IIIF 合规认证。
- Module 3 增加通用只读 POST、JSON 请求体分页和目录头配置；大目录去重改为集合索引。旧 14 条机构配方逐项比对未变，新方法另行保存。
- Module 3–8 共 149 项测试通过，另有 7 项子测试；20,000 条去重插入的纯内存基准约 0.23 秒，不是网络吞吐量。
- 此次使用 AI 辅助调查并留存经验证的配方；运行时尚未接入自动调查未知机构的 LLM API。
- 沿用 10 月 15 日同一份机构清单，未跑通条目由 61 减至 60；这是累计记录，不是本次重新联网检查全部 94 条，也不等于去重后的机构数。

## 参考文本检查范围

公共 item JSON 已检查 13,488 个不同 ID，收到 JSON 13,488 份；其中 3,067 份的 originalTranscript 字段非空，195 份为单页候选。该数与已通过 Module 6 配图的文本数不同。
本轮 item 检查停止状态：`仍在继续`。未检查的 ID 不能算作没有文本。详情见 `reference_availability.json`；语言值保留机构原文，多语标签不强行拆成页面比例。

## 文件与重跑

- `stage_counts.csv`：模块输入/输出数量及单位；`catalogue_type_counts.csv`：各文献类型统计。
- `catalogue_declared_language_counts.csv`：已检查 item JSON 中 data.generalInfo.languages 的机构语言标签，按条目统计，不按图片页数统计；不是 OCR 自动识别结果，也没有用翻译语言或英文目录标题补值。
- `final/module3/output/manifest_urls.jsonl`：完整候选列表。
- `final/module4/output/`：结构结果、原始问题与图片清单；原文及补丁在 `final/module4/raw_manifests/`。
- `final/module7/output/`：主记录、图片关联、OCR 画像、机构参考文本。
- `reference_batch/module8/output/all/with_reference/`：实际图片、三个主要 JSON、机构转录索引和 TXT。
- `additional_references/module8/output/all/with_reference/`：新增参考页；`reference_delivery_index.csv` 将所有对齐候选与真实本地文件、失败原因逐一对应。
- `catalogue_document_transcripts.jsonl`：另存目录中清理后非空的文献级原文，保留来源、权限和配页状态；未配页的全文没有混入图片训练样例。数量见 `document_transcript_summary.json`。
- `diverse_downloads/module8/output/all/`：按 with_reference / without_reference 保存的类型样例。
- `identity_audit/`、`missing_image_diagnosis/`、各模块日志：身份核对与失败证据。
- `reproduce_commands.txt`：可复制的 PowerShell 命令；默认明确重放快照，新增 URL 仍会联网。Module 4 的全量核验复用了 Module 3 当次真实 HTTP 原文，没有谎报成第二轮独立联网请求。
- [官方指南](https://iiif.io/guides/guides/blavatnikarchive.org/)；[留存的方法与边界](../../knowledge/institutions/2026-10-16_blavatnik.md)。
