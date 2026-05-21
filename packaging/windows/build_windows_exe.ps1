param(
    [switch]$SkipVenv
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $RepoRoot

if (-not $SkipVenv) {
    if (-not (Test-Path ".venv-win")) {
        py -3 -m venv .venv-win
    }
    & ".\.venv-win\Scripts\python.exe" -m pip install --upgrade pip
    & ".\.venv-win\Scripts\python.exe" -m pip install pyinstaller
    $Python = ".\.venv-win\Scripts\python.exe"
} else {
    $Python = "python"
}

& $Python -m compileall local_beta

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --console `
    --name EUDAMED_Local_Beta `
    --add-data "local_beta;local_beta" `
    --add-data "EUDAMED_TOOL_v2;EUDAMED_TOOL_v2" `
    --add-data "official_docs;official_docs" `
    --add-data "EUDAMED_Template_v2.4.xlsx;." `
    --add-data "README.md;." `
    run_local_beta.py

$ZipPath = "dist\EUDAMED_Local_Beta_Windows.zip"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}
Compress-Archive -Path "dist\EUDAMED_Local_Beta\*" -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\EUDAMED_Local_Beta\EUDAMED_Local_Beta.exe"
Write-Host "  $ZipPath"
Write-Host ""
Write-Host "Send the whole ZIP folder to testers. Do not send the .exe alone, because templates, XSD files and static assets are bundled next to it."
