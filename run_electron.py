import os
import subprocess
import sys

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    dist_exe = os.path.join(root, "frontend", "dist-package", "Telegram Style Messenger 1.0.0.exe")
    unpacked_exe = os.path.join(root, "frontend", "dist-package", "win-unpacked", "Telegram Style Messenger.exe")

    if os.path.exists(dist_exe):
        print(f"[+] Khoi chay Telegram Desktop Portable: {dist_exe}")
        subprocess.Popen([dist_exe], cwd=root)
    elif os.path.exists(unpacked_exe):
        print(f"[+] Khoi chay Telegram Desktop Unpacked: {unpacked_exe}")
        subprocess.Popen([unpacked_exe], cwd=root)
    else:
        print("[*] Dang khoi chay Electron tu source code...")
        subprocess.run(["npx", "electron", "."], cwd=os.path.join(root, "frontend"), shell=True)

if __name__ == "__main__":
    main()

