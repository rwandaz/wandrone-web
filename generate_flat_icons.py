import math
import os
from PIL import Image, ImageDraw, ImageFont

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TEAL = (45, 212, 191)         # #2DD4BF
TEAL_DARK = (15, 118, 110)     # #0F766E
EMERALD = (16, 185, 129)      # #10B981
EMERALD_DARK = (5, 150, 105)   # #059669
AMBER = (245, 158, 11)        # #F59E0B
RED = (239, 68, 68)           # #EF4444
PURPLE = (168, 85, 247)       # #A855F7
BLUE = (59, 130, 246)         # #3B82F6
SLATE_900 = (15, 23, 42)      # #0F172A
SLATE_800 = (30, 41, 59)      # #1E293B
SLATE_700 = (51, 65, 85)      # #334155
SLATE_500 = (100, 116, 139)   # #64748B
SLATE_400 = (148, 163, 184)   # #94A3B8

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def create_canvas(w=1600, h=900):
    im = Image.new("RGBA", (w, h), BLACK)
    draw = ImageDraw.Draw(im)
    return im, draw

def save_scaled(im, out_path, final_size):
    # Downsample for ultra-smooth anti-aliased flat vector look
    rgb = im.convert("RGB")
    final = rgb.resize(final_size, Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    final.save(out_path, "PNG")
    print(f"Saved {out_path} ({final_size[0]}x{final_size[1]})")

def draw_header_badge(draw, text, color=TEAL, x=70, y=60, font_size=32):
    font = get_font(FONT_BOLD, font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    px, py = 24, 12
    draw.rounded_rectangle([x, y, x + tw + px*2, y + th + py*2], radius=10, fill=SLATE_900, outline=color, width=4)
    draw.text((x + px, y + py - 3), text, font=font, fill=color)

def draw_drone(draw, cx, cy, size=65, color=TEAL, heading=0):
    arm = size * 0.95
    cos_a, sin_a = math.cos(math.radians(heading + 45)), math.sin(math.radians(heading + 45))
    cos_b, sin_b = math.cos(math.radians(heading + 135)), math.sin(math.radians(heading + 135))
    
    # 4 arms
    draw.line([cx - arm*cos_a, cy - arm*sin_a, cx + arm*cos_a, cy + arm*sin_a], fill=SLATE_700, width=9)
    draw.line([cx - arm*cos_b, cy - arm*sin_b, cx + arm*cos_b, cy + arm*sin_b], fill=SLATE_700, width=9)
    
    # 4 rotors
    for dx, dy in [(cos_a, sin_a), (-cos_a, -sin_a), (cos_b, sin_b), (-cos_b, -sin_b)]:
        rx, ry = cx + arm*dx, cy + arm*dy
        draw.ellipse([rx - 24, ry - 14, rx + 24, ry + 14], outline=color, width=4, fill=SLATE_900)
        draw.ellipse([rx - 7, ry - 7, rx + 7, ry + 7], fill=WHITE)
    
    # Central fuselage
    draw.rounded_rectangle([cx - size*0.4, cy - size*0.4, cx + size*0.4, cy + size*0.4], radius=14, fill=SLATE_900, outline=color, width=5)
    draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=color)


# ==============================================================================
# 1. ICON HOBBY (512x512)
# ==============================================================================
def gen_icon_hobby():
    im, draw = create_canvas(1024, 1024)
    # Background subtle grid
    for x in range(112, 1024, 160):
        draw.line([x, 100, x, 924], fill=SLATE_800, width=2)
    for y in range(112, 1024, 160):
        draw.line([100, y, 924, y], fill=SLATE_800, width=2)
        
    # Mapping path under drone
    path = [(250, 750), (450, 680), (620, 780), (800, 650)]
    for i in range(len(path)-1):
        draw.line([path[i], path[i+1]], fill=TEAL_DARK, width=6)
    for pt in path:
        draw.ellipse([pt[0]-14, pt[1]-14, pt[0]+14, pt[1]+14], fill=SLATE_900, outline=TEAL, width=4)
        draw.ellipse([pt[0]-6, pt[1]-6, pt[0]+6, pt[1]+6], fill=WHITE)
        
    # Large Center Drone
    draw_drone(draw, 512, 450, size=150, color=TEAL)
    
    # Header badge
    font = get_font(FONT_BOLD, 42)
    draw.rounded_rectangle([330, 80, 694, 160], radius=16, fill=SLATE_900, outline=TEAL, width=4)
    draw.text((370, 96), "HOBBY EDITION", font=font, fill=TEAL)
    
    save_scaled(im, "images/icon_hobby.png", (512, 512))


# ==============================================================================
# 2. ICON PRO (512x512)
# ==============================================================================
def gen_icon_pro():
    im, draw = create_canvas(1024, 1024)
    # 3D Elevation Contours
    for r, col, w in [(360, SLATE_800, 3), (280, SLATE_700, 4), (200, EMERALD_DARK, 5)]:
        draw.arc([512 - r, 540 - r*0.5, 512 + r, 540 + r*0.5], 0, 360, fill=col, width=w)
        
    # LiDAR scanning rays downward
    for dx in [-180, -90, 0, 90, 180]:
        draw.line([512 + dx*0.2, 480, 512 + dx*1.6, 750], fill=TEAL_DARK, width=3)
        draw.ellipse([512 + dx*1.6 - 6, 750 - 6, 512 + dx*1.6 + 6, 750 + 6], fill=EMERALD)
        
    # Pro Heavy Survey Drone
    draw_drone(draw, 512, 420, size=160, color=EMERALD)
    
    # Crown/Diamond Pro Badge
    font = get_font(FONT_BOLD, 42)
    draw.rounded_rectangle([354, 80, 670, 160], radius=16, fill=SLATE_900, outline=EMERALD, width=4)
    draw.text((395, 96), "PRO EDITION", font=font, fill=EMERALD)
    
    save_scaled(im, "images/icon_pro.png", (512, 512))


# ==============================================================================
# 3. KML MULTI-BOUNDARIES (800x450)
# ==============================================================================
def gen_feat_multi_area():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "KML MULTI-BOUNDARIES // MULTI-POLYGON IMPORT", TEAL)
    
    # Polygon 1 (Teal)
    p1 = [(150, 320), (520, 240), (620, 650), (220, 750)]
    draw.polygon(p1, fill=(15, 45, 45), outline=TEAL)
    draw.line(p1 + [p1[0]], fill=TEAL, width=7)
    for pt in p1:
        draw.ellipse([pt[0]-14, pt[1]-14, pt[0]+14, pt[1]+14], fill=WHITE, outline=TEAL, width=4)
        
    # Polygon 2 (Emerald)
    p2 = [(680, 280), (1120, 220), (1020, 680), (640, 580)]
    draw.polygon(p2, fill=(15, 45, 30), outline=EMERALD)
    draw.line(p2 + [p2[0]], fill=EMERALD, width=7)
    for pt in p2:
        draw.ellipse([pt[0]-14, pt[1]-14, pt[0]+14, pt[1]+14], fill=WHITE, outline=EMERALD, width=4)
        
    # Polygon 3 (Purple)
    p3 = [(1160, 340), (1480, 280), (1420, 720), (1080, 760)]
    draw.polygon(p3, fill=(35, 20, 50), outline=PURPLE)
    draw.line(p3 + [p3[0]], fill=PURPLE, width=7)
    for pt in p3:
        draw.ellipse([pt[0]-14, pt[1]-14, pt[0]+14, pt[1]+14], fill=WHITE, outline=PURPLE, width=4)
        
    # Area Labels
    font = get_font(FONT_BOLD, 36)
    draw.text((280, 480), "PARCEL A\n14.8 Ha", font=font, fill=TEAL, align="center")
    draw.text((790, 430), "PARCEL B\n22.5 Ha", font=font, fill=EMERALD, align="center")
    draw.text((1210, 480), "PARCEL C\n11.2 Ha", font=font, fill=PURPLE, align="center")
    
    save_scaled(im, "images/features/multi_area.png", (800, 450))
    save_scaled(im, "images/features/feat_kml_multi_boundaries.png", (800, 450))


