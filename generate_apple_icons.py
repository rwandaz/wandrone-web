import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WHITE = (255, 255, 255)
BG_CARD = (245, 245, 247)
APPLE_LINE = (229, 229, 234)
APPLE_LINE_DARK = (210, 210, 215)
APPLE_INK = (29, 29, 31)
APPLE_SLATE = (134, 134, 139)
APPLE_LIGHT_SLATE = (200, 200, 205)

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
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_gradient_squircle(draw_target, bbox, r, color1, color2):
    # Draw vertical linear gradient within squircle
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
    
    # Mask
    mask = Image.new("L", (w, h), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([0, 0, w, h], radius=r, fill=255)
    
    draw_target.paste(grad, (x0, y0), mask)

def make_apple_icon(grad1, grad2, glyph_fn, out_path, badge_text=""):
    canvas = Image.new("RGBA", (2048, 2048), WHITE)
    
    # Squircle bounding box: 1400x1400 centered
    x0, y0, x1, y1 = 324, 324, 1724, 1724
    radius = 320
    
    # Soft drop shadow
    shadow = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle([x0 + 10, y0 + 30, x1 + 10, y1 + 50], radius=radius, fill=(0, 0, 0, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(40))
    canvas = Image.alpha_composite(canvas, shadow)
    
    # Draw gradient squircle
    draw_gradient_squircle(canvas, (x0, y0, x1, y1), radius, grad1, grad2)
    
    # Inner border for Apple glass rim
    cdraw = ImageDraw.Draw(canvas)
    cdraw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, 60), width=6)
    
    # Draw custom glyph
    glyph_fn(cdraw, (x0, y0, x1, y1))
    
    if badge_text:
        # Subtle badge inside or below
        font = get_font(FONT_BOLD, 52)
        bbox = cdraw.textbbox((0, 0), badge_text, font=font)
        bw = bbox[2] - bbox[0]
        bx = 1024 - bw // 2
        by = y1 - 120
        cdraw.rounded_rectangle([bx - 36, by - 16, bx + bw + 36, by + 68], radius=24, fill=(0, 0, 0, 90))
        cdraw.text((bx, by), badge_text, font=font, fill=WHITE)
        
    rgb = canvas.convert("RGB")
    final = rgb.resize((1024, 1024), Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    final.save(out_path, "PNG", optimize=True)
    print(f"Generated Apple license icon: {out_path}")

# Glyph for Hobby Edition: Drone + Mapping Compass
def glyph_hobby(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2 - 30
    
    # Mapping grid compass ring
    r_ring = 360
    draw.ellipse([cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring], outline=(255, 255, 255, 90), width=8)
    draw.ellipse([cx - r_ring + 60, cy - r_ring + 60, cx + r_ring - 60, cy + r_ring - 60], outline=(255, 255, 255, 50), width=4)
    # Crosshairs
    draw.line([(cx - r_ring - 40, cy), (cx + r_ring + 40, cy)], fill=(255, 255, 255, 100), width=6)
    draw.line([(cx, cy - r_ring - 40), (cx, cy + r_ring + 40)], fill=(255, 255, 255, 100), width=6)
    
    # 4 Drone Rotors
    arm_len = 220
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        mx = cx + dx * arm_len
        my = cy + dy * arm_len
        # arm
        draw.line([(cx, cy), (mx, my)], fill=WHITE, width=22)
        # motor pod
        draw.ellipse([mx - 50, my - 50, mx + 50, my + 50], fill=WHITE)
        draw.ellipse([mx - 32, my - 32, mx + 32, my + 32], fill=APPLE_BLUE)
        # spinning blade ring
        draw.ellipse([mx - 90, my - 90, mx + 90, my + 90], outline=(255, 255, 255, 180), width=8)
        
    # Central Drone Fuselage
    draw.rounded_rectangle([cx - 85, cy - 110, cx + 85, cy + 110], radius=50, fill=WHITE)
    # Camera Gimbal lens
    draw.ellipse([cx - 45, cy - 80, cx + 45, cy + 10], fill=(20, 20, 25))
    draw.ellipse([cx - 30, cy - 65, cx + 30, cy - 5], fill=APPLE_MINT)
    draw.ellipse([cx - 14, cy - 49, cx + 14, cy - 21], fill=(255, 255, 255, 220))

# Glyph for Pro Edition: 3D Mountain Terrain + Diamond Crown + Drone
def glyph_pro(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2 - 20
    
    # 3D Mountain Contour Ridges
    contour_pts1 = [(cx - 420, cy + 280), (cx - 200, cy + 80), (cx, cy + 160), (cx + 240, cy + 30), (cx + 420, cy + 280)]
    contour_pts2 = [(cx - 380, cy + 340), (cx - 180, cy + 170), (cx + 20, cy + 240), (cx + 220, cy + 130), (cx + 380, cy + 340)]
    contour_pts3 = [(cx - 320, cy + 390), (cx - 140, cy + 260), (cx + 40, cy + 310), (cx + 200, cy + 220), (cx + 320, cy + 390)]
    
    draw.line(contour_pts1, fill=APPLE_YELLOW, width=12)
    draw.line(contour_pts2, fill=(255, 204, 0, 180), width=8)
    draw.line(contour_pts3, fill=(255, 204, 0, 120), width=6)
    
    # Diamond / Crown Pro Emblem
    d_top = cy - 260
    diamond = [(cx, d_top), (cx + 140, d_top + 130), (cx, d_top + 260), (cx - 140, d_top + 130)]
    draw.polygon(diamond, fill=APPLE_YELLOW)
    draw.polygon([(cx, d_top + 20), (cx + 120, d_top + 130), (cx, d_top + 240), (cx - 120, d_top + 130)], outline=WHITE, width=6)
    
    # Facets on Diamond
    draw.line([(cx - 140, d_top + 130), (cx + 140, d_top + 130)], fill=WHITE, width=6)
    draw.line([(cx, d_top), (cx, d_top + 260)], fill=WHITE, width=6)
    
    # Drone in flight above mountain
    drone_y = cy - 40
    arm_len = 160
    for dx, dy in [(-1, -0.6), (1, -0.6), (-1, 0.6), (1, 0.6)]:
        mx = int(cx + dx * arm_len)
        my = int(drone_y + dy * arm_len)
        draw.line([(cx, drone_y), (mx, my)], fill=WHITE, width=16)
        draw.ellipse([mx - 38, my - 38, mx + 38, my + 38], fill=WHITE)
        draw.ellipse([mx - 60, my - 60, mx + 60, my + 60], outline=(255, 255, 255, 180), width=6)
    draw.rounded_rectangle([cx - 65, drone_y - 75, cx + 65, drone_y + 75], radius=35, fill=WHITE)
    draw.ellipse([cx - 28, drone_y - 28, cx + 28, drone_y + 28], fill=APPLE_YELLOW)

# Generate License Icons
make_apple_icon(APPLE_BLUE, APPLE_MINT, glyph_hobby, "images/icon_hobby.png", "HOBBY")
make_apple_icon((20, 24, 45), APPLE_INDIGO, glyph_pro, "images/icon_pro.png", "PRO")

print("License icons successfully generated with Apple standard styling on pure white canvas.")

def create_feature_graphic(grad1, grad2, glyph_icon_fn, draw_diagram_fn, title_badge, filename):
    canvas = Image.new("RGBA", (1600, 900), WHITE)
    
    # 1. Left: Apple Squircle Icon (440x440)
    ix0, iy0, ix1, iy1 = 90, 230, 530, 670
    radius = 100
    
    # Soft drop shadow for icon
    shadow = Image.new("RGBA", (1600, 900), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle([ix0 + 6, iy0 + 16, ix1 + 6, iy1 + 26], radius=radius, fill=(0, 0, 0, 30))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    canvas = Image.alpha_composite(canvas, shadow)
    
    # Draw gradient squircle
    draw_gradient_squircle(canvas, (ix0, iy0, ix1, iy1), radius, grad1, grad2)
    
    cdraw = ImageDraw.Draw(canvas)
    # Glass rim
    cdraw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=radius, outline=(255, 255, 255, 70), width=4)
    # Draw glyph inside icon
    glyph_icon_fn(cdraw, (ix0, iy0, ix1, iy1))
    
    # 2. Right: Apple-style Card
    cx0, cy0, cx1, cy1 = 580, 80, 1510, 820
    cdraw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=32, fill=BG_CARD, outline=APPLE_LINE, width=2)
    
    # Category / Title Badge
    font_badge = get_font(FONT_BOLD, 30)
    bbox = cdraw.textbbox((0, 0), title_badge, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    cdraw.rounded_rectangle([cx0 + 40, cy0 + 40, cx0 + 40 + bw + 36, cy0 + 40 + bh + 20], radius=14, fill=WHITE, outline=APPLE_LINE, width=2)
    cdraw.text((cx0 + 58, cy0 + 48), title_badge, font=font_badge, fill=grad1)
    
    # Draw Diagram inside Right Card
    draw_diagram_fn(cdraw, (cx0 + 40, cy0 + 120, cx1 - 40, cy1 - 40))
    
    # Outer canvas boundary subtle line
    cdraw.rounded_rectangle([20, 20, 1580, 880], radius=24, outline=APPLE_LINE, width=2)
    
    rgb = canvas.convert("RGB")
    final = rgb.resize((800, 450), Image.Resampling.LANCZOS)
    out_dir = "images/features"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    final.save(out_path, "PNG", optimize=True)
    print(f"Generated feature graphic: {out_path}")

# --- 1. KML Multi-Boundaries ---
def glyph_kml(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Multiple overlapping polygon parcels
    p1 = [(cx - 120, cy - 80), (cx + 40, cy - 110), (cx + 80, cy + 20), (cx - 50, cy + 60)]
    draw.polygon(p1, fill=(255, 255, 255, 90), outline=WHITE, width=6)
    p2 = [(cx - 30, cy - 20), (cx + 120, cy - 40), (cx + 100, cy + 100), (cx - 60, cy + 80)]
    draw.polygon(p2, fill=(255, 255, 255, 140), outline=WHITE, width=6)
    # Pins
    for px, py in [(cx - 120, cy - 80), (cx + 40, cy - 110), (cx + 120, cy - 40), (cx + 100, cy + 100)]:
        draw.ellipse([px - 14, py - 14, px + 14, py + 14], fill=APPLE_YELLOW, outline=WHITE, width=4)

def diag_kml(draw, bbox):
    x0, y0, x1, y1 = bbox
    # Draw 3 distinct property boundary blocks
    # Block A
    bA = [(x0 + 40, y0 + 100), (x0 + 360, y0 + 60), (x0 + 320, y0 + 360), (x0 + 60, y0 + 320)]
    draw.polygon(bA, fill=(52, 199, 89, 40), outline=APPLE_GREEN, width=4)
    # Block B
    bB = [(x0 + 380, y0 + 80), (x0 + 780, y0 + 120), (x0 + 720, y0 + 420), (x0 + 340, y0 + 380)]
    draw.polygon(bB, fill=(0, 122, 255, 40), outline=APPLE_BLUE, width=4)
    # Block C
    bC = [(x0 + 100, y0 + 360), (x0 + 520, y0 + 420), (x0 + 460, y0 + 560), (x0 + 80, y0 + 520)]
    draw.polygon(bC, fill=(175, 82, 222, 40), outline=APPLE_PURPLE, width=4)
    
    font_lbl = get_font(FONT_BOLD, 26)
    draw.text((x0 + 140, y0 + 200), "Blok 1 (SHM 041)", font=font_lbl, fill=APPLE_INK)
    draw.text((x0 + 460, y0 + 240), "Blok 2 (Sawit A2)", font=font_lbl, fill=APPLE_INK)
    draw.text((x0 + 200, y0 + 460), "Blok 3 (Perluasan)", font=font_lbl, fill=APPLE_INK)
    
    # Vertices pins
    for poly in [bA, bB, bC]:
        for px, py in poly:
            draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=WHITE, outline=APPLE_INK, width=3)

# --- 2. Boustrophedon Grid ---
def glyph_grid(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Zigzag sweep lines
    pts = [
        (cx - 110, cy - 100), (cx + 110, cy - 100),
        (cx + 110, cy - 30), (cx - 110, cy - 30),
        (cx - 110, cy + 40), (cx + 110, cy + 40),
        (cx + 110, cy + 110), (cx - 110, cy + 110)
    ]
    draw.line(pts, fill=WHITE, width=12)
    for px, py in pts:
        draw.ellipse([px - 14, py - 14, px + 14, py + 14], fill=APPLE_YELLOW)

def diag_grid(draw, bbox):
    x0, y0, x1, y1 = bbox
    # Polygon boundary
    poly = [(x0 + 60, y0 + 60), (x0 + 780, y0 + 40), (x0 + 820, y0 + 520), (x0 + 80, y0 + 540)]
    draw.polygon(poly, fill=WHITE, outline=APPLE_BLUE, width=4)
    # Grid lines inside
    y_lines = [y0 + 120, y0 + 200, y0 + 280, y0 + 360, y0 + 440]
    zigzag = []
    for i, ly in enumerate(y_lines):
        lx1, lx2 = x0 + 120, x0 + 740
        if i % 2 == 0:
            zigzag.extend([(lx1, ly), (lx2, ly)])
        else:
            zigzag.extend([(lx2, ly), (lx1, ly)])
    draw.line(zigzag, fill=APPLE_BLUE, width=5)
    # Camera photo triggers
    for i in range(len(zigzag) - 1):
        pA, pB = zigzag[i], zigzag[i+1]
        for t in [0.25, 0.5, 0.75]:
            tx = int(pA[0] + t * (pB[0] - pA[0]))
            ty = int(pA[1] + t * (pB[1] - pA[1]))
            draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=APPLE_GREEN, outline=WHITE, width=2)
    font_lbl = get_font(FONT_BOLD, 24)
    draw.text((x0 + 100, y0 + 480), "Overlap Depan 80% • Overlap Samping 70% • GSD 2.1 cm/px", font=font_lbl, fill=APPLE_SLATE)

# --- 3. Speed Clamping ---
def glyph_speed(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Gauge arc
    draw.arc([cx - 120, cy - 120, cx + 120, cy + 120], start=140, end=40, fill=WHITE, width=16)
    # Needle pointing safe
    draw.line([(cx, cy), (cx - 40, cy - 70)], fill=APPLE_YELLOW, width=10)
    draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=WHITE)
    # Camera shutter symbol
    draw.ellipse([cx + 40, cy + 40, cx + 100, cy + 100], fill=APPLE_MINT, outline=WHITE, width=6)

def diag_speed(draw, bbox):
    x0, y0, x1, y1 = bbox
    # Comparison bars
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    # Bad: Speed too fast
    draw.rounded_rectangle([x0 + 40, y0 + 80, x0 + 780, y0 + 220], radius=16, fill=WHITE, outline=APPLE_LINE, width=2)
    draw.text((x0 + 70, y0 + 105), "❌ Tanpa Speed Clamping (15 m/s)", font=font_t, fill=APPLE_RED)
    draw.text((x0 + 70, y0 + 145), "Kamera DJI jeda 2.0s • Shutter lambat • Hasil foto blur & bolong", font=font_sub, fill=APPLE_SLATE)
    
    # Good: Clamped
    draw.rounded_rectangle([x0 + 40, y0 + 260, x0 + 780, y0 + 430], radius=16, fill=WHITE, outline=APPLE_GREEN, width=3)
    draw.text((x0 + 70, y0 + 290), "✅ Otomatis Clamped TW-Mapper (5.4 m/s)", font=font_t, fill=APPLE_GREEN)
    draw.text((x0 + 70, y0 + 335), "Kecepatan dihitung matematis berbasis sensor 12/48 MP", font=font_sub, fill=APPLE_SLATE)
    draw.text((x0 + 70, y0 + 375), "Hasil: 100% foto tajam bebas blur, tanpa ada area yang bolong", font=font_sub, fill=APPLE_INK)

# --- 4. Corridor Buffer ---
def glyph_corridor(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Curving road with left and right offset boundaries
    pts_c = [(cx - 100, cy + 110), (cx - 20, cy + 20), (cx + 40, cy - 20), (cx + 100, cy - 110)]
    draw.line(pts_c, fill=WHITE, width=12)
    # Left buffer dashed
    draw.line([(p[0] - 50, p[1]) for p in pts_c], fill=(255, 255, 255, 140), width=6)
    # Right buffer wider
    draw.line([(p[0] + 80, p[1]) for p in pts_c], fill=(255, 255, 255, 140), width=6)

def diag_corridor(draw, bbox):
    x0, y0, x1, y1 = bbox
    # Centerline road
    road_pts = [(x0 + 60, y0 + 440), (x0 + 300, y0 + 340), (x0 + 550, y0 + 220), (x0 + 800, y0 + 100)]
    # Asymmetric buffer polygons
    # Left buffer (30m)
    b_left = [(p[0] - 40, p[1] - 40) for p in road_pts]
    # Right buffer (70m - wider)
    b_right = [(p[0] + 90, p[1] + 90) for p in road_pts]
    
    corridor_poly = b_left + list(reversed(b_right))
    draw.polygon(corridor_poly, fill=(255, 149, 0, 35), outline=APPLE_ORANGE, width=3)
    draw.line(road_pts, fill=APPLE_INK, width=6)
    
    font_lbl = get_font(FONT_BOLD, 24)
    draw.text((x0 + 120, y0 + 180), "Batas Kiri: 30 meter", font=font_lbl, fill=APPLE_ORANGE)
    draw.text((x0 + 420, y0 + 380), "Batas Kanan: 70 meter (Asimetris)", font=font_lbl, fill=APPLE_ORANGE)
    draw.text((x0 + 80, y0 + 490), "Cocok untuk survei jalur transmisi PLN, jalan tol, dan bantaran sungai", font=font_lbl, fill=APPLE_SLATE)

# --- 5. Flash Inject ---
def glyph_flash(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Lightning bolt into remote
    bolt = [(cx + 20, cy - 130), (cx - 60, cy - 10), (cx + 10, cy - 10), (cx - 20, cy + 130), (cx + 70, cy + 10), (cx, cy + 10)]
    draw.polygon(bolt, fill=WHITE)

def diag_flash(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_step = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    # Flow diagram
    steps = [
        ("1. Rancang Rute", "Peta satelit TW-Mapper", APPLE_BLUE),
        ("2. Flash Inject", "Injeksi memori < 1 detik", APPLE_ORANGE),
        ("3. Buka DJI Fly", "Misi langsung siap terbang", APPLE_GREEN)
    ]
    for i, (title, sub, col) in enumerate(steps):
        bx = x0 + 40 + i * 260
        by = y0 + 160
        draw.rounded_rectangle([bx, by, bx + 240, by + 180], radius=20, fill=WHITE, outline=col, width=3)
        draw.text((bx + 20, by + 40), title, font=font_step, fill=col)
        draw.text((bx + 20, by + 90), sub, font=font_sub, fill=APPLE_SLATE)
        if i < 2:
            # Arrow
            ax = bx + 245
            draw.line([(ax, by + 90), (ax + 20, by + 90)], fill=APPLE_LIGHT_SLATE, width=6)
    draw.text((x0 + 60, y0 + 440), "⚡ Membutuhkan TW Tweaks • Tanpa restart remote • 1-Detik langsung terbang", font=font_step, fill=APPLE_INK)

# --- 6. Fleet Sync ---
def glyph_fleet(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # 2 controller screens with radio wifi wave
    draw.rounded_rectangle([cx - 130, cy - 80, cx - 30, cy + 80], radius=16, fill=WHITE)
    draw.rounded_rectangle([cx + 30, cy - 80, cx + 130, cy + 80], radius=16, fill=WHITE)
    # Sync radio waves
    draw.arc([cx - 40, cy - 40, cx + 40, cy + 40], start=300, end=60, fill=APPLE_YELLOW, width=8)
    draw.arc([cx - 40, cy - 40, cx + 40, cy + 40], start=120, end=240, fill=APPLE_YELLOW, width=8)

def diag_fleet(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    # Remote A & Remote B cards
    draw.rounded_rectangle([x0 + 50, y0 + 120, x0 + 380, y0 + 360], radius=24, fill=WHITE, outline=APPLE_BLUE, width=3)
    draw.text((x0 + 80, y0 + 150), "Remote 1 (Pilot Utama)", font=font_t, fill=APPLE_BLUE)
    draw.text((x0 + 80, y0 + 195), "DJI RC 2 / RC Pro\nMembuat rencana jalur terbang", font=font_sub, fill=APPLE_SLATE)
    
    draw.rounded_rectangle([x0 + 470, y0 + 120, x0 + 800, y0 + 360], radius=24, fill=WHITE, outline=APPLE_INDIGO, width=3)
    draw.text((x0 + 500, y0 + 150), "Remote 2 (Pilot Tim)", font=font_t, fill=APPLE_INDIGO)
    draw.text((x0 + 500, y0 + 195), "Remote cadangan / rekan tim\nTerima misi dalam 1 detik", font=font_sub, fill=APPLE_SLATE)
    
    # Bi-directional arrows
    draw.line([(x0 + 385, y0 + 240), (x0 + 465, y0 + 240)], fill=APPLE_YELLOW, width=8)
    draw.text((x0 + 375, y0 + 260), "Local Sync", font=font_sub, fill=APPLE_ORANGE)
    draw.text((x0 + 70, y0 + 430), "Direct Wi-Fi / Hotspot lokal tanpa kuota internet atau perantara laptop", font=font_t, fill=APPLE_INK)

# --- 7. Offline Maps ---
def glyph_offline(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Folded map
    p = [(cx - 120, cy - 80), (cx - 40, cy - 110), (cx + 40, cy - 80), (cx + 120, cy - 110),
         (cx + 120, cy + 90), (cx + 40, cy + 120), (cx - 40, cy + 90), (cx - 120, cy + 120)]
    draw.polygon(p, fill=WHITE)
    # Down arrow download
    draw.line([(cx, cy - 30), (cx, cy + 50)], fill=APPLE_TEAL, width=12)
    draw.line([(cx - 25, cy + 25), (cx, cy + 50), (cx + 25, cy + 25)], fill=APPLE_TEAL, width=12)

def diag_offline(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    draw.rounded_rectangle([x0 + 40, y0 + 100, x0 + 800, y0 + 380], radius=24, fill=WHITE, outline=APPLE_TEAL, width=3)
    draw.text((x0 + 70, y0 + 140), "🗺️ Penyimpanan Peta Satelit Offline (SQLite Tile)", font=font_t, fill=APPLE_TEAL)
    draw.text((x0 + 70, y0 + 190), "• Unduh sebelum berangkat ke pedalaman / area blank spot\n• Citra satelit Google & ArcGIS tersimpan di microSD / internal\n• Zoom level 15 - 19 tetap jernih & tajam tanpa sinyal GSM", font=font_sub, fill=APPLE_INK)
    draw.text((x0 + 70, y0 + 320), "Status Lapangan: Sinyal 0 Bar • Peta 100% Aktif", font=font_t, fill=APPLE_GREEN)

# --- 8. DEM Server ---
def glyph_dem(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Layered 3D elevation server stack
    for dy in [-60, 0, 60]:
        draw.ellipse([cx - 110, cy + dy - 30, cx + 110, cy + dy + 30], fill=WHITE, outline=(255, 255, 255, 200), width=4)
    draw.ellipse([cx - 70, cy - 60 - 15, cx + 70, cy - 60 + 15], fill=APPLE_YELLOW)

def diag_dem(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    draw.rounded_rectangle([x0 + 40, y0 + 100, x0 + 800, y0 + 380], radius=24, fill=WHITE, outline=APPLE_PURPLE, width=3)
    draw.text((x0 + 70, y0 + 140), "⛰️ Local Elevation Server (DEM)", font=font_t, fill=APPLE_PURPLE)
    draw.text((x0 + 70, y0 + 190), "• Database elevasi permukaan bumi lokal di dalam remote\n• Menghitung ketinggian bukit, lembah, dan jurang secara real-time\n• Latensi lookup < 5 milidetik tanpa butuh server cloud eksternal", font=font_sub, fill=APPLE_INK)
    draw.text((x0 + 70, y0 + 320), "Akurasi Resolusi Vertikal: DEM SRTM / Copernicus 30m / DEMNAS", font=font_t, fill=APPLE_BLUE)

# --- 9. Follow Terrain ---
def glyph_terrain(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Hill contour
    hill = [(cx - 130, cy + 110), (cx - 40, cy - 20), (cx + 30, cy + 30), (cx + 130, cy - 80)]
    draw.line(hill, fill=APPLE_YELLOW, width=12)
    # Drone dashed path above
    path = [(p[0], p[1] - 60) for p in hill]
    draw.line(path, fill=WHITE, width=8)

def diag_terrain(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    # Mountain profile
    mountain = [
        (x0 + 40, y0 + 440), (x0 + 200, y0 + 320), (x0 + 360, y0 + 380),
        (x0 + 540, y0 + 200), (x0 + 680, y0 + 290), (x0 + 820, y0 + 160)
    ]
    draw.line(mountain, fill=APPLE_SLATE, width=8)
    
    # Drone trajectory constant AGL
    flight = [(p[0], p[1] - 120) for p in mountain]
    draw.line(flight, fill=APPLE_ORANGE, width=6)
    
    # Altitude arrows
    for p_m, p_f in zip(mountain[1:5], flight[1:5]):
        draw.line([p_m, p_f], fill=APPLE_GREEN, width=3)
    
    draw.text((x0 + 60, y0 + 100), "Ketinggian Relatif AGL Tetap Konstan (misal: 80 meter)", font=font_t, fill=APPLE_GREEN)
    draw.text((x0 + 60, y0 + 470), "GSD seragam di puncak bukit maupun dasar lembah • Aman dari risiko tabrak lereng", font=font_sub, fill=APPLE_INK)

# --- 10. Split Mission ---
def glyph_split(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Battery icon divided into 3 pieces
    draw.rounded_rectangle([cx - 110, cy - 60, cx + 90, cy + 60], radius=16, fill=WHITE)
    draw.rounded_rectangle([cx + 90, cy - 25, cx + 110, cy + 25], radius=6, fill=WHITE)
    # Division cut lines
    draw.line([(cx - 40, cy - 60), (cx - 40, cy + 60)], fill=APPLE_BLUE, width=8)
    draw.line([(cx + 30, cy - 60), (cx + 30, cy + 60)], fill=APPLE_BLUE, width=8)

def diag_split(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    # Area split into 3 segments
    draw.rounded_rectangle([x0 + 40, y0 + 120, x0 + 280, y0 + 380], radius=20, fill=(0, 122, 255, 30), outline=APPLE_BLUE, width=3)
    draw.text((x0 + 60, y0 + 160), "Bagian 1", font=font_t, fill=APPLE_BLUE)
    draw.text((x0 + 60, y0 + 210), "Baterai #1\n120 foto\nEstimasi 18m", font=font_sub, fill=APPLE_INK)
    
    draw.rounded_rectangle([x0 + 300, y0 + 120, x0 + 540, y0 + 380], radius=20, fill=(52, 199, 89, 30), outline=APPLE_GREEN, width=3)
    draw.text((x0 + 320, y0 + 160), "Bagian 2", font=font_t, fill=APPLE_GREEN)
    draw.text((x0 + 320, y0 + 210), "Baterai #2\n115 foto\nEstimasi 17m", font=font_sub, fill=APPLE_INK)
    
    draw.rounded_rectangle([x0 + 560, y0 + 120, x0 + 800, y0 + 380], radius=20, fill=(175, 82, 222, 30), outline=APPLE_PURPLE, width=3)
    draw.text((x0 + 580, y0 + 160), "Bagian 3", font=font_t, fill=APPLE_PURPLE)
    draw.text((x0 + 580, y0 + 210), "Baterai #3\n90 foto\nEstimasi 14m", font=font_sub, fill=APPLE_INK)
    
    draw.text((x0 + 60, y0 + 440), "Pemetaan lahan ratusan hektar tanpa khawatir kehabisan baterai di tengah misi", font=font_t, fill=APPLE_INK)

# --- 11. Orbit Helix ---
def glyph_orbit(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Vertical pillar / tower in center
    draw.rounded_rectangle([cx - 25, cy - 120, cx + 25, cy + 120], radius=10, fill=WHITE)
    # Spiral loops
    draw.ellipse([cx - 100, cy - 80, cx + 100, cy - 20], outline=APPLE_YELLOW, width=8)
    draw.ellipse([cx - 110, cy - 20, cx + 110, cy + 40], outline=APPLE_YELLOW, width=8)
    draw.ellipse([cx - 120, cy + 40, cx + 120, cy + 100], outline=APPLE_YELLOW, width=8)

def diag_orbit(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    # Tower schematic in center
    tx = x0 + 420
    draw.rectangle([tx - 30, y0 + 100, tx + 30, y0 + 460], fill=APPLE_LIGHT_SLATE)
    draw.polygon([(tx, y0 + 60), (tx - 50, y0 + 100), (tx + 50, y0 + 100)], fill=APPLE_SLATE)
    
    # Climbing spiral lines
    for sy in range(y0 + 140, y0 + 440, 60):
        draw.arc([tx - 180, sy - 40, tx + 180, sy + 40], start=0, end=180, fill=APPLE_TEAL, width=5)
        draw.arc([tx - 180, sy - 40, tx + 180, sy + 40], start=180, end=360, fill=(48, 176, 199, 120), width=4)
        
    draw.text((x0 + 50, y0 + 120), "Inspeksi Tower & Kubah", font=font_t, fill=APPLE_TEAL)
    draw.text((x0 + 50, y0 + 170), "Pola spiral kontinu naik\nGimbal otomatis mengarah\nke pusat objek (-35°)", font=font_sub, fill=APPLE_INK)
    draw.text((x0 + 50, y0 + 480), "Hemat baterai tanpa henti belok 90° • Model 3D detail dan presisi", font=font_t, fill=APPLE_SLATE)

# --- 12. Breakpoint Resume ---
def glyph_resume(draw, bbox):
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    # Pause bar -> Arrow resume
    draw.line([(cx - 70, cy - 60), (cx - 70, cy + 60)], fill=WHITE, width=16)
    draw.line([(cx - 30, cy - 60), (cx - 30, cy + 60)], fill=WHITE, width=16)
    # Resume triangle
    draw.polygon([(cx + 20, cy - 60), (cx + 100, cy), (cx + 20, cy + 60)], fill=APPLE_GREEN)

def diag_resume(draw, bbox):
    x0, y0, x1, y1 = bbox
    font_t = get_font(FONT_BOLD, 26)
    font_sub = get_font(FONT_REG, 22)
    # Flow
    draw.rounded_rectangle([x0 + 40, y0 + 120, x0 + 260, y0 + 360], radius=20, fill=WHITE, outline=APPLE_RED, width=3)
    draw.text((x0 + 60, y0 + 160), "1. Baterai Low", font=font_t, fill=APPLE_RED)
    draw.text((x0 + 60, y0 + 210), "Drone otomatis RTH\nTitik foto terakhir\ntersimpan otomatis", font=font_sub, fill=APPLE_INK)
    
    draw.rounded_rectangle([x0 + 300, y0 + 120, x0 + 520, y0 + 360], radius=20, fill=WHITE, outline=APPLE_YELLOW, width=3)
    draw.text((x0 + 320, y0 + 160), "2. Ganti Baterai", font=font_t, fill=APPLE_ORANGE)
    draw.text((x0 + 320, y0 + 210), "Ganti baterai baru\ndi darat tanpa perlu\nulang buat misi", font=font_sub, fill=APPLE_INK)
    
    draw.rounded_rectangle([x0 + 560, y0 + 120, x0 + 800, y0 + 360], radius=20, fill=WHITE, outline=APPLE_GREEN, width=3)
    draw.text((x0 + 580, y0 + 160), "3. Auto Resume", font=font_t, fill=APPLE_GREEN)
    draw.text((x0 + 580, y0 + 210), "Drone terbang langsung\nke titik jeda terakhir\ndan tuntaskan misi", font=font_sub, fill=APPLE_INK)
    
    draw.text((x0 + 60, y0 + 440), "Akurasi titik sambung sub-meter tanpa ada foto atau jalur yang terlompat", font=font_t, fill=APPLE_INK)

# Generate 12 Feature Graphics
create_feature_graphic(APPLE_GREEN, APPLE_MINT, glyph_kml, diag_kml, "SURVEI MULTI-AREA", "feat_kml_multi_boundaries.png")
create_feature_graphic(APPLE_BLUE, APPLE_BLUE_LIGHT, glyph_grid, diag_grid, "JALUR GRID OTOMATIS", "boustrophedon_grid.png")
create_feature_graphic(APPLE_GREEN, APPLE_TEAL, glyph_speed, diag_speed, "OPTIMALISASI FOTO", "speed_clamping.png")
create_feature_graphic(APPLE_ORANGE, APPLE_YELLOW, glyph_corridor, diag_corridor, "SURVEI KORIDOR", "corridor_buffer.png")
create_feature_graphic(APPLE_YELLOW, APPLE_ORANGE, glyph_flash, diag_flash, "INJEKSI INSTAN", "flash_inject.png")
create_feature_graphic(APPLE_INDIGO, APPLE_BLUE, glyph_fleet, diag_fleet, "KONEKTIVITAS LAPANGAN", "fleet_sync.png")
create_feature_graphic(APPLE_TEAL, APPLE_MINT, glyph_offline, diag_offline, "NAVIGASI OFFLINE", "offline_maps.png")
create_feature_graphic(APPLE_PURPLE, APPLE_INDIGO, glyph_dem, diag_dem, "SERVER ELEVASI", "dem_server.png")
create_feature_graphic(APPLE_ORANGE, APPLE_RED, glyph_terrain, diag_terrain, "TERRAIN FOLLOW DEM", "follow_terrain.png")
create_feature_graphic(APPLE_BLUE, APPLE_INDIGO, glyph_split, diag_split, "MANAJEMEN BATERAI", "split_mission.png")
create_feature_graphic(APPLE_TEAL, APPLE_BLUE, glyph_orbit, diag_orbit, "PEMODELAN 3D", "orbit_helix.png")
create_feature_graphic(APPLE_GREEN, APPLE_YELLOW, glyph_resume, diag_resume, "LANJUT TERBANG", "breakpoint_resume.png")

print("All 12 feature graphics generated with Apple standard styling on pure white canvas.")
