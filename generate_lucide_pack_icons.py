import math
import os
from PIL import Image, ImageDraw, ImageFilter

WHITE = (255, 255, 255)

# Apple System Colors
APPLE_BLUE = (0, 122, 255)         # #007AFF
APPLE_INDIGO = (88, 86, 214)       # #5856D6
APPLE_PURPLE = (175, 82, 222)      # #AF52DE
APPLE_TEAL = (48, 176, 199)        # #30B0C7
APPLE_MINT = (0, 199, 190)         # #00C7BE
APPLE_GREEN = (52, 199, 89)        # #34C759
APPLE_YELLOW = (255, 204, 0)       # #FFCC00
APPLE_ORANGE = (255, 149, 0)       # #FF9500
APPLE_RED = (255, 59, 48)          # #FF3B30
APPLE_SLATE_DARK = (44, 44, 46)    # #2C2C2E
APPLE_SLATE_LIGHT = (99, 99, 102)  # #636366
APPLE_CYAN = (50, 173, 230)        # #32ADE6
APPLE_PINK = (255, 45, 85)         # #FF2D55

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

def make_apple_squircle_icon(grad1, grad2, draw_glyph_fn, out_path, size=1024):
    canvas = Image.new("RGBA", (2048, 2048), WHITE)
    
    x0, y0, x1, y1 = 256, 256, 1792, 1792
    radius = 360
    
    # Ambient shadow
    shadow = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle([x0 + 10, y0 + 40, x1 + 10, y1 + 60], radius=radius, fill=(0, 0, 0, 36))
    shadow = shadow.filter(ImageFilter.GaussianBlur(50))
    canvas = Image.alpha_composite(canvas, shadow)
    
    # Gradient squircle
    draw_gradient_squircle(canvas, (x0, y0, x1, y1), radius, grad1, grad2)
    
    # Glass highlight rim
    cdraw = ImageDraw.Draw(canvas)
    cdraw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, 75), width=8)
    
    # Draw vector icon glyph in pure white
    draw_glyph_fn(cdraw, (x0, y0, x1, y1))
    
    rgb = canvas.convert("RGB")
    final = rgb.resize((size, size), Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    final.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path}")

# --- Helper: Map standard 24x24 Lucide coordinates to Squircle inner box ---
def map_coords(cx, cy, scale, x, y):
    # Map from (x, y) in [0..24] to canvas coords centered at (cx, cy)
    return (cx + (x - 12) * scale, cy + (y - 12) * scale)

def draw_lucide_layers(draw, bbox): # KML Multi-Boundaries
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    # Top diamond
    p1 = [map_coords(cx, cy, s, 12, 2), map_coords(cx, cy, s, 22, 7), map_coords(cx, cy, s, 12, 12), map_coords(cx, cy, s, 2, 7)]
    draw.polygon(p1, outline=WHITE, width=w)
    # Middle line
    p2 = [map_coords(cx, cy, s, 2, 12), map_coords(cx, cy, s, 12, 17), map_coords(cx, cy, s, 22, 12)]
    draw.line(p2, fill=WHITE, width=w, joint="curve")
    # Bottom line
    p3 = [map_coords(cx, cy, s, 2, 17), map_coords(cx, cy, s, 12, 22), map_coords(cx, cy, s, 22, 17)]
    draw.line(p3, fill=WHITE, width=w, joint="curve")

def draw_lucide_grid(draw, bbox): # Grid & Zig-zag Otomatis
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    r_box = [map_coords(cx, cy, s, 3, 3), map_coords(cx, cy, s, 21, 21)]
    draw.rounded_rectangle([r_box[0][0], r_box[0][1], r_box[1][0], r_box[1][1]], radius=40, outline=WHITE, width=w)
    # horizontal lines
    draw.line([map_coords(cx, cy, s, 3, 9), map_coords(cx, cy, s, 21, 9)], fill=WHITE, width=w)
    draw.line([map_coords(cx, cy, s, 3, 15), map_coords(cx, cy, s, 21, 15)], fill=WHITE, width=w)
    # vertical lines
    draw.line([map_coords(cx, cy, s, 9, 3), map_coords(cx, cy, s, 9, 21)], fill=WHITE, width=w)
    draw.line([map_coords(cx, cy, s, 15, 3), map_coords(cx, cy, s, 15, 21)], fill=WHITE, width=w)

