# IIIF 模块化流水线统一运行器

运行器按照编号依次执行模块 1–7，记录每条命令、标准输出、错误输出和返回码；任一模块失败时立即停止。每个模块仍可独立运行，并保留自己的配置、输出和日志。

完整运行：

```powershell
cd Code_git/Pipeline_Runner
python -m pip install -e .
python -m iiif_pipeline_runner --config pipeline.example.json
```

完整运行会在模块 1–4 访问网络，耗时取决于机构可用性和发现的 Manifest 数量。已有上游结果时可从中间恢复：

```powershell
python -m iiif_pipeline_runner --config pipeline.example.json --from-module 3 --to-module 7
```

缓存样本的端到端检查使用：

```powershell
python -m iiif_pipeline_runner --config pipeline.smoke.json
```

总日志保存在 `data/log/Pipeline_<本机时间>_log.json`。测试命令为 `python -m pytest -q`。
受限的真实模块 1–7 联调使用：

```powershell
python -m iiif_pipeline_runner --config pipeline.fragmentarium-smoke.json
```

该配置只选择一个已知机构，最多发现两个 Manifest，并把结果隔离保存在 `data/e2e_validation/`，不会启动大规模抓取。
