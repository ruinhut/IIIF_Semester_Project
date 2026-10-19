# IIIF 官方机构操作知识库说明

本目录保存 IIIF 官方“Finding IIIF resources”指南中的机构级操作知识。
2026-10-08 的导入对应官方仓库提交
`c94b51bc335c6050667a536f2ba737807b92f8dc`，共包含 69 个可见的机构或资源条目，
并归纳为 9 类候选技能。

## 两层知识库

- `config/official_guide_knowledge.json`：保存官方指南原文中的操作、截图、链接、
  来源版本、检查日期和候选技能。它是调查证据，不能直接视为已经跑通。
- `config/discovery_knowledge.json`：只保存经过实际 HTTP、JSON 和 IIIF 类型验证后，
  可以由程序执行的机构配置与技能。

这样做可以避免把“官方页面告诉人如何复制 Manifest”错误地当成“程序已经能遍历
该机构的全部资源”。机构只有在完整链路得到验证后，才能从候选知识进入可执行知识。

## 主要文件

- `provider_skill_inventory.md`：69 个条目的可读表格，列出官方操作、候选技能和验证状态。
- `../../config/official_guide_knowledge.json`：供程序读取的完整机器可读版本。
- `../discovery_playbook.md`：对未知机构进行调查、验证和迁移测试的标准步骤。

目前的 9 类技能包括：筛选结果遍历、条目页 Manifest 提取、查看器配置提取、
标识符到 Manifest 模板、目录 API 标识符枚举、IIIF Collection 遍历、Wikidata P6108、
Image API 文件名解析，以及旧平台迁移复查。

本次导入中，5 个机构在旧版限量测试中已经找到 Manifest；EPFL Plume 另有已经验证的
可执行知识。其余 63 条仍是官方文档候选，需要逐条进行实时验证。
