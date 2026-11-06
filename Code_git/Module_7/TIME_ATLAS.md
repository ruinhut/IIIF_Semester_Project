# Time Atlas 导出与团队 schema 核对

本功能是 Module 7 的可选导出，保留原有 Arsha/OCR 输出，不增加第九个流水线模块，也不上传或公开任何资源。

## 核对结果

教师文件第 58–60 页要求：采集记录进入公共模式，并供内容提取和 Time Atlas 使用。第 46–47 页说明 Kaile 的 canonical record 工作，核心包括稳定标识符、带精度的日期、地点、语言、版权和来源，但没有给出可执行的 JSON Schema。

仓库现有 `provisional-0.1` 是我们自己的临时交换格式；`schemas/record-0.1.schema.json` 中的 `example.org` 不是 Atlas 官方模式地址。本地未找到 Kaile/Ziyi 发布的正式团队规范，因此不能声称已通过团队 schema 验收。

本次检查了 EPFL Time Machine 的真实实现：

- [官方数据模型](https://epfl-timemachine.github.io/time-atlas-python/data_model.html)
- [官方文件序列化与校验说明](https://epfl-timemachine.github.io/time-atlas-python/api/timeatlas.html)
- [官方源码固定版本](https://github.com/epfl-timemachine/time-atlas-python/tree/2c7d59e03298bd5eec31faec74c7530254e026fa)

目标是 `time-atlas-python 0.3.0`，提交 `2c7d59e03298bd5eec31faec74c7530254e026fa`，检查日期 2026-11-06。它要求 Python 3.12；普通流水线和我们的 JSON 导出仍可使用原来的 Python 3.10 环境。

## 输入如何对应

| 当前输入 | Atlas 导出 | 保留原则 |
|---|---|---|
| 一次采集的数据集合 | `Dataset` | 配置名称、slug、版本，生成 UUID v5 |
| 一条 `common_records` | 文献级 `HistoricalRecord` | 不是 Arsha 已经提取出的历史事件 |
| 原 `record_id` 和 Manifest URL | 稳定 HR UUID + `record_links.jsonl` | 不替换现有 OCR 关联键；UUID 由固定命名空间、dataset slug、Manifest URL 决定 |
| `object.dates` | `start_time` / `end_time` | 年份展开为整年区间，所有原始日期、精度和 approximate 保留 |
| `object.places` | HR 元数据 | 地名文本不会自动变成坐标；馆藏所在地不冒充历史事件所在地 |
| `rights` | HR 元数据及 `rights_attribution` | unknown/restricted 继续保留研究使用；公开和商业限制不变 |
| `source` | HR 的来源、提供机构和完整原始记录 | 外部 URL 不冒充 Atlas 内部 source UUID |
| `common_media` | HR 的 `metadata.media` | 原图地址、Image API 服务、resource_id、Canvas 均保留 |
| `institution_reference_texts` | HR 的同名元数据数组 | 保留图片—Canvas—参考文本对应关系；声明不等于已下载或人工校正真值 |
| `ocr_document_profiles` | `staging/ocr_document_profiles.jsonl` | 完整保留；继续供 OCR 下游使用 |

默认一份 Manifest 对应一条文献级 HR。更细的页面、段落、人物或事件记录属于后续提取结果，不能用采集元数据代替。

## 一条命令启用

在项目根目录运行已有流水线命令时，加入 `--atlas-export`：

```powershell
python pipeline.py --modules 1-7 --institution "Ecole Polytechnique Fédérale de Lausanne (EPFL)" --max-manifests 3 --atlas-export
```

如需同时下载，使用原来的 `--modules 1-8` 和下载参数即可；Atlas 输出不影响 M8 的参考文本分类。首次安装仍使用 `python pipeline.py --setup`。

查看输出：终端打印的 run directory 下，`module_7/output/` 是现有 OCR 交付；`atlas/` 是新增 Atlas 导出。

自定义数据集身份时复制 `profiles/time-atlas-0.3.json` 后使用：

```powershell
python pipeline.py --modules 1-7 --institution "INSTITUTION_NAME" --atlas-profile "PATH_TO_YOUR_PROFILE.json"
```

`--atlas-profile` 自动启用导出。固定 `namespace_url` 和 `dataset_slug` 可保持 UUID 稳定；不要每次更换。

## 不重新采集，直接转换现有 M7 文件

把两个示例路径换成真实路径，输出目录必须是新的或空的：

```powershell
& .\Code_git\.venv\Scripts\python.exe -m iiif_common_exporter atlas --input-directory "PATH_TO_EXISTING_RUN\module_7\output" --output-directory "PATH_TO_NEW_ATLAS_OUTPUT"
```

该命令没有网络请求，也不运行 M1–6/M8。原来的输入文件不修改。如果同一个 run 已生成过 `atlas/`，再次转换请用这个命令选择新的输出目录，防止旧导入文件混入新结果。

## 输出文件

```text
atlas/
|-- rde/
|   |-- dataset.json
|   |-- historical_records.json
|   |-- observations.json         # 只有明确坐标证据时才生成
|   |-- areas.json                # 只有可建立真实范围时才生成
|   +-- collection.jsonl          # 每行一个官方格式 envelope
|-- staging/
|   |-- records.jsonl             # 全部原始 common records、图片和参考文本
|   +-- ocr_document_profiles.jsonl
|-- record_links.jsonl            # 原 record_id -> Atlas UUID
|-- record_readiness.jsonl        # 逐文献缺项/导出状态
|-- atlas_export_report.json      # 总量、空间索引及未完成事项
|-- profile_used.json
|-- files.json                   # 文件清单；校验和不是新资源准入白名单
+-- log/Atlas_电脑时间_log.txt
```

`dataset.json` 等仅在对应实体存在时生成。日期缺失/不支持/冲突的记录完整进入 staging，不伪造年份以通过模型。所有日期都不可表示时，RDE 包为空，研究数据仍在。

包使用官方 envelope 字段 `name`、`type_in_file`、`creation_time`、`related_dataset_slugs`、`rde_objects`。本项目新增的 `time-atlas-rde-0.3.schema.json` 是依据源码编写的本地校验子集，**不是**官方或 Kaile 签发的完整 schema。

## 日期、地点与空间索引

目标 SDK 的 HistoricalRecord 和 Dataset 要求时间范围。当前只把已有的公元 1–9999 年有效区间转换成整年 UTC 边界，表示精度没有提升。兼容且重叠的日期选择最窄的原有区间，原始声明全部保留；不相交的区间进入待明确状态，不擅自取交集或任选一个。BCE、未知年份和其他不可表示日期留在 staging。

严格集合校验还要求 Dataset 关联 Area。仅有地名或可下载图片不满足这个条件。默认不会地理编码，不会用全球范围、学校或图书馆坐标凑数。

可选地，在 profile 的 `spatial_annotations_jsonl` 指定已有的、带证据的坐标文件（相对路径按 profile 所在目录解析）。每行格式：

```json
{"annotation_id":"place-1","record_id":"YOUR_RECORD_ID","geometry":{"type":"Point","coordinates":[6.57,46.52]},"relationship":"YOUR_EXPLICIT_LOCATION_RELATION","source_url":"https://YOUR_SOURCE/evidence","evidence":"SOURCE_SUPPORTING_THIS_COORDINATE_AND_RELATION"}
```

上面的坐标只是格式示例，不能用于给真实文献定位。应使用机构明确提供或下游确认的 WGS84 坐标，顺序为经度、纬度，并说明地点与文献的关系。只有成功导出的 HR 才生成关联 Observation；其真实点范围可生成 Area。坐标证据原样保留在 HR 元数据中。

若平台管理员已提供正确的 Area UUID，可在 `external_area_ids` 中列出。导出不会联网确认它是否存在；报告会标出仍需目标服务器核验，不能把离线通过当作可上线。

`Dataset.sources` 暂为空，因为尚未向目标 Atlas 注册 IIIF source 对象；所有原始 Manifest/图片/Canvas URL 已在 HR 元数据里保留。源对象注册和界面原生 IIIF 查看器接线仍需按具体部署确认，不能只填一个随机 UUID。

## 官方 SDK 验证（可选独立环境）

保留原流水线环境，另外使用 Python 3.12：

```powershell
py -3.12 -m venv Code_git/Module_7/.venv
& .\Code_git\Module_7\.venv\Scripts\python.exe -m pip install -r Code_git/Module_7/requirements-atlas-validation.txt
& .\Code_git\Module_7\.venv\Scripts\python.exe Code_git/Pipeline_Runner/tools/validate_atlas_bundle.py --bundle "PATH_TO_ATLAS_OUTPUT" --output "PATH_TO_VALIDATION_REPORT.json"
```

缺少空间区域时，严格校验退出码为 2，并写明原因。加 `--allow-staging` 可用作只检查可读取暂存包的诊断，但报告的 `strict_collection_valid` 仍为 false。脚本还检查 JSONL 包和分类型 JSON 是否相同，以及 SDK 读取后关键字段、图片和文本元数据是否保留。

这不执行服务器上传。正式部署还需团队最终字段规范、目标实例、相应 team/token、有效区域和来源登记，以及平台端导入验证；公开发布必须另行遵守每条记录的权限。

## 2026-11-06 的实际验证

- 原 Python 3.10：Module 7 **51 passed、2 个 SDK 专项跳过**；Pipeline Runner **24 passed**。
- 独立 Python 3.12 + 固定官方 SDK：Module 7 **53 passed**，其中 Atlas 专项 23 项。包括完整且带合成坐标证据的测试集合严格通过；合成测试坐标不当作真实文献的地理信息。
- 复用用户当天的两份真实文献，以启动器运行 M7 + Atlas：2 个文献、37 条图片关联、34 条参考文本声明、2 个 OCR profiles，原 OCR 输出正常。
- 官方 SDK 读取真实导出并保留关键内容：成功，读取 1 Dataset + 2 HR。
- 真实包严格空间校验：**未通过**，因为这两份输入没有坐标/区域；已如实保留，没有编造。未上传、未测试真实服务器导入。

本地结果：`Code_git/Pipeline_Runner/data/atlas_validation_20261106/integrated_run/atlas/`；SDK 报告在上级 `atlas_validation_20261106/integrated_sdk_validation.json`。运行数据不提交 Git，保留可复现程序和验证摘要。