# ==============================================================================
# 4. GRID & ZIG-ZAG OTOMATIS (800x450)
# ==============================================================================
def gen_feat_boustrophedon_grid():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "BOUSTROPHEDON GRID // ZIG-ZAG AUTOPILOT", TEAL)
    
    # Boundary box
    draw.rectangle([180, 220, 1420, 780], outline=SLATE_700, width=4)
    
    # Zig-zag flight lines
    x_coords = [280, 460, 640, 820, 1000, 1180, 1360]
    points = []
    for i, x in enumerate(x_coords):
        if i % 2 == 0:
            points.extend([(x, 720), (x, 280)])
        else:
            points.extend([(x, 280), (x, 720)])
            
    # Draw path
    for i in range(len(points)-1):
        draw.line([points[i], points[i+1]], fill=TEAL, width=8)
        
    # Shutter exposure dots
    for p in points:
        draw.ellipse([p[0]-12, p[1]-12, p[0]+12, p[1]+12], fill=WHITE, outline=TEAL, width=4)
        
    # Drone at current point
    draw_drone(draw, 1000, 500, size=70, color=EMERALD, heading=90)
    
    # Stats badge bottom
    font_mono = get_font(FONT_MONO, 32)
    draw.rounded_rectangle([420, 790, 1180, 860], radius=10, fill=SLATE_900, outline=SLATE_700, width=3)
    draw.text((450, 805), "GSD: 2.1 cm/px | OVERLAP: 80% / 70% | FLIGHT: AUTO", font=font_mono, fill=TEAL)
    
    save_scaled(im, "images/features/boustrophedon_grid.png", (800, 450))


