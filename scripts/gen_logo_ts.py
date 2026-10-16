import base64

def generate_logo_ts():
    with open('frontend/public/logo.png', 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('utf-8')
    with open('frontend/src/assets/logo.ts', 'w', encoding='utf-8') as f:
        f.write(f'export const APP_LOGO = "data:image/png;base64,{b64}";\nexport default APP_LOGO;\n')
    print(f"Generated logo.ts successfully, length={len(b64)}")

if __name__ == '__main__':
    generate_logo_ts()
