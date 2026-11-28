param([string]$In, [string]$Out)
# Converts a .docx to .pdf with Microsoft Word (wdFormatPDF = 17).
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($In, $false, $true)
    $doc.SaveAs([ref]$Out, [ref]17)
    $doc.Close([ref]0)
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
Write-Output "PDF written: $Out"
