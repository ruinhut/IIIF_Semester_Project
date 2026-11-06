# 团队 schema 与 Time Atlas 输入核对

核对日期：2026-11-06。

当前代码在开发前已保存：提交 `595b02e`，远端分支 `backup/pre-time-atlas-2026-11-06`，标签 `pre-time-atlas-2026-11-06`。原有 GitHub main 未覆盖。

## 老师要求与已确认格式

教师原 PDF 第 59–60 页要求我们的采集记录符合公共模式，准备供提取和 Time Atlas 使用；第 58 页说明采集与 Hafidz 提取共同进入公共记录；第 46–47 页把 canonical record 与 Time Atlas crosswalk 的设计交给 Kaile。最低公共信息包括稳定 identifier、带精度的 date、place、language、rights、source。

仓库中没有发现 Kaile/Ziyi 提供的正式可执行 schema。现有 M7 的 `provisional-0.1` 和 `example.org` schema ID 是临时本地格式，不能冒充团队或 Atlas 官方规范。需要区分“已实现导出”和“已通过团队验收”。

本次另外取得了 [EPFL 官方 Time Atlas Python 库](https://github.com/epfl-timemachine/time-atlas-python/tree/2c7d59e03298bd5eec31faec74c7530254e026fa)，版本 0.3.0。它实际使用 Dataset、HistoricalRecord、Observation、Area 等 RDE 实体，及带 `type_in_file` / `rde_objects` 的导入 envelope；现有 M7 JSONL 不能直接冒充这种输入。

## 本次完成

Module 7 新增独立 Atlas 导出，可用 `--atlas-export` 接入原一键流水线，也可以单独转换已有 M7 文件。它提供稳定 UUID 和原 record_id 对照，保留完整日期、地点、版权、来源、图片和参考文本关联；原 Arsha/OCR 文件不替换。

unknown 和禁止公开再利用的记录继续进入研究数据。没有日期或日期冲突的记录完整暂存，不伪造时间。仅有地名时不创建经纬度，不把图书馆位置当作文献内容涉及的历史位置。

已有明确坐标及证据时，可通过 profile 指定空间注释，产生关联 Observation 和范围 Area；也可配置平台给出的现成 Area UUID，后者仍需目标平台确认存在。本次未执行远端上传、来源注册或公开发布。

## 测试与边界

- 原流水线 Python 3.10：M7 51 项通过，2 项 SDK 测试因环境版本跳过；启动器 24 项通过。
- 独立 Python 3.12 与官方 SDK：M7 53 项全部通过，包括严格空间集合校验的合成测试。合成坐标不代表真实文献位置。
- 两份真实文献重放 M7：2 个 HR、1 个 Dataset，保留 37 条图片关联、34 条参考文本声明和 2 个 OCR profile。
- 官方 SDK 能读取真实导出，关键元数据与对应关系保留。
- 真实演示输入缺少坐标/区域，因此严格空间校验明确报缺少 Area，不能据此声称已地图导入。服务器端导入也没有执行。

仍需确认的对接信息：团队最终 schema 与稳定 ID 方案、目标 Atlas 实例和团队权限、地理区域选择与证据、IIIF source 登记和查看器关联、平台端导入结果。这些信息尚未在当前文件中提供。

命令、字段对照、输出目录与验证方法详见 [Module 7 Time Atlas 使用说明](../../../Code_git/Module_7/TIME_ATLAS.md)。
