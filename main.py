import pygame
import sys
import random
import os
import time

# --- 1. Configuration & Constants ---
GRID_SIZE = 80
CELL_SIZE = 10 
BOARD_SIZE = GRID_SIZE * CELL_SIZE
SIDE_PANEL_WIDTH = 300 
WINDOW_WIDTH = BOARD_SIZE + (SIDE_PANEL_WIDTH * 2) 
WINDOW_HEIGHT = BOARD_SIZE
FPS = 60

# Colors
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
PLAYER_COLOR, AI_COLOR = (0, 200, 100), (230, 70, 70)
GLOW_COLOR, COOLDOWN_COLOR = (0, 255, 255), (255, 165, 0)
PANEL_BG, DESTROYED_COLOR = (20, 20, 25), (40, 40, 40)
COOLDOWN_GRAY = (100, 100, 105) 
OCEAN_DEEP = (0, 50, 90)
OCEAN_MID = (0, 70, 110)
OCEAN_LIGHT = (0, 90, 140)
OCEAN_FOAM = (100, 180, 220)
PREVIEW_COLOR = (0, 255, 255, 80) 

# Unit Visual Mapping
UNIT_SCHEMES = {
    "Scout": {"color": (200, 255, 100), "detail": "rect"},
    "Corvette": {"color": (100, 200, 255), "detail": "stripe"},
    "Frigate": {"color": (200, 100, 255), "detail": "dots"},
    "Destroyer": {"color": (255, 150, 50), "detail": "cross"},
    "Carrier": {"color": (210, 225, 235), "detail": "deck"} # Updated: Lighter Steel Blue
}

# Asset Directory
ASSET_DIR = "doodads"

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Sinker 1945: Strategic Intel")

# --- 2. Asset Loading Logic ---
def load_sound(filename):
    path = os.path.join(ASSET_DIR, filename)
    if os.path.exists(path):
        try: return pygame.mixer.Sound(path)
        except: print(f"Error loading {path}")
    return None

def load_image(filename, scale=None):
    path = os.path.join(ASSET_DIR, filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if scale: return pygame.transform.scale(img, scale)
            return img
        except: print(f"Error loading {path}")
    return None

sonar_sound = load_sound("sonar.mp3")
shot_1_sound = load_sound("shot_1.mp3")
shot_2_sound = load_sound("shot_2.mp3")
plane_sound = load_sound("plane.mp3")
bell_sound = load_sound("bell.mp3")
start_sound = load_sound("start.mp3")
move_sound = load_sound("move.mp3")

music_path = os.path.join(ASSET_DIR, "music.mp3")
if os.path.exists(music_path):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.65) 
        pygame.mixer.music.play(-1)
    except: pass

splash_img = load_image("splash.png", (WINDOW_WIDTH, WINDOW_HEIGHT))

# Fonts
header_font = pygame.font.SysFont("Consolas", 22, bold=True)
font = pygame.font.SysFont("Consolas", 14, bold=True)
log_font = pygame.font.SysFont("Consolas", 13)
health_font = pygame.font.SysFont("Consolas", 10, bold=True)
name_tag_font = pygame.font.SysFont("Consolas", 9, bold=True)
clock = pygame.time.Clock()

# --- 3. Patterns & Data ---
CROSS_COORDS = [(0,1), (1,0), (1,1), (1,2), (2,1)]

# --- 4. Ocean Pre-render ---
water_map = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        base_col = random.choice([OCEAN_DEEP, OCEAN_MID, OCEAN_MID, OCEAN_LIGHT])
        pygame.draw.rect(water_map, base_col, rect)
        if random.random() > 0.95:
            px, py = random.randint(0, CELL_SIZE-1), random.randint(0, CELL_SIZE-1)
            water_map.set_at((x * CELL_SIZE + px, y * CELL_SIZE + py), OCEAN_FOAM)

