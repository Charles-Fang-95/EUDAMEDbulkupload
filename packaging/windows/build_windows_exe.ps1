param(
    [switch]$SkipVenv,
    [switch]$Console
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
    & ".\.venv-win\Scripts\python.exe" -m pip install pyinstaller openpyxl et_xmlfile
    if ($LASTEXITCODE -ne 0) { throw "Build dependency installation failed" }
    $Python = ".\.venv-win\Scripts\python.exe"
} else {
    $Python = "python"
}

& $Python -m compileall local_beta EUDAMED_TOOL_v2/validator.py
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed" }

$ConsoleMode = "--windowed"
if ($Console) {
    $ConsoleMode = "--console"
}

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    $ConsoleMode `
    --name EUDAMED_Local_Beta `
    --add-data "local_beta;local_beta" `
    --add-data "EUDAMED_TOOL_v2/lib;EUDAMED_TOOL_v2/lib" `
    --add-data "EUDAMED_TOOL_v2/validator.py;EUDAMED_TOOL_v2" `
    --add-data "official_docs/unpacked/xsd_production;official_docs/unpacked/xsd_production" `
    --add-data "EUDAMED_Template_v2.14.xlsx;." `
    --add-data "EUDAMED_Template_v2.14_EN.xlsx;." `
    --add-data "README.md;." `
    run_local_beta.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed; refusing to archive stale artifacts" }

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
