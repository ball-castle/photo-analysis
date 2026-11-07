# 匀速直线运动 PSF 作业

作者：蔡斌，数学jd2401，1024001338。定稿日期：2026-11-05。

五页 LaTeX PDF 包含模型与离散规则、AI 初版代码、修改分析、最终函数、测试结果，以及三张实际 AI 问答的摘录排版截图。

## 提交文件

`提交/运动模糊PSF报告_数学jd2401_蔡斌_1024001338.pdf` 是定稿 PDF。
`提交/运动模糊PSF作业_源码与记录.zip` 包含报告、LaTeX 源码、MATLAB 函数、验证脚本、问答记录与配图。
压缩包内的定稿 PDF 置于根目录，其余文件保持编译所需的目录结构。

## 重新编译

安装含 `ctex` 的 TeX Live 后，在本文件所在目录运行：

```powershell
.\compile_report.ps1
```

生成文件为 `output/pdf/运动模糊PSF复现报告.pdf`。也可运行 `python build_report.py`。

## 运行验证

在 MATLAB R2023b 中将当前目录切换到本文件所在目录，运行：

```matlab
capture_results
compare_ai_initial
compare_overlap
audit_motion_psf
audit_test_sensitivity
```

需要 Image Processing Toolbox 中的 `fspecial` 作为测试参照。最终函数 `motion_psf.m` 自身不调用该内置函数；离散构造的出处见报告参考资料。

## 文件说明

- `motion_psf_ai.m`：本次 AI 第一轮原始代码，用于错误分析。
- `motion_psf_overlap.m`：修正参数化后的像素方格交长实现。
- `motion_psf.m`：与 R2023b 对照的最终函数。
- `test_motion_psf.m`：104 组常规参数及 2 种默认调用。
- `audit_motion_psf.m`：385 组边界参数、1000 组随机参数及核的基本性质检查。CSV 用 17 位有效数字保存参数并验证回读一致性。
- `audit_test_sensitivity.m`：故意改变半长、上下翻转、浮点归一化和三角函数求值方式，检查测试能否识别错误。
- `results/`：实际测试日志、参数明细和表格片段。
- `交互记录/`：实际问答 JSON、摘录内容、HTML 页面及其截图。
- `AI交互过程.md`：本次问答及对 AI 建议的核查记录。
- `对抗性审计记录.txt`：内容、表述和排版的终审记录。

现有 PNG 已足够重编译报告。重新生成问答截图需 Python、Playwright 和 Microsoft Edge，运行 `python -X utf8 render_dialogue.py`。