# ==============================================================================
# 5. SPEED CLAMPING AMAN (800x450)
# ==============================================================================
def gen_feat_speed_clamping():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "DYNAMIC SPEED CLAMPING // ANTI-MOTION BLUR", AMBER)
    
    cx, cy, r = 800, 540, 280
    # Dial arcs
    # Safe zone (Green): 180 to 270 deg
    draw.arc([cx-r, cy-r, cx+r, cy+r], 180, 270, fill=EMERALD, width=36)
    # Warning zone (Amber): 270 to 320 deg
    draw.arc([cx-r, cy-r, cx+r, cy+r], 270, 320, fill=AMBER, width=36)
    # Clamp zone (Red): 320 to 360 deg
    draw.arc([cx-r, cy-r, cx+r, cy+r], 320, 360, fill=RED, width=36)
    
    # Speed Needle pointing to 7.8 m/s (safe clamp)
    angle = math.radians(285)
    nx, ny = cx + (r - 40)*math.cos(angle), cy + (r - 40)*math.sin(angle)
    draw.line([cx, cy, nx, ny], fill=WHITE, width=10)
    draw.ellipse([cx-25, cy-25, cx+25, cy+25], fill=WHITE, outline=SLATE_900, width=6)
    
    # Digital Speed Readout
    font_bold = get_font(FONT_BOLD, 72)
    font_sub = get_font(FONT_BOLD, 32)
    draw.text((cx, cy - 140), "7.8 m/s", font=font_bold, fill=WHITE, anchor="mm")
    draw.text((cx, cy - 70), "OPTIMAL SHUTTER SPEED", font=font_sub, fill=EMERALD, anchor="mm")
    
    # Clamping Limit Tag
    draw.rounded_rectangle([cx - 260, cy + 80, cx + 260, cy + 150], radius=12, fill=SLATE_900, outline=AMBER, width=4)
    draw.text((cx, cy + 115), "SPEED CLAMP ACTIVE: MAX 8.0 m/s", font=font_sub, fill=AMBER, anchor="mm")
    
    save_scaled(im, "images/features/speed_clamping.png", (800, 450))


