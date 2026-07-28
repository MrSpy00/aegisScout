import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def create_aegis_logo(size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    scale = size / 512.0
    rx = int(120 * scale)
    margin = int(16 * scale)
    
    for i in range(size - 2 * margin):
        ratio = i / float(size - 2 * margin)
        r = int(15 * (1 - ratio) + 30 * ratio)
        g = int(23 * (1 - ratio) + 27 * ratio)
        b = int(42 * (1 - ratio) + 75 * ratio)
        y = margin + i
        draw.line([(margin, y), (size - margin, y)], fill=(r, g, b, 255))
        
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=rx, fill=255)
    
    bg_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_img.paste(img, (0, 0), mask=mask)
    
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    
    pts = [
        (20 * 12.8, 9 * 12.8),
        (10 * 12.8, 13.5 * 12.8),
        (10 * 12.8, 20.5 * 12.8),
        (20 * 12.8, 33.5 * 12.8),
        (30 * 12.8, 20.5 * 12.8),
        (30 * 12.8, 13.5 * 12.8),
    ]
    
    stroke_w = int(24 * scale)
    odraw.polygon(pts, outline=(99, 102, 241, 255), width=stroke_w)
    
    glow = overlay.filter(ImageFilter.GaussianBlur(radius=int(10 * scale)))
    
    cx, cy = int(256 * scale), int(256 * scale)
    orb_r = int(48 * scale)
    odraw.ellipse([cx - orb_r, cy - orb_r, cx + orb_r, cy + orb_r], fill=(129, 140, 248, 255))
    
    final_img = Image.alpha_composite(bg_img, glow)
    final_img = Image.alpha_composite(final_img, overlay)
    return final_img

if __name__ == "__main__":
    assets_dir = Path(__file__).parent.parent / "src" / "aegisScout" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    logo_512 = create_aegis_logo(512)
    png_path = assets_dir / "logo.png"
    ico_path = assets_dir / "logo.ico"
    
    logo_512.save(png_path, format="PNG")
    print(f"[OK] Saved {png_path}")
    
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    logo_512.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"[OK] Saved {ico_path}")
