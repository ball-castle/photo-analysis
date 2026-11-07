# ROUND 2 模板与内容审计

## 结论

**ROUND2_TEMPLATE_AND_CONTENT_PASS**

ROUND 2 在原始 Word 模板上完成了定点填写和附页修订。ROUND 1 文件仍保存在 output 根目录；本轮报告和审计资料位于 output/round2_final。

## 模板保留

- 母版为 Downloads/实验报告模板.doc，ROUND 2 构建脚本直接复制该 .doc 后进行内容编辑，没有重建模板。母版 SHA256：1C550BABA970EC5E25CF625F777AEDAD6993B56F34EF72E4BE4BD53EC2EC68C0；冻结基线与原件哈希一致。
- Word COM 结构核验通过，状态为 TEMPLATE_PRESERVATION_PASS，无失败项。最终 .doc 为 OLE/Word 97–2003 格式，23 页。
- 原有页面为 A4（595.30 × 841.90 pt），页边距上/下/左/右为 62.30/72.00/90.00/90.00 pt；单节结构保持。
- 原表格仍为 7 行、6 列、22 个单元格。各行固定高度保持 31.45、31.05、29.45、29.45、130.15、353.40、598.95 pt；单元格宽度、字体、字号、粗体和行距与基线核验一致。
- 原学校抬头、栏目标签、课程名称位置、表格线和边界、原有提示、第二页底部备注及结果栏内的“写不完时，可另附稿纸”均保留。班级“数学jd2401”和姓名“蔡斌”按用户提供的信息填入原有栏位；日期、实验室、成绩和老师签名保持空白。
- 第一页目的及内容、原理步骤及核心代码栏，以及第二页结果栏均在原固定单元格中填写；未缩小模板字号、改行距或调整行高。
- Blank 原模板、ROUND 1、ROUND 2 的前两页均以渲染图对照检查。抬头、课程栏、网格和固定备注位置保持；ROUND 2 前两页的内容明显更完整。

模板核验记录：verification_results/template_verification.json

## 前两页内容

第一页列出直方图计算、均衡化与规定化、Roberts/Sobel/Prewitt/Laplacian、三类噪声、六种滤波和评价指标；同页还给出 CDF/均衡化公式、规定化映射规则、Laplacian 正负响应处理、滤波原理、实际步骤和源码片段。

第二页写入实测亮度统计、边缘算子观察、三类噪声参数、滤波效果特点、六种滤波的 PSNR/SSIM/时间、最佳指标的适用范围、局限和实验总结。美容平滑仍只作视觉分析，不报告没有真实参考图的 PSNR/SSIM。

## 四项数值与叙述核对

### A. 中值 5×5 时间

原始结果表中，窗口敏感性调用为 0.0905147 s，报告显示 0.0905 s；六种滤波综合调用为 0.0854655 s，表格按三位小数显示 0.085 s，正文显示 0.0855 s。两次调用位于同一次 run_experiment.py 主程序运行中，使用相同混合噪声图和滤波参数，但由两个分析函数分别单次计时；不是不同噪声批次，也不是笔误。报告第 2、8、10 页已按各自表格作用说明。

### B. 双峰目标

histogram.py 函数默认值确为 sigma=12、weight1=0.5；run_experiment.py 实际调用显式传入 peak1=65、peak2=185、sigma=13、weight1=0.52，故第二峰权重为 0.48。报告第 1、3 页写明实际调用值和默认值差异。

### C. MATLAB histeq

