param(
    [switch]$OneFile = $true,
    [switch]$InstallBuildDeps = $true,
    [string]$DistPath = "dist"
)

$ErrorActionPreference = "Stop"

Write-Host "== XIMEA GUI Windows Build =="
Write-Host "Working directory: $(Get-Location)"

if ($InstallBuildDeps) {
    Write-Host "Installing build dependency: pyinstaller"
    py -m pip install --upgrade pyinstaller
}

$buildModeArgs = @()
if ($OneFile) {
    $buildModeArgs += "--onefile"
} else {
    $buildModeArgs += "--onedir"
}

# Avoid OneDrive/locked-file issues by building in a temp work path.
$tempBuildRoot = Join-Path $env:TEMP "XimeaCameraGUI_pyinstaller"
$workPath = Join-Path $tempBuildRoot "work"
$specPath = Join-Path $tempBuildRoot "spec"
New-Item -ItemType Directory -Force -Path $workPath | Out-Null
New-Item -ItemType Directory -Force -Path $specPath | Out-Null
New-Item -ItemType Directory -Force -Path $DistPath | Out-Null

Write-Host "Building executable..."
py -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "XimeaCameraGUI" `
    --hidden-import "ximea" `
    --hidden-import "PIL._tkinter_finder" `
    --workpath "$workPath" `
    --specpath "$specPath" `
    --distpath "$DistPath" `
    @buildModeArgs `
    ximea_gui.py

Write-Host ""
Write-Host "Build completed."
if ($OneFile) {
    Write-Host "Executable: $DistPath\\XimeaCameraGUI.exe"
} else {
    Write-Host "Folder build: $DistPath\\XimeaCameraGUI\\"
}
Write-Host ""
Write-Host "Reminder: target PCs still need XIMEA drivers + XiAPI SDK installed."
