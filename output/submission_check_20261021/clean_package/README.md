# 第一次上机实验：图像增强的空域方法

这是自包含的实验包，包含 Python 源码、源图像、512×512 输入图像、实验结果图和 CSV 数据。

## 在解压目录运行

1. 解压本 ZIP。用 PowerShell 或终端进入解压后包含 `run_experiment.py` 和 `requirements.txt` 的目录。
2. 安装依赖：

   `python -m pip install -r requirements.txt`

3. 运行完整实验：

   `python run_experiment.py --seed 20261008`

脚本以自身所在目录为根路径，可从该目录直接运行；结果写回 `data/processed/` 和 `results/`。

## 环境与验证

使用 Python 3.9.7 编写，依赖版本锁定在 `requirements.txt`。可运行 `python -m pytest tests -q` 执行单元测试。核心增强和滤波算法使用 NumPy 实现，scikit-image 仅用于 PSNR/SSIM 指标计算。MATLAB 对照脚本为可选项，不影响 Python 实验运行。

## 目录

- `dip_lab/`：直方图、空域滤波、边缘、噪声及指标实现。
- `data/source/`：实验源图像及其来源说明。
- `data/processed/`：实验灰度输入图像。
- `results/`：结果图、指标 CSV、敏感性分析和运行记录。
- `tests/`：算法和指标单元测试。
- `run_experiment.py`：完整实验入口。
