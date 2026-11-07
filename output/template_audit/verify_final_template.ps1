$ErrorActionPreference = 'Stop'
$auditDir = $PSScriptRoot
$outputDir = Split-Path $auditDir -Parent
$baselinePath = Join-Path $auditDir 'template_structure_baseline.json'
$baseline = Get-Content -LiteralPath $baselinePath -Raw -Encoding UTF8 | ConvertFrom-Json
$backup = Get-ChildItem -LiteralPath $auditDir -Filter '*.doc' | Select-Object -First 1
$report = Get-ChildItem -LiteralPath $outputDir -Filter '*.doc' | Select-Object -First 1
if ($null -eq $backup -or $null -eq $report) { throw 'Expected backup and final .doc files.' }

function Normalize-Text([string]$Text) {
    return (($Text -replace '[\r\n\a\v]+', ' ') -replace '\s+', ' ').Trim()
}

function Get-DocumentInfo([object]$Document) {
    $sectionData = @()
    foreach ($section in $Document.Sections) {
        $page = $section.PageSetup
        $sectionData += [pscustomobject]@{
            PageWidthPt = [double]$page.PageWidth
            PageHeightPt = [double]$page.PageHeight
            TopMarginPt = [double]$page.TopMargin
            BottomMarginPt = [double]$page.BottomMargin
            LeftMarginPt = [double]$page.LeftMargin
            RightMarginPt = [double]$page.RightMargin
            HeaderDistancePt = [double]$page.HeaderDistance
            FooterDistancePt = [double]$page.FooterDistance
            Orientation = [int]$page.Orientation
        }
    }
    $table = $Document.Tables.Item(1)
    $cells = @()
    for ($i = 1; $i -le $table.Range.Cells.Count; $i++) {
        $cell = $table.Range.Cells.Item($i)
        $cells += [pscustomobject]@{
            Row = [int]$cell.RowIndex
            Column = [int]$cell.ColumnIndex
            WidthPt = [double]$cell.Width
            HeightPt = [double]$cell.Height
            Text = Normalize-Text ([string]$cell.Range.Text)
            Font = [string]$cell.Range.Font.Name
            FontFarEast = [string]$cell.Range.Font.NameFarEast
            FontSizePt = [double]$cell.Range.Font.Size
            Bold = ([int]$cell.Range.Font.Bold -ne 0)
            LineSpacingPt = [double]$cell.Range.ParagraphFormat.LineSpacing
        }
    }
    $rowHeights = @()
    for ($row = 1; $row -le $table.Rows.Count; $row++) {
        $rowHeights += [pscustomobject]@{
            Index = $row
            HeightPt = [double]$table.Rows.Item($row).Height
            HeightRule = [int]$table.Rows.Item($row).HeightRule
        }
    }
    return [pscustomobject]@{
        PageCount = [int]$Document.ComputeStatistics(2)
        SectionCount = [int]$Document.Sections.Count
        Sections = $sectionData
        TableCount = [int]$Document.Tables.Count
        TableRows = [int]$table.Rows.Count
        TableColumns = [int]$table.Columns.Count
        TableCells = [int]$table.Range.Cells.Count
        Cells = $cells
        RowHeights = $rowHeights
        FullText = [string]$Document.Content.Text
        OriginalResultCell = [string]$table.Cell(7, 2).Range.Text
        PersonalCells = @(
            (Normalize-Text ([string]$table.Cell(1, 2).Range.Text)),
            (Normalize-Text ([string]$table.Cell(1, 4).Range.Text)),
            (Normalize-Text ([string]$table.Cell(1, 6).Range.Text)),
            (Normalize-Text ([string]$table.Cell(2, 2).Range.Text)),
            (Normalize-Text ([string]$table.Cell(2, 4).Range.Text)),
            (Normalize-Text ([string]$table.Cell(2, 6).Range.Text))
        )
    }
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$originalDoc = $null
$finalDoc = $null
try {
    $originalDoc = $word.Documents.Open($backup.FullName, $false, $true, $false)
    $finalDoc = $word.Documents.Open($report.FullName, $false, $true, $false)
    $originalInfo = Get-DocumentInfo $originalDoc
    $finalInfo = Get-DocumentInfo $finalDoc
} finally {
    if ($null -ne $finalDoc) { $finalDoc.Close(0) }
    if ($null -ne $originalDoc) { $originalDoc.Close(0) }
    $word.Quit()
}

$failures = New-Object 'System.Collections.Generic.List[string]'
$sourceHash = (Get-FileHash -LiteralPath $baseline.SourcePath -Algorithm SHA256).Hash
$backupHash = (Get-FileHash -LiteralPath $backup.FullName -Algorithm SHA256).Hash
if ($sourceHash -ne $baseline.SourceSHA256) { $failures.Add('Original source template hash changed.') }
if ($backupHash -ne $baseline.SourceSHA256) { $failures.Add('Frozen backup hash does not match source template.') }
if ($finalInfo.SectionCount -ne $baseline.SectionCount) { $failures.Add('Section count changed.') }
if ($finalInfo.TableCount -lt $baseline.TableCount) { $failures.Add('Original template table is missing.') }
if ($finalInfo.TableRows -ne $baseline.Tables[0].Rows -or $finalInfo.TableColumns -ne $baseline.Tables[0].Columns -or $finalInfo.TableCells -ne $baseline.Tables[0].Cells.Count) {
    $failures.Add('Original template table geometry changed.')
}
if ($finalInfo.Sections.Count -ne $baseline.Sections.Count) { $failures.Add('Section geometry count changed.') }
for ($i = 0; $i -lt $baseline.Sections.Count; $i++) {
    foreach ($property in @('PageWidthPt','PageHeightPt','TopMarginPt','BottomMarginPt','LeftMarginPt','RightMarginPt','HeaderDistancePt','FooterDistancePt','Orientation')) {
        if ([math]::Abs([double]$finalInfo.Sections[$i].$property - [double]$baseline.Sections[$i].$property) -gt 0.1) {
            $failures.Add("Section $($i + 1) $property changed.")
        }
    }
}
if ($finalInfo.Cells.Count -ne $baseline.Tables[0].Cells.Count) { $failures.Add('Template cell count changed.') }
for ($i = 0; $i -lt [math]::Min($finalInfo.Cells.Count, $baseline.Tables[0].Cells.Count); $i++) {
    $actual = $finalInfo.Cells[$i]
    $expected = $baseline.Tables[0].Cells[$i]
    $sourceCell = $originalInfo.Cells[$i]
    foreach ($property in @('WidthPt','HeightPt','FontSizePt','LineSpacingPt')) {
        if ([math]::Abs([double]$actual.$property - [double]$expected.$property) -gt 0.1) {
            $failures.Add("Template cell $($expected.Row),$($expected.Column) $property changed.")
        }
    }
    $filledCell = ($expected.Column -eq 2 -and $expected.Row -ge 3)
    if ($filledCell) {
        # Word may report Name=宋体 for a Chinese-only run; compare its actual East Asian font to the blank source field.
        if ($actual.FontFarEast -ne $sourceCell.FontFarEast) { $failures.Add("Template cell $($expected.Row),$($expected.Column) East Asian font changed.") }
    } elseif ($actual.Font -ne $expected.Font -or $actual.FontFarEast -ne $sourceCell.FontFarEast) {
        $failures.Add("Template cell $($expected.Row),$($expected.Column) font changed.")
    }
    if ([bool]$actual.Bold -ne [bool]$expected.Bold) { $failures.Add("Template cell $($expected.Row),$($expected.Column) bold style changed.") }
    if (-not $filledCell -and ($actual.Text -replace '\s+', '') -ne ((Normalize-Text ([string]$expected.Text)) -replace '\s+', '')) {
        $failures.Add("Template label at cell $($expected.Row),$($expected.Column) changed.")
    }
}
for ($i = 0; $i -lt [math]::Min($finalInfo.RowHeights.Count, $baseline.Tables[0].RowHeights.Count); $i++) {
    $actual = $finalInfo.RowHeights[$i]
    $expected = $baseline.Tables[0].RowHeights[$i]
    if ([math]::Abs([double]$actual.HeightPt - [double]$expected.HeightPt) -gt 0.1 -or [int]$actual.HeightRule -ne [int]$expected.HeightRule) {
        $failures.Add("Template row $($i + 1) height or rule changed.")
    }
}
$expectedResultNote = Normalize-Text ([string](($baseline.Tables[0].Cells | Where-Object { $_.Row -eq 7 -and $_.Column -eq 2 }).Text))
$resultNotePresent = (Normalize-Text $finalInfo.OriginalResultCell).Contains($expectedResultNote)
if (-not $resultNotePresent) { $failures.Add('Original result-cell note is missing.') }
if ($finalInfo.PersonalCells.Where({ $_ -ne '' }).Count -gt 0) { $failures.Add('An unprovided personal/grade/signature field is not blank.') }
if ($finalInfo.FullText -notmatch '武汉理工大学数统学院数学系课程实验报告') { $failures.Add('Original school title is missing.') }
if ($finalInfo.FullText -notmatch '备注：不交此报告者，本次实验为“不合格”。') { $failures.Add('Original bottom remark is missing.') }

$bytes = [System.IO.File]::ReadAllBytes($report.FullName)
$oleSignature = 'D0CF11E0A1B11AE1'
$actualSignature = ([System.BitConverter]::ToString($bytes[0..7])).Replace('-', '')
if ($actualSignature -ne $oleSignature) { $failures.Add('Final report is not an OLE .doc file.') }
$result = [pscustomobject]@{
    Status = if ($failures.Count -eq 0) { 'TEMPLATE_PRESERVATION_PASS' } else { 'FAIL' }
    Failures = @($failures)
    SourceSHA256 = $sourceHash
    BackupSHA256 = $backupHash
    FinalWordPages = $finalInfo.PageCount
    FinalDocLength = (Get-Item -LiteralPath $report.FullName).Length
    FinalDocSignature = $actualSignature
    SectionGeometry = $finalInfo.Sections
    OriginalTable = [pscustomobject]@{
        Rows = $finalInfo.TableRows
        Columns = $finalInfo.TableColumns
        Cells = $finalInfo.TableCells
        RowHeights = $finalInfo.RowHeights
        CellGeometryAndStyle = $finalInfo.Cells
    }
    PersonalGradeSignatureFieldsBlank = ($finalInfo.PersonalCells.Where({ $_ -ne '' }).Count -eq 0)
    OriginalResultNotePresent = $resultNotePresent
}
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $auditDir 'final_template_verification.json') -Encoding UTF8
$result | Select-Object Status,FinalWordPages,FinalDocLength,FinalDocSignature,SourceSHA256,BackupSHA256 | Format-List | Out-String | Write-Output
if ($failures.Count -gt 0) { $failures | ForEach-Object { Write-Error $_ } }
