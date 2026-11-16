# Converte um .docx ou .pptx em PDF via automação do Word/PowerPoint e
# informa o número de páginas. Uso:
#
#   powershell -File src/converter_pdf.ps1 relatorio/Relatorio_A1.docx
#
# Word é a única via disponível nesta máquina (não há LibreOffice).

param([Parameter(Mandatory = $true)][string]$Arquivo)

$ErrorActionPreference = "Stop"
$origem = (Resolve-Path $Arquivo).Path
$destino = [System.IO.Path]::ChangeExtension($origem, ".pdf")
if (Test-Path $destino) { Remove-Item $destino -Force }

$wdExportFormatPDF = 17
$msoForceDisable = 3   # bloqueia macros do documento durante a automação

if ($origem -like "*.pptx") {
    $app = New-Object -ComObject PowerPoint.Application
    $app.DisplayAlerts = 1
    $apresentacao = $app.Presentations.Open($origem, $true, $false, $false)
    $apresentacao.SaveAs($destino, 32)
    $paginas = $apresentacao.Slides.Count
    $apresentacao.Close()
} else {
    $app = New-Object -ComObject Word.Application
    $app.Visible = $false
    $app.DisplayAlerts = 0
    $app.AutomationSecurity = $msoForceDisable
    $doc = $app.Documents.Open($origem, $false, $true, $false)
    $doc.Repaginate()
    $paginas = $doc.ComputeStatistics(2)   # wdStatisticPages
    $doc.ExportAsFixedFormat($destino, $wdExportFormatPDF)
    $doc.Close(0)
}

$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
[GC]::Collect()

"paginas=$paginas"
"pdf=$destino"
