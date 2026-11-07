$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$backup = Join-Path $root 'reference\实验报告模板_原始备份.doc'
$reportDirectory = Join-Path $root '提交'
$report = Join-Path $reportDirectory '实验二_图像增强的频域方法_实验报告.docx'
$results = Join-Path $root 'results'
if (-not (Test-Path -LiteralPath $backup)) { throw "Template backup is missing: $backup" }
if (-not (Test-Path -LiteralPath (Join-Path $results 'run_metadata.json'))) { throw 'Run the experiment first; results/run_metadata.json is missing.' }

New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$app.DisplayAlerts = 0
$doc = $null

function Set-CellText([object]$cell, [string]$text) {
    $cell.Range.Text = $text
}

function Add-Paragraph {
    param(
        [string]$Text,
        [double]$Size = 10.5,
        [bool]$Bold = $false,
        [int]$Alignment = 0,
        [string]$FontName = '宋体',
        [bool]$KeepWithNext = $false
    )
    $selection = $app.Selection
    $selection.EndKey(6) | Out-Null
    $selection.Font.Name = $FontName
    try { $selection.Font.NameFarEast = $FontName } catch {}
    $selection.Font.Size = $Size
    $selection.Font.Bold = $Bold
    $selection.ParagraphFormat.Alignment = $Alignment
    $selection.ParagraphFormat.LineSpacingRule = 0
    $selection.ParagraphFormat.SpaceAfter = 3
    $selection.ParagraphFormat.KeepWithNext = if ($KeepWithNext) { -1 } else { 0 }
    $selection.TypeText($Text)
    $selection.TypeParagraph()
}

function Add-PageBreak {
    $selection = $app.Selection
    $selection.EndKey(6) | Out-Null
    $selection.InsertBreak(7)
}

function Add-AppendixSection {
    $selection = $app.Selection
    $selection.EndKey(6) | Out-Null
    $selection.InsertBreak(2)

    $section = $doc.Sections.Item($doc.Sections.Count)
    $pageSetup = $section.PageSetup
    $pageSetup.TopMargin = 74.3
    $pageSetup.BottomMargin = 192.65
    $pageSetup.LeftMargin = 107.5
    $pageSetup.RightMargin = 72.8

    # The template form pages also receive a page-level frame so the title
    # above the table and the remark below it remain inside a box. Set this
    # section first because Word may copy its border settings to the next
    # section when the latter is created.
    $formBorders = $doc.Sections.Item(1).Borders
    $formBorders.Enable = -1
    $formBorders.DistanceFrom = 1
    $formBorders.DistanceFromTop = 24
    $formBorders.DistanceFromBottom = 24
    $formBorders.DistanceFromLeft = 24
    $formBorders.DistanceFromRight = 24
    foreach ($side in 1..4) {
        $border = $formBorders.Item($side)
        $border.LineStyle = 1
        $border.LineWidth = 4
        $border.Color = -16777216
    }

    # Keep the original form table unchanged and frame appendix pages using
    # the template's 450 x 598.95 pt results-box geometry. Enable first because
    # Word resets the distances to 24 pt when a border is enabled afterward.
    $borders = $section.Borders
    $borders.Enable = -1
    $borders.DistanceFrom = 0
    $borders.DistanceFromTop = 12
    $borders.DistanceFromBottom = 12
    $borders.DistanceFromLeft = 17.5
    $borders.DistanceFromRight = 17.5
    $borders.SurroundHeader = 0
    $borders.SurroundFooter = 0
    $borders.AlwaysInFront = 0
    foreach ($side in 1..4) {
        $border = $borders.Item($side)
        $border.LineStyle = 1
        $border.LineWidth = 4
        $border.Color = -16777216
    }
}

function Add-Figure {
    param([string]$Path, [string]$Caption, [double]$Width = 400)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Figure is missing: $Path" }
    Add-Paragraph -Text $Caption -Size 9 -Alignment 1 -KeepWithNext $true
    $selection = $app.Selection
    $selection.EndKey(6) | Out-Null
    $selection.ParagraphFormat.Alignment = 1
    $shape = $selection.InlineShapes.AddPicture($Path, $false, $true)
    $shape.LockAspectRatio = -1
    $shape.Width = $Width
    $selection.TypeParagraph()
}

