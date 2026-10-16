import os
import sys
import shutil
from PIL import Image

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

SRC_PATH = r"C:\Users\admin\.gemini\antigravity\brain\fe5c3103-bccb-4eff-9dfe-3ce54d50e8e9\.user_uploaded\media_1792131602386_c220e6d3.png"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(ROOT_DIR, "frontend", "public")
DIST_DIR = os.path.join(ROOT_DIR, "frontend", "dist")
ASSETS_DIR = os.path.join(ROOT_DIR, "frontend", "src", "assets")

os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(DIST_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# 1. Open original image
img = Image.open(SRC_PATH).convert("RGBA")
width, height = img.size

# 2. Crop top black line (first 6 pixels)
cropped_top = 6
cropped_bottom = height
crop_height = cropped_bottom - cropped_top

# Center crop to make square 500x500
crop_width = min(width, crop_height)
offset_x = (width - crop_width) // 2

square_img = img.crop((offset_x, cropped_top, offset_x + crop_width, cropped_top + crop_width))

# 3. Resize to 512x512 with high quality Lanczos filter
logo_512 = square_img.resize((512, 512), Image.Resampling.LANCZOS)

# 4. Save PNG logos
png_targets = [
    os.path.join(ROOT_DIR, "logo.png"),
    os.path.join(PUBLIC_DIR, "logo.png"),
    os.path.join(DIST_DIR, "logo.png"),
    os.path.join(ASSETS_DIR, "logo.png"),
]

for p in png_targets:
    logo_512.save(p, "PNG")
    print(f"[OK] Saved PNG: {p}")

# 5. Generate Multi-resolution Windows ICO
ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ico_targets = [
    os.path.join(ROOT_DIR, "app.ico"),
    os.path.join(PUBLIC_DIR, "favicon.ico"),
    os.path.join(PUBLIC_DIR, "app.ico"),
    os.path.join(DIST_DIR, "favicon.ico"),
]

for p in ico_targets:
    logo_512.save(p, format="ICO", sizes=ico_sizes)
    print(f"[OK] Saved ICO: {p}")

print("\n[SUCCESS] Logo and icon assets created successfully!")
