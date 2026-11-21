import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WHITE = (255, 255, 255)
APPLE_LINE = (229, 229, 234)
APPLE_INK = (29, 29, 31)
APPLE_SLATE = (134, 134, 139)

APPLE_BLUE = (0, 122, 255)       # #007AFF
APPLE_BLUE_LIGHT = (90, 200, 250) # #5AC8FA
APPLE_INDIGO = (88, 86, 214)     # #5856D6
APPLE_PURPLE = (175, 82, 222)    # #AF52DE
APPLE_TEAL = (48, 176, 199)      # #30B0C7
APPLE_MINT = (0, 199, 190)       # #00C7BE
APPLE_GREEN = (52, 199, 89)      # #34C759
APPLE_YELLOW = (255, 204, 0)     # #FFCC00
APPLE_ORANGE = (255, 149, 0)     # #FF9500
APPLE_RED = (255, 59, 48)        # #FF3B30

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_gradient_squircle(draw_target, bbox, r, color1, color2):
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / max(h - 1, 1)
        r_c = int(color1[0] + t * (color2[0] - color1[0]))
        g_c = int(color1[1] + t * (color2[1] - color1[1]))
        b_c = int(color1[2] + t * (color2[2] - color1[2]))
        gdraw.line([(0, y), (w, y)], fill=(r_c, g_c, b_c, 255))
    
    mask = Image.new("L", (w, h), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([0, 0, w, h], radius=r, fill=255)
    
    draw_target.paste(grad, (x0, y0), mask)

def make_pure_apple_icon(grad1, grad2, glyph_fn, out_path, size=1024):
    canvas = Image.new("RGBA", (2048, 2048), WHITE)
    
    # Large centered squircle: 1560x1560 on 2048x2048 canvas (leaves elegant white padding)
    x0, y0, x1, y1 = 244, 244, 1804, 1804
    radius = 360
    
    # Ambient Apple drop shadow
    shadow = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle([x0 + 10, y0 + 35, x1 + 10, y1 + 55], radius=radius, fill=(0, 0, 0, 36))
    shadow = shadow.filter(ImageFilter.GaussianBlur(45))
    canvas = Image.alpha_composite(canvas, shadow)
    
    # Draw gradient squircle
    draw_gradient_squircle(canvas, (x0, y0, x1, y1), radius, grad1, grad2)
    
    # Glass highlight rim
    cdraw = ImageDraw.Draw(canvas)
    cdraw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, 75), width=8)
    
    # Draw glyph
    glyph_fn(cdraw, (x0, y0, x1, y1))
    
    rgb = canvas.convert("RGB")
    final = rgb.resize((size, size), Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    final.save(out_path, "PNG", optimize=True)
    print(f"Saved pure square Apple icon: {out_path} ({size}x{size})")

# Glyphs scaled to fit 1560x1560 squircle
def glyph_kml(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # 2 prominent polygon parcels
    p1 = [(cx - 380, cy - 240), (cx + 120, cy - 360), (cx + 260, cy + 40), (cx - 160, cy + 180)]
    draw.polygon(p1, fill=(255, 255, 255, 80), outline=WHITE, width=20)
    p2 = [(cx - 100, cy - 60), (cx + 380, cy - 120), (cx + 320, cy + 320), (cx - 200, cy + 260)]
    draw.polygon(p2, fill=(255, 255, 255, 150), outline=WHITE, width=20)
    # Survey pins
    for px, py in [(cx - 380, cy - 240), (cx + 120, cy - 360), (cx + 380, cy - 120), (cx + 320, cy + 320), (cx - 200, cy + 260)]:
        draw.ellipse([px - 40, py - 40, px + 40, py + 40], fill=APPLE_YELLOW, outline=WHITE, width=12)

def glyph_grid(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    pts = [
        (cx - 360, cy - 320), (cx + 360, cy - 320),
        (cx + 360, cy - 100), (cx - 360, cy - 100),
        (cx - 360, cy + 120), (cx + 360, cy + 120),
        (cx + 360, cy + 340), (cx - 360, cy + 340)
    ]
    draw.line(pts, fill=WHITE, width=36)
    for px, py in pts:
        draw.ellipse([px - 45, py - 45, px + 45, py + 45], fill=APPLE_YELLOW, outline=WHITE, width=8)

def glyph_speed(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Speedometer gauge
    draw.arc([cx - 400, cy - 400, cx + 400, cy + 400], start=140, end=40, fill=WHITE, width=50)
    # Green safe zone mark
    draw.arc([cx - 400, cy - 400, cx + 400, cy + 400], start=210, end=290, fill=APPLE_YELLOW, width=50)
    # Needle
    draw.line([(cx, cy), (cx - 160, cy - 260)], fill=APPLE_YELLOW, width=32)
    draw.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=WHITE)
    # Camera aperture
    draw.ellipse([cx + 160, cy + 160, cx + 360, cy + 360], fill=APPLE_MINT, outline=WHITE, width=18)
    draw.ellipse([cx + 220, cy + 220, cx + 300, cy + 300], fill=WHITE)

def glyph_corridor(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    pts_c = [(cx - 340, cy + 360), (cx - 80, cy + 80), (cx + 120, cy - 60), (cx + 340, cy - 360)]
    draw.line(pts_c, fill=WHITE, width=42)
    # Left buffer
    draw.line([(p[0] - 140, p[1]) for p in pts_c], fill=(255, 255, 255, 140), width=18)
    # Right buffer
    draw.line([(p[0] + 200, p[1]) for p in pts_c], fill=(255, 255, 255, 140), width=18)
    # Waypoints
    for px, py in pts_c[1:3]:
        draw.ellipse([px - 35, py - 35, px + 35, py + 35], fill=APPLE_YELLOW, outline=WHITE, width=8)

def glyph_flash(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    bolt = [
        (cx + 60, cy - 440), (cx - 200, cy - 40), (cx + 40, cy - 40),
        (cx - 60, cy + 440), (cx + 220, cy + 40), (cx - 20, cy + 40)
    ]
    draw.polygon(bolt, fill=WHITE)
    # Inner accent
    draw.polygon([
        (cx + 50, cy - 380), (cx - 140, cy - 50), (cx + 10, cy - 50),
        (cx - 40, cy + 380), (cx + 160, cy + 50), (cx - 10, cy + 50)
    ], fill=(255, 255, 255, 200))

def glyph_fleet(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # 2 Remote devices
    draw.rounded_rectangle([cx - 420, cy - 260, cx - 100, cy + 260], radius=50, fill=WHITE)
    draw.rounded_rectangle([cx - 380, cy - 180, cx - 140, cy + 180], radius=25, fill=APPLE_INDIGO)
    
    draw.rounded_rectangle([cx + 100, cy - 260, cx + 420, cy + 260], radius=50, fill=WHITE)
    draw.rounded_rectangle([cx + 140, cy - 180, cx + 380, cy + 180], radius=25, fill=APPLE_BLUE)
    
    # Radio sync beam
    for r in [120, 180, 240]:
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=300, end=60, fill=APPLE_YELLOW, width=18)
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=120, end=240, fill=APPLE_YELLOW, width=18)

def glyph_offline(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Folded map
    p = [(cx - 380, cy - 260), (cx - 130, cy - 340), (cx + 130, cy - 260), (cx + 380, cy - 340),
         (cx + 380, cy + 280), (cx + 130, cy + 360), (cx - 130, cy + 280), (cx - 380, cy + 360)]
    draw.polygon(p, fill=WHITE)
    # Folds
    draw.line([(cx - 130, cy - 340), (cx - 130, cy + 280)], fill=(220, 220, 225), width=8)
    draw.line([(cx + 130, cy - 260), (cx + 130, cy + 360)], fill=(220, 220, 225), width=8)
    # Down arrow
    draw.line([(cx, cy - 120), (cx, cy + 140)], fill=APPLE_TEAL, width=38)
    draw.line([(cx - 80, cy + 60), (cx, cy + 140), (cx + 80, cy + 60)], fill=APPLE_TEAL, width=38)

def glyph_dem(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # 3D layered elevation terrain stack
    for dy in [-180, 0, 180]:
        draw.ellipse([cx - 360, cy + dy - 100, cx + 360, cy + dy + 100], fill=WHITE, outline=(255, 255, 255, 200), width=12)
    draw.ellipse([cx - 240, cy - 180 - 60, cx + 240, cy - 180 + 60], fill=APPLE_YELLOW)

def glyph_terrain(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    hill = [(cx - 400, cy + 320), (cx - 140, cy - 80), (cx + 80, cy + 90), (cx + 400, cy - 240)]
    draw.line(hill, fill=APPLE_YELLOW, width=38)
    path = [(p[0], p[1] - 180) for p in hill]
    draw.line(path, fill=WHITE, width=28)
    for p_m, p_f in zip(hill[1:3], path[1:3]):
        draw.line([p_m, p_f], fill=WHITE, width=10)

def glyph_split(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Battery icon divided into 3 pieces
    draw.rounded_rectangle([cx - 360, cy - 200, cx + 300, cy + 200], radius=50, fill=WHITE)
    draw.rounded_rectangle([cx + 300, cy - 80, cx + 360, cy + 80], radius=20, fill=WHITE)
    # Split cut lines
    draw.line([(cx - 120, cy - 200), (cx - 120, cy + 200)], fill=APPLE_BLUE, width=26)
    draw.line([(cx + 100, cy - 200), (cx + 100, cy + 200)], fill=APPLE_BLUE, width=26)

def glyph_orbit(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Vertical pillar
    draw.rounded_rectangle([cx - 70, cy - 380, cx + 70, cy + 380], radius=35, fill=WHITE)
    # Spiral rings
    draw.ellipse([cx - 320, cy - 240, cx + 320, cy - 60], outline=APPLE_YELLOW, width=28)
    draw.ellipse([cx - 350, cy - 70, cx + 350, cy + 110], outline=APPLE_YELLOW, width=28)
    draw.ellipse([cx - 380, cy + 100, cx + 380, cy + 280], outline=APPLE_YELLOW, width=28)

def glyph_resume(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Pause bars
    draw.line([(cx - 240, cy - 200), (cx - 240, cy + 200)], fill=WHITE, width=50)
    draw.line([(cx - 100, cy - 200), (cx - 100, cy + 200)], fill=WHITE, width=50)
    # Resume arrow
    draw.polygon([(cx + 60, cy - 220), (cx + 340, cy), (cx + 60, cy + 220)], fill=APPLE_YELLOW)

# Generate pure square icons (size 1024x1024)
features = [
    (APPLE_GREEN, APPLE_MINT, glyph_kml, "feat_kml_multi_boundaries.png"),
    (APPLE_BLUE, APPLE_BLUE_LIGHT, glyph_grid, "boustrophedon_grid.png"),
    (APPLE_GREEN, APPLE_TEAL, glyph_speed, "speed_clamping.png"),
    (APPLE_ORANGE, APPLE_YELLOW, glyph_corridor, "corridor_buffer.png"),
    (APPLE_YELLOW, APPLE_ORANGE, glyph_flash, "flash_inject.png"),
    (APPLE_INDIGO, APPLE_BLUE, glyph_fleet, "fleet_sync.png"),
    (APPLE_TEAL, APPLE_MINT, glyph_offline, "offline_maps.png"),
    (APPLE_PURPLE, APPLE_INDIGO, glyph_dem, "dem_server.png"),
    (APPLE_ORANGE, APPLE_RED, glyph_terrain, "follow_terrain.png"),
    (APPLE_BLUE, APPLE_INDIGO, glyph_split, "split_mission.png"),
    (APPLE_TEAL, APPLE_BLUE, glyph_orbit, "orbit_helix.png"),
    (APPLE_GREEN, APPLE_YELLOW, glyph_resume, "breakpoint_resume.png")
]

for g1, g2, fn, name in features:
    p = os.path.join("images/features", name)
    make_pure_apple_icon(g1, g2, fn, p, size=1024)
    # Also copy feat_kml_multi_boundaries to multi_area.png
    if name == "feat_kml_multi_boundaries.png":
        make_pure_apple_icon(g1, g2, fn, "images/features/multi_area.png", size=1024)

print("All 12 feature icons successfully generated as PURE SQUARE APPLE ICONS!")
