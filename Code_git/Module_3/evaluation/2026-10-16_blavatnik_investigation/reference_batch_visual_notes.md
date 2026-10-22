# 首批参考样例的目视核验

日期：2026-10-16。98 张成功下载图片均已实际解码，像素尺寸全部与机构
目录记录一致；294 个主要 JSON 已通过 schema 检查，98 份文本逐一与
机构 `originalTranscript` 清理后的原文比较一致，图片哈希及 Canvas 关联正确。
这些检查证明来源与对应关系，不证明转录内容逐字无误。

另选三张进行目视检查（不是对全部 98 张进行版面或质量分类）：

- `manifest-dc6a483307c2b2cf`：俄文信件，西里尔手写字。纸张破损、褶皱、
  缺失处明显，适合观察困难的历史手写材料；转录可能包含编辑性处理，
  不能假定缺纸处也有像素可供识别。
- `manifest-915193520d0d0804`：机构语言标为 Yiddish。页面含希伯来字母
  手写正文及印刷信笺抬头，抬头另含西里尔文字；这说明文献语言标签
  不等于页面只有一种 script 或只有手写内容。
- `manifest-c575cf96a79c71b0`：机构语言标为 English;Russian。
  电报式印刷表格上有英文和俄文手写字，确实具有混合文字与印刷/手写内容。

三张图片的具体路径见 `reference_batch_image_verification.json` 中
`example_images_by_reported_language`，完整图片、三份主要 JSON 和对应转录位于：

`reference_batch/module8/output/all/with_reference/<record_id>/<resource_folder>/`

文件包括 `image.jpg`、`common_record.json`、`common_media.json`、
`ocr_document_profile.json`、`institution_reference_texts.json` 和
`institution_reference_001.txt`。

注意：`ocr_ground_truth_candidates.jsonl` 是原有的代表页抽样建议，本批因
每机构默认抽样上限而只有 4 条，不是全部机构参考文本。全部 99 条已关联
文本在 Module 7 的 `institution_reference_texts.jsonl`；其中 98 条的图片
实际下载成功，1 条源图 404。不要用那 4 条候选替代完整参考文本输出。
