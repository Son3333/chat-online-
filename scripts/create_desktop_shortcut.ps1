$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$scPath = Join-Path $desktop "Vibe Nguoi Tot.lnk"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$vbsPath = Join-Path $scriptDir "launch_silent.vbs"
$icoPath = Join-Path $rootDir "app.ico"

$sc = $ws.CreateShortcut($scPath)
$sc.TargetPath = "$env:SystemRoot\System32\wscript.exe"
$sc.Arguments = "`"$vbsPath`""
$sc.WorkingDirectory = $rootDir
if (Test-Path $icoPath) {
    $sc.IconLocation = "$icoPath,0"
}
$sc.Description = "Vibe Người Tốt - Ứng dụng nhắn tin và truyền thông tin"
$sc.WindowStyle = 1
$sc.Save()

Write-Output "[OK] Da tao shortcut Desktop chay ngam thanh cong: $scPath"
