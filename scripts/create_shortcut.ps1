$desktop = [System.Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop "Vibe Người Tốt.lnk"
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)
$root = (Get-Item "$PSScriptRoot\..").FullName
$bat = Join-Path $root "CHAY_UNG_DUNG.bat"
$sc.TargetPath = "$env:ComSpec"
$sc.Arguments = "/c `"$bat`""
$sc.WorkingDirectory = "$root"
$sc.Description = "Vibe Người Tốt - Ứng dụng nhắn tin"
$ico = Join-Path $root "frontend\node_modules\electron\dist\electron.exe"
if (Test-Path $ico) {
    $sc.IconLocation = "$ico,0"
}
$sc.WindowStyle = 1
$sc.Save()
Write-Host "[OK] Da tao shortcut thanh cong tai: $shortcutPath"