function Add-WordTable {
    param(
        [System.Collections.Generic.List[object]]$Data,
        [double[]]$Widths,
        [double]$FontSize = 8.2
    )
    $selection = $app.Selection
    $selection.EndKey(6) | Out-Null
    $columnCount = ([object[]]$Data[0]).Count
    $table = $doc.Tables.Add($selection.Range, $Data.Count, $columnCount)
    $table.Borders.Enable = 1
    $table.AllowAutoFit = $false
    try { $table.AutoFitBehavior(0) } catch {}
    try { $table.PreferredWidth = 408 } catch {}
    for ($column = 1; $column -le $columnCount; $column++) {
        try { $table.Columns.Item($column).Width = $Widths[$column - 1] } catch {}
    }
    for ($row = 1; $row -le $Data.Count; $row++) {
        $values = [object[]]$Data[$row - 1]
        for ($column = 1; $column -le $columnCount; $column++) {
            $cell = $table.Cell($row, $column)
            $cell.Range.Text = [string]$values[$column - 1]
            $cell.Range.Font.Name = '宋体'
            try { $cell.Range.Font.NameFarEast = '宋体' } catch {}
            $cell.Range.Font.Size = $FontSize
            $cell.Range.ParagraphFormat.SpaceAfter = 0
            $cell.Range.ParagraphFormat.LineSpacingRule = 0
            $cell.VerticalAlignment = 1
            $cell.Range.ParagraphFormat.Alignment = 1
            if ($row -eq 1) { $cell.Range.Font.Bold = $true }
        }
    }
    $selection.EndKey(6) | Out-Null
    $selection.TypeParagraph()
}

function Add-CodeFile([string]$RelativePath, [string]$Heading, [bool]$StartNewPage = $false) {
    $sourcePath = Join-Path $root $RelativePath
    if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Source file is missing: $sourcePath" }
    if ($StartNewPage) { Add-PageBreak }
    Add-Paragraph -Text $Heading -Size 11 -Bold $true -KeepWithNext $true
    $code = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
    $code = $code -replace "`r?`n", "`r"
    $code = $code.TrimEnd([char]13)
    $selection = $app.Selection
    $selection.EndKey(6) | Out-Null
    $selection.Font.Name = 'Consolas'
    try { $selection.Font.NameFarEast = '宋体' } catch {}
    $selection.Font.Size = 7.2
    $selection.Font.Bold = $false
    $selection.ParagraphFormat.Alignment = 0
    $selection.ParagraphFormat.LineSpacingRule = 4
    $selection.ParagraphFormat.LineSpacing = 8.0
    $selection.ParagraphFormat.SpaceAfter = 0
    $selection.ParagraphFormat.KeepWithNext = 0
    $selection.TypeText($code)
    $selection.TypeParagraph()
}

function Fmt([string]$Value, [string]$Pattern = 'F3') {
    $number = [double]::Parse($Value, [System.Globalization.CultureInfo]::InvariantCulture)
    return $number.ToString($Pattern, [System.Globalization.CultureInfo]::InvariantCulture)
}

