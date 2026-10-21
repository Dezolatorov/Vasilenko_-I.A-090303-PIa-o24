param(
    [string]$TitlePart = "каталог",
    [string]$Out = "C:\elkin\lab_11\screens\11-15-catalog.png"
)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class ShotPage {
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

[ShotPage]::SetProcessDPIAware() | Out-Null

Start-Process "http://127.0.0.1:5000/"
Start-Sleep -Seconds 8

$script:found = [IntPtr]::Zero
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    $callback = {
        param($hWnd, $lParam)
        if (-not [ShotPage]::IsWindowVisible($hWnd)) { return $true }
        $sb = New-Object System.Text.StringBuilder 512
        [ShotPage]::GetWindowText($hWnd, $sb, 512) | Out-Null
        if ($sb.ToString() -like "*$TitlePart*") { $script:found = $hWnd; return $false }
        return $true
    }
    [ShotPage]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
    if ($script:found -ne [IntPtr]::Zero) { break }
    Start-Sleep -Milliseconds 700
}

if ($script:found -eq [IntPtr]::Zero) { Write-Output "окно страницы не найдено"; exit 1 }

[ShotPage]::ShowWindow($script:found, 3) | Out-Null
[ShotPage]::SetForegroundWindow($script:found) | Out-Null
Start-Sleep -Milliseconds 2000

$rect = New-Object ShotPage+RECT
[ShotPage]::GetWindowRect($script:found, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "saved $Out ($w x $h)"
