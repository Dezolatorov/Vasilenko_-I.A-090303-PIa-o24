param(
    [Parameter(Mandatory = $true)][string]$Title,
    [Parameter(Mandatory = $true)][string]$PayloadFile,
    [Parameter(Mandatory = $true)][string]$Out,
    [int]$WaitMs = 6000,
    [int]$Cols = 140,
    [int]$Rows = 42
)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class WinShot3 {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int max);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
"@

[WinShot3]::SetProcessDPIAware() | Out-Null

$marker = "SHOT-" + [Guid]::NewGuid().ToString("N").Substring(0, 8)
$payloadPath = Join-Path $env:TEMP ("shot-payload-" + $marker + ".ps1")
Copy-Item -LiteralPath $PayloadFile -Destination $payloadPath -Force

$inner = "chcp 65001>nul & mode con: cols=$Cols lines=$Rows & title $marker $Title & powershell -NoProfile -ExecutionPolicy Bypass -File `"$payloadPath`" & echo. & echo [выполнено]"
$proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $inner -PassThru -WindowStyle Normal

function Find-ByMarker([string]$needle) {
    $script:found = [IntPtr]::Zero
    $callback = {
        param($hWnd, $lParam)
        if ($script:found -ne [IntPtr]::Zero) { return $true }
        if (-not [WinShot3]::IsWindowVisible($hWnd)) { return $true }
        $sb = New-Object System.Text.StringBuilder 512
        [WinShot3]::GetWindowText($hWnd, $sb, 512) | Out-Null
        if ($sb.ToString().StartsWith($needle)) { $script:found = $hWnd }
        return $true
    }
    [WinShot3]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
    return $script:found
}

$handle = [IntPtr]::Zero
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 300
    $handle = Find-ByMarker $marker
    if ($handle -ne [IntPtr]::Zero) { break }
}

if ($handle -eq [IntPtr]::Zero) {
    Write-Output "window not found: $Title"
    & taskkill /PID $proc.Id /T /F | Out-Null
    exit 1
}

Start-Sleep -Milliseconds $WaitMs
[WinShot3]::ShowWindow($handle, 5) | Out-Null
[WinShot3]::SetForegroundWindow($handle) | Out-Null
Start-Sleep -Milliseconds 1200

$rect = New-Object WinShot3+RECT
[WinShot3]::GetWindowRect($handle, [ref]$rect) | Out-Null
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top

$bmp = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bmp.Dispose()

& taskkill /PID $proc.Id /T /F | Out-Null
Remove-Item -LiteralPath $payloadPath -Force -ErrorAction SilentlyContinue
Write-Output "saved $Out ($width x $height)"
