param()
$ErrorActionPreference = 'Stop'
$taskDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $taskDir 'tmp\latex'
$outputDir = Join-Path $taskDir 'output\pdf'
$source = Join-Path $taskDir '运动模糊PSF报告.tex'
$builtPdf = Join-Path $buildDir '运动模糊PSF报告.pdf'
$finalPdf = Join-Path $outputDir '运动模糊PSF复现报告.pdf'
New-Item -ItemType Directory -Force -Path $buildDir, $outputDir | Out-Null
Push-Location $taskDir
try {
    & xelatex -interaction=nonstopmode -halt-on-error -file-line-error "-output-directory=$buildDir" '运动模糊PSF报告.tex'
    if ($LASTEXITCODE -ne 0) { throw 'XeLaTeX 第一次编译失败。' }
    & xelatex -interaction=nonstopmode -halt-on-error -file-line-error "-output-directory=$buildDir" '运动模糊PSF报告.tex'
    if ($LASTEXITCODE -ne 0) { throw 'XeLaTeX 第二次编译失败。' }
    Copy-Item -LiteralPath $builtPdf -Destination $finalPdf -Force
} finally {
    Pop-Location
}
Write-Output $finalPdf
