import os
import sys
import subprocess

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PS_HELPER_PATH = os.path.join(os.path.dirname(__file__), "_create_sc.ps1")

PS_CODE = r'''
param(
    [string]$shortcutPath,
    [string]$targetPath,
    [string]$arguments,
    [string]$workingDir,
    [string]$iconPath,
    [string]$description,
    [int]$showCmd = 1
)

$code = @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;

[ComImport]
[Guid("00021401-0000-0000-C000-000000000046")]
public class ShellLink { }

[ComImport]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
[Guid("000214F9-0000-0000-C000-000000000046")]
public interface IShellLinkW {
    void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszFile, int cchMaxPath, out IntPtr pfd, int fFlags);
    void GetIDList(out IntPtr ppidl);
    void SetIDList(IntPtr pidl);
    void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszName, int cchMaxName);
    void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszDir, int cchMaxPath);
    void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string pszDir);
    void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszArgs, int cchMaxPath);
    void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string pszArgs);
    void GetHotkey(out short pwHotkey);
    void SetHotkey(short wHotkey);
    void GetShowCmd(out int piShowCmd);
    void SetShowCmd(int iShowCmd);
    void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszIconPath, int cchIconPath, out int piIcon);
    void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string pszIconPath, int iIcon);
    void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string pszPathRel, int dwReserved);
    void Resolve(IntPtr hwnd, int fFlags);
    void SetPath([MarshalAs(UnmanagedType.LPWStr)] string pszFile);
}

public class ShellUtil {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);

    public static void CreateShortcut(string shortcutPath, string targetPath, string arguments, string workingDir, string iconPath, string description, int showCmd) {
        IShellLinkW link = (IShellLinkW)new ShellLink();
        link.SetPath(targetPath);
        if (!string.IsNullOrEmpty(arguments)) {
            link.SetArguments(arguments);
        }
        if (!string.IsNullOrEmpty(workingDir)) {
            link.SetWorkingDirectory(workingDir);
        }
        if (!string.IsNullOrEmpty(iconPath)) {
            link.SetIconLocation(iconPath, 0);
        }
        if (!string.IsNullOrEmpty(description)) {
            link.SetDescription(description);
        }
        link.SetShowCmd(showCmd);
        IPersistFile file = (IPersistFile)link;
        file.Save(shortcutPath, true);
        SHChangeNotify(0x08000000, 0x0000, IntPtr.Zero, IntPtr.Zero);
    }
}
'@

Add-Type -TypeDefinition $code -Language CSharp

[ShellUtil]::CreateShortcut($shortcutPath, $targetPath, $arguments, $workingDir, $iconPath, $description, $showCmd)
Write-Output "SUCCESS: Created $shortcutPath"
'''

def write_ps_helper():
    with open(PS_HELPER_PATH, "w", encoding="utf-8-sig") as f:
        f.write(PS_CODE)

def make_shortcut(shortcut_path, target_path, arguments="", working_dir="", icon_path="", description="", show_cmd=1):
    write_ps_helper()
    try:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
    except Exception:
        pass

    args = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", PS_HELPER_PATH,
        "-shortcutPath", shortcut_path,
        "-targetPath", target_path,
        "-arguments", arguments,
        "-workingDir", working_dir,
        "-iconPath", icon_path,
        "-description", description,
        "-showCmd", str(show_cmd)
    ]
    res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    return os.path.exists(shortcut_path)

def create_desktop_shortcut(force=False):
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    if not os.path.exists(desktop):
        return False

    final_path = os.path.join(desktop, "Vibe Người Tốt.lnk")
    if os.path.exists(final_path) and not force:
        # Check size to ensure not corrupted (corrupt shortcuts are < 500 bytes or empty)
        if os.path.getsize(final_path) > 500:
            return True

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bat_path = os.path.join(root, "CHAY_UNG_DUNG.bat")
    ico_path = os.path.join(root, "app.ico")

    return make_shortcut(
        shortcut_path=final_path,
        target_path=bat_path,
        arguments="",
        working_dir=root,
        icon_path=ico_path,
        description="Vibe Người Tốt - Ứng dụng nhắn tin bảo mật",
        show_cmd=1
    )

if __name__ == "__main__":
    ok = create_desktop_shortcut(force=True)
    if ok:
        print("[OK] Đã tạo thành công lối tắt ngoài Desktop: Vibe Người Tốt.lnk với Icon Shin-chan chuẩn xác.")
    else:
        print("[-] Không thể tạo lối tắt ngoài Desktop.")