R2023b 实际对同一 512×512 uint8 输入运行 MATLAB histeq(I) 与 histeq(I,256)。与 Python 输出比较：默认档 MAE 29.384757996、最大差 49；256 档 MAE 29.414672852、最大差 51。两 MATLAB 输出之间 MAE 1.183578491；Python 的 CDF_min 映射可精确重建，MAE 为 0；MATLAB 256 档输出与直接全 CDF 映射之间 MAE 为 1.376071930。换用 256 档并未消除约 29.4 的主差异；测试确认输入一致，主要差别是 MATLAB 近似匹配平坦目标直方图的单调映射与 Python 的 CDF_min 减除、线性重标定映射不同，而不是未经验证地归因于默认 64 档量化。R2023b 官方说明： [MathWorks histeq](https://www.mathworks.com/help/releases/R2023b/images/ref/histeq.html)。

实际运行数据、代码和对比图：verification_results/histeq_method_comparison.csv、verification_results/histeq_bin_comparison.txt、verification_results/compare_histeq_bins.m、verification_results/matlab_histeq_bins_comparison.png。

### D. 最优指标的范围

- 窗口敏感性组：中值 5×5 的 PSNR 最高，为 32.494 dB；中值 7×7 的 SSIM 最高，为 0.8661，PSNR 31.836 dB、时间 0.1582 s。
- 六种配置组：中值 5×5 在该组六个配置中 PSNR/SSIM 最高，为 32.494 dB/0.8502；均值 5×5 最快，实测 0.0087222 s。
- 两组数据使用同一最终主程序运行中的不同单次计时调用；所有滤波指标均针对同一混合噪声输入，参考图为加噪前原图。报告没有把局部最优外推为通用结论。
- 参数敏感性和 NLM 搜索窗时间的结论均限定于本次单图及噪声参数。

## 算法与指标审计

人工逐项对照算法公式、源码和报告描述：

- 灰度直方图按 0–255 计数；均衡化以第一个非零 CDF 作 CDF_min；规定化以首个不小于源 CDF 的目标灰度映射。
- 相关运算、均值/高斯/中值、Roberts/Sobel/Prewitt 和 Laplacian 计算与报告公式一致。边界使用 reflect，单像素维度退回 symmetric；数组内部运算使用浮点，输出显示时才舍入/裁剪。
- Laplacian 使用中心为正的四邻域核；带符号响应对应 I+L 锐化。绝对值和线性拉伸作为响应显示，未冒充原图增强结果。
- 双边滤波空间/灰度权重、引导滤波局部线性系数、NLM 补丁均方距离和噪声偏差校正均与描述一致；NLM 遍历指定搜索位移，积分图盒均值计算补丁距离，输出按权重和归一化。
- 均值核经归一化；高斯一维核归一化后分离计算；引导滤波、均值和 NLM 所用盒均值通过积分图实现。
- 高斯与椒盐噪声由固定种子生成；混合噪声在单个种子生成器上依次抽取高斯值和椒盐掩码。R2 源码快照仅将 noise.py 中误称“独立 RNG 流”的 docstring 修正为“一个 seeded RNG 流”；算法计算与随机序列未变。
- PSNR 使用 data_range=255；SSIM 使用 data_range=255、单通道输入并要求最小边长至少 7。合成噪声恢复以加噪前原图作参考；没有无瑕疵真值的人脸平滑不计算这两个指标。
- 未发现需要改动计算逻辑的错误；报告审计期间没有修改参数或重写 Round 1 结果。为验证提交包，在独立解压目录用固定种子 20261008 实际运行了完整实验，并重新跑完 16 项测试。

测试输出：verification_results/pytest_round2.txt 和 verification_results/pytest_round2_snapshot.txt，均为 16 passed。

## PDF 与版式检查

- 最终 .doc 由 Word COM 导出 PDF。Word 与 PDF 页数均为 23，页面均为 A4。
- 最终 PDF 第 1–23 页均以 130 dpi 实际渲染并逐页目视检查；第 1–2 页另与原空白模板和 ROUND 1 对照。附页图表、正文和代码清晰，没有空白整页、遮挡、裁切、溢出或表格变形。
- 长源代码按原顺序连续跨页，页间续接处仍可读；每个核心模块均收录。
- PDF 文本/页框自动核验 9 项全部通过；Word 模板核验无失败项。

PDF 检查记录：verification_results/pdf_verification.json
Word 页面图：rendered_pages/page-01.png 至 rendered_pages/page-23.png

## 提交附件验证

- 按用户提供的信息，将班级“数学jd2401”和姓名“蔡斌”填入原表；学号“1024001338”用于附件命名。
- 提交 PDF 为 23 页 A4，大小约 1.25 MB。导出 PDF 文本并检查 23 页均有内容，课程报告标题、姓名、班级、第二页备注和实测指标均存在；个人信息更新后重渲染检查了前两页。
- 源代码 ZIP 约 16.3 MB，包含 70 个条目，解压根目录直接包含 README、run_experiment.py、requirements.txt、dip_lab、data、results 和 tests，无额外嵌套目录；压缩包低于作业页面 200 MB 限制。
- 已从 ZIP 解压到独立目录，在解压根目录运行 `python run_experiment.py --seed 20261008` 成功；在同一目录运行 `python -W error -m pytest tests -q`，16 项通过。
- 详细提交包检查记录：verification_results/submission_package_verification.json。

## 最终文件

- submission/第一次上机实验报告_数学jd2401_蔡斌_1024001338.pdf
- submission/第一次上机源代码_数学jd2401_蔡斌_1024001338.zip
- 实验一_图像增强的空域方法实现_最终实验报告.doc（Word 源报告）
- ROUND2_AUDIT.md
- ROUND2_CHANGELOG.md

提交用 PDF 与源代码 ZIP 分别另存于 output/round2_final/submission；报告正文其余内容与已审计版本相同。附件可直接下载后上传到课程页面。