# ==============================================================================
# 6. ASYMMETRICAL CORRIDOR (800x450)
# ==============================================================================
def gen_feat_corridor_buffer():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "ASYMMETRICAL CORRIDOR // INFRASTRUCTURE & RIVER", TEAL)
    
    # Center centerline curve (S-Curve)
    center_pts = [(160, 450), (450, 320), (800, 580), (1150, 340), (1440, 460)]
    
    # Asymmetric buffer polygons
    # Left buffer (Wide: +70m)
    left_pts = [(160, 240), (450, 110), (800, 370), (1150, 130), (1440, 250)]
    # Right buffer (Narrow: -30m)
    right_pts = [(160, 570), (450, 440), (800, 700), (1150, 460), (1440, 580)]
    
    # Fill buffers
    draw.polygon(left_pts + center_pts[::-1], fill=(15, 35, 45))
    draw.polygon(center_pts + right_pts[::-1], fill=(15, 45, 30))
    
    # Draw buffer boundary lines
    for i in range(len(left_pts)-1):
        draw.line([left_pts[i], left_pts[i+1]], fill=TEAL, width=5)
    for i in range(len(right_pts)-1):
        draw.line([right_pts[i], right_pts[i+1]], fill=EMERALD, width=5)
        
    # Draw centerline (Highway/Pipeline)
    for i in range(len(center_pts)-1):
        draw.line([center_pts[i], center_pts[i+1]], fill=AMBER, width=8)
        
    # Drone on corridor
    draw_drone(draw, 800, 580, size=65, color=WHITE)
    
    # Labels
    font = get_font(FONT_BOLD, 36)
    draw.text((450, 200), "LEFT BUFFER: +70m", font=font, fill=TEAL, anchor="mm")
    draw.text((450, 510), "RIGHT BUFFER: -30m", font=font, fill=EMERALD, anchor="mm")
    draw.text((1150, 400), "CENTERLINE TRACK", font=font, fill=AMBER, anchor="mm")
    
    save_scaled(im, "images/features/corridor_buffer.png", (800, 450))


# ==============================================================================
# 7. FLASH INJECT INSTAN (800x450)
# ==============================================================================
def gen_feat_flash_inject():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "FLASH INJECT // DIRECTORY INJECTION < 1 SECOND", TEAL)
    
    # Left Card: TW-Mapper App
    draw.rounded_rectangle([180, 280, 540, 680], radius=16, fill=SLATE_900, outline=TEAL, width=5)
    font_card = get_font(FONT_BOLD, 36)
    draw.text((360, 340), "TW-MAPPER", font=font_card, fill=TEAL, anchor="mm")
    draw.text((360, 400), "Flight Engine", font=get_font(FONT_REG, 28), fill=SLATE_400, anchor="mm")
    # Mission icon inside
    draw.rectangle([250, 460, 470, 600], outline=TEAL_DARK, fill=SLATE_800, width=3)
    draw.text((360, 530), "WAYPOINT\nMISSION.KMZ", font=get_font(FONT_MONO, 24), fill=WHITE, align="center", anchor="mm")
    
    # Center Lightning Flash Bolt
    bolt = [(650, 380), (840, 380), (760, 500), (950, 500), (730, 720), (800, 550), (620, 550)]
    draw.polygon(bolt, fill=TEAL, outline=WHITE)
    draw.text((800, 310), "< 1s INJECT", font=get_font(FONT_BOLD, 46), fill=WHITE, anchor="mm")
    draw.text((800, 760), "ZERO RESTART", font=get_font(FONT_BOLD, 32), fill=EMERALD, anchor="mm")
    
    # Right Card: DJI Fly Remote Storage
    draw.rounded_rectangle([1060, 280, 1420, 680], radius=16, fill=SLATE_900, outline=EMERALD, width=5)
    draw.text((1240, 340), "DJI FLY REMOTE", font=font_card, fill=EMERALD, anchor="mm")
    draw.text((1240, 400), "RC 2 / RC Pro Storage", font=get_font(FONT_REG, 28), fill=SLATE_400, anchor="mm")
    draw.rectangle([1130, 460, 1350, 600], outline=EMERALD_DARK, fill=SLATE_800, width=3)
    draw.text((1240, 530), "STATUS:\nREADY TO FLY", font=get_font(FONT_BOLD, 26), fill=EMERALD, align="center", anchor="mm")
    
    save_scaled(im, "images/features/flash_inject.png", (800, 450))