def draw_lucide_gauge(draw, bbox): # Speed Clamping Aman
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    # Outer arc
    arc_box = [cx - 10 * s, cy - 10 * s + 60, cx + 10 * s, cy + 10 * s + 60]
    draw.arc(arc_box, start=145, end=395, fill=WHITE, width=w)
    # Needle
    draw.line([map_coords(cx, cy, s, 12, 14), map_coords(cx, cy, s, 16, 10)], fill=WHITE, width=w)
    # Center pin
    draw.ellipse([cx - 24, cy - 24 + 80, cx + 24, cy + 24 + 80], fill=WHITE)

def draw_lucide_route(draw, bbox): # Asymmetrical Corridor
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    # start circle
    c1 = map_coords(cx, cy, s, 6, 19)
    draw.ellipse([c1[0] - 3*s, c1[1] - 3*s, c1[0] + 3*s, c1[1] + 3*s], outline=WHITE, width=w)
    # end circle
    c2 = map_coords(cx, cy, s, 18, 5)
    draw.ellipse([c2[0] - 3*s, c2[1] - 3*s, c2[0] + 3*s, c2[1] + 3*s], outline=WHITE, width=w)
    # S-curve path
    pts = [
        map_coords(cx, cy, s, 9, 19),
        map_coords(cx, cy, s, 14.5, 19),
        map_coords(cx, cy, s, 18, 15.5),
        map_coords(cx, cy, s, 18, 12),
        map_coords(cx, cy, s, 6, 12),
        map_coords(cx, cy, s, 6, 8.5),
        map_coords(cx, cy, s, 9.5, 5),
        map_coords(cx, cy, s, 15, 5)
    ]
    draw.line(pts, fill=WHITE, width=w, joint="curve")

def draw_lucide_zap(draw, bbox): # Flash Inject Instan
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 44
    pts = [
        map_coords(cx, cy, s, 13, 2),
        map_coords(cx, cy, s, 3, 14),
        map_coords(cx, cy, s, 12, 14),
        map_coords(cx, cy, s, 11, 22),
        map_coords(cx, cy, s, 21, 10),
        map_coords(cx, cy, s, 12, 10)
    ]
    draw.polygon(pts, fill=WHITE)

def draw_lucide_refresh(draw, bbox): # Direct & Fleet Sync
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    # Two arc loops
    draw.arc([cx - 9*s, cy - 9*s, cx + 9*s, cy + 9*s], start=210, end=350, fill=WHITE, width=w)
    draw.arc([cx - 9*s, cy - 9*s, cx + 9*s, cy + 9*s], start=30, end=170, fill=WHITE, width=w)
    # Arrows
    p_arrow1 = [map_coords(cx, cy, s, 21, 3), map_coords(cx, cy, s, 21, 8), map_coords(cx, cy, s, 16, 8)]
    draw.line(p_arrow1, fill=WHITE, width=w)
    p_arrow2 = [map_coords(cx, cy, s, 3, 21), map_coords(cx, cy, s, 3, 16), map_coords(cx, cy, s, 8, 16)]
    draw.line(p_arrow2, fill=WHITE, width=w)

def draw_lucide_map(draw, bbox): # 100% Peta Offline
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 30
    poly = [
        map_coords(cx, cy, s, 3, 6),
        map_coords(cx, cy, s, 9, 3),
        map_coords(cx, cy, s, 15, 6),
        map_coords(cx, cy, s, 21, 3),
        map_coords(cx, cy, s, 21, 18),
        map_coords(cx, cy, s, 15, 21),
        map_coords(cx, cy, s, 9, 18),
        map_coords(cx, cy, s, 3, 21)
    ]
    draw.polygon(poly, outline=WHITE, width=w)
    draw.line([map_coords(cx, cy, s, 9, 3), map_coords(cx, cy, s, 9, 18)], fill=WHITE, width=w)
    draw.line([map_coords(cx, cy, s, 15, 6), map_coords(cx, cy, s, 15, 21)], fill=WHITE, width=w)

