# 双古籍Demo演示步骤

更新：2026-11-06。主演示已换为两份古籍，不再使用此前的EPFL图片。

## 1. 这次演示什么

一条启动命令依次运行两组独立的M1–8全流程，每组处理一份已知Manifest、下载一张样例图，并保留自己的输入、输出与日志。

| 案例 | 文献 | 下载类别 | 实测图片 |
|---|---|---|---|
| with_reference_case | 巴伐利亚州立图书馆，1694年德文印刷品 Aquila Apocalyptica | with_reference | 1688×2216，带页面关联的机构hOCR与抽取纯文本 |
| without_reference_case | Fragmentarium F-u3vo，Tübingen KH 5184手稿残片，来源日期1275–1325年 | without_reference | 6801×2999，本次没有页面关联参考文本 |

原来的download-example在整个输入里只下载一张，不会自动为每种类别各选一张。新工具是演示包装器：调用原有启动器两次，M8每次仍使用download-example。没有修改八个模块的生产行为，也不会下载整本古籍。

开场可说：

> This demonstration runs the complete pipeline for two historical documents: a 1694 printed book with institutional OCR, and a medieval manuscript fragment without a declared page-linked reference text.

两份输入都是已知Manifest。这演示全流程交接与下载分类；不是从未知机构首页自动发现资源，也没有调用LLM。

## 2. 打开PowerShell并初始化目录

以下代码在同一个终端执行；不要复制终端提示符。

~~~powershell
$ProjectRoot = 'E:\exchange-epfl\Semester_Project'
Set-Location -LiteralPath $ProjectRoot
$DemoRoot = Join-Path -Path $ProjectRoot -ChildPath ('Code_git\Pipeline_Runner\data\runs\paired_demo_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
~~~

启动器位于Semester_Project根目录，项目环境位于Code_git\.venv；现有环境可直接使用，不需重新激活或安装。

## 3. 录屏时执行这一条采集命令

~~~powershell
python Code_git/Pipeline_Runner/tools/run_presentation_demo.py --output-root "$DemoRoot"
~~~

包装器依次执行两个案例；每个案例都显示Module 1/8到Module 8/8。八模块各自保存输出和日志。

实际采用的参数为：八模块全跑、每案例最多一份Manifest、M8只下载一个样例、M4重新获取Manifest、关闭LLM。带文本案例另外要求成功取得页面关联文本。

可说：

> One command runs two independent eight-module cases. Each case downloads one image, and the reference-bearing case must also retrieve its linked institutional text.

网络等待可在视频中加速并标注。不要把带文本案例当作没有文本的案例再次使用，也不要将机构OCR说成人工校正答案。

## 4. 确认成功并查看两类结果

~~~powershell
$DemoResult = Get-Content -LiteralPath (Join-Path $DemoRoot 'demo_summary.json') -Encoding UTF8 | ConvertFrom-Json
$DemoResult.cases | Select-Object category,modules_completed,downloaded_images,reference_texts
Invoke-Item -LiteralPath $DemoRoot
~~~

成功结果应为两行：每行modules_completed为8、downloaded_images为1；with_reference的reference_texts至少为1，without_reference为0。

输出结构：

~~~text
本次DemoRoot/
  demo_summary.json
  with_reference_case/
    module_1/ ... module_8/
    module_8/output/example/with_reference/<文献>/<页面>/
      image.jpg
      common_record.json
      common_media.json
      ocr_document_profile.json
      institution_reference_texts.json
      institution_reference_001.hocr.html
      institution_reference_001.txt
  without_reference_case/
    module_1/ ... module_8/
    module_8/output/example/without_reference/<文献>/<页面>/
      image.jpg
      common_record.json
      common_media.json
      ocr_document_profile.json
~~~

两个类别在各自案例的M8输出中，不是一个共享M8运行结果；父目录汇总两个案例。

## 5. 先展示带文本的1694年印刷品

~~~powershell
$WithReference = $DemoResult.cases | Where-Object { $_.category -eq 'with_reference' }
Invoke-Item -LiteralPath $WithReference.image_path
Invoke-Item -LiteralPath $WithReference.bundle_directory
~~~

展示图像中的古老印刷字体、文献年份；然后打开抽取纯文本、原始hOCR和institution_reference_texts.json。指出Canvas、record_id和resource_id连接同一页面。

> This 1694 printed page has institutional hOCR linked to the same Canvas and image resource. The pipeline downloads the image, original hOCR, extracted text and the associated JSON records.

机构OCR准确率未经人工核验；文件齐全与页面关联成功不等于文字完全正确。

## 6. 再展示不带文本的中世纪手稿

~~~powershell
$WithoutReference = $DemoResult.cases | Where-Object { $_.category -eq 'without_reference' }
Invoke-Item -LiteralPath $WithoutReference.image_path
Invoke-Item -LiteralPath $WithoutReference.bundle_directory
~~~

展示羊皮纸残片、手写文字和三份基础JSON。没有页面关联参考文本时，输出仍完整保留图片、文献记录和OCR画像。

> This manuscript fragment is dated to 1275–1325 in the source metadata. No page-linked institutional reference text was declared in this example, so its downloaded image and metadata are stored under without_reference.

## 7. 三份JSON各解释一句

| 文件 | 英文解释 |
|---|---|
| common_record.json | The document record preserves its description, provenance and rights information. |
| common_media.json | The media record identifies this image, its Canvas and its parent document. |
| ocr_document_profile.json | The OCR profile records available document characteristics for downstream OCR selection. |

三份JSON的record_id一致；页面图片和参考文本通过resource_id及Canvas关联。M8文件夹中的institution_reference_texts.json记录实际取得的文本及下载证据。

## 8. 结束演示

> The pipeline supports both reference-bearing and reference-free historical documents, keeping their images, metadata and available institutional texts explicitly linked.

## 已完成实测

2026-11-06已在新目录真实执行两个案例，结果为：两组M1–8全部完成、两张新下载图片、六份通过schema及ID检查的基础JSON，以及一份页面关联hOCR、纯文本和参考文本JSON。两张图片均实际解码检查通过，两组图片失败、文本下载失败均为0。

实测目录：
Code_git/Pipeline_Runner/data/runs/paired_heritage_demo_20261106_135548_650945/

本次BSB样例是Canvas 1，不是此前历史测试的Canvas 10；不要混用旧样例的尺寸或词数。前面的100来源M1–7实验依然没有运行M8，这次两例是独立的下载演示。

录制时再次运行命令会在新的时间戳目录采集。若失败，先查看父目录的案例console日志和子目录module_N/log；旧目录不会被新演示覆盖。
