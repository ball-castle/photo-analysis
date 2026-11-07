# 实验一交付与质量检查

## 完成状态

- `TEMPLATE_PRESERVATION_PASS`
- `EXPERIMENT_VERIFIED_PASS`
- 按指导书第 4–5 页正式任务 **1、3、4** 完成；未补造任务 2。
- 已提交原始 `.doc` 母版副本、PDF、可复现 Python 项目、结果图和指标数据。
- 未填写姓名、班级、日期、实验室、成绩或教师签名等未提供信息。
- 未发现未解决阻塞。

## 可复现实现

- 运行环境：Windows、Python 3.9.7、NumPy 2.0.2、Pillow 11.2.1、Matplotlib 3.9.4、scikit-image 0.24.0（仅 PSNR/SSIM）、pytest 8.4.2；随机种子为 `20261008`。
- 输入为 Unsplash 摄影师发布的两张真实人像，来源和许可链接记录在 `data/source/SOURCES.md`。直方图图像为 3000×3000 暗调皱纹人像；雀斑人像为 3000×2000，中心裁方后按比例缩放。处理输入均为 512×512 灰度图；未使用生成图像。
- `dip_lab/` 中独立实现直方图统计、CDF 均衡化和规定化、Roberts/Sobel/Prewitt/Laplacian、均值/中值/高斯、双边、引导及 NLM。核心算法使用 NumPy；Pillow 用于图像 I/O 与预处理。没有调用 OpenCV、SciPy 或 scikit-image 的滤波实现；`skimage.metrics` 只用于 PSNR/SSIM。
- NLM 对给定搜索窗遍历每个位移，以矩阵化平移和积分图补丁均方差计算，避免逐像素 Python 循环；更大的搜索窗仍显著增加真实运行时间。
- MATLAB R2023b Image Processing Toolbox 的 `histeq` 已实际运行作对照。该版本没有 `imhisteq` 函数；同一输入与手写实现的 MAE 为 **29.385**，最大绝对差为 **49**。
- 测试命令 `python -W error -m pytest tests -q`：**16 passed**。测试覆盖常值图、小图、边界、零噪声和指标函数。实际实验入口为 `python run_experiment.py --seed 20261008`；运行环境、图像摘要和结果统计保存在 `results/run_metadata.json`。

## 真实结果摘要

暗调人像原图均值为 **42.14**、标准差 **48.98**、P99 为 **180**。均衡化后均值 **103.25**、标准差 **82.54**、P99 **252**，暗部层次展开但高光更亮；双峰规定化后均值 **125.02**、标准差 **59.10**、P1–P99 为 **61–212**，灰度更集中。对应统计表与图见 `results/histogram_statistics.csv`、`results/histogram_comparison.png`。

下表为同一张 512×512 雀斑人像加入固定种子混合噪声后，各方法的一次实测结果。PSNR/SSIM 的参考图是加噪前的原始像素图，不是无瑕疵皮肤真值。时间受运行环境和负载影响，不能视为通用基准。

| 方法 | 实测参数 | 时间（秒） | PSNR（dB） | SSIM | 理论复杂度 |
|---|---|---:|---:|---:|---|
| 均值 | 5×5 | 0.0087 | 30.497 | 0.7671 | O(N)，积分图盒均值 |
| 中值 | 5×5 | 0.0855 | 32.494 | 0.8502 | O(Nk²)，邻域选择 |
| 高斯 | 7×7，σ=1.6 | 0.0103 | 31.017 | 0.8004 | O(Nk)，可分离卷积 |
| 双边 | r=3，σs=2，σr=40 | 0.2569 | 21.309 | 0.5881 | O(Nk²) |
| 引导 | r=3，ε=1600 | 0.0354 | 26.298 | 0.6404 | O(N)，积分图盒均值 |
| NLM | patch=5×5，search=7×7，h=30 | 0.4930 | 26.730 | 0.7006 | O(Ns²)，搜索位移 |

具体结果和参数敏感性数据见 `results/six_filter_comparison.csv`、`results/classical_sensitivity.csv`、`results/advanced_sensitivity.csv`。NLM 在 h=22 时搜索窗从 5×5 扩至 11×11，单次实测时间从 **0.261 s** 增至 **1.425 s**。人脸平滑实验只有带真实雀斑、纹理的照片，没有无瑕疵参考图，因此该实验只提供视觉对比，不报告 PSNR/SSIM。

## 模板保真与文档检查

- 使用用户提供的 `实验报告模板.doc` 作为母版，在副本内通过 Microsoft Word COM 定点填写；不可改动的备份为 `template_audit/实验报告模板_原始备份.doc`。原始文件与备份 SHA-256 相同：`1C550BABA970EC5E25CF625F777AEDAD6993B56F34EF72E4BE4BD53EC2EC68C0`。
- 最终 Word 文件为 OLE `.doc`（签名 `D0CF11E0A1B11AE1`），没有转换为 `.docx`。原始页设置为 A4（595.3×841.9 pt），页边距上/下/左/右为 62.3/72/90/90 pt；原模板表格保持 7 行、6 列、22 个单元格及原行高 31.45、31.05、29.45、29.45、130.15、353.40、598.95 pt。单元格宽度、字号、粗体和行距通过 `template_audit/verify_final_template.ps1` 与冻结基线核对通过。
- 原始学校标题、栏位标签、表格边界、第二页备注及“写不完时可另附稿纸”提示均保留；成绩、签名和个人信息栏为空。最终首页和第二页已与基线页面图对照检查，原表格版面未挤压或重排。
- 最终 PDF 为 **24 页 A4**：原模板 2 页，附页 22 页，包含实验原理、实测图表与分析以及实际核心算法源码。所有页面均渲染到 `final_report_render_v2/` 并逐页检查；最后修订的参数分析、指标公式、首页字体设置和代码分页也已复查，没有空白附页、裁切或图像拉伸。
- 最终结构审计数据保存在 `template_audit/final_template_verification.json`；Word 生成与 PDF 导出脚本为 `build_report.ps1`、`export_report_pdf.ps1`。

## 交付文件与复跑命令

- `实验一_图像增强的空域方法实现_实验报告.doc`
- `实验一_图像增强的空域方法实现_实验报告.pdf`
- `dip_lab/`、`tests/`、`run_experiment.py`、`requirements.txt`、`README.md`
- `data/source/`、`data/processed/`、`results/`

在 PowerShell 中进入 `output` 后执行：

```powershell
python -m pip install -r requirements.txt
python -W error -m pytest tests -q
python run_experiment.py --seed 20261008
```

重新生成 `.doc` 和 PDF 需要 Windows Microsoft Word COM：

```powershell
.\build_report.ps1
.\export_report_pdf.ps1
.\template_audit\verify_final_template.ps1
```
