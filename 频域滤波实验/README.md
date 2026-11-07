# 实验二：图像增强的频域方法

项目实现了二维傅里叶变换、六种径向低通/高通滤波器、高频强调滤波，以及四幅课程图像的高斯陷波处理。运行入口使用固定随机种子生成高斯噪声，保存图表、指标和每项指标的参考图说明。

## 环境与运行

需要 Python 3.9.7 及 `requirements.txt` 中的 NumPy、Pillow 和 Matplotlib。在 PowerShell 中进入本目录后运行：

```powershell
python -m pip install -r requirements.txt
python -X utf8 run_experiment.py
```

频谱交互程序以 `data/source/16.jpg` 为例：

```powershell
python -X utf8 -m src.notch_editor --image data/source/16.jpg --output results/gui/16_filtered.png --d0 3
```

在频谱图左键点选一个亮峰，程序会自动加入其共轭峰；右键删除最近的一组。拖动 D0 滑块比较滤波结果，按“保存结果”后同时生成图像和参数 JSON。频率坐标按中心化 FFT 的整数 bin 表示，`(v,u)` 分别是行、列方向偏移。

## 结果说明

- `results/binary_fft_spectrum.png` 展示中心 16 行×4 列二值矩形的幅度谱、相位谱、移位和还原；直接 DFT 与 `numpy.fft.fft2` 的误差写入 `run_metadata.json`。
- `results/gaussian_lowpass_metrics.csv` 和 `gaussian_lowpass_grid.png` 是 `cameraman.tif` 加入 σ=20 高斯噪声后的 12 组低通结果；PSNR 参考加噪前的 `cameraman.tif`。
- `results/highpass_grid.png` 展示三类高通响应；每幅图按 1%–99% 百分位范围独立拉伸显示，`highpass_parameters.csv` 记录未拉伸响应的极值。高频强调参数为 Butterworth 阶数 2、D0=24、a=0.6、b=1.4；未裁剪浮点输出的 DC 分量和图像均值为原值的 60%，超出 `[0,255]` 的像素在保存为 8 位 PNG 时会被裁剪。
- `results/notch_filtered/` 保存四幅课程图像的陷波结果；峰坐标、半径与候选频谱峰分别记录在 CSV 中。
- 四张课程图没有配对的干净参考图。因此 `notch_psnr_sweep.csv` 用每张原图作为受控正弦噪声注入前的参考图，寻找这组新增调幅周期噪声的 D0；这些 PSNR 不代表四张原始噪声图的真实恢复分数。

## 重建报告

在安装了 Microsoft Word 的 Windows 环境中，从项目根目录运行：

```powershell
pwsh -NoProfile -File .\build_report.ps1
```

脚本按课程模板生成 DOCX。需要 PDF 时，在 Word 中打开生成的 DOCX，并使用“另存为”导出 PDF。

原始课程图像与实验说明保存在 `data/source/` 和 `reference/`。`提交/` 下提供最终 DOCX、PDF 和可复现源码与结果压缩包。
