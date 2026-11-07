$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backup = 'C:\Users\CAI BIN\Downloads\实验报告模板.doc'
$report = Join-Path $PSScriptRoot '实验一_图像增强的空域方法实现_最终实验报告.doc'
$results = Join-Path $root 'results'
$round2 = $PSScriptRoot
$codeRoot = Join-Path $round2 'source_snapshot'
$verification = Join-Path $round2 'verification_results'
if (-not (Test-Path -LiteralPath $backup)) { throw "Template backup is missing: $backup" }

Copy-Item -LiteralPath $backup -Destination $report -Force
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$app.DisplayAlerts = 0
$doc = $null

function Set-CellText([object]$cell, [string]$text) {
    $normalized = [regex]::Replace($text, "\r?\n", [string][char]13)
    $cell.Range.Text = $normalized
}

function Fill-CellParagraphLines([object]$cell, [string[]]$lines) {
    $originalCount = $cell.Range.Paragraphs.Count
    if ($lines.Count -ge $originalCount) { throw 'Result text exceeds the existing blank paragraph slots.' }
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $paragraph = $cell.Range.Paragraphs.Item($i + 1)
        $body = $doc.Range($paragraph.Range.Start, $paragraph.Range.End - 1)
        $body.Text = $lines[$i]
    }
    if ($cell.Range.Paragraphs.Count -ne $originalCount) { throw 'Result cell paragraph structure changed.' }
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
    if ($KeepWithNext) { $selection.ParagraphFormat.KeepWithNext = -1 }
    $selection.TypeText($Text)
    $selection.TypeParagraph()
}

function Add-PageBreak {
    $selection = $app.Selection
    $selection.EndKey(6) | Out-Null
    $selection.InsertBreak(7)
}