def draw_lucide_server(draw, bbox): # Local Elevation Server
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 30
    # Top unit
    r1 = [map_coords(cx, cy, s, 2, 3), map_coords(cx, cy, s, 22, 10)]
    draw.rounded_rectangle([r1[0][0], r1[0][1], r1[1][0], r1[1][1]], radius=20, outline=WHITE, width=w)
    draw.ellipse([r1[0][0] + 50, cy - 5*s - 15, r1[0][0] + 80, cy - 5*s + 15], fill=WHITE)
    # Bottom unit
    r2 = [map_coords(cx, cy, s, 2, 14), map_coords(cx, cy, s, 22, 21)]
    draw.rounded_rectangle([r2[0][0], r2[0][1], r2[1][0], r2[1][1]], radius=20, outline=WHITE, width=w)
    draw.ellipse([r2[0][0] + 50, cy + 6*s - 15, r2[0][0] + 80, cy + 6*s + 15], fill=WHITE)

def draw_lucide_mountain(draw, bbox): # Follow Terrain
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 42
    w = 32
    # Mountain peaks: 8,3 -> 12,11 -> 17,6 -> 22,21 -> 2,21
    pts = [
        map_coords(cx, cy, s, 8, 3),
        map_coords(cx, cy, s, 12, 11),
        map_coords(cx, cy, s, 17, 6),
        map_coords(cx, cy, s, 22, 21),
        map_coords(cx, cy, s, 2, 21)
    ]
    draw.polygon(pts, outline=WHITE, width=w)

def draw_lucide_battery(draw, bbox): # Split Misi Multi-Baterai
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    # Battery body
    r = [map_coords(cx, cy, s, 2, 6), map_coords(cx, cy, s, 20, 18)]
    draw.rounded_rectangle([r[0][0], r[0][1], r[1][0], r[1][1]], radius=30, outline=WHITE, width=w)
    # Terminal
    draw.line([map_coords(cx, cy, s, 22, 11), map_coords(cx, cy, s, 22, 13)], fill=WHITE, width=w+8)
    # Bolt inside
    bolt = [
        map_coords(cx, cy, s, 12, 7),
        map_coords(cx, cy, s, 7, 12),
        map_coords(cx, cy, s, 11, 12),
        map_coords(cx, cy, s, 10, 17),
        map_coords(cx, cy, s, 15, 12),
        map_coords(cx, cy, s, 12, 12)
    ]
    draw.polygon(bolt, fill=WHITE)

def draw_lucide_box(draw, bbox): # Orbit Helix 3D
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    # 3D isometric cube
    p_top = [map_coords(cx, cy, s, 12, 2), map_coords(cx, cy, s, 21, 7), map_coords(cx, cy, s, 12, 12), map_coords(cx, cy, s, 3, 7)]
    draw.polygon(p_top, outline=WHITE, width=w)
    # Left face
    p_left = [map_coords(cx, cy, s, 3, 7), map_coords(cx, cy, s, 12, 12), map_coords(cx, cy, s, 12, 22), map_coords(cx, cy, s, 3, 17)]
    draw.polygon(p_left, outline=WHITE, width=w)
    # Right face
    p_right = [map_coords(cx, cy, s, 12, 12), map_coords(cx, cy, s, 21, 7), map_coords(cx, cy, s, 21, 17), map_coords(cx, cy, s, 12, 22)]
    draw.polygon(p_right, outline=WHITE, width=w)

def draw_lucide_play(draw, bbox): # Breakpoint Resume
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 40
    w = 32
    # Circle
    draw.ellipse([cx - 10*s, cy - 10*s, cx + 10*s, cy + 10*s], outline=WHITE, width=w)
    # Play triangle
    p_play = [map_coords(cx, cy, s, 10, 8), map_coords(cx, cy, s, 16, 12), map_coords(cx, cy, s, 10, 16)]
    draw.polygon(p_play, fill=WHITE)

