$docx = "C:\elkin\Отчёты\Практика 11 Василенко И.А.docx"
$pdf = "C:\Users\gorak\AppData\Local\Temp\gigatool\report-preview.pdf"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

$document = $word.Documents.Open($docx, $false, $false)
Write-Output "страниц: $($document.ComputeStatistics(2))"
Write-Output "слов: $($document.ComputeStatistics(0))"

$document.ExportAsFixedFormat($pdf, 17)
Write-Output "pdf: $pdf"

$document.Save()
Write-Output "saved docx"

$word.Visible = $true
$word.Activate()
Write-Output "word opened"