# ==============================================================================
# 8. DIRECT & FLEET SYNC (800x450)
# ==============================================================================
def gen_feat_fleet_sync():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "DIRECT & FLEET SYNC // DECENTRALIZED P2P MESH", TEAL)
    
    # 3 Remote nodes in triangle
    nodes = [(400, 380, "RC 2 (Leader)"), (1200, 380, "RC Pro (Co-Pilot)"), (800, 700, "Android Phone")]
    
    # Connective sync lines
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            draw.line([nodes[i][:2], nodes[j][:2]], fill=TEAL_DARK, width=6)
            
    # Node boxes
    font_node = get_font(FONT_BOLD, 32)
    font_sub = get_font(FONT_MONO, 24)
    for x, y, name in nodes:
        draw.rounded_rectangle([x-180, y-80, x+180, y+80], radius=16, fill=SLATE_900, outline=TEAL, width=5)
        draw.text((x, y-20), name, font=font_node, fill=WHITE, anchor="mm")
        draw.text((x, y+25), "SYNC ACTIVE [P2P]", font=font_sub, fill=EMERALD, anchor="mm")
        
    # Center Sync Icon
    cx, cy = 800, 460
    draw.ellipse([cx-70, cy-70, cx+70, cy+70], fill=SLATE_900, outline=WHITE, width=4)
    draw.text((cx, cy-12), "100%", font=font_node, fill=TEAL, anchor="mm")
    draw.text((cx, cy+20), "OFFLINE", font=font_sub, fill=WHITE, anchor="mm")
    
    save_scaled(im, "images/features/fleet_sync.png", (800, 450))


# ==============================================================================
# 9. 100% PETA OFFLINE (800x450)
# ==============================================================================
def gen_feat_offline_maps():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "100% OFFLINE MAPS // HIGH-RES SATELLITE CACHE", TEAL)
    
    # 3x3 Tile Grid
    start_x, start_y = 480, 260
    tile_w, tile_h = 200, 140
    gap = 20
    for r in range(3):
        for c in range(3):
            tx = start_x + c*(tile_w + gap)
            ty = start_y + r*(tile_h + gap)
            color = EMERALD if (r, c) == (1, 1) else SLATE_700
            draw.rounded_rectangle([tx, ty, tx+tile_w, ty+tile_h], radius=8, fill=SLATE_900, outline=color, width=3)
            # Contour / terrain hint inside tile
            draw.line([tx+30, ty+100, tx+100, ty+40, tx+170, ty+80], fill=SLATE_800, width=4)
            
    # Center tile badge: CACHED
    cx, cy = start_x + tile_w + gap + tile_w//2, start_y + tile_h + gap + tile_h//2
    draw.text((cx, cy), "CACHED\nOFFLINE", font=get_font(FONT_BOLD, 26), fill=EMERALD, align="center", anchor="mm")
    
    # Left status panel
    draw.rounded_rectangle([150, 340, 420, 660], radius=16, fill=SLATE_900, outline=EMERALD, width=4)
    font_bold = get_font(FONT_BOLD, 32)
    font_reg = get_font(FONT_REG, 24)
    draw.text((285, 410), "ZERO SIGNAL", font=font_bold, fill=WHITE, anchor="mm")
    draw.text((285, 460), "NO INTERNET", font=font_bold, fill=AMBER, anchor="mm")
    draw.text((285, 520), "Cached Zoom: 19", font=font_reg, fill=SLATE_400, anchor="mm")
    draw.text((285, 570), "Storage: Flash OK", font=font_reg, fill=EMERALD, anchor="mm")
    
    save_scaled(im, "images/features/offline_maps.png", (800, 450))


