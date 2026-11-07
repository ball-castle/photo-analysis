# 数字图像处理实验一：图像增强的空域方法实现

## 运行环境

本项目在 Windows 10、Python 3.9.7 环境中运行。依赖版本见 `requirements.txt`。核心直方图、边缘算子、均值/中值/高斯、双边、引导和 NLM 算法均由 `dip_lab/` 中的 NumPy 代码实现。scikit-image 只用于 PSNR/SSIM 指标，不调用其滤波函数。

## 运行

在 PowerShell 中进入 `output` 目录：

```powershell
python -m pip install -r requirements.txt
python -m pytest tests -q
python run_experiment.py --seed 20261008
```

实验使用 512×512 灰度图，固定随机种子 20261008。图像、CSV 指标、运行时、参数敏感性图和环境记录写入 `data/processed/` 与 `results/`。

## 算法边界

- Pillow 只读取、裁剪、缩放和保存图像；尺寸变换保持纵横比，先中心裁为正方形。
- 核心滤波没有调用 OpenCV、SciPy 或 scikit-image 的滤波实现。
- 直方图统计使用 `numpy.bincount`；均值、加权均值、中值、高斯和四种边缘算子均在本项目代码中计算。
- 双边滤波对局部空间权重与灰度权重逐位移做 NumPy 矩阵运算；引导滤波用积分图盒式均值；NLM 对每个搜索位移矩阵化计算补丁距离，并用积分图加速，不遍历像素 Python 循环。
- 人像美容平滑没有无瑕疵真值，故不计算或宣称该任务的 PSNR/SSIM。

## MATLAB 对照

本环境检测到 MATLAB R2023b 与 Image Processing Toolbox。该版本实际提供的内置均衡函数名为 `histeq`，未提供名为 `imhisteq` 的函数；对照脚本 `matlab_compare_histeq.m` 只用于比较，不参与 Python 核心实现。可在 `output` 目录中运行：

```powershell
matlab -batch "run('matlab_compare_histeq.m')"
python run_experiment.py --seed 20261008
```

## 目录

- `dip_lab/`：独立可调用算法函数。
- `tests/`：常值图、小图、边界、零噪声、固定种子和指标测试。
- `data/source/`：输入照片及来源/许可记录。
- `data/processed/`：512×512 灰度实验输入。
- `results/`：实验图、实际运行时间、PSNR/SSIM 与参数敏感性数据。
- `run_experiment.py`：唯一实验运行入口。
- `REPORT_QA.md`：逐项完成状态与模板保真结论。
