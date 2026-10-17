$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$scPath = Join-Path $desktop "Vibe Nguoi Tot.lnk"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$batPath = Join-Path $rootDir "CHAY_UNG_DUNG.bat"
$icoPath = Join-Path $rootDir "app.ico"

# Sử dụng cmd.exe /c để tương thích 100% với đường dẫn Unicode tiếng Việt
$sc = $ws.CreateShortcut($scPath)
$sc.TargetPath = "$env:SystemRoot\System32\cmd.exe"
$sc.Arguments = "/c `"`"$batPath`"`""
$sc.WorkingDirectory = $rootDir
if (Test-Path $icoPath) {
    $sc.IconLocation = "$icoPath,0"
}
$sc.Description = "Vibe Người Tốt - Ứng dụng nhắn tin và truyền thông tin"
$sc.WindowStyle = 7 # Minimized khi khởi động để không nhấp nháy cửa sổ đen
$sc.Save()

Write-Output "[OK] Da tao shortcut Desktop thanh cong: $scPath"
