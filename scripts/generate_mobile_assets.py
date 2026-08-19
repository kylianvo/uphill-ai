import os
from PIL import Image, ImageDraw

def create_brand_assets():
    assets_dir = os.path.abspath("frontend/assets")
    os.makedirs(assets_dir, exist_ok=True)

    BG_COLOR = (13, 12, 13, 255) # #0d0c0d
    ACCENT_COLOR = (25, 206, 139, 255) # #19ce8b

    # 1. Generate 1024x1024 Icon
    icon_size = 1024
    scale = icon_size / 256.0
    stroke_w = int(20 * scale)

    icon_img = Image.new("RGBA", (icon_size, icon_size), BG_COLOR)
    draw = ImageDraw.Draw(icon_img)

    # Translate (50, 60) scaled
    tx = 50 * scale
    ty = 60 * scale

    def pt(x, y):
        return (tx + x * scale, ty + y * scale)

    # Polyline 1: (156, 8) -> (76, 108) -> (46, 68) -> (8, 116)
    p1 = [pt(156, 8), pt(76, 108), pt(46, 68), pt(8, 116)]
    draw.line(p1, fill=ACCENT_COLOR, width=stroke_w, joint="round")
    for p in p1:
        draw.ellipse([p[0] - stroke_w/2, p[1] - stroke_w/2, p[0] + stroke_w/2, p[1] + stroke_w/2], fill=ACCENT_COLOR)

    # Polyline 2: (108, 8) -> (156, 8) -> (156, 56)
    p2 = [pt(108, 8), pt(156, 8), pt(156, 56)]
    draw.line(p2, fill=ACCENT_COLOR, width=stroke_w, joint="round")
    for p in p2:
        draw.ellipse([p[0] - stroke_w/2, p[1] - stroke_w/2, p[0] + stroke_w/2, p[1] + stroke_w/2], fill=ACCENT_COLOR)

    icon_path = os.path.join(assets_dir, "logo.png")
    icon_only_path = os.path.join(assets_dir, "icon-only.png")
    icon_fg_path = os.path.join(assets_dir, "icon-foreground.png")
    icon_img.save(icon_path, "PNG")
    icon_img.save(icon_only_path, "PNG")
    icon_img.save(icon_fg_path, "PNG")

    # Icon background
    bg_img = Image.new("RGBA", (icon_size, icon_size), BG_COLOR)
    bg_img.save(os.path.join(assets_dir, "icon-background.png"), "PNG")

    # 2. Generate 2732x2732 Splash Screen
    splash_size = 2732
    splash_img = Image.new("RGBA", (splash_size, splash_size), BG_COLOR)
    
    # Place a 512x512 centered logo in splash
    logo_splash = icon_img.resize((600, 600), Image.Resampling.LANCZOS)
    offset = ((splash_size - 600) // 2, (splash_size - 600) // 2)
    splash_img.paste(logo_splash, offset, logo_splash)

    splash_path = os.path.join(assets_dir, "splash.png")
    splash_dark_path = os.path.join(assets_dir, "splash-dark.png")
    splash_img.save(splash_path, "PNG")
    splash_img.save(splash_dark_path, "PNG")

    print(f"Successfully generated brand assets in {assets_dir}")

if __name__ == "__main__":
    create_brand_assets()