# ==============================================================================
# 10. LOCAL ELEVATION SERVER (800x450)
# ==============================================================================
def gen_feat_dem_server():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "LOCAL DEM SERVER // ON-DEVICE ELEVATION DATABASE", PURPLE)
    
    # Microchip / Server icon
    cx, cy = 800, 520
    draw.rectangle([cx-260, cy-180, cx+260, cy+180], fill=SLATE_900, outline=PURPLE, width=6)
    
    # Contour slices inside
    for i, offset in enumerate([-100, -40, 20, 80]):
        y = cy + offset
        draw.line([cx-220, y, cx-60, y-30, cx+80, y+40, cx+220, y], fill=TEAL if i==2 else SLATE_700, width=5)
        draw.text((cx+140, y-25), f"+{120 + i*40}m", font=get_font(FONT_MONO, 22), fill=PURPLE if i!=2 else TEAL)
        
    # Server status lights
    for i in range(4):
        draw.ellipse([cx-220 + i*35, cy-140, cx-200 + i*35, cy-120], fill=EMERALD)
        
    font_bold = get_font(FONT_BOLD, 36)
    draw.text((cx, cy+130), "EMBEDDED DEM SERVER", font=font_bold, fill=WHITE, anchor="mm")
    
    save_scaled(im, "images/features/dem_server.png", (800, 450))