# --- 5. Animation Classes ---
class BurningPixel:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.life = random.randint(15, 45)
        self.vx, self.vy = random.uniform(-0.3, 0.3), random.uniform(-0.8, -0.1)
        
    def update(self):
        self.life -= 1
        self.x += self.vx
        self.y += self.vy
        return self.life > 0

    def draw(self, surface):
        if self.life > 25: col = (255, 255, 150)
        elif self.life > 12: col = (255, 100, 0)
        else: col = (150, 20, 0)
        pygame.draw.rect(surface, col, (self.x + SIDE_PANEL_WIDTH, self.y, max(1, self.life//12), max(1, self.life//12)))

# --- 6. Game Logic & Classes ---
class Unit:
    def __init__(self, name, size, x, y, orientation, side, evasion, ammo):
        self.name, self.size, self.side, self.evasion, self.ammo_capacity = name, size, side, evasion, ammo
        self.orientation = orientation
        self.cooldown, self.health_map, self.is_selected = 0, [True] * size, False
        self.grid_pos = []
        self.rects = []
        self.is_revealed = False 
        self.scheme = UNIT_SCHEMES.get(name, {"color": PLAYER_COLOR, "detail": "rect"})
        self.update_geometry(x, y)

    def update_geometry(self, x, y):
        self.grid_pos = []
        self.rects = []
        for i in range(self.size):
            gx, gy = (x + i, y) if self.orientation == "H" else (x, y + i)
            self.grid_pos.append((gx, gy))
            self.rects.append(pygame.Rect(gx * CELL_SIZE + SIDE_PANEL_WIDTH, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    @property
    def current_hp(self): return sum(self.health_map)
    @property
    def is_destroyed(self): return self.current_hp == 0

    def draw(self, surface):
        known = False
        min_x = min(r.x for r in self.rects)
        max_x = max(r.right for r in self.rects)
        max_y = max(r.bottom for r in self.rects)
        
        for i, rect in enumerate(self.rects):
            rev = ai_fog[self.grid_pos[i][1]][self.grid_pos[i][0]] >= 1 or not self.health_map[i]
            if rev: self.is_revealed = True
            
            if self.side == "player" or rev:
                known = True
                base_col = self.scheme["color"]
                if self.side == "player" and self.cooldown > 0: base_col = COOLDOWN_GRAY
                if not self.health_map[i]: base_col = (60, 20, 20) if self.side == "ai" else (50, 50, 50)
                if self.is_destroyed: base_col = DESTROYED_COLOR
                if self.is_selected: base_col = GLOW_COLOR
                
                pygame.draw.rect(surface, base_col, rect)
                
                detail = self.scheme["detail"]
                detail_col = (max(0, base_col[0]-40), max(0, base_col[1]-40), max(0, base_col[2]-40))
                if detail == "stripe":
                    pygame.draw.line(surface, detail_col, rect.topleft, rect.bottomright, 1)
                elif detail == "dots":
                    pygame.draw.circle(surface, detail_col, rect.center, 2)
                elif detail == "cross":
                    pygame.draw.line(surface, detail_col, (rect.centerx, rect.top), (rect.centerx, rect.bottom), 1)
                elif detail == "deck":
                    pygame.draw.rect(surface, (100, 100, 100), rect.inflate(-4, -4))

                pygame.draw.rect(surface, BLACK, rect, 1)

        if known and not self.is_destroyed:
            surface.blit(health_font.render(f"{self.current_hp}/{self.size}", True, WHITE), (self.rects[0].x, self.rects[0].y - 12))
            name_tag = name_tag_font.render(self.name, True, (200, 200, 200))
            text_x = min_x + (max_x - min_x)//2 - name_tag.get_width()//2
            surface.blit(name_tag, (text_x, max_y + 2))

def fire_at(tx, ty, targets, side_firing):
    global player_stats, ai_stats, active_fires, current_score
    stats = player_stats if side_firing == "PLAYER" else ai_stats
    for unit in targets:
        if (tx, ty) in unit.grid_pos:
            idx = unit.grid_pos.index((tx, ty))
            if not unit.health_map[idx]: return "ALREADY_HIT"
            stats["shots"] += 1
            if random.random() > unit.evasion:
                unit.health_map[idx] = False
                stats["hits"] += 1
                if side_firing == "PLAYER":
                    # Unified real-time score updates
                    current_score += 100
                    if unit.is_destroyed: current_score += 500
                
                for _ in range(20):
                    active_fires.append(BurningPixel(tx * CELL_SIZE + random.randint(0, 8), ty * CELL_SIZE + random.randint(0, 8)))
                
                add_log(side_firing, "STRIKE", f"Impact! {unit.name} hit at {tx},{ty}", is_hit=True)
                return "HIT"
            else:
                add_log(side_firing, "STRIKE", f"Target at {tx},{ty} evaded.")
                return "EVADED"
    stats["shots"] += 1
    add_log(side_firing, "MISS", f"Splash at {tx},{ty}.")
    return "MISS"

def calculate_final_score():
    global final_score
    # Ensures final score calculation is a derivation of current_score
    eff_multiplier = (player_stats["hits"] / max(1, player_stats["shots"]))
    survival_bonus = sum(u.current_hp for u in player_units) * 200
    final_score = int((current_score * eff_multiplier * survival_bonus)/300)  # Balanced scaling for final score

def add_log(side, action_type, message, is_hit=False):
    color = PLAYER_COLOR if side == "PLAYER" else (AI_COLOR if side == "AI" else WHITE)
    full_msg = f"[{side}] [{action_type}] {message}"
    words = full_msg.split(' ')
    lines, current_line = [], []
    for word in words:
        if log_font.size(' '.join(current_line + [word]))[0] < SIDE_PANEL_WIDTH - 40:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    for line in lines:
        admirals_log.append({"msg": line, "hit": is_hit, "color": color})
    if len(admirals_log) > 40: admirals_log.pop(0)

def draw_tooltip(surface, text_lines, pos):
    padding = 8
    line_height = 16
    max_w = max(font.size(line)[0] for line in text_lines) + (padding * 2)
    total_h = (len(text_lines) * line_height) + (padding * 2)
    tx, ty = pos[0] + 15, pos[1] + 15
    if tx + max_w > WINDOW_WIDTH: tx = pos[0] - max_w - 15
    if ty + total_h > WINDOW_HEIGHT: ty = pos[1] - total_h - 15
    tip_rect = pygame.Rect(tx, ty, max_w, total_h)
    pygame.draw.rect(surface, (30, 30, 40), tip_rect)
    pygame.draw.rect(surface, GLOW_COLOR, tip_rect, 1)
    for i, line in enumerate(text_lines):
        surface.blit(font.render(line, True, WHITE), (tx + padding, ty + padding + (i * line_height)))

def draw_panels(ai_thinking=False):
    # --- Left Panel ---
    pygame.draw.rect(screen, PANEL_BG, (0, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    pygame.draw.line(screen, WHITE, (SIDE_PANEL_WIDTH, 0), (SIDE_PANEL_WIDTH, WINDOW_HEIGHT), 2)
    screen.blit(header_font.render("ADMIRAL'S LOG", True, GLOW_COLOR), (20, 20))
    y_off = WINDOW_HEIGHT - 40
    for entry in reversed(admirals_log):
        col = (255, 50, 50) if entry["hit"] else entry["color"]
        screen.blit(log_font.render(entry["msg"], True, col), (15, y_off))
        y_off -= 18
        if y_off < 60: break

    # --- Right Panel ---
    stats_x = SIDE_PANEL_WIDTH + BOARD_SIZE
    pygame.draw.rect(screen, PANEL_BG, (stats_x, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    pygame.draw.line(screen, WHITE, (stats_x, 0), (stats_x, WINDOW_HEIGHT), 2)
    screen.blit(header_font.render("FLEET INTEL", True, GLOW_COLOR), (stats_x + 20, 20))
    
    if ai_thinking:
        pulse = (pygame.time.get_ticks() // 200) % 2
        col = AI_COLOR if pulse else (255, 255, 255)
        screen.blit(font.render("AI IS ANALYZING TACTICS...", True, col), (stats_x + 20, 60))
    else:
        t_col = PLAYER_COLOR if turn == "player" else AI_COLOR
        screen.blit(font.render(f"TURN: {turn.upper()}", True, t_col), (stats_x + 20, 60))
    
    # Live score display
    screen.blit(font.render(f"SCORE: {current_score:06}", True, WHITE), (stats_x + 20, 80))
    
    if selected_unit:
        pygame.draw.rect(screen, (40, 40, 50), (stats_x + 10, 105, SIDE_PANEL_WIDTH - 20, 45))
        screen.blit(font.render(f"CMD: {selected_unit.name.upper()}", True, GLOW_COLOR), (stats_x + 20, 110))
        screen.blit(font.render(f"AMMO: {shots_remaining}", True, WHITE), (stats_x + 20, 130))

    curr_y = 170
    screen.blit(font.render("PLAYER FLEET", True, PLAYER_COLOR), (stats_x + 20, curr_y))
    curr_y += 20
    for u in player_units:
        col = WHITE if not u.is_destroyed else (150, 50, 50)
        cd_text = f"CD: {u.cooldown}" if u.cooldown > 0 else "READY"
        u_text = f"{u.name:10} HP: {u.current_hp}/{u.size} [{cd_text}]"
        screen.blit(log_font.render(u_text, True, col), (stats_x + 25, curr_y))
        curr_y += 16

    curr_y += 20
    screen.blit(font.render("AI FLEET (INTEL)", True, AI_COLOR), (stats_x + 20, curr_y))
    curr_y += 20
    for u in ai_units:
        revealed = u.is_revealed or any(ai_fog[p[1]][p[0]] > 0 for p in u.grid_pos) or u.current_hp < u.size
        name_str = u.name if revealed else "????"
        hp_str = f"{u.current_hp}/{u.size}" if revealed else "?/?"
        col = WHITE if not u.is_destroyed else (150, 50, 50)
        u_text = f"{name_str:12} HP: {hp_str} [{'SUNK' if u.is_destroyed else 'OK'}]"
        screen.blit(log_font.render(u_text, True, col), (stats_x + 25, curr_y))
        curr_y += 16

# --- 7. Global State ---
game_state = "WELCOME"
admirals_log, player_stats, ai_stats = [], {"shots": 0, "hits": 0}, {"shots": 0, "hits": 0}
winner, player_units, ai_units = None, [], []
turn, selected_unit, shots_remaining = "player", None, 0
current_score, final_score = 0, 0
ai_fog = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
player_map = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
active_fires = []
ai_water_offset = 0
player_water_offset = 0

def reset_game():
    global player_units, ai_units, ai_fog, player_map, player_stats, ai_stats, admirals_log, turn, game_state, selected_unit, winner, active_fires, current_score
    pool = [("Scout", 1, 0.0, 1), ("Corvette", 2, 0.4, 1), ("Frigate", 3, 0.2, 2), ("Destroyer", 4, 0.15, 1), ("Carrier", 5, 0.08, 5)]
    player_units, ai_units, active_fires = [], [], []
    for side, y_bounds in [("ai", (1, 38)), ("player", (41, 78))]:
        occ = set()
        selection = pool if side == "player" else [random.choice(pool) for _ in range(5)]
        for name, size, eva, ammo in selection:
            placed = False
            while not placed:
                ori = random.choice(["H", "V"])
                mx, my = GRID_SIZE - (size if ori == "H" else 1), y_bounds[1] - (size if ori == "V" else 0)
                sx, sy = random.randint(0, mx), random.randint(y_bounds[0], my)
                cells = [(sx+i, sy) if ori == "H" else (sx, sy+i) for i in range(size)]
                if not any(c in occ for c in cells):
                    u = Unit(name, size, sx, sy, ori, side, eva, ammo)
                    if side == "ai": ai_units.append(u)
                    else: player_units.append(u)
                    occ.update(cells); placed = True
    ai_fog = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    player_map = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    player_stats, ai_stats = {"shots": 0, "hits": 0}, {"shots": 0, "hits": 0}
    admirals_log, turn, game_state, winner, current_score = [], "player", "PLAYING", None, 0

def random_pause_thinking():
    start_time = time.time()
    duration = random.uniform(0.4, 0.9)
    while time.time() - start_time < duration:
        draw_game_elements(ai_thinking=True)
        pygame.display.flip()
        clock.tick(FPS)

def draw_game_elements(ai_thinking=False):
    screen.fill(BLACK)
    global ai_water_offset, player_water_offset
    ai_water_offset = (ai_water_offset - 0.5) % BOARD_SIZE
    player_water_offset = (player_water_offset + 0.5) % BOARD_SIZE
    ai_rect = pygame.Rect(0, 0, BOARD_SIZE, BOARD_SIZE//2)
    screen.blit(water_map, (SIDE_PANEL_WIDTH + ai_water_offset, 0), ai_rect)
    screen.blit(water_map, (SIDE_PANEL_WIDTH + ai_water_offset - BOARD_SIZE, 0), ai_rect)
    player_rect = pygame.Rect(0, BOARD_SIZE//2, BOARD_SIZE, BOARD_SIZE//2)
    screen.blit(water_map, (SIDE_PANEL_WIDTH + player_water_offset, BOARD_SIZE//2), player_rect)
    screen.blit(water_map, (SIDE_PANEL_WIDTH + player_water_offset - BOARD_SIZE, BOARD_SIZE//2), player_rect)
    
    draw_panels(ai_thinking=ai_thinking)
    
    for y in range(40):
        for x in range(GRID_SIZE):
            gx = x*CELL_SIZE + SIDE_PANEL_WIDTH
            if ai_fog[y][x] == 0:
                s = pygame.Surface((CELL_SIZE, CELL_SIZE)); s.set_alpha(170); s.fill((10, 15, 30))
                screen.blit(s, (gx, y*CELL_SIZE))
            elif ai_fog[y][x] == 2: pygame.draw.circle(screen, WHITE, (gx + 5, y*CELL_SIZE + 5), 1)
    for y in range(40, GRID_SIZE):
        for x in range(GRID_SIZE):
            if player_map[y][x] == 1: pygame.draw.rect(screen, (255, 120, 0), (x*CELL_SIZE + SIDE_PANEL_WIDTH+3, y*CELL_SIZE+3, 4, 4))

    for u in player_units + ai_units: u.draw(screen)
    
    for fire in active_fires[:]:
        if not fire.update(): active_fires.remove(fire)
        else: fire.draw(screen)
    
    pygame.draw.line(screen, (0, 100, 255), (SIDE_PANEL_WIDTH, 40*CELL_SIZE), (WINDOW_WIDTH - SIDE_PANEL_WIDTH, 40*CELL_SIZE), 2)

# --- 8. Main Loop ---
start_btn = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 60, 200, 60)

while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        
    if game_state == "WELCOME":
        screen.fill(BLACK)
        if splash_img: screen.blit(splash_img, (0, 0))
        s_hover = start_btn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, PLAYER_COLOR if s_hover else (0, 150, 80), start_btn, border_radius=8)
        btn_text = header_font.render("START MISSION", True, WHITE)
        screen.blit(btn_text, (start_btn.centerx - btn_text.get_width()//2, start_btn.centery - btn_text.get_height()//2))
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and start_btn.collidepoint(event.pos):
                if start_sound: start_sound.play(); reset_game()

    elif game_state == "PLAYING":
        draw_game_elements()
        m_pos = pygame.mouse.get_pos()
        mx, my = (m_pos[0] - SIDE_PANEL_WIDTH) // CELL_SIZE, m_pos[1] // CELL_SIZE

        hovered_unit = next((u for u in player_units if any(r.collidepoint(m_pos) for r in u.rects)), None)
        unit_to_show = hovered_unit or (selected_unit if selected_unit else None)
        if unit_to_show and unit_to_show.side == "player":
            intel = [f"UNIT: {unit_to_show.name.upper()}"]
            patterns = {
                "Scout": ["Type: RECON", "Effect: Reveal 16x16 Area", "CD: 6 Turns"],
                "Destroyer": ["Type: AOE", "Effect: Cross Pattern (+)", "CD: 4 Turns"],
                "Carrier": ["Type: HEAVY STRIKE", "Effect: 2x2 Square", "CD: 6 Turns"],
                "Frigate": ["Type: LIGHT STRIKE", "Effect: 2x2 Square", "CD: 2 Turns"],
                "Corvette": ["Type: SCOUT STRIKE", "Effect: 1x1 Precise", "CD: 0 Turns"]
            }
            intel.extend(patterns.get(unit_to_show.name, ["Type: Standard", "Effect: 1x1 Precise"]))
            draw_tooltip(screen, intel, m_pos)

        if turn == "player" and selected_unit and 0 <= mx < GRID_SIZE and 0 <= my < 40:
            preview_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            if selected_unit.name == "Destroyer":
                for dx, dy in CROSS_COORDS:
                    if 0 <= mx+dx < GRID_SIZE and 0 <= my+dy < 40:
                        pygame.draw.rect(preview_surface, PREVIEW_COLOR, pygame.Rect((mx+dx)*CELL_SIZE + SIDE_PANEL_WIDTH, (my+dy)*CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif selected_unit.name == "Scout":
                pygame.draw.rect(preview_surface, (0, 255, 255, 40), pygame.Rect((mx-8)*CELL_SIZE + SIDE_PANEL_WIDTH, (my-8)*CELL_SIZE, 16*CELL_SIZE, 16*CELL_SIZE))
            else:
                rad = {"Carrier": 2, "Frigate": 2}.get(selected_unit.name, 1)
                for dy in range(rad):
                    for dx in range(rad):
                        if 0 <= mx+dx < GRID_SIZE and 0 <= my+dy < 40:
                            pygame.draw.rect(preview_surface, PREVIEW_COLOR, pygame.Rect((mx+dx)*CELL_SIZE + SIDE_PANEL_WIDTH, (my+dy)*CELL_SIZE, CELL_SIZE, CELL_SIZE))
            screen.blit(preview_surface, (0,0))

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                add_log("PLAYER", "SURRENDER", "Admiral retreat initiated.")
                calculate_final_score(); winner, game_state = "AI", "GAME_OVER"
            
            if event.type == pygame.MOUSEBUTTONDOWN and turn == "player":
                clicked = next((u for u in player_units if any(r.collidepoint(m_pos) for r in u.rects)), None)
                if clicked and not clicked.is_destroyed and clicked.cooldown == 0:
                    if bell_sound: bell_sound.play()
                    if selected_unit: selected_unit.is_selected = False
                    selected_unit = clicked; selected_unit.is_selected = True
                    shots_remaining = selected_unit.ammo_capacity
                elif selected_unit and 0 <= mx < GRID_SIZE and 0 <= my < 40:
                    fresh_strike = False
                    if selected_unit.name == "Destroyer":
                        for dx, dy in CROSS_COORDS:
                            if 0 <= mx+dx < GRID_SIZE and 0 <= my+dy < 40:
                                res = fire_at(mx+dx, my+dy, ai_units, "PLAYER")
                                if res != "ALREADY_HIT": fresh_strike = True
                                ai_fog[my+dy][mx+dx] = 2
                        if fresh_strike and shot_2_sound: shot_2_sound.play()
                    elif selected_unit.name == "Scout":
                        if sonar_sound: sonar_sound.play()
                        for ry in range(my-8, my+8):
                            for rx in range(mx-8, mx+8):
                                if 0 <= rx < GRID_SIZE and 0 <= ry < 40:
                                    if ai_fog[ry][rx] != 2: ai_fog[ry][rx] = 1
                        fresh_strike = True
                    else:
                        rad = {"Carrier": 2, "Frigate": 2}.get(selected_unit.name, 1)
                        for dy in range(rad):
                            for dx in range(rad):
                                if 0 <= mx+dx < GRID_SIZE and 0 <= my+dy < 40:
                                    res = fire_at(mx+dx, my+dy, ai_units, "PLAYER")
                                    if res != "ALREADY_HIT": fresh_strike = True
                                    ai_fog[my+dy][mx+dx] = 2
                        sfx = {"Corvette": shot_1_sound, "Frigate": shot_1_sound, "Carrier": plane_sound}
                        if fresh_strike and sfx.get(selected_unit.name): sfx[selected_unit.name].play()
                    
                    if fresh_strike:
                        shots_remaining -= 1
                        if shots_remaining <= 0:
                            selected_unit.cooldown = {"Frigate": 2, "Destroyer": 4, "Carrier": 6, "Scout": 6}.get(selected_unit.name, 0)
                            selected_unit.is_selected = False; selected_unit = None
                            for u in player_units: 
                                if u.cooldown > 0: u.cooldown -= 1
                            random_pause_thinking(); turn = "ai"

        if turn == "ai":
            random_pause_thinking()
            avail = [u for u in ai_units if not u.is_destroyed and u.cooldown == 0]
            if avail:
                attacker = random.choice(avail)
                sfx_map = {"Corvette": shot_1_sound, "Frigate": shot_1_sound, "Destroyer": shot_2_sound, "Carrier": plane_sound}
                attack_sfx = sfx_map.get(attacker.name)
                if attack_sfx: attack_sfx.play()

                ammo = attacker.ammo_capacity
                while ammo > 0:
                    tx, ty = random.randint(0, GRID_SIZE-3), random.randint(40, GRID_SIZE-3)
                    if attacker.name == "Destroyer":
                        for dx, dy in CROSS_COORDS:
                            if 0 <= tx+dx < GRID_SIZE and 40 <= ty+dy < GRID_SIZE:
                                fire_at(tx+dx, ty+dy, player_units, "AI"); player_map[ty+dy][tx+dx] = 1
                    else:
                        rad = {"Carrier": 2, "Frigate": 2}.get(attacker.name, 1)
                        for dy in range(rad):
                            for dx in range(rad):
                                if 0 <= tx+dx < GRID_SIZE and 40 <= ty+dy < GRID_SIZE:
                                    fire_at(tx+dx, ty+dy, player_units, "AI"); player_map[ty+dy][tx+dx] = 1
                    ammo -= 1
                attacker.cooldown = {"Frigate": 2, "Destroyer": 4, "Carrier": 6}.get(attacker.name, 0)
            for u in ai_units: 
                if u.cooldown > 0: u.cooldown -= 1
            random_pause_thinking(); turn = "player"

        if sum(u.current_hp for u in ai_units) == 0:
            calculate_final_score(); winner, game_state = "PLAYER", "GAME_OVER"
        if sum(u.current_hp for u in player_units) == 0:
            calculate_final_score(); winner, game_state = "AI", "GAME_OVER"

    elif game_state == "GAME_OVER":
        screen.fill(BLACK)
        title_col = PLAYER_COLOR if winner == "PLAYER" else AI_COLOR
        
        # Header
        screen.blit(header_font.render(f"{winner} VICTORY", True, title_col), (WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 120))
        
        # Itemized Scoring breakdown
        eff = (player_stats["hits"] / max(1, player_stats["shots"]))
        surv_points = sum(u.current_hp for u in player_units) * 200
        
        score_items = [
            "[ FORMULA: (BASE COMBAST SCORE * MISSION ACCURACY * FLEET SURVIVAL) / 300 ]",
            f"-------------------------------",
            f"BASE COMBAT SCORE:  {current_score:06}",
            f"MISSION ACCURACY:   {eff*100:.1f}%",
            f"FLEET SURVIVAL:     {surv_points:06}",
            "-------------------------------",
            f"FINAL TOTAL SCORE:  {final_score:06}"
        ]
        
        item_y = WINDOW_HEIGHT // 2 - 40
        for i, line in enumerate(score_items):
            # Highlight the total score in the list
            col = GLOW_COLOR if "TOTAL" in line else WHITE
            screen.blit(font.render(line, True, col), (WINDOW_WIDTH//2 - 130, item_y + (i * 25)))

        # Footer Instruction
        screen.blit(font.render("PRESS R TO RETURN TO HQ", True, (150, 150, 150)), (WINDOW_WIDTH//2 - 110, item_y + 165))
        
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: 
                game_state = "WELCOME"
                
    pygame.display.flip()
    clock.tick(FPS)