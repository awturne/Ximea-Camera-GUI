param(
    [switch]$OneFile = $true,
    [switch]$InstallBuildDeps = $true
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

Write-Host "Building executable..."
py -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "XimeaCameraGUI" `
    --hidden-import "ximea" `
    --hidden-import "PIL._tkinter_finder" `
    @buildModeArgs `
    ximea_gui.py

Write-Host ""
Write-Host "Build completed."
if ($OneFile) {
    Write-Host "Executable: dist\\XimeaCameraGUI.exe"
} else {
    Write-Host "Folder build: dist\\XimeaCameraGUI\\"
}
Write-Host ""
Write-Host "Reminder: target PCs still need XIMEA drivers + XiAPI SDK installed."