function Add-Figure {
    param([string]$Path, [string]$Caption, [double]$Width = 400)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Figure is missing: $Path" }
    Add-Paragraph -Text $Caption -Size 9 -Bold $false -Alignment 1
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

function Fmt([string]$Value, [string]$Pattern = 'F3') {
    $number = [double]::Parse($Value, [System.Globalization.CultureInfo]::InvariantCulture)
    return $number.ToString($Pattern, [System.Globalization.CultureInfo]::InvariantCulture)
}

try {
    $doc = $app.Documents.Open($report, $false, $false, $false)
    $templateTable = $doc.Tables.Item(1)

    # Fill the class and name from the user-provided submission details.
    Set-CellText $templateTable.Cell(1, 2) '数学jd2401'
    Set-CellText $templateTable.Cell(2, 2) '蔡斌'
    # Leave date, lab, grade, and teacher signature empty.
    $courseParagraph = $doc.Paragraphs.Item(3).Range
    $courseStart = $courseParagraph.Start + 8
    $courseRange = $doc.Range($courseStart, $courseStart + 6)
    $courseRange.Text = '数字图像处理'

    Set-CellText $templateTable.Cell(3, 2) '实验一 图像增强的空域方法实现'
    # Match the original blank field's mixed Latin/East Asian font assignment.
    $titleCell = $templateTable.Cell(3, 2)
    try { $titleCell.Range.Font.NameFarEast = '宋体' } catch {}
    $titleCell.Range.Font.Name = 'Times New Roman'
    Set-CellText $templateTable.Cell(4, 2) 'Python 3.9.7、NumPy、Pillow、Matplotlib；MATLAB R2023b（仅均衡化对照）'
    $purposeLines = @(
        '目的：理解空域图像增强的原理与实现过程。',
        '完成：直方图计算、均衡化及规定化。',
        '比较：Roberts、Sobel、Prewitt、Laplacian 锐化。',
        '生成：高斯噪声、椒盐噪声和混合噪声。',
        '比较均值、中值、高斯、双边、引导与NLM六种滤波。',
        '以PSNR、SSIM、运行时间与视觉效果进行评价。'
    )
    Set-CellText $templateTable.Cell(5, 2) ($purposeLines -join [char]13)

    $originalPrompt = '（按第一次上机实验的内容逐一填写）'
    $coreLines = @(
        '直方图：H(k)=n_k，p(k)=n_k/(MN)，CDF(k)=Σ_{j≤k}p(j)。',
        '均衡化：s=round[255(CDF−CDFmin)/(1−CDFmin)]，将有效',
        'CDF 线性映射至[0,255]；规定化查找首个CDF_target≥CDF_source。',
        '本次目标为0.52·N(65,13²)+0.48·N(185,13²)（主程序传参）。',
        '锐化：Roberts为2×2交叉差分；Sobel/Prewitt用3×3梯度核，',
        '以E=√(Gx²+Gy²)取幅值。Laplacian采用中心为正的四邻域核。',
        '正中心核锐化用I+L；保留浮点符号响应，末端clip至[0,255]。',
        '平滑：均值为归一化加权和；中值取窗口次序统计量中位数。',
        '高斯权重Gσ∝exp[−(x²+y²)/(2σ²)]，使用归一化可分离核。',
        '双边权重结合空间距离和灰度差；引导滤波拟合局部线性q=aI+b。',
        'NLM按补丁距离加权，w=exp[−max(d²−2σn²,0)/h²]。',
        '步骤：读入两张灰度图并统一512×512，记录输入统计。',
        '按固定种子生成高斯、椒盐与混合噪声；执行指导书任务1、3、4。',
        '保存图像、参数敏感性表及运行时间；用干净参考计算PSNR/SSIM。',
        '人脸美容平滑无无瑕疵参考，只作视觉分析。',
        '直方图均衡化代码（histogram.py）：',
        'lut = np.clip(np.rint((cdf - cdf_min) * (255.0 / denominator)), 0, 255)',
        'return lut[source].astype(np.uint8)',
        'Laplacian叠加代码（spatial.py）：',
        '"overlay": np.clip(np.rint(source + response), 0, 255).astype(np.uint8),'
    )
    $coreCell = $templateTable.Cell(6, 2)
    if (-not $coreCell.Range.Text.Contains($originalPrompt)) { throw 'Original page-1 instruction prompt was not found.' }
    Set-CellText $coreCell ($originalPrompt + [char]13 + ($coreLines -join [char]13))

    $resultLines = @(
        '均衡化：均值42.14→103.25，标准差48.98→82.54，P99由180升至252。',
        '暗部层次展开、亮部变强；均值/分布变化不能单独说明视觉更优。',
        '规定化：均值125.02、标准差59.10、P1–P99=61–212，熵5.486 bit。',
        'Roberts、Sobel、Prewitt、Laplacian均增强边缘；Sobel响应较连续。',
        'Prewitt权重均匀；Roberts定位细但易受噪声影响。',
        'Laplacian中心正核I+L保留亮暗方向；|L|和拉伸仅作响应图显示。',
        '噪声：高斯σ=18，椒盐总密度0.04，混合σ=12/密度0.02。',
        '方法性质：均值/高斯平滑随机噪声；中值更能去除椒盐脉冲。',
        '边缘保持：双边按空间和灰度加权；引导、NLM留较多邻近结构。',
        '以下指标用同一512×512混合噪声和加噪前图作参考。',
        '均值5×5：30.497dB/0.7671/0.0087s（六法组最快）。',
        '中值5×5：32.494dB/0.8502/0.0855s（该组PSNR、SSIM均最高）。',
        '高斯7×7：31.017/0.8004/0.0103s；双边：21.309/0.5881/0.2569s。',
        '引导：26.298/0.6404/0.0354s；NLM：26.730/0.7006/0.4930s。',
        '窗口组中值5×5最高PSNR32.494，计时0.0905s；综合表另测0.0855s。',
        '两值来自同次主程序运行中的不同计时调用；中值7×7 SSIM最高0.8661。',
        '但其PSNR31.836、耗时0.1582s；“最佳”需限定评价指标。',
        '参数敏感性中σr、ε、h增大提升本混合噪声指标；更平滑会损纹理。',
        'NLM搜索窗5×5→11×11（h=22）耗时0.261→1.425s。',
        '完成任务1、3、4；美容平滑无真值，只作视觉评价；结论限于单图和本轮噪声。'
    )
    $resultCell = $templateTable.Cell(7, 2)
    $resultParagraphCount = $resultCell.Range.Paragraphs.Count
    Fill-CellParagraphLines $resultCell $resultLines
    if (-not $resultCell.Range.Text.Contains('（写不完时，可另附稿纸。）')) { throw 'Original page-2 note was changed.' }
    if ($resultCell.Range.Paragraphs.Count -ne $resultParagraphCount) { throw 'Result cell paragraph count changed.' }
    $six = @(Import-Csv -LiteralPath (Join-Path $results 'six_filter_comparison.csv') -Encoding UTF8)
    $classic = @(Import-Csv -LiteralPath (Join-Path $results 'classical_sensitivity.csv') -Encoding UTF8)
    $advanced = @(Import-Csv -LiteralPath (Join-Path $results 'advanced_sensitivity.csv') -Encoding UTF8)
    $hist = @(Import-Csv -LiteralPath (Join-Path $results 'histogram_statistics.csv') -Encoding UTF8)
    $matlab = Get-Content -LiteralPath (Join-Path $results 'matlab_histeq_comparison.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $histeqMethods = @(Import-Csv -LiteralPath (Join-Path $verification 'histeq_method_comparison.csv') -Encoding UTF8)
    $histeqStats = @{}; Get-Content -LiteralPath (Join-Path $verification 'histeq_bin_comparison.txt') -Encoding UTF8 | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { $histeqStats[$matches[1]] = $matches[2] } }
    $histeqDefault = $histeqMethods | Where-Object { $_.method -eq 'MATLAB histeq(I), default' }
    $histeq256 = $histeqMethods | Where-Object { $_.method -eq 'MATLAB histeq(I,256)' }

    # Start appended report pages after the unchanged source template and its note.
    Add-PageBreak
    Add-Paragraph -Text '实验一 图像增强的空域方法实现（附页）' -Size 16 -Bold $true -Alignment 1
    Add-Paragraph -Text '实验条件、数据来源与复现设置' -Size 12 -Bold $true
    Add-Paragraph -Text '软件：Python 3.9.7、NumPy 2.0.2、Pillow 11.2.1、Matplotlib 3.9.4、scikit-image 0.24.0（仅用于 PSNR/SSIM）、pytest 8.4.2；另用 MATLAB R2023b Image Processing Toolbox 的 histeq 作单独对照。操作系统为 Windows 10。所有实验图均为 512×512 灰度图，随机种子为 20261008。'
    Add-Paragraph -Text '图像1：Alex Guillaume 摄影，Unsplash《An older woman with wrinkles on her face》，原图 3000×3000，暗调皱纹人像，用于直方图实验。来源：https://unsplash.com/photos/an-older-woman-with-wrinkles-on-her-face-mSh9yhcJk1A。'
    Add-Paragraph -Text '图像2：Robert Piosik 摄影，Unsplash 灰度女性面部人像，原图 3000×2000，含清晰雀斑，用于边缘与滤波实验。先中心裁剪为 2000×2000，再缩放为 512×512，不拉伸。来源：https://unsplash.com/es/fotos/foto-en-escala-de-grises-de-la-cara-de-la-mujer-bJR4cvkfxf0。许可：https://unsplash.com/license。'
    Add-Paragraph -Text '任务1：直方图均衡化与规定化' -Size 12 -Bold $true
    Add-Paragraph -Text '灰度直方图 H(k)=n_k，相对频率 p(k)=n_k/(MN)，累积分布 CDF(k)=Σ_{j≤k}p(j)。离散均衡化按 s_k=round(255·(CDF(k)-CDF_min)/(1-CDF_min)) 映射；规定化先求源、目标 CDF，再将源 CDF 映射到第一个不小于该概率的目标灰度级。实际主程序显式传入 peak1=65、peak2=185、sigma=13、weight1=0.52，覆盖函数默认 sigma=12、weight1=0.5；目标为归一化的0.52·N(65,13²)+0.48·N(185,13²)。'

    $histRows = New-Object 'System.Collections.Generic.List[object]'
    $histRows.Add([object[]]@('图像', '均值', '标准差', 'P1–P99', '熵(bit)')) | Out-Null
    foreach ($row in $hist) {
        $histRows.Add([object[]]@(
            $row.image,
            (Fmt $row.mean_gray 'F2'),
            (Fmt $row.std_gray 'F2'),
            ((Fmt $row.p01_gray 'F0') + '–' + (Fmt $row.p99_gray 'F0')),
            (Fmt $row.entropy_bits 'F3')
        )) | Out-Null
    }
    Add-WordTable -Data $histRows -Widths @(100, 55, 65, 75, 75) -FontSize 8.5
    Add-Figure -Path (Join-Path $results 'histogram_comparison.png') -Caption '图1 暗调原图、手写均衡化、双峰规定化及灰度直方图' -Width 400

    Add-PageBreak
    Add-Paragraph -Text '任务1结果分析与 MATLAB 对照' -Size 13 -Bold $true
    Add-Paragraph -Text ('暗调原图灰度均值为 ' + (Fmt $hist[0].mean_gray 'F2') + '，标准差为 ' + (Fmt $hist[0].std_gray 'F2') + '，P99 为 ' + (Fmt $hist[0].p99_gray 'F0') + '。均衡化后均值为 ' + (Fmt $hist[1].mean_gray 'F2') + '、标准差为 ' + (Fmt $hist[1].std_gray 'F2') + '、P99 为 ' + (Fmt $hist[1].p99_gray 'F0') + '；面部暗部层次被展开，但脸部高光明显变亮，背景与皮肤纹理有过增强现象。')
    Add-Paragraph -Text ('规定化后均值为 ' + (Fmt $hist[2].mean_gray 'F2') + '、标准差为 ' + (Fmt $hist[2].std_gray 'F2') + '。双峰目标把大量暗像素映射到约 61 的灰度附近，暗背景被抬亮；面部过渡较均衡，但灰度层级更集中，局部对比度下降。目标分布决定了面部亮度和肤色层次，不能仅凭峰值更多判断视觉质量。')
    $defaultMae = Fmt $histeqDefault.mae_vs_python 'F3'
    $defaultMax = [string]$histeqDefault.max_abs_diff_vs_python
    $bins256Mae = Fmt $histeq256.mae_vs_python 'F3'
    $bins256Max = [string]$histeq256.max_abs_diff_vs_python
    $defaultVs256Mae = Fmt $histeqStats['DEFAULT64_VS_256_MAE'] 'F3'
    $matlab256VsCdf = Fmt $histeqStats['MATLAB256_VS_DIRECT_FULL_CDF_MAE'] 'F3'
    $pythonCdfMinCheck = Fmt $histeqStats['PYTHON_CDFMIN_RECONSTRUCTION_MAE'] 'F3'
    Add-Paragraph -Text ("MATLAB R2023b histeq(I) 默认匹配64档近似平坦的目标直方图。对同一512×512 uint8输入，默认结果相对Python的MAE=$defaultMae、最大差=$defaultMax；histeq(I,256)为MAE=$bins256Mae、最大差=$bins256Max。两张MATLAB结果之间MAE仅$defaultVs256Mae；Python输出可由当前CDF_min减除与重标定公式精确重建（MAE=$pythonCdfMinCheck）。MATLAB按目标直方图近似匹配选择单调映射，Python则作CDF_min减除和线性重标定；256档结果与直接全CDF映射仍差$matlab256VsCdf。故64档量化不是约29.4 MAE的主因，输入也一致。")
    Add-Figure -Path (Join-Path $verification 'matlab_histeq_bins_comparison.png') -Caption '图2 同一输入下 Python CDF_min 均衡化与 MATLAB 默认64档、256档 histeq 对照' -Width 400    Add-PageBreak
    Add-Paragraph -Text '任务3：传统边缘锐化' -Size 13 -Bold $true
    Add-Paragraph -Text 'Roberts 使用 2×2 交叉差分核 Gx=[[1,0],[0,-1]]、Gy=[[0,1],[-1,0]]；Sobel 的水平核为[[-1,0,1],[-2,0,2],[-1,0,1]]，垂直核为其转置方向；Prewitt 将中间行/列权重改为1。边缘幅值 E=√(Gx²+Gy²)。代码以 E−mean3×3(E) 作为局部细节掩膜，再计算 clip(I+0.2·D,0,255)，同时输出共同比例的边缘响应。'
    Add-Paragraph -Text 'Laplacian 使用中心为正的四邻域核 L=[[0,-1,0],[-1,4,-1],[0,-1,0]]。亮点中心的响应为正、相邻暗位置为负；因此锐化方向为 I+L。若采用中心为负的相反符号核，则应使用 I−L。'
    Add-Figure -Path (Join-Path $results 'edge_responses.png') -Caption '图3 Roberts、Sobel、Prewitt、Laplacian 响应（各响应采用同一稳健上限）及 Laplacian 叠加结果' -Width 400
    Add-Paragraph -Text '四种算子都能突出眼部、发丝、雀斑和轮廓。Sobel 对中心邻域加权，边缘更连续但响应也更强；Prewitt 权重均匀；Roberts 核小，定位细而对噪声更敏感。边缘锐化只是将局部高频掩膜叠加回原图，幅度过大会放大噪声。'

    Add-PageBreak
    Add-Paragraph -Text 'Laplacian 负值处理比较' -Size 13 -Bold $true
    Add-Paragraph -Text '本实验对同一有符号响应 L 分别采用 |L|、线性拉伸 255·(L−Lmin)/(Lmax−Lmin)，以及 clip(I+L,0,255)。绝对值保留边缘强弱但丢失正负方向；线性拉伸能同时显示两种极性，却把零响应映射到中间灰度，结果是边缘图而非保持原亮度的增强图；原图叠加保留低频外观，并用正负响应提升亮暗边界对比。'
    Add-Figure -Path (Join-Path $results 'laplacian_negative_handling.png') -Caption '图4 Laplacian 绝对值、线性拉伸和原图叠加截断对比' -Width 400
    Add-Paragraph -Text '本例中原图叠加最符合增强细节的目标，因为它保留原图结构并叠加带符号的高频变化。截断到[0,255]会在极亮或极暗处损失少量响应；绝对值法和线性拉伸会改变亮度语义，不适合作为原图增强结果直接替代。'

    Add-PageBreak
    Add-Paragraph -Text '任务4：噪声模型与传统平滑' -Size 13 -Bold $true
    Add-Paragraph -Text '以雀斑人像为无噪声参考 f。高斯噪声为 g=f+n，n~N(0,σ²)，本次 σ=18；椒盐噪声按总密度0.04随机置0或255；混合噪声先加 σ=12 高斯噪声，再以总密度0.02加入椒盐点。各随机过程使用固定种子 20261008（子过程使用确定性偏移），便于复现。'
    Add-Figure -Path (Join-Path $results 'noise_models.png') -Caption '图5 干净参考图与三类固定种子噪声' -Width 400
    Add-Paragraph -Text '均值滤波 g(x,y)=Σw(i,j)f(x−i,y−j)/Σw，均匀核为所有 w=1；加权核突出中心邻域。中值滤波取窗口样本中位数，适合椒盐脉冲。高斯滤波权重 Gσ(i,j)∝exp(−(i²+j²)/(2σ²))，本实现按两个一维核分离计算。边界使用反射填充，数组先转为 float，最终显示时才裁剪回[0,255]。'

    Add-PageBreak
    Add-Paragraph -Text '传统滤波窗口参数实验' -Size 13 -Bold $true
    $classicRows = New-Object 'System.Collections.Generic.List[object]'
    $classicRows.Add([object[]]@('方法', '参数', '时间(s)', 'PSNR(dB)', 'SSIM')) | Out-Null
    foreach ($row in $classic) {
        $classicRows.Add([object[]]@($row.method, $row.parameters, (Fmt $row.runtime_seconds 'F4'), (Fmt $row.psnr_db 'F3'), (Fmt $row.ssim 'F4'))) | Out-Null
    }
    Add-WordTable -Data $classicRows -Widths @(55, 145, 65, 68, 65) -FontSize 7.8
    Add-Figure -Path (Join-Path $results 'classical_sensitivity.png') -Caption '图6 3×3、5×5、7×7 与加权模板的视觉敏感性' -Width 400
    Add-Paragraph -Text '评价对象均为混合噪声结果，PSNR/SSIM 参考加噪前的原始雀斑图。窗口敏感性组内，中值5×5取得最高PSNR 32.494 dB，SSIM为0.8502；中值7×7取得最高SSIM 0.8661，但PSNR降至31.836 dB、耗时升至0.1582 s。窗口表中值5×5单次计时为0.0905 s；综合表对相同输入和参数另作一次单次调用，计时0.0855 s（表格四舍五入为0.085 s）。两项来自同一主程序运行中的不同计时调用，不是不同噪声批次，也不是笔误。均值/高斯扩大窗口会加强平滑并软化边缘；3×3加权均值在本次混合噪声下仍有脉冲残留。'

    Add-PageBreak
    Add-Paragraph -Text '现代边缘保持滤波与参数敏感性' -Size 13 -Bold $true
    Add-Paragraph -Text '双边滤波 w(p,q)=exp(−||p−q||²/(2σs²))·exp(−(I(p)−I(q))²/(2σr²))，按空间距离和灰度差共同加权。引导滤波在局部窗口拟合 q=aI+b，a=cov(I,p)/(var(I)+ε)，b=mean(p)−a·mean(I)，再平均系数。NLM 以补丁距离 d²(p,q) 计算 w=exp(−max(d²−2σn²,0)/h²)，输出为加权平均；本实现逐位移矩阵计算补丁均方差并用积分图盒式均值加速，没有调用现成 NLM。'
    $advancedRows = New-Object 'System.Collections.Generic.List[object]'
    $advancedRows.Add([object[]]@('方法', '参数', '时间(s)', 'PSNR(dB)', 'SSIM')) | Out-Null
    foreach ($row in $advanced) {
        $advancedRows.Add([object[]]@($row.method, $row.parameters, (Fmt $row.runtime_seconds 'F3'), (Fmt $row.psnr_db 'F3'), (Fmt $row.ssim 'F4'))) | Out-Null
    }
    Add-WordTable -Data $advancedRows -Widths @(50, 155, 65, 68, 65) -FontSize 7.4
    Add-Figure -Path (Join-Path $results 'advanced_sensitivity.png') -Caption '图7 双边 σr、引导 ε、NLM h 与搜索窗敏感性' -Width 400
    Add-Paragraph -Text '本次 σr=15→40、ε=256→1600、h=14→30 时 PSNR/SSIM 均上升，表示对当前混合噪声更强的平滑提高了与受控干净参考的相似度。NLM 搜索窗从5×5扩大到11×11，h=22时耗时由实测0.261 s增至1.425 s，指标也变化；成本随搜索位移数增加。所用NLM通过每个搜索位移的积分图距离计算，将逐像素 Python 循环改为矩阵化运算，但仍比简单盒式或可分离滤波耗时。'

    Add-PageBreak
    Add-Paragraph -Text '六种滤波算法综合对比' -Size 13 -Bold $true
    Add-Paragraph -Text '下表所有指标都来自同一张512×512混合噪声图；PSNR/SSIM 以加噪前人像作为干净参考。耗时为本机 perf_counter 单次实测，不是理论值。复杂度按像素数 N、核宽 k、NLM 搜索边长 s 表示；引导与均值使用积分图盒均值。'
    Add-Paragraph -Text '指标定义：MSE=(1/MN)Σ(I−K)²，PSNR=10log₁₀(255²/MSE)；SSIM=((2μIμK+C₁)(2σIK+C₂))/((μI²+μK²+C₁)(σI²+σK²+C₂))，均值、方差和协方差在局部窗口计算，C₁、C₂用于稳定分母。'
    $sixRows = New-Object 'System.Collections.Generic.List[object]'
    $sixRows.Add([object[]]@('方法', '参数', '时间(s)', 'PSNR(dB)', 'SSIM', '理论复杂度')) | Out-Null
    foreach ($row in $six) {
        $sixRows.Add([object[]]@($row.method, $row.parameters, (Fmt $row.runtime_seconds 'F3'), (Fmt $row.psnr_db 'F3'), (Fmt $row.ssim 'F4'), $row.complexity)) | Out-Null
    }
    Add-WordTable -Data $sixRows -Widths @(42, 100, 48, 55, 44, 122) -FontSize 7.6
    Add-Figure -Path (Join-Path $results 'six_filter_visual_comparison.png') -Caption '图8 六种滤波结果（统一灰度范围）' -Width 400
    Add-Paragraph -Text '在这六种配置中，中值5×5的PSNR最高32.494 dB、SSIM最高0.8502；均值5×5最快，实测0.0087 s。高斯7×7在抑噪与结构保留间折中。双边在本混合噪声组内指标较低，强脉冲不符合局部灰度相似假设；引导和NLM随ε/h增大而改善，但纹理也更平滑。窗口敏感性组的最高SSIM来自中值7×7（0.8661），不应与本六配置组混为一谈。排序依赖噪声、参数和参考图，不代表通用优劣。'

    Add-PageBreak
    Add-Paragraph -Text '有参考去噪与人脸平滑的区别' -Size 13 -Bold $true
    Add-Paragraph -Text '加噪实验保留了真实拍摄的人像作为人工加噪前的像素参考，因此该实验的 PSNR/SSIM 衡量恢复到输入照片的程度。美容平滑实验直接处理带雀斑的人像；原图包含真实雀斑和皮肤纹理，并非无瑕疵真值，所以该实验不报告 PSNR/SSIM。'
    Add-Figure -Path (Join-Path $results 'facial_smoothing_no_reference.png') -Caption '图9 对真实雀斑人像进行六种平滑的无参考视觉比较' -Width 400
    Add-Figure -Path (Join-Path $results 'face_detail_comparison.png') -Caption '图10 混合噪声去噪的128×128局部对比' -Width 400
    Add-Paragraph -Text '均值与高斯会一起削弱肤色细纹和雀斑；中值更能抑制孤立点，但窗口变大也会损失细纹；双边、引导与 NLM 在边缘附近保留较多结构，参数过大时同样会让斑点和纹理变淡。视觉上更光滑不等于恢复了真实无瑕疵皮肤。'
    Add-Paragraph -Text '实验总结：完成指导书任务1、3、4，实现直方图映射、边缘锐化与多类平滑；效果受噪声和参数影响，评价需结合视觉质量与参考指标。美容平滑无无瑕疵真值，只作视觉评价。'

    # Include the R2 source snapshot and avoid hard breaks between modules.
    $codeFiles = @('histogram.py', 'spatial.py', 'noise.py', 'advanced.py', 'metrics.py')
    $firstCodeFile = $true
    foreach ($file in $codeFiles) {
        if ($firstCodeFile) { Add-PageBreak; $firstCodeFile = $false }
        Add-Paragraph -Text ('附录A 核心运行源码：dip_lab/' + $file) -Size 11 -Bold $true -KeepWithNext $true
        $sourcePath = Join-Path $codeRoot ('dip_lab\' + $file)
        $code = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
        $code = $code -replace "`r?`n", "`r"
        $code = $code.TrimEnd([char]13)
        $selection = $app.Selection
        $selection.EndKey(6) | Out-Null
        $selection.Font.Name = 'Consolas'
        try { $selection.Font.NameFarEast = '宋体' } catch {}
        $selection.Font.Size = 7.4
        $selection.Font.Bold = $false
        $selection.ParagraphFormat.Alignment = 0
        $selection.ParagraphFormat.LineSpacingRule = 0
        $selection.ParagraphFormat.SpaceAfter = 0
        $selection.TypeText($code)
        $selection.TypeParagraph()
    }

    $doc.Save()
    Write-Output "REPORT=$report"
    Write-Output "REPORT_PAGES=$($doc.ComputeStatistics(2))"
    Write-Output "SOURCE_TABLE_ROWS=$($templateTable.Rows.Count)"
    Write-Output "SOURCE_TABLE_COLUMNS=$($templateTable.Columns.Count)"
    Write-Output "SOURCE_TABLE_CELLS=$($templateTable.Range.Cells.Count)"
    Write-Output "SOURCE_TABLE_ROW_HEIGHTS=" + (($templateTable.Rows | ForEach-Object { [math]::Round($_.Height, 2) }) -join ',')
    Write-Output "ORIGINAL_RESULT_NOTE_PRESENT=$($templateTable.Cell(7,2).Range.Text.Contains('（写不完时，可另附稿纸。）'))"
    Write-Output "GRADE_AND_SIGNATURE_EMPTY=$((($templateTable.Cell(1,6).Range.Text -replace '[\r\a]','').Trim().Length -eq 0) -and (($templateTable.Cell(2,6).Range.Text -replace '[\r\a]','').Trim().Length -eq 0))"
} finally {
    if ($null -ne $doc) { $doc.Close(0) }
    $app.Quit()
}





