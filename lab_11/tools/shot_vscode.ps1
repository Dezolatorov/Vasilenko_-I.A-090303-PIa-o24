Add-Type -AssemblyName System.Windows.Forms, System.Drawing

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class ShotNow {
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

[ShotNow]::SetProcessDPIAware() | Out-Null

$script:found = [IntPtr]::Zero
$callback = {
    param($hWnd, $lParam)
    if (-not [ShotNow]::IsWindowVisible($hWnd)) { return $true }
    $sb = New-Object System.Text.StringBuilder 512
    [ShotNow]::GetWindowText($hWnd, $sb, 512) | Out-Null
    if ($sb.ToString() -like "*lab_11 - Visual Studio Code*") { $script:found = $hWnd; return $false }
    return $true
}
[ShotNow]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null

if ($script:found -eq [IntPtr]::Zero) { Write-Output "окно VS Code не найдено"; exit 1 }

[ShotNow]::ShowWindow($script:found, 3) | Out-Null
[ShotNow]::SetForegroundWindow($script:found) | Out-Null
Start-Sleep -Milliseconds 1500

$rect = New-Object ShotNow+RECT
[ShotNow]::GetWindowRect($script:found, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
$out = "C:\elkin\lab_11\screens\11-14-vscode.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "saved $out ($w x $h)"