# ==============================================================================
# 11. FOLLOW TERRAIN (800x450)
# ==============================================================================
def gen_feat_follow_terrain():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "FOLLOW TERRAIN // CONSTANT AGL ELEVATION FLIGHT", EMERALD)
    
    # Mountain terrain curve
    hill_pts = [(100, 780), (380, 720), (700, 440), (1050, 360), (1350, 680), (1500, 780)]
    draw.polygon(hill_pts + [(1500, 850), (100, 850)], fill=(15, 35, 25))
    for i in range(len(hill_pts)-1):
        draw.line([hill_pts[i], hill_pts[i+1]], fill=EMERALD, width=7)
        
    # Flight path (exactly 180px above terrain)
    flight_pts = [(p[0], p[1] - 180) for p in hill_pts]
    for i in range(len(flight_pts)-1):
        draw.line([flight_pts[i], flight_pts[i+1]], fill=TEAL, width=8)
        
    # Constant height arrows & laser beams
    font_mono = get_font(FONT_MONO, 28)
    for i in [1, 2, 3, 4]:
        fx, fy = flight_pts[i]
        hx, hy = hill_pts[i]
        draw.line([fx, fy, hx, hy], fill=WHITE, width=3)
        draw.text((fx + 15, (fy + hy)//2 - 15), "AGL 80m", font=font_mono, fill=WHITE)
        
    # Drone on flight path
    draw_drone(draw, flight_pts[3][0], flight_pts[3][1], size=65, color=WHITE)
    
    save_scaled(im, "images/features/follow_terrain.png", (800, 450))


# ==============================================================================
# 12. SPLIT MISI MULTI-BATERAI (800x450)
# ==============================================================================
def gen_feat_split_mission():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "SPLIT MISSION // MULTI-BATTERY SECTOR DIVISION", AMBER)
    
    # 3 Sector boxes side-by-side
    sectors = [
        (220, 260, 560, 740, TEAL, "SUB-MISSION 1\nBATTERY 1\n18 MIN"),
        (620, 260, 980, 740, EMERALD, "SUB-MISSION 2\nBATTERY 2\n19 MIN"),
        (1040, 260, 1380, 740, AMBER, "SUB-MISSION 3\nBATTERY 3\n17 MIN"),
    ]
    font_bold = get_font(FONT_BOLD, 36)
    for x1, y1, x2, y2, color, text in sectors:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=14, fill=SLATE_900, outline=color, width=6)
        # Miniature grid line inside
        for y in range(y1+80, y2-100, 60):
            draw.line([x1+40, y, x2-40, y], fill=SLATE_800, width=3)
        draw.text(((x1+x2)//2, (y1+y2)//2), text, font=font_bold, fill=color, align="center", anchor="mm")
        
    save_scaled(im, "images/features/split_mission.png", (800, 450))


# ==============================================================================
# 13. ORBIT HELIX SPIRAL 3D (800x450)
# ==============================================================================
def gen_feat_orbit_helix():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "CONTINUOUS HELIX 3D // 360° VERTICAL FACADE", TEAL)
    
    cx, cy = 800, 520
    # Central Tower
    draw.rounded_rectangle([cx-90, cy-220, cx+90, cy+220], radius=10, fill=SLATE_900, outline=SLATE_700, width=5)
    # Structural lattice
    for y in range(cy-200, cy+220, 70):
        draw.line([cx-90, y, cx+90, y], fill=SLATE_800, width=3)
        draw.line([cx-90, y-70, cx+90, y], fill=SLATE_800, width=2)
        
    # Spiral loops descending
    y_starts = [cy-180, cy-100, cy-20, cy+60, cy+140]
    for i, y in enumerate(y_starts):
        # Front loop curve
        draw.arc([cx-320, y-60, cx+320, y+60], 0, 180, fill=TEAL, width=7)
        # Waypoint camera dot
        draw.ellipse([cx+280-i*40 - 10, y+20 - 10, cx+280-i*40 + 10, y+20 + 10], fill=WHITE, outline=TEAL, width=4)
        
    # Drone focusing camera inward
    draw_drone(draw, cx+320, cy-60, size=60, color=EMERALD)
    draw.line([cx+320, cy-60, cx, cy-100], fill=WHITE, width=2)
    
    font = get_font(FONT_BOLD, 32)
    draw.text((cx, cy+260), "INWARD GIMBAL ROI LOCKED", font=font, fill=WHITE, anchor="mm")
    
    save_scaled(im, "images/features/orbit_helix.png", (800, 450))


# ==============================================================================
# 14. BREAKPOINT RESUME OTOMATIS (800x450)
# ==============================================================================
def gen_feat_breakpoint_resume():
    im, draw = create_canvas(1600, 900)
    draw_header_badge(draw, "AUTOMATIC BREAKPOINT RESUME // ZERO MISSION LOSS", EMERALD)
    
    # Path line: Completed (Green) -> Breakpoint -> Remaining (Dashed Cyan)
    start_pt = (200, 500)
    break_pt = (800, 500)
    end_pt = (1400, 500)
    
    # Completed leg
    draw.line([start_pt, break_pt], fill=EMERALD, width=10)
    # Remaining leg (dashed)
    for x in range(800, 1400, 40):
        draw.line([x, 500, x+25, 500], fill=TEAL, width=8)
        
    # Breakpoint Pin & Beacon
    draw.ellipse([800-45, 500-45, 800+45, 500+45], fill=SLATE_900, outline=AMBER, width=6)
    draw.ellipse([800-16, 500-16, 800+16, 500+16], fill=AMBER)
    
    font_bold = get_font(FONT_BOLD, 36)
    font_mono = get_font(FONT_MONO, 28)
    draw.text((800, 400), "BREAKPOINT (BATTERY LOW)", font=font_bold, fill=AMBER, anchor="mm")
    draw.text((800, 445), "Photo #42 Saved", font=font_mono, fill=WHITE, anchor="mm")
    
    draw.text((450, 560), "COMPLETED TRACK", font=font_bold, fill=EMERALD, anchor="mm")
    draw.text((1150, 560), "RESUME TRACK (NEW BATTERY)", font=font_bold, fill=TEAL, anchor="mm")
    
    save_scaled(im, "images/features/breakpoint_resume.png", (800, 450))


if __name__ == "__main__":
    print("Generating all 14 flat design graphics...")
    gen_icon_hobby()
    gen_icon_pro()
    gen_feat_multi_area()
    gen_feat_boustrophedon_grid()
    gen_feat_speed_clamping()
    gen_feat_corridor_buffer()
    gen_feat_flash_inject()
    gen_feat_fleet_sync()
    gen_feat_offline_maps()
    gen_feat_dem_server()
    gen_feat_follow_terrain()
    gen_feat_split_mission()
    gen_feat_orbit_helix()
    gen_feat_breakpoint_resume()
    print("ALL 14 FLAT DESIGN GRAPHICS GENERATED SUCCESSFULLY!")
