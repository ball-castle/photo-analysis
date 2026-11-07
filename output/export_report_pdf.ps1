$ErrorActionPreference = 'Stop'
$report = Join-Path $PSScriptRoot '实验一_图像增强的空域方法实现_实验报告.doc'
$pdf = Join-Path $PSScriptRoot '实验一_图像增强的空域方法实现_实验报告.pdf'
if (-not (Test-Path -LiteralPath $report)) { throw "Report .doc is missing: $report" }
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$app.DisplayAlerts = 0
$doc = $null
try {
    $doc = $app.Documents.Open($report, $false, $true, $false)
    $doc.ExportAsFixedFormat($pdf, 17)
    Write-Output "PDF=$pdf"
    Write-Output "PAGES=$($doc.ComputeStatistics(2))"
} finally {
    if ($null -ne $doc) { $doc.Close(0) }
    $app.Quit()
}
