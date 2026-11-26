param(
    [switch]$PreviewOnly,
    [string]$ScreenshotOut = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.Windows.Forms.Application]::EnableVisualStyles()
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

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
$script:cancelled = $false
$form.Add_FormClosing({
    if ($form.Tag -ne 0) { $script:cancelled = $true }
})

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

function Download-FileWithProgress([string[]]$urls, [string]$destPath, [int]$startPct, [int]$endPct) {
    foreach ($url in $urls) {
        if ($script:cancelled) { return $false }
        $req = $null
        $resp = $null
        $inStream = $null
        $outStream = $null
        try {
            $req = [System.Net.HttpWebRequest]::Create($url)
            $req.Timeout = 15000
            $req.ReadWriteTimeout = 15000
            $req.AllowAutoRedirect = $true
            $req.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            $resp = $req.GetResponse()
            $totalBytes = $resp.ContentLength
            $inStream = $resp.GetResponseStream()
            $outStream = [System.IO.File]::Create($destPath)
            $buffer = New-Object byte[] 65536
            $downloaded = [long]0
            $lastUiUpdate = [DateTime]::MinValue

            while (-not $script:cancelled) {
                $read = $inStream.Read($buffer, 0, $buffer.Length)
                if ($read -le 0) { break }
                $outStream.Write($buffer, 0, $read)
                $downloaded += $read

                $now = [DateTime]::Now
                if (($now - $lastUiUpdate).TotalMilliseconds -ge 100) {
                    $lastUiUpdate = $now
                    $mbDone = [math]::Round($downloaded / 1MB, 1)
                    if ($totalBytes -gt 0) {
                        $ratio = $downloaded / $totalBytes
                        $pct = $startPct + [int](($endPct - $startPct) * $ratio)
                        $mbTotal = [math]::Round($totalBytes / 1MB, 1)
                        Set-Progress $pct "Đang tải bộ chạy ứng dụng: $mbDone / $mbTotal MB"
                    } else {
                        Set-Progress $startPct "Đang tải bộ chạy ứng dụng: $mbDone MB..."
                    }
                }
            }
            $outStream.Close()
            $inStream.Close()
            $resp.Close()

            if ($script:cancelled) {
                if (Test-Path $destPath) { Remove-Item $destPath -Force -ErrorAction SilentlyContinue }
                return $false
            }
            if ((Test-Path $destPath) -and ((Get-Item $destPath).Length -gt 50000000)) {
                return $true
            }
        } catch {
            try { if ($outStream) { $outStream.Close() } } catch {}
            try { if ($inStream) { $inStream.Close() } } catch {}
            try { if ($resp) { $resp.Close() } } catch {}
            if (Test-Path $destPath) { Remove-Item $destPath -Force -ErrorAction SilentlyContinue }
        }
    }
    return $false
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
    $startTime = [DateTime]::Now
    $baseMsg = $statusMsg.TrimEnd('.')
    $tick = 0
    while (-not $proc.HasExited) {
        $tick++
        $elapsed = [int]([DateTime]::Now - $startTime).TotalSeconds
        $dots = "." * (($tick % 3) + 1)
        $liveMsg = "$baseMsg$dots ($($elapsed)s)"
        $span = $endPct - $startPct
        if ($span -gt 0 -and ($tick % 12 -eq 0)) {
            $nextPct = $script:currentPct + 1
            if ($nextPct -lt $endPct) {
                Set-Progress $nextPct $liveMsg
            } else {
                Set-Progress $script:currentPct $liveMsg
            }
        } elseif ($tick % 4 -eq 0) {
            Set-Progress $script:currentPct $liveMsg
        }
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 120
    }
    Set-Progress $endPct $statusMsg
    return $proc.ExitCode
}

$form.Add_Shown({
    $form.Activate()
    $form.TopMost = $false
    if ($PreviewOnly) {
        for ($i = 0; $i -le 68; $i += 4) {
            $msg = if ($i -lt 20) { "Đang kiểm tra bộ chạy ứng dụng..." }
                   elseif ($i -lt 55) { "Đang tải bộ chạy ứng dụng: 46.2 / 102.4 MB" }
                   else { "Đang giải nén bộ chạy ứng dụng..." }
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
        Set-Progress 5 "Đang kiểm tra dữ liệu ứng dụng..."
        $electronDist = Join-Path $frontendDir "node_modules\electron\dist"
        $electronExe = Join-Path $electronDist "electron.exe"

        if (-not (Test-Path $electronExe)) {
            $zipPath = Join-Path $env:TEMP "vibe_electron_33_2_0.zip"
            if (Test-Path $zipPath) { Remove-Item $zipPath -Force -ErrorAction SilentlyContinue }

            $urls = @(
                "https://npmmirror.com/mirrors/electron/33.2.0/electron-v33.2.0-win32-x64.zip",
                "https://github.com/electron/electron/releases/download/v33.2.0/electron-v33.2.0-win32-x64.zip"
            )

            Set-Progress 8 "Đang kết nối máy chủ tải ứng dụng..."
            $ok = Download-FileWithProgress $urls $zipPath 10 80
            if (-not $ok) {
                if (-not $script:cancelled) {
                    [System.Windows.Forms.MessageBox]::Show("Không thể tải bộ chạy ứng dụng. Vui lòng kiểm tra kết nối Internet và thử lại.", "Vibe Người Tốt", "OK", "Error") | Out-Null
                }
                $form.Tag = 1
                $form.Close()
                return
            }

            Set-Progress 82 "Đang giải nén bộ chạy ứng dụng..."
            if (Test-Path $electronDist) {
                Remove-Item $electronDist -Recurse -Force -ErrorAction SilentlyContinue
            }
            New-Item -ItemType Directory -Path $electronDist -Force | Out-Null
            [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $electronDist)
            if (Test-Path $zipPath) { Remove-Item $zipPath -Force -ErrorAction SilentlyContinue }
            Set-Progress 92 "Giải nén hoàn tất!"
        } else {
            Set-Progress 92 "Bộ chạy ứng dụng đã sẵn sàng!"
        }

        $distIndex = Join-Path $frontendDir "dist\index.html"
        $mainJs = Join-Path $frontendDir "dist-electron\main.js"
        if ((-not (Test-Path $distIndex)) -or (-not (Test-Path $mainJs))) {
            Run-HiddenWait "cmd.exe" "/c npm install --no-audit --no-fund && npm run build && npm run build:electron" $frontendDir 92 97 "Đang biên dịch mã nguồn..." | Out-Null
        }

        Set-Progress 97 "Đang tạo lối tắt Desktop..."
        $scPs = Join-Path $scriptDir "create_desktop_shortcut.ps1"
        if (Test-Path $scPs) {
            Run-HiddenWait "powershell.exe" "-NoProfile -ExecutionPolicy Bypass -File `"$scPs`"" $rootDir 97 100 "Hoàn tất! Đang mở Vibe Người Tốt..." | Out-Null
        } else {
            Set-Progress 100 "Hoàn tất! Đang mở Vibe Người Tốt..."
        }
        Start-Sleep -Milliseconds 250
        $form.Tag = 0
        $form.Close()
    } catch {
        [System.Windows.Forms.MessageBox]::Show("Có lỗi xảy ra khi thiết lập lần đầu: $($_.Exception.Message)", "Vibe Người Tốt", "OK", "Error") | Out-Null
        $form.Tag = 1
        $form.Close()
    }
})

[void]$form.ShowDialog()
if ($form.Tag -eq 1 -or $script:cancelled) { exit 1 }
exit 0