try {
    $doc = $app.Documents.Open($backup, $false, $false, $false)
    $doc.SaveAs2($report, 12)
    $doc = $app.ActiveDocument
    $templateTable = $doc.Tables.Item(1)

    # Fill only known student/course fields. Grade and teacher signature remain blank.
    $courseParagraph = $doc.Paragraphs.Item(3).Range
    $courseStart = $courseParagraph.Start + 8
    $courseRange = $doc.Range($courseStart, $courseStart + 6)
    $courseRange.Text = '数字图像处理'
    $courseRange.Font.Name = '宋体'
    try { $courseRange.Font.NameFarEast = '宋体' } catch {}
    $courseRange.Font.Size = 12
    $courseRange.Font.Underline = 0
    Set-CellText $templateTable.Cell(1, 2) '数学jd2401'
    Set-CellText $templateTable.Cell(1, 4) '2026.11.6'
    $dateCell = $templateTable.Cell(1, 4)
    $dateCell.Range.Font.Size = 10
    Set-CellText $templateTable.Cell(2, 2) '蔡斌'
    Set-CellText $templateTable.Cell(3, 2) '实验二 图像增强的频域方法'
    $titleCell = $templateTable.Cell(3, 2)
    try { $titleCell.Range.Font.NameFarEast = '宋体' } catch {}
    $titleCell.Range.Font.Name = 'Times New Roman'
    Set-CellText $templateTable.Cell(4, 2) 'Python 3.9.7、NumPy 2.0.2、Pillow 11.2.1、Matplotlib 3.9.4；MATLAB R2023b 样例图像'
    Set-CellText $templateTable.Cell(5, 2) '目的：掌握频域平滑、锐化和周期噪声陷波。内容：傅里叶频谱、六种径向滤波器、高频强调及四幅周期噪声图处理，详见附页。'
    Set-CellText $templateTable.Cell(6, 2) '实验公式、参数、运行结果、图表分析及 Python 核心源代码详见附页。'
    $resultCell = $templateTable.Cell(7, 2)
    Set-CellText $resultCell '滤波结果图、PSNR 数据及分析见附页。'
    $resultCell.Range.Font.Name = '宋体'
    try { $resultCell.Range.Font.NameFarEast = '宋体' } catch {}
    $resultCell.Range.Font.Size = 9
    $resultCell.Range.Font.Underline = 0

    $metadata = Get-Content -LiteralPath (Join-Path $results 'run_metadata.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $lowpass = @(Import-Csv -LiteralPath (Join-Path $results 'gaussian_lowpass_metrics.csv') -Encoding UTF8)
    $notchParameters = @(Import-Csv -LiteralPath (Join-Path $results 'notch_real_image_parameters.csv') -Encoding UTF8)
    $notchBest = @(Get-Content -LiteralPath (Join-Path $results 'notch_psnr_best.json') -Raw -Encoding UTF8 | ConvertFrom-Json)

    Add-AppendixSection
    Add-Paragraph -Text '实验二 图像增强的频域方法（附页）' -Size 16 -Bold $true -Alignment 1
    Add-Paragraph -Text '实验条件与数据' -Size 12 -Bold $true
    Add-Paragraph -Text ('程序运行于 Windows 10、Python ' + $metadata.python.Split(' ')[0] + '、NumPy ' + $metadata.numpy + '、Pillow ' + $metadata.pillow + '、Matplotlib ' + $metadata.matplotlib + '。低通与高通实验使用 MATLAB R2023b `imdata` 目录内的 256×256 `cameraman.tif`；噪声随机种子为 ' + $metadata.random_seed + '。任务提供的 7.PNG、10.jpg、11.jpg、16.jpg 保留原始尺寸，用于频谱峰定位和陷波。')
    Add-Paragraph -Text '频域滤波把图像变换为复数频谱 F(u,v)，逐频率乘以实值传递函数 H(u,v)，再作逆变换：g(x,y)=F⁻¹{H(u,v)F(u,v)}。径向距离 D(u,v)=√(u²+v²) 以中心化频谱零点为原点，D0 的单位是频率 bin。'
    Add-Paragraph -Text '本次比较的低通函数为：理想低通 H=1(D≤D0)；巴特沃斯低通 H=1/[1+(D/D0)^(2n)]，n=2；高斯低通 H=exp(−D²/(2D0²))。高通由 HHP=1−HLP 得到；高频强调为 Hhfe=a+b·HHP。'

    Add-Paragraph -Text '1. 二值图像的傅里叶变换' -Size 13 -Bold $true
    Add-Paragraph -Text '在 256×256 黑色背景中心放置 16 行×4 列白色矩形。除调用 `numpy.fft.fft2` 外，还按 DFT 定义构造行、列变换矩阵计算二维结果。手写 DFT 与 fft2 的最大绝对误差为 5.361×10⁻¹²；经过 fftshift/ifftshift 后再逆变换，像素最大误差为 4.441×10⁻¹⁶。'
    Add-Paragraph -Text '取 log(1+|F|) 显示幅度谱，使用 angle(F) 显示相位谱。未移位频谱的零频在左上角；fftshift 把它移到中心，便于按半径观察频率分量。'
    Add-Figure -Path (Join-Path $results 'binary_fft_spectrum.png') -Caption '图1 二值矩形、未移位与中心化幅度谱/相位谱；右下列出手写 DFT 和逆变换误差' -Width 400

    Add-PageBreak
    Add-Paragraph -Text '2. 高斯噪声与低通滤波' -Size 13 -Bold $true
    Add-Paragraph -Text ('对 cameraman.tif 加入零均值、高斯标准差 σ=' + $metadata.gaussian_sigma + ' 的独立噪声，并截断到 [0,255]。含噪图相对加噪前原图的 PSNR 为 ' + (Fmt ([string]$metadata.gaussian_noisy_psnr_db) 'F3') + ' dB。频谱图中，噪声加入后背景频率能量上升。')
    Add-Figure -Path (Join-Path $results 'gaussian_noise_spectra.png') -Caption '图2 高斯噪声加入前后的图像与中心化对数幅度谱' -Width 390
    Add-Paragraph -Text '三个低通滤波器使用 D0=8、16、32、64 bin；含噪图滤波后均以原始 cameraman.tif 为 PSNR 参照。表中 PSNR/MSE 按未裁剪浮点输出计算，保存的 PNG 则转换为 8 位灰度图；数值来自同一次固定种子运行。'

    $lowpassRows = New-Object 'System.Collections.Generic.List[object]'
    $lowpassRows.Add([object[]]@('低通类型', 'D0=8', 'D0=16', 'D0=32', 'D0=64')) | Out-Null
    foreach ($family in @('ideal', 'butterworth', 'gaussian')) {
        $label = switch ($family) { 'ideal' { '理想' } 'butterworth' { '巴特沃斯（n=2）' } 'gaussian' { '高斯' } }
        $values = New-Object 'System.Collections.Generic.List[object]'
        $values.Add($label) | Out-Null
        foreach ($cutoff in @(8, 16, 32, 64)) {
            $item = $lowpass | Where-Object { $_.filter -eq $family -and [double]$_.D0_bins -eq $cutoff } | Select-Object -First 1
            $values.Add((Fmt ([string]$item.PSNR_dB) 'F3')) | Out-Null
        }
        $lowpassRows.Add([object[]]$values.ToArray()) | Out-Null
    }
    Add-Paragraph -Text '表1 三类低通滤波器的 PSNR 对比（dB）' -Size 9 -Alignment 1 -KeepWithNext $true
    Add-WordTable -Data $lowpassRows -Widths @(118, 72, 72, 72, 72) -FontSize 8.2
    Add-Figure -Path (Join-Path $results 'gaussian_lowpass_grid.png') -Caption '图3 理想、巴特沃斯和高斯低通在四个截止频率下的输出（各图标题含 PSNR）' -Width 395
    Add-Paragraph -Text '在本次 σ=20 的图像和 D0=8–64 的范围内，三类滤波器的 PSNR 都随 D0 增大而升高；高斯低通 D0=64 得到 26.455 dB，是本组最高值。小 D0 压低更多高频，轮廓变软；增大 D0 后细节恢复，噪声也会有更多残留。因此 D0 的效果需要结合图像和噪声强度判断。'

    Add-PageBreak
    Add-Paragraph -Text '3. 理想低通的振铃现象' -Size 13 -Bold $true
    Add-Paragraph -Text '理想低通在频域以圆形边界突然从 1 跳到 0；其空间域冲激响应具有延伸的振荡旁瓣。图像边缘与该响应卷积后，会在亮暗跳变附近出现过冲和欠冲。下图在同一条高对比边缘上比较原图、D0=16 理想低通和高斯低通；红色曲线越过原图亮度范围后再回摆，体现了振铃。'
    Add-Figure -Path (Join-Path $results 'ideal_lowpass_ringing.png') -Caption '图4 cameraman.tif 局部边缘和灰度剖面；理想低通产生的振荡比平滑过渡的高斯低通明显' -Width 400

    Add-PageBreak
    Add-Paragraph -Text '4. 高通滤波与高频强调' -Size 13 -Bold $true
    Add-Paragraph -Text '对自然场景 cameraman.tif 分别使用理想、巴特沃斯和高斯高通，D0 仍取 8、16、32、64 bin。高通响应图按每幅响应的 1%–99% 百分位范围独立线性拉伸，便于观察不同截止频率下的纹理响应；CSV 记录未拉伸响应的最小值和最大值。D0 小时只抑制靠近原点的一小圈频率，边缘和细纹响应较强；D0 增大后抑制的低频范围变宽。'
    Add-Figure -Path (Join-Path $results 'highpass_grid.png') -Caption '图5 三类高通滤波器在四个截止频率下的响应（独立显示拉伸）' -Width 395
    Add-Paragraph -Text '高频强调使用 Hhfe=0.6+1.4HHP，巴特沃斯阶数 n=2、D0=24。0.6 倍低频基线与 1.4 倍高通分量共同提高边缘对比；由于 Hhfe(0)=0.6，图像均值由 118.72 降至 71.23。滤波结果中约 8.70% 的像素超出 [0,255]，保存为 8 位图像时会被裁剪。'
    Add-Figure -Path (Join-Path $results 'high_frequency_emphasis_comparison.png') -Caption '图6 原场景、高通响应和高频强调结果；增强参数 a=0.6、b=1.4、D0=24、n=2' -Width 400

    Add-PageBreak
    Add-Paragraph -Text '5. 四幅周期噪声图的陷波处理' -Size 13 -Bold $true
    Add-Paragraph -Text '实值图像的周期干扰在傅里叶幅度谱中成共轭亮峰。程序将选中的中心 (v,u) 与 (−v,−u) 同时加入高斯陷波器；每个中心的抑制量为 1−exp(−Dk²/(2D0²))，成对相乘后得到实值、中心对称的传递函数。界面支持左键选峰、右键删除最近一组、拖动 D0 滑块和保存输出。'
    Add-Paragraph -Text '频谱峰先由程序列出候选，再按图像中明显的孤立峰人工选择。各图保留输入尺寸；坐标是中心化频谱中的行偏移 v 和列偏移 u，单位为 bin。'
    $peakRows = New-Object 'System.Collections.Generic.List[object]'
    $peakRows.Add([object[]]@('输入图像', 'H×W', '陷波中心 (v,u)', 'D0')) | Out-Null
    foreach ($row in $notchParameters) {
        $pairs = ConvertFrom-Json -InputObject $row.selected_peak_pairs_v_u -NoEnumerate
        $pairText = @($pairs | ForEach-Object { '(' + $_[0] + ',' + $_[1] + ')' }) -join '、'
        $peakRows.Add([object[]]@($row.image, ($row.height + '×' + $row.width), $pairText, (Fmt ([string]$row.D0_bins) 'F1'))) | Out-Null
    }
    Add-Paragraph -Text '表2 四幅输入图像的陷波中心与半径' -Size 9 -Alignment 1 -KeepWithNext $true
    Add-WordTable -Data $peakRows -Widths @(62, 58, 220, 48) -FontSize 7.8
    Add-Figure -Path (Join-Path $results 'notch_all_four.png') -Caption '图7 四幅指定图像的输入、Gaussian notch 输出与陷波位置响应' -Width 395
    Add-Figure -Path (Join-Path $results 'notch_spectrum_16.png') -Caption '图8 16.jpg 的中心化对数频谱；青圈标出实际陷波中心及其共轭位置' -Width 330

    Add-PageBreak
    Add-Paragraph -Text '6. 陷波半径的 PSNR 搜索' -Size 13 -Bold $true
    Add-Paragraph -Text '四幅给定周期噪声图均没有对应的干净参考图。本节以每幅输入图像作为新增干扰注入前的参考，叠加频率已知、振幅受控的调幅正弦干扰，并扫描 D0=0.5–8 bin。报告的 PSNR 衡量新增合成干扰的恢复质量；原始周期噪声图则依据频谱峰位置与滤波前后图像变化评价。'
    Add-Paragraph -Text '合成干扰为 18·cos(2π(ux/W+vy/H))·[1+0.5cos(2π·2x/W)]，包含载频和两侧调制频率。评价参考是加干扰前的给定图像；PSNR=10log10(255²/MSE)。半径按最高 PSNR 选取。'
    $bestRows = New-Object 'System.Collections.Generic.List[object]'
    $bestRows.Add([object[]]@('图像', '搜索最优 D0 (bin)', 'PSNR (dB)')) | Out-Null
    foreach ($row in $notchBest) {
        $bestRows.Add([object[]]@($row.image, (Fmt ([string]$row.best_D0_bins) 'F1'), (Fmt ([string]$row.best_PSNR_dB) 'F3'))) | Out-Null
    }
    Add-Paragraph -Text '表3 合成噪声搜索的最佳 D0 与 PSNR' -Size 9 -Alignment 1 -KeepWithNext $true
    Add-WordTable -Data $bestRows -Widths @(150, 125, 110) -FontSize 8.2
    Add-Figure -Path (Join-Path $results 'notch_psnr_sweep.png') -Caption '图9 四幅图各自的受控调幅噪声 D0 搜索曲线；虚线标出本次搜索的最高 PSNR 点' -Width 395
    Add-Paragraph -Text '在这次合成信号和搜索网格上，7.PNG 与 16.jpg 的最高点位于 5 bin，10.jpg 与 11.jpg 位于 3 bin。曲线先升后降：过小半径保留调制边带，半径继续增大则抑制邻近图像频率成分。真实四图的陷波参数仍根据各自频谱峰位置和输出图像选择，见表2；两组 D0 的用途不同。'

    Add-PageBreak
    Add-Paragraph -Text '实验小结' -Size 13 -Bold $true
    Add-Paragraph -Text '这次实验把径向滤波和陷波的分工表现得很清楚：径向低通或高通按距频谱中心的半径统一改变频率分量；陷波则围绕少数周期噪声峰局部衰减。低通 D0 增大后细节保留更多，理想低通的锐利频域边界会在空间边缘附近带来振铃。高频强调以 0.6 倍低频基线叠加 1.4 倍高通分量，提高本次测试场景的边缘对比。'
    Add-Paragraph -Text '实现中，频率坐标需要与 fftshift 后的数组索引保持一致；每个噪声峰与其共轭位置成对处理，使传递函数保持共轭对称。高通响应跨越正负灰度，展示图按每幅响应的 1%–99% 百分位拉伸；CSV 记录未拉伸响应的极值。'
    Add-Paragraph -Text 'PSNR 结果覆盖两组具有已知加噪前参考的实验：cameraman.tif 高斯噪声滤波，以及四张输入图上的受控合成陷波搜索。四幅实际周期噪声图则依据频谱峰位置和滤波前后图像变化评价。'

    Add-CodeFile -RelativePath 'src\frequency_filters.py' -Heading '附录A 频域滤波核心函数：src/frequency_filters.py' -StartNewPage $true
    Add-CodeFile -RelativePath 'run_experiment.py' -Heading '附录B 实验运行与结果生成程序：run_experiment.py'
    Add-CodeFile -RelativePath 'src\notch_editor.py' -Heading '附录C 交互式陷波程序：src/notch_editor.py'

    $doc.Save()
    Write-Output "REPORT=$report"
    Write-Output "REPORT_PAGES=$($doc.ComputeStatistics(2))"
    Write-Output "SOURCE_TABLE_ROWS=$($templateTable.Rows.Count)"
    Write-Output "SOURCE_TABLE_COLUMNS=$($templateTable.Columns.Count)"
    Write-Output "SOURCE_TABLE_CELLS=$($templateTable.Range.Cells.Count)"
    Write-Output "ORIGINAL_RESULT_NOTE_PRESENT=$($templateTable.Cell(7,2).Range.Text.Contains('（写不完时，可另附稿纸。）'))"
    Write-Output "GRADE_AND_SIGNATURE_EMPTY=$((($templateTable.Cell(1,6).Range.Text -replace '[\r\a]','').Trim().Length -eq 0) -and (($templateTable.Cell(2,6).Range.Text -replace '[\r\a]','').Trim().Length -eq 0))"
} finally {
    if ($null -ne $doc) { $doc.Close(0) }
    $app.Quit()
}
