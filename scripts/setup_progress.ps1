param(
    [switch]$PreviewOnly,
    [string]$ScreenshotOut = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

Add-Type -Name WinConsole -Namespace Native -MemberDefinition @"
[DllImport("kernel32.dll")]
public static extern IntPtr GetConsoleWindow();
[DllImport("user32.dll")]
public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
"@
$consoleHwnd = [Native.WinConsole]::GetConsoleWindow()
if ($consoleHwnd -ne [IntPtr]::Zero) {
    [Native.WinConsole]::ShowWindow($consoleHwnd, 0) | Out-Null
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $rootDir "frontend"
$icoPath = Join-Path $rootDir "app.ico"

$form = New-Object System.Windows.Forms.Form
$form.Text = "Vibe Người Tốt - Thiết lập lần đầu"
$form.Size = New-Object System.Drawing.Size(480, 230)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.WindowState = [System.Windows.Forms.FormWindowState]::Normal
$form.ShowInTaskbar = $true
$form.TopMost = $true
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.BackColor = [System.Drawing.ColorTranslator]::FromHtml("#0e1621")
$form.ForeColor = [System.Drawing.Color]::White
if (Test-Path $icoPath) {
    try { $form.Icon = New-Object System.Drawing.Icon($icoPath) } catch {}
}

$card = New-Object System.Windows.Forms.Panel
$card.Location = New-Object System.Drawing.Point(16, 16)
$card.Size = New-Object System.Drawing.Size(432, 160)
$card.BackColor = [System.Drawing.ColorTranslator]::FromHtml("#17212b")
$form.Controls.Add($card)

$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "Vibe Người Tốt"
$lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$lblTitle.ForeColor = [System.Drawing.Color]::White
$lblTitle.Location = New-Object System.Drawing.Point(20, 18)
$lblTitle.Size = New-Object System.Drawing.Size(300, 28)
$card.Controls.Add($lblTitle)

$lblPercent = New-Object System.Windows.Forms.Label
$lblPercent.Text = "0%"
$lblPercent.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$lblPercent.ForeColor = [System.Drawing.ColorTranslator]::FromHtml("#38bdf8")
$lblPercent.Location = New-Object System.Drawing.Point(340, 19)
$lblPercent.Size = New-Object System.Drawing.Size(72, 26)
$lblPercent.TextAlign = "TopRight"
$card.Controls.Add($lblPercent)

$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Text = "Đang chuẩn bị môi trường cho lần khởi chạy đầu tiên..."
$lblStatus.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$lblStatus.ForeColor = [System.Drawing.ColorTranslator]::FromHtml("#94a3b8")
$lblStatus.Location = New-Object System.Drawing.Point(20, 52)
$lblStatus.Size = New-Object System.Drawing.Size(392, 24)
$card.Controls.Add($lblStatus)

$barBg = New-Object System.Windows.Forms.Panel
$barBg.Location = New-Object System.Drawing.Point(20, 88)
$barBg.Size = New-Object System.Drawing.Size(392, 14)
$barBg.BackColor = [System.Drawing.ColorTranslator]::FromHtml("#242f3d")
$card.Controls.Add($barBg)

$barFill = New-Object System.Windows.Forms.Panel
$barFill.Location = New-Object System.Drawing.Point(0, 0)
$barFill.Size = New-Object System.Drawing.Size(0, 14)
$barFill.BackColor = [System.Drawing.ColorTranslator]::FromHtml("#2481cc")
$barBg.Controls.Add($barFill)

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Quá trình này chỉ diễn ra một lần duy nhất trên thiết bị mới."
$lblSub.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
$lblSub.ForeColor = [System.Drawing.ColorTranslator]::FromHtml("#64748b")
$lblSub.Location = New-Object System.Drawing.Point(20, 116)
$lblSub.Size = New-Object System.Drawing.Size(392, 22)
$card.Controls.Add($lblSub)

$script:currentPct = 0
function Set-Progress([int]$pct, [string]$statusText) {
    if ($pct -lt 0) { $pct = 0 }
    if ($pct -gt 100) { $pct = 100 }
    $script:currentPct = $pct
    $lblPercent.Text = "$pct%"
    if ($statusText) { $lblStatus.Text = $statusText }
    $w = [int](392 * $pct / 100)
    $barFill.Size = New-Object System.Drawing.Size($w, 14)
    [System.Windows.Forms.Application]::DoEvents()
}

function Run-HiddenWait([string]$filePath, [string]$args, [string]$workDir, [int]$startPct, [int]$endPct, [string]$statusMsg) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $filePath
    $psi.Arguments = $args
    $psi.WorkingDirectory = $workDir
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $psi.CreateNoWindow = $true
    $psi.UseShellExecute = $false
    $proc = [System.Diagnostics.Process]::Start($psi)
    $tick = 0
    while (-not $proc.HasExited) {
        $tick++
        $span = $endPct - $startPct
        if ($span -gt 0 -and ($tick % 5 -eq 0)) {
            $nextPct = $script:currentPct + 1
            if ($nextPct -lt $endPct) {
                Set-Progress $nextPct $statusMsg
            }
        }
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 120
    }
    Set-Progress $endPct $statusMsg
    return $proc.ExitCode
}

function Find-PythonCmd {
    foreach ($cmd in @("python", "py")) {
        try {
            $p = Start-Process -FilePath $cmd -ArgumentList "--version" -WindowStyle Hidden -PassThru -Wait -ErrorAction Stop
            if ($p.ExitCode -eq 0) { return $cmd }
        } catch {}
    }
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:ProgramFiles\Python314\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python310\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

$form.Add_Shown({
    $form.Activate()
    $form.TopMost = $false
    if ($PreviewOnly) {
        for ($i = 0; $i -le 68; $i += 4) {
            $msg = if ($i -lt 20) { "Đang kiểm tra môi trường hệ thống..." }
                   elseif ($i -lt 55) { "Đang tải và cài đặt thành phần ứng dụng..." }
                   else { "Đang hoàn tất thiết lập giao diện..." }
            Set-Progress $i $msg
            Start-Sleep -Milliseconds 35
        }
        if ($ScreenshotOut -ne "") {
            Start-Sleep -Milliseconds 150
            $bmp = New-Object System.Drawing.Bitmap($form.Width, $form.Height)
            $form.DrawToBitmap($bmp, (New-Object System.Drawing.Rectangle(0, 0, $form.Width, $form.Height)))
            $bmp.Save($ScreenshotOut, [System.Drawing.Imaging.ImageFormat]::Png)
            $bmp.Dispose()
        }
        $form.Tag = 0
        $form.Close()
        return
    }

    try {
        Set-Progress 5 "Đang kiểm tra nền tảng xử lý..."
        $pyCmd = Find-PythonCmd
        if (-not $pyCmd) {
            [System.Windows.Forms.MessageBox]::Show("Thiết bị chưa cài đặt Python 3.10+. Vui lòng cài Python (tích chọn Add Python to PATH) rồi mở lại ứng dụng.", "Vibe Người Tốt", "OK", "Warning") | Out-Null
            $form.Tag = 1
            $form.Close()
            return
        }

        Set-Progress 12 "Đang kiểm tra thành phần bảo mật..."
        $pBcrypt = Start-Process -FilePath $pyCmd -ArgumentList "-c `"import bcrypt, requests`"" -WindowStyle Hidden -PassThru -Wait
        if ($pBcrypt.ExitCode -ne 0) {
            Run-HiddenWait $pyCmd "-m pip install bcrypt requests" $rootDir 12 22 "Đang cài đặt thành phần bảo mật..." | Out-Null
        } else {
            Set-Progress 22 "Thành phần bảo mật đã sẵn sàng..."
        }

        Set-Progress 25 "Đang kiểm tra môi trường giao diện..."
        foreach ($np in @(
            "C:\Users\admin\tools\node-v20.18.0-win-x64",
            "$env:LOCALAPPDATA\Programs\nodejs",
            "$env:ProgramFiles\nodejs",
            "C:\Program Files (x86)\nodejs"
        )) {
            if (Test-Path (Join-Path $np "node.exe")) {
                $env:PATH = "$np;$env:PATH"
            }
        }
        $hasNode = $false
        try {
            $pn = Start-Process -FilePath "node" -ArgumentList "-v" -WindowStyle Hidden -PassThru -Wait -ErrorAction Stop
            if ($pn.ExitCode -eq 0) { $hasNode = $true }
        } catch {}

        if (-not $hasNode) {
            [System.Windows.Forms.MessageBox]::Show("Thiết bị chưa cài đặt Node.js LTS (v20/v22). Vui lòng cài đặt từ https://nodejs.org/ rồi mở lại ứng dụng.", "Vibe Người Tốt", "OK", "Warning") | Out-Null
            $form.Tag = 1
            $form.Close()
            return
        }

        $electronExe = Join-Path $frontendDir "node_modules\electron\dist\electron.exe"
        if (-not (Test-Path $electronExe)) {
            $rc = Run-HiddenWait "cmd.exe" "/c npm install" $frontendDir 30 75 "Đang tải và cài đặt các gói giao diện..."
            if ($rc -ne 0) {
                [System.Windows.Forms.MessageBox]::Show("Cài đặt gói giao diện thất bại. Vui lòng kiểm tra kết nối mạng và thử lại.", "Vibe Người Tốt", "OK", "Error") | Out-Null
                $form.Tag = 1
                $form.Close()
                return
            }
        } else {
            Set-Progress 75 "Các gói giao diện đã sẵn sàng..."
        }

        $distIndex = Join-Path $frontendDir "dist\index.html"
        if (-not (Test-Path $distIndex)) {
            Run-HiddenWait "cmd.exe" "/c npm run build" $frontendDir 75 86 "Đang tối ưu hóa giao diện ứng dụng..." | Out-Null
        } else {
            Set-Progress 86 "Giao diện ứng dụng đã sẵn sàng..."
        }

        $mainJs = Join-Path $frontendDir "dist-electron\main.js"
        if (-not (Test-Path $mainJs)) {
            Run-HiddenWait "cmd.exe" "/c npm run build:electron" $frontendDir 86 94 "Đang hoàn tất cấu hình ứng dụng..." | Out-Null
        } else {
            Set-Progress 94 "Cấu hình ứng dụng đã sẵn sàng..."
        }

        Set-Progress 96 "Đang hoàn tất thiết lập và tạo lối tắt..."
        $scPs = Join-Path $scriptDir "create_desktop_shortcut.ps1"
        if (Test-Path $scPs) {
            Run-HiddenWait "powershell.exe" "-NoProfile -ExecutionPolicy Bypass -File `"$scPs`"" $rootDir 96 100 "Hoàn tất! Đang mở Vibe Người Tốt..." | Out-Null
        } else {
            Set-Progress 100 "Hoàn tất! Đang mở Vibe Người Tốt..."
        }
        Start-Sleep -Milliseconds 300
        $form.Tag = 0
        $form.Close()
    } catch {
        [System.Windows.Forms.MessageBox]::Show("Có lỗi xảy ra khi thiết lập lần đầu: $($_.Exception.Message)", "Vibe Người Tốt", "OK", "Error") | Out-Null
        $form.Tag = 1
        $form.Close()
    }
})

[void]$form.ShowDialog()
if ($form.Tag -eq 1) { exit 1 }
exit 0