def draw_lucide_compass(draw, bbox): # Paket Hobby
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    s = 42
    w = 32
    # Outer circle
    draw.ellipse([cx - 10*s, cy - 10*s, cx + 10*s, cy + 10*s], outline=WHITE, width=w)
    # Diamond needle: 16.24, 7.76 -> 14.12, 14.12 -> 7.76, 16.24 -> 9.88, 9.88
    needle = [
        map_coords(cx, cy, s, 16.24, 7.76),
        map_coords(cx, cy, s, 14.12, 14.12),
        map_coords(cx, cy, s, 7.76, 16.24),
        map_coords(cx, cy, s, 9.88, 9.88)
    ]
    draw.polygon(needle, fill=WHITE)

def draw_lucide_award(draw, bbox): # Paket Pro
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2 - 40
    s = 42
    w = 32
    # Medal circle
    c_y = cy - 2*s
    draw.ellipse([cx - 6*s, c_y - 6*s, cx + 6*s, c_y + 6*s], outline=WHITE, width=w)
    # Inner star / diamond inside circle
    d = 2.5 * s
    draw.polygon([(cx, c_y - d), (cx + d, c_y), (cx, c_y + d), (cx - d, c_y)], fill=(255, 214, 10))
    # Ribbons: 15.48, 12.89 -> 17, 22 -> 12, 19 -> 7, 22 -> 8.52, 12.89
    r_pts = [
        map_coords(cx, cy, s, 15.48, 12.89),
        map_coords(cx, cy, s, 17, 22),
        map_coords(cx, cy, s, 12, 19),
        map_coords(cx, cy, s, 7, 22),
        map_coords(cx, cy, s, 8.52, 12.89)
    ]
    draw.line(r_pts, fill=WHITE, width=w, joint="curve")

# Render all
features = [
    (APPLE_GREEN, APPLE_MINT, draw_lucide_layers, "images/features/feat_kml_multi_boundaries.png"),
    (APPLE_GREEN, APPLE_MINT, draw_lucide_layers, "images/features/multi_area.png"),
    (APPLE_BLUE, APPLE_INDIGO, draw_lucide_grid, "images/features/boustrophedon_grid.png"),
    (APPLE_ORANGE, APPLE_YELLOW, draw_lucide_gauge, "images/features/speed_clamping.png"),
    (APPLE_PURPLE, APPLE_INDIGO, draw_lucide_route, "images/features/corridor_buffer.png"),
    (APPLE_YELLOW, APPLE_ORANGE, draw_lucide_zap, "images/features/flash_inject.png"),
    (APPLE_INDIGO, APPLE_BLUE, draw_lucide_refresh, "images/features/fleet_sync.png"),
    (APPLE_TEAL, APPLE_MINT, draw_lucide_map, "images/features/offline_maps.png"),
    (APPLE_SLATE_DARK, APPLE_SLATE_LIGHT, draw_lucide_server, "images/features/dem_server.png"),
    (APPLE_ORANGE, APPLE_RED, draw_lucide_mountain, "images/features/follow_terrain.png"),
    (APPLE_BLUE, APPLE_CYAN, draw_lucide_battery, "images/features/split_mission.png"),
    (APPLE_PURPLE, APPLE_PINK, draw_lucide_box, "images/features/orbit_helix.png"),
    (APPLE_GREEN, (40, 205, 65), draw_lucide_play, "images/features/breakpoint_resume.png"),
]

for g1, g2, fn, path in features:
    make_apple_squircle_icon(g1, g2, fn, path)

# Licenses
make_apple_squircle_icon(APPLE_BLUE, APPLE_CYAN, draw_lucide_compass, "images/icon_hobby.png")
make_apple_squircle_icon((28, 28, 30), (58, 58, 60), draw_lucide_award, "images/icon_pro.png")

print("All pure square Apple Lucide-pack icons generated successfully!")
