import datetime
from datetime import datetime
import pygame
import sys
import random
import os
import time
import math

# --- 1. Configuration & Constants ---
GRID_SIZE = 80
CELL_SIZE = 10
BOARD_SIZE = GRID_SIZE * CELL_SIZE
SIDE_PANEL_WIDTH = 300
WINDOW_WIDTH = BOARD_SIZE + (SIDE_PANEL_WIDTH * 2)
WINDOW_HEIGHT = BOARD_SIZE
FPS = 60

# --- Intel Panel Dimensions ---
INTEL_W = 260  # Width of the ship images
INTEL_H = 180  # Height of each individual ship image
INTEL_GAP = 10 # Gap between the two images
INTEL_TOTAL_H = (INTEL_H * 2) + INTEL_GAP # Total height for the rain/lightning area

# Weather Constants
INTEL_RAIN_COLOR = (100, 100, 120, 150)
# Initialize rain drops based on the dynamic width and total height
intel_rain_drops = [[random.randint(0, INTEL_W), random.randint(0, INTEL_TOTAL_H)] for _ in range(50)]
last_lightning_time = 0
lightning_alpha = 0

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

UNIT_SCHEMES = {
    "Scout": {"color": (200, 255, 100), "detail": "rect"},
    "Corvette": {"color": (100, 200, 255), "detail": "battery"},
    "Frigate": {"color": (200, 100, 255), "detail": "battery"},
    "Destroyer": {"color": (255, 150, 50), "detail": "battery"},
    "Carrier": {"color": (70, 130, 180), "detail": "deck"},
    "Dreadnought": {"color": (150, 0, 0), "detail": "heavy_battery"} # New: Deep Red color
}

ASSET_DIR = "doodads"
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Sinker 1945: Strategic Intel")


def load_sound(filename):
    path = os.path.join(ASSET_DIR, filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except:
            print(f"Error loading {path}")
    return None


def load_image(filename, scale=None):
    path = os.path.join(ASSET_DIR, filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if scale: return pygame.transform.scale(img, scale)
            return img
        except:
            print(f"Error loading {path}")
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
    except:
        pass

splash_img = load_image("splash.png", (WINDOW_WIDTH, WINDOW_HEIGHT))
# --- Load End Game Backgrounds ---
ai_win_img = load_image("AI_win.png", (WINDOW_WIDTH, WINDOW_HEIGHT))
player_win_img = load_image("Player_win.png", (WINDOW_WIDTH, WINDOW_HEIGHT))

header_font = pygame.font.SysFont("Consolas", 22, bold=True)
font = pygame.font.SysFont("Consolas", 14, bold=True)
log_font = pygame.font.SysFont("Consolas", 13)
health_font = pygame.font.SysFont("Consolas", 10, bold=True)
name_tag_font = pygame.font.SysFont("Consolas", 9, bold=True)
clock = pygame.time.Clock()

water_map = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        base_col = random.choice([OCEAN_DEEP, OCEAN_MID, OCEAN_MID, OCEAN_LIGHT])
        pygame.draw.rect(water_map, base_col, rect)
        if random.random() > 0.95:
            px, py = random.randint(0, CELL_SIZE - 1), random.randint(0, CELL_SIZE - 1)
            water_map.set_at((x * CELL_SIZE + px, y * CELL_SIZE + py), OCEAN_FOAM)


class SHDSonarPulse:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 0
        self.max_radius = 120
        self.life = 255
        self.speed = 3.5

    def update(self):
        self.radius += self.speed
        self.life -= (255 / (self.max_radius / self.speed))
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, int(self.life))
        # Classic SHD Orange: (255, 120, 0)
        col = (0, 255, 80, alpha)
        # Draw main ring
        pygame.draw.circle(surface, col, (self.x, self.y), int(self.radius), 2)
        # Draw a faint inner ring for depth
        if self.radius > 10:
            pygame.draw.circle(surface, (255, 120, 0, alpha // 2), (self.x, self.y), int(self.radius - 8), 1)


class TacticalCloud:
    def __init__(self, side="player"):
        self.side = side
        self.reset()
        self.x = random.randint(SIDE_PANEL_WIDTH, SIDE_PANEL_WIDTH + BOARD_SIZE)

    def reset(self):
        if self.side == "ai":
            self.x = SIDE_PANEL_WIDTH + BOARD_SIZE + 100
            self.speed = random.uniform(-0.8, -0.3)
            self.y = random.randint(50, (BOARD_SIZE // 2) - 40)
        else:
            self.x = SIDE_PANEL_WIDTH - 100
            self.speed = random.uniform(0.3, 0.8)
            self.y = random.randint((BOARD_SIZE // 2) + 40, BOARD_SIZE - 50)
        self.opacity = random.randint(30, 80)
        self.size = random.randint(40, 80)
        self.blobs = [(random.randint(-20, 20), random.randint(-15, 15), random.uniform(0.8, 1.2)) for _ in range(3)]

    def update(self):
        self.x += self.speed
        if self.side == "player" and self.x > SIDE_PANEL_WIDTH + BOARD_SIZE + 100:
            self.reset()
        elif self.side == "ai" and self.x < SIDE_PANEL_WIDTH - 100:
            self.reset()

    def draw(self, surface):
        cloud_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        for bx, by, b_scale in self.blobs:
            r = int(self.size * b_scale)
            pygame.draw.circle(cloud_surf, (220, 230, 255, self.opacity), (100 + bx, 100 + by), r)
        clip_rect = pygame.Rect(SIDE_PANEL_WIDTH, 0, BOARD_SIZE, BOARD_SIZE // 2) if self.side == "ai" else pygame.Rect(
            SIDE_PANEL_WIDTH, BOARD_SIZE // 2, BOARD_SIZE, BOARD_SIZE // 2)
        surface.set_clip(clip_rect)
        surface.blit(cloud_surf, (self.x - 100, self.y - 100))
        surface.set_clip(None)


class WindParticle:
    def __init__(self):
        self.x = random.randint(SIDE_PANEL_WIDTH, SIDE_PANEL_WIDTH + BOARD_SIZE)
        self.y = random.randint(0, WINDOW_HEIGHT)
        self.vx = random.uniform(1.2, 2.5)
        self.length = random.randint(20, 60)
        self.opacity = random.randint(20, 60)

    def update(self):
        self.x += self.vx
        if self.x > SIDE_PANEL_WIDTH + BOARD_SIZE:
            self.x = SIDE_PANEL_WIDTH - self.length
            self.y = random.randint(0, WINDOW_HEIGHT)
        return True

    def draw(self, surface):
        wind_surf = pygame.Surface((self.length, 1), pygame.SRCALPHA)
        wind_surf.fill((255, 255, 255, self.opacity))
        surface.blit(wind_surf, (self.x, self.y))


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
        if self.life > 25:
            col = (255, 255, 150)
        elif self.life > 12:
            col = (255, 100, 0)
        else:
            col = (150, 20, 0)
        pygame.draw.rect(surface, col, (self.x, self.y, max(1, self.life // 12), max(1, self.life // 12)))


class SmokeParticle:
    def __init__(self, x, y, drift_speed):
        self.x, self.y = x, y
        self.life = random.randint(20, 50)
        self.vx = drift_speed
        self.vy = random.uniform(-0.5, -0.2)
        self.size = random.randint(2, 4)

    def update(self):
        self.life -= 1
        self.x += self.vx
        self.y += self.vy
        return self.life > 0

    def draw(self, surface):
        alpha = min(255, self.life * 5)
        gray = min(200, 255 - (self.life * 2))
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        s.fill((gray, gray, gray, alpha))
        surface.blit(s, (self.x + SIDE_PANEL_WIDTH, self.y))


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
        # Dreadnought Passive: Ignores the first 2 hits
        self.heavy_armor = 2 if name == "Dreadnought" else 0
        self.update_geometry(x, y)


    def update_geometry(self, x, y):
        self.grid_pos = []
        self.rects = []
        for i in range(self.size):
            gx, gy = (x + i, y) if self.orientation == "H" else (x, y + i)
            self.grid_pos.append((gx, gy))
            self.rects.append(pygame.Rect(gx * CELL_SIZE + SIDE_PANEL_WIDTH, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    @property
    def current_hp(self):
        return sum(self.health_map)

    @property
    def is_destroyed(self):
        return self.current_hp == 0

    def draw(self, surface):
        known = False
        # Calculate a floating offset based on time
        # 3.0 is the speed of the bobbing, 3.0 is the height (pixels)
        if not self.is_destroyed:
            bobbing_offset = math.sin(time.time() * 3.0 + (self.grid_pos[0][0] * 0.5)) * 3.0
        else:
            bobbing_offset = 0  # Sunk ships rest still on the seabed/surface

        min_x = min(r.x for r in self.rects)
        max_x = max(r.right for r in self.rects)
        max_y = max(r.bottom for r in self.rects)

        # Determine gun aim direction based on side
        gun_tip_offset = (0, -8) if self.side == "player" else (0, 8)

        for i, rect in enumerate(self.rects):
            # Apply the wobble to a temporary rect for drawing
            draw_rect = rect.copy()
            draw_rect.y += bobbing_offset

            rev = ai_fog[self.grid_pos[i][1]][self.grid_pos[i][0]] >= 1 or not self.health_map[i]
            if rev: self.is_revealed = True

            if self.side == "player" or rev:
                known = True
                base_col = self.scheme["color"]
                if self.side == "player" and self.cooldown > 0: base_col = COOLDOWN_GRAY
                if not self.health_map[i]: base_col = (60, 20, 20) if self.side == "ai" else (50, 50, 50)
                if self.is_destroyed: base_col = DESTROYED_COLOR
                if self.is_selected: base_col = GLOW_COLOR

                # --- Bow Logic ---
                if i == 0 and self.name != "Scout":
                    if self.orientation == "H":
                        pts = [draw_rect.midleft, draw_rect.topright, draw_rect.bottomright]
                    else:
                        pts = [draw_rect.midtop, draw_rect.bottomleft, draw_rect.bottomright]
                    pygame.draw.polygon(surface, base_col, pts)
                    pygame.draw.polygon(surface, BLACK, pts, 1)
                else:
                    pygame.draw.rect(surface, base_col, draw_rect)
                    pygame.draw.rect(surface, BLACK, draw_rect, 1)

                # --- Gun Battery Logic ---
                if not self.is_destroyed:
                    detail = self.scheme["detail"]
                    gun_col = (40, 40, 45)

                    if detail == "battery":
                        if self.name == "Corvette" and i == 1:
                            self._draw_battery(surface, draw_rect.center, gun_tip_offset, gun_col)
                        elif self.name == "Frigate" and i in [1, 2]:
                            self._draw_battery(surface, draw_rect.center, gun_tip_offset, gun_col)
                        elif self.name == "Destroyer" and i in [1, 3]:
                            for off in [-3, 0, 3]:
                                start_pos = (
                                    draw_rect.centerx + off, draw_rect.centery) if self.orientation == "V" else (
                                    draw_rect.centerx, draw_rect.centery + off)
                                self._draw_battery(surface, start_pos, gun_tip_offset, gun_col)
                    elif detail == "heavy_battery":
                        # Draw 3 Triple-Turrets along the 6-length hull
                        if i in [1, 3, 5]:
                            for off in [-4, 0, 4]:
                                # Corrected start_pos using draw_rect.centery
                                start_pos = (
                                draw_rect.centerx + off, draw_rect.centery) if self.orientation == "V" else (
                                draw_rect.centerx, draw_rect.centery + off)
                                self._draw_battery(surface, start_pos, gun_tip_offset, (20, 20, 20))
                    elif detail == "deck":
                        pygame.draw.rect(surface, (100, 100, 100), draw_rect.inflate(-4, -4))

        if known:
            # 1. Handle the Status Label (HP or [SUNK])
            if not self.is_destroyed:
                # Show HP if alive
                status_surf = health_font.render(f"{self.current_hp}/{self.size}", True, WHITE)
            else:
                # Show [SUNK] if destroyed
                status_surf = health_font.render("[SUNK]", True, (255, 50, 50))  # Red text for sunk

            surface.blit(status_surf, (self.rects[0].x, self.rects[0].y - 12 + bobbing_offset))
            # 2. Always draw the Name Tag (Set to WHITE as requested)
            name_tag = name_tag_font.render(self.name, True, WHITE)  # Changed from tuple to WHITE

            text_x = min_x + (max_x - min_x) // 2 - name_tag.get_width() // 2
            surface.blit(name_tag, (text_x, max_y + 2 + bobbing_offset))

            # 2. Always draw the Name Tag
            # Use a slightly darker color if sunk to differentiate
            text_color = (200, 200, 200) if not self.is_destroyed else (120, 120, 120)
            name_tag = name_tag_font.render(self.name, True, text_color)

            text_x = min_x + (max_x - min_x) // 2 - name_tag.get_width() // 2
            surface.blit(name_tag, (text_x, max_y + 2 + bobbing_offset))

    def _draw_battery(self, surface, center, tip_offset, color):
        end_pos = (center[0] + tip_offset[0], center[1] + tip_offset[1])
        pygame.draw.line(surface, (150, 150, 150), center, end_pos, 2)
        pygame.draw.circle(surface, color, center, 3)
        pygame.draw.circle(surface, BLACK, center, 3, 1)


def fire_at(tx, ty, targets, side_firing, source_pos=None, ignore_evasion=False):
    global player_stats, ai_stats, active_fires, current_score, active_trails
    stats = player_stats if side_firing == "PLAYER" else ai_stats

    for unit in targets:
        if (tx, ty) in unit.grid_pos:
            idx = unit.grid_pos.index((tx, ty))
            if not unit.health_map[idx]: return "ALREADY_HIT", None

            stats["shots"] += 1
            evaded = random.random() < unit.evasion if not ignore_evasion else False

            if not evaded:
                # DREADNOUGHT PASSIVE: Absorbs hits until armor is gone
                if unit.name == "Dreadnought" and unit.heavy_armor > 0:
                    unit.heavy_armor -= 1
                    return "ARMOR_BLOCKED", unit.name  # Handled in log

                unit.health_map[idx] = False
                stats["hits"] += 1
                if side_firing == "PLAYER": current_score += 100
                target_rect = unit.rects[idx]
                for _ in range(20):
                    px, py = target_rect.x + random.randint(0, CELL_SIZE), target_rect.y + random.randint(0, CELL_SIZE)
                    active_fires.append(BurningPixel(px, py))

                if unit.is_destroyed:
                    if side_firing == "PLAYER": current_score += 500
                    return "SUNK", unit.name
                return "HIT", unit.name
            else:
                return "EVADED", unit.name

    stats["shots"] += 1
    return "MISS", None


def log_attack_results(side, attacker_name, results):
    hits = [r for r in results if r[0] in ["HIT", "SUNK"]]
    sunk = [r[1] for r in results if r[0] == "SUNK"]
    evaded = any(r[0] == "EVADED" for r in results)

    if not hits:
        msg = "All rounds missed or evaded." if evaded else "No signatures detected in splash zone."
        add_log(side, "MISSED", f"{attacker_name} strike failed to connect. {msg}")
    else:
        targets_hit = list(set([r[1] for r in hits]))
        summary = f"{attacker_name} strike engaged {', '.join(targets_hit)}. {len(hits)} direct impacts."
        if sunk:
            summary += f" CRITICAL: {', '.join(list(set(sunk)))} neutralized."
            add_log(side, "CONFIRMED KILL", summary, is_hit=True)
        else:
            add_log(side, "DIRECT HIT", summary, is_hit=True)


def add_log(side, action_type, message, is_hit=False):
    color = PLAYER_COLOR if side == "PLAYER" else (AI_COLOR if side == "AI" else WHITE)
    if action_type == "CONFIRMED KILL":
        color = WHITE

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
    for line in lines: admirals_log.append({"msg": line, "hit": is_hit, "color": color})
    admirals_log.append({"msg": "[//" + str(datetime.now().isoformat()) + "//]", "hit": False, "color": color})
    admirals_log.append({"msg": "                                    ", "hit": False, "color": color})
    if len(admirals_log) > 40: admirals_log.pop(0)


def draw_aircraft(surface, center, target_pos, color, alpha):
    cx, cy = center
    tx, ty = target_pos
    angle = math.atan2(ty - cy, tx - cx)
    length, wing_span = 12, 14

    # Coordinates
    nose = (length * math.cos(angle), length * math.sin(angle))
    tail = (-length * math.cos(angle), -length * math.sin(angle))
    wing_angle = angle + math.pi / 2
    wing_l = (wing_span * math.cos(wing_angle), wing_span * math.sin(wing_angle))
    wing_r = (-wing_span * math.cos(wing_angle), -wing_span * math.sin(wing_angle))

    # --- AFTERBURNER LOGIC ---
    # Draw the flame behind the tail
    # We randomize the length slightly each frame to create a flicker
    flame_len = random.randint(5, 15)
    # The flame points in the opposite direction of the nose
    flame_tip = (cx + (length + flame_len) * math.cos(angle + math.pi),
                 cy + (length + flame_len) * math.sin(angle + math.pi))

    # Outer flame (Orange/Red)
    pygame.draw.line(surface, (255, 100, 0, alpha), (cx + tail[0], cy + tail[1]), flame_tip, 4)
    # Inner flame (Yellow/White core)
    pygame.draw.line(surface, (255, 255, 150, alpha), (cx + tail[0], cy + tail[1]),
                     (cx + (length + flame_len * 0.6) * math.cos(angle + math.pi),
                      cy + (length + flame_len * 0.6) * math.sin(angle + math.pi)), 2)

    # --- AIRCRAFT BODY ---
    pts = [(cx + nose[0], cy + nose[1]),
           (cx + wing_l[0], cy + wing_l[1]),
           (cx + tail[0] * 0.8, cy + tail[1] * 0.8),
           (cx + wing_r[0], cy + wing_r[1])]

    pygame.draw.polygon(surface, (*color, alpha), pts)
    # Cockpit detail
    pygame.draw.circle(surface, (255, 255, 255, alpha), (int(cx + nose[0] * 0.3), int(cy + nose[1] * 0.3)), 2)

def draw_tooltip(surface, text_lines, pos):
    padding, line_height = 8, 16
    max_w = max(font.size(line)[0] for line in text_lines) + (padding * 2)
    total_h = (len(text_lines) * line_height) + (padding * 2)
    tx, ty = pos[0] + 15, pos[1] + 15
    if tx + max_w > WINDOW_WIDTH: tx = pos[0] - max_w - 15
    if ty + total_h > WINDOW_HEIGHT: ty = pos[1] - total_h - 15
    pygame.draw.rect(surface, (30, 30, 40), (tx, ty, max_w, total_h))
    pygame.draw.rect(surface, GLOW_COLOR, (tx, ty, max_w, total_h), 1)
    for i, line in enumerate(text_lines): surface.blit(font.render(line, True, WHITE),
                                                       (tx + padding, ty + padding + (i * line_height)))


def draw_panels(ai_thinking=False):
    global last_lightning_time, lightning_alpha, next_pulse_time
    global log_sweep_y, log_next_sweep_time
    pygame.draw.rect(screen, PANEL_BG, (0, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    pygame.draw.line(screen, WHITE, (SIDE_PANEL_WIDTH, 0), (SIDE_PANEL_WIDTH, WINDOW_HEIGHT), 2)
    stats_x = SIDE_PANEL_WIDTH + BOARD_SIZE
    pygame.draw.rect(screen, PANEL_BG, (stats_x, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    screen.blit(header_font.render("ADMIRAL'S LOG", True, GLOW_COLOR), (20, 20))

    # --- UPDATED: Dual Panel Sweep Logic ---
    current_ticks = pygame.time.get_ticks()

    # 1. Check if we should start a new sweep
    if log_sweep_y < 0 and current_ticks >= log_next_sweep_time:
        log_sweep_y = 0

    # 2. If a sweep is currently active
    if log_sweep_y >= 0:
        # Create the line surface
        s_line = pygame.Surface((SIDE_PANEL_WIDTH, 2), pygame.SRCALPHA)
        flicker = random.randint(15, 35)
        s_line.fill((0, 255, 100, flicker))

        # DRAW TO ADMIRAL'S LOG (Left Side)
        screen.blit(s_line, (0, int(log_sweep_y)))

        # DRAW TO FLEET INTEL (Right Side)
        # Position is SIDE_PANEL_WIDTH + BOARD_SIZE
        intel_x_pos = SIDE_PANEL_WIDTH + BOARD_SIZE
        screen.blit(s_line, (stats_x, int(log_sweep_y)))

        # Move the line down uniformly
        log_sweep_y += log_sweep_speed

        # 3. Reset and set random delay (0.5s to 3s)
        if log_sweep_y >= WINDOW_HEIGHT:
            log_sweep_y = -10.0
            delay = random.randint(500, 3000)
            log_next_sweep_time = current_ticks + delay

    y_off = WINDOW_HEIGHT - 40
    current_time = pygame.time.get_ticks()

    if current_time > next_pulse_time:
        # Randomly trigger a pulse near a log entry
        px = random.randint(50, SIDE_PANEL_WIDTH - 50)
        py = random.randint(100, WINDOW_HEIGHT - 100)
        log_pulses.append(SHDSonarPulse(px, py))
        # Play sonar sound if available
        # if sonar_sound:
        # sonar_sound.play()
        next_pulse_time = current_time + random.randint(3000, 8000)

    # Create a surface for alpha blending pulses
    pulse_surf = pygame.Surface((SIDE_PANEL_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    for p in log_pulses[:]:
        if p.update():
            p.draw(pulse_surf)
        else:
            log_pulses.remove(p)
    screen.blit(pulse_surf, (0, 0))

    for entry in reversed(admirals_log):
        col = (255, 50, 50) if entry["hit"] else entry["color"]
        screen.blit(log_font.render(entry["msg"], True, col), (15, y_off))
        y_off -= 18
        if y_off < 60: break

    stats_x = SIDE_PANEL_WIDTH + BOARD_SIZE  # This defines the start of the right panel
    pygame.draw.rect(screen, PANEL_BG, (stats_x, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    pygame.draw.line(screen, WHITE, (stats_x, 0), (stats_x, WINDOW_HEIGHT), 2)

    # Put your specific layout elements here
    screen.blit(header_font.render("FLEET INTEL", True, GLOW_COLOR), (stats_x + 20, 20))

    if ai_thinking:
        pulse = (pygame.time.get_ticks() // 200) % 2
        screen.blit(font.render("AI IS ANALYZING TACTICS...", True, AI_COLOR if pulse else WHITE), (stats_x + 20, 60))
    else:
        screen.blit(font.render(f"TURN: {turn.upper()}", True, PLAYER_COLOR if turn == "player" else AI_COLOR),
                    (stats_x + 20, 60))

    screen.blit(font.render(f"SCORE: {current_score:06}", True, WHITE), (stats_x + 20, 80))
    if selected_unit:
        pygame.draw.rect(screen, (40, 40, 50), (stats_x + 10, 105, SIDE_PANEL_WIDTH - 20, 45))
        screen.blit(font.render(f"CMD: {selected_unit.name.upper()}", True, GLOW_COLOR), (stats_x + 20, 110))
        screen.blit(font.render(f"AMMO: {shots_remaining}", True, WHITE), (stats_x + 20, 130))

    curr_y = 170
    screen.blit(font.render("PLAYER FLEET", True, PLAYER_COLOR), (stats_x + 20, curr_y))
    curr_y += 20
    show_blink = (pygame.time.get_ticks() // 500) % 2 == 0
    for u in player_units:
        base_col = WHITE if not u.is_destroyed else (150, 50, 50)
        screen.blit(log_font.render(f"{u.name:10} HP: {u.current_hp}/{u.size}", True, base_col), (stats_x + 25, curr_y))
        if u.is_destroyed:
            status_text, status_col = "[SUNK]", (100, 100, 100)
        elif u.cooldown > 0:
            status_text, status_col = f"[CD: {u.cooldown}]", (255, 50, 50)
        else:
            status_text, status_col = "[READY]", (0, 255, 100)
        if u.cooldown > 0 or show_blink or u.is_destroyed: screen.blit(log_font.render(status_text, True, status_col),
                                                                       (stats_x + 180, curr_y))
        curr_y += 16

    curr_y += 20
    screen.blit(font.render("AI FLEET (INTEL)", True, AI_COLOR), (stats_x + 20, curr_y))
    curr_y += 20
    for u in ai_units:
        revealed = u.is_revealed or any(ai_fog[p[1]][p[0]] > 0 for p in u.grid_pos) or u.current_hp < u.size
        name_str, hp_str = (u.name, f"{u.current_hp}/{u.size}") if revealed else ("????", "?/?")
        col = WHITE if not u.is_destroyed else (150, 50, 50)
        screen.blit(log_font.render(f"{name_str:12} HP: {hp_str} [{'SUNK' if u.is_destroyed else 'OK'}]", True, col),
                    (stats_x + 25, curr_y))
        curr_y += 16

    # --- Revamped Fleet Intel Display ---
    current_display_img = get_current_intel_image()
    if current_display_img:
        stats_x = SIDE_PANEL_WIDTH + BOARD_SIZE
        img_x = stats_x + 20

        # Calculate Y positions dynamically
        img_y_bottom = WINDOW_HEIGHT - (INTEL_H + 20)
        img_y_top = img_y_bottom - (INTEL_H + INTEL_GAP)
        screen.blit(current_display_img, (img_x, img_y_bottom))

        # --- Weather Overlay (Lightning/Rain) ---
        # --- Weather Overlay (Lightning/Rain) ---
        if time.time() - last_lightning_time > random.uniform(3.0, 7.0):
            lightning_alpha, last_lightning_time = 180, time.time()
        # --- Updated drawing logic in draw_panels ---
        if lightning_alpha > 0:
            # Surface size adjusted to single ship (INTEL_W, INTEL_H)
            flash_surf = pygame.Surface((INTEL_W, INTEL_H), pygame.SRCALPHA)
            flash_surf.fill((200, 220, 255, int(lightning_alpha)))
            # Blit moved to bottom ship position
            screen.blit(flash_surf, (img_x, img_y_bottom))
            lightning_alpha *= 0.85

        # Rain surface size adjusted to single ship
        rain_surf = pygame.Surface((INTEL_W, INTEL_H), pygame.SRCALPHA)
        for drop in intel_rain_drops:
            drop[1] += 12
            drop[0] -= 2
            # Reset height adjusted to INTEL_H
            if drop[1] > INTEL_H:
                drop[1], drop[0] = random.randint(-20, 0), random.randint(0, INTEL_W)
            pygame.draw.line(rain_surf, INTEL_RAIN_COLOR, (drop[0], drop[1]), (drop[0] - 1, drop[1] + 5), 1)
        # Blit moved to bottom ship position
        screen.blit(rain_surf, (img_x, img_y_bottom))


def reset_game(num_enemies=5):  # Default to easy
    global active_clouds, active_wind, player_units, ai_units, ai_fog, player_map, player_stats, ai_stats, admirals_log, turn, game_state, selected_unit, winner, active_fires, active_smoke, current_score, shot_queue
    shot_queue = []  # Ensure queue is cleared
    active_wind = [WindParticle() for _ in range(25)]
    active_clouds = [TacticalCloud(side="ai") for _ in range(6)] + [TacticalCloud(side="player") for _ in range(6)]

    pool = [
        ("Scout", 1, 0.0, 1),
        ("Corvette", 2, 0.4, 1),
        ("Frigate", 3, 0.2, 2),
        ("Destroyer", 4, 0.15, 1),
        ("Carrier", 5, 0.08, 5),
        ("Dreadnought", 6, 0.05, 1)  # Size 6, 5% Evasion, 1 Barrage per turn
    ]
    player_units, ai_units, active_fires, active_smoke = [], [], [], []

    # --- Inside reset_game() ---
    cooldown_values = {
        "Frigate": 2,
        "Destroyer": 4,
        "Carrier": 6,
        "Dreadnought": 6  # Long cooldown for massive power
    }

    # Place Player (Always X units)
    occ = set()
    for name, size, eva, ammo in pool:
        placed = False
        while not placed:
            ori = random.choice(["H", "V"])
            sx, sy = random.randint(0, GRID_SIZE - size), random.randint(41, 78 - size)
            cells = [(sx + i, sy) if ori == "H" else (sx, sy + i) for i in range(size)]
            if not any(c in occ for c in cells):
                player_units.append(Unit(name, size, sx, sy, ori, "player", eva, ammo))
                occ.update(cells)
                placed = True

    # Place AI (Based on Difficulty)
    occ_ai = set()
    for _ in range(num_enemies):
        name, size, eva, ammo = random.choice(pool)
        placed = False
        attempts = 0  # Track attempts to prevent infinite loops
        while not placed and attempts < 100:
            ori = random.choice(["H", "V"])
            # Use 0 to 39 for the AI's top half of the grid
            sx = random.randint(0, GRID_SIZE - size)
            sy = random.randint(0, 39 - size)

            cells = [(sx + i, sy) if ori == "H" else (sx, sy + i) for i in range(size)]

            if not any(c in occ_ai for c in cells):
                ai_units.append(Unit(name, size, sx, sy, ori, "ai", eva, ammo))
                occ_ai.update(cells)
                placed = True
            attempts += 1
    for u in player_units + ai_units:
        u.cooldown = cooldown_values.get(u.name, 0)

    print(f"DEBUG: Spawned {len(ai_units)} AI ships.")

    ai_fog = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    player_map = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    player_stats, ai_stats = {"shots": 0, "hits": 0}, {"shots": 0, "hits": 0}
    admirals_log, turn, game_state, winner, current_score = [], "player", "PLAYING", None, 0

def get_bezier(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1])


def random_pause_thinking():
    start_time = time.time()
    duration = random.uniform(0.4, 0.9)
    while time.time() - start_time < duration:
        draw_game_elements(ai_thinking=True)
        pygame.display.flip()
        clock.tick(FPS)


def draw_game_elements(ai_thinking=False):
    screen.fill(BLACK)
    global ai_water_offset, player_water_offset, active_smoke
    ai_water_offset = (ai_water_offset - 0.5) % BOARD_SIZE
    player_water_offset = (player_water_offset + 0.5) % BOARD_SIZE
    screen.blit(water_map, (SIDE_PANEL_WIDTH + ai_water_offset, 0), pygame.Rect(0, 0, BOARD_SIZE, BOARD_SIZE // 2))
    screen.blit(water_map, (SIDE_PANEL_WIDTH + ai_water_offset - BOARD_SIZE, 0),
                pygame.Rect(0, 0, BOARD_SIZE, BOARD_SIZE // 2))
    screen.blit(water_map, (SIDE_PANEL_WIDTH + player_water_offset, BOARD_SIZE // 2),
                pygame.Rect(0, BOARD_SIZE // 2, BOARD_SIZE, BOARD_SIZE // 2))
    screen.blit(water_map, (SIDE_PANEL_WIDTH + player_water_offset - BOARD_SIZE, BOARD_SIZE // 2),
                pygame.Rect(0, BOARD_SIZE // 2, BOARD_SIZE, BOARD_SIZE // 2))

    # --- UPDATED: Higher Visibility Grid Overlay ---
    grid_overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)

    for i in range(0, GRID_SIZE + 1):
        # Major sectors every 10 cells
        is_major = (i % 10 == 0)

        # INCREASED ALPHAS: 90 for major lines, 40 for minor lines
        alpha = 90 if is_major else 40

        # Brighter cyan for major, softer blue for minor
        color = (0, 255, 255, alpha) if is_major else (180, 200, 255, alpha)

        # Vertical and Horizontal lines
        pygame.draw.line(grid_overlay, color, (i * CELL_SIZE, 0), (i * CELL_SIZE, BOARD_SIZE), 1)
        pygame.draw.line(grid_overlay, color, (0, i * CELL_SIZE), (BOARD_SIZE, i * CELL_SIZE), 1)

    # Intersection markers (increased alpha to 120 for a tactical pop)
    for gy in range(0, GRID_SIZE + 1, 10):
        for gx in range(0, GRID_SIZE + 1, 10):
            pygame.draw.circle(grid_overlay, (0, 255, 255, 120), (gx * CELL_SIZE, gy * CELL_SIZE), 2)

    screen.blit(grid_overlay, (SIDE_PANEL_WIDTH, 0))
    # -----------------------------------------------

    for wind in active_wind: wind.update(); wind.draw(screen)
    for cloud in active_clouds: cloud.update(); cloud.draw(screen)
    for u in player_units + ai_units:
        if not u.is_destroyed and u.health_map[0]:
            should_emit = True
            if u.side == "player" or ai_fog[u.grid_pos[0][1]][u.grid_pos[0][0]] > 0:
                if should_emit and random.random() > 0.85:
                    drift = -0.5 if u.side == "ai" else 0.5
                    # Calculate current bobbing to spawn smoke at the right height
                    bob = math.sin(time.time() * 3.0 + (u.grid_pos[0][0] * 0.5)) * 3.0
                    pos = u.rects[0].center
                    active_smoke.append(SmokeParticle(pos[0] - SIDE_PANEL_WIDTH, pos[1] + bob, drift))

    draw_panels(ai_thinking=ai_thinking)
    for y in range(40):
        for x in range(GRID_SIZE):
            if ai_fog[y][x] == 0:
                s = pygame.Surface((CELL_SIZE, CELL_SIZE));
                s.set_alpha(170);
                s.fill((10, 15, 30));
                screen.blit(s, (x * CELL_SIZE + SIDE_PANEL_WIDTH, y * CELL_SIZE))
            elif ai_fog[y][x] == 2:
                pygame.draw.circle(screen, WHITE, (x * CELL_SIZE + SIDE_PANEL_WIDTH + 5, y * CELL_SIZE + 5), 1)
    for y in range(40, GRID_SIZE):
        for x in range(GRID_SIZE):
            if player_map[y][x] == 1: pygame.draw.rect(screen, (255, 120, 0),
                                                       (x * CELL_SIZE + SIDE_PANEL_WIDTH + 3, y * CELL_SIZE + 3, 4, 4))
    for u in player_units + ai_units: u.draw(screen)
    # --- ADD STARTING HERE (approx Line 698) ---
    time_ms = pygame.time.get_ticks()
    for u in player_units:
        if u.cooldown == 0 and not u.is_destroyed:
            # Calculate center of the unit
            mid_rect = u.rects[len(u.rects) // 2]
            center_x, center_y = mid_rect.center
            # --- 360 Degree Continuous Sweep (5 blocks long) ---
            # 5 blocks * 10 pixels = 50 pixels length
            radar_range = 30

            # Rotation speed (0.05 for that slow, deliberate feel)
            rotation_angle = (time_ms * 0.05) % 360
            rad_angle = math.radians(rotation_angle)

            # Create surface for transparency
            radar_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

            # 1. Draw a faint 360-degree background circle (The radar "field")
            pygame.draw.circle(radar_surf, (0, 80, 0, 40), (center_x, center_y), radar_range)

            # 2. Calculate the end point for the 360-degree sweeping line
            end_x = center_x + radar_range * math.cos(rad_angle)
            end_y = center_y + radar_range * math.sin(rad_angle)

            # 3. Draw the bright sweep line
            pygame.draw.line(radar_surf, (100, 255, 100, 255), (center_x, center_y), (end_x, end_y), 2)

            # 4. Optional: Draw a subtle outer ring
            pygame.draw.circle(radar_surf, (100, 255, 100, 100), (center_x, center_y), radar_range, 1)
            screen.blit(radar_surf, (0, 0))

            if u.name == "Carrier":
                # Loop to create 5 distinct planes
                for i in range(5):
                    # 1. Give each plane a unique time offset so they aren't stacked
                    # We multiply the index (i) by a large number to 'stagger' them
                    t = (time_ms * 0.002) + (i * 1.5)

                    # 2. Slightly vary the width and height for each plane
                    # so some fly wider/taller than others
                    width = 30 + (i * 5)
                    height = 15 + (i * 3)

                    off_x = math.sin(t) * width
                    off_y = math.sin(t * 2) * height

                    # 3. Draw the plane
                    p_pos = (center_x + int(off_x), center_y + int(off_y))
                    pygame.draw.circle(screen, (200, 200, 200), p_pos, 2)
                    pygame.draw.line(screen, WHITE, (p_pos[0] - 3, p_pos[1]), (p_pos[0] + 3, p_pos[1]), 1)

            elif u.name == "Dreadnought":
                # --- Dreadnought: Heavy Battery Charge Effect ---

                # 1. Pulsing Red Core (Glowing hull effect)
                # Oscillates between 50 and 180 alpha for a "breathing" look
                pulse_alpha = 115 + math.sin(time_ms * 0.005) * 65
                glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 0, 0, pulse_alpha), (15, 15), 15)
                # Blit the glow over the center of the massive 6-block ship
                screen.blit(glow_surf, (center_x - 15, center_y - 15))

                # 2. Orbital Power Rings
                # Two rings rotating in opposite directions
                for i, speed in enumerate([0.003, -0.002]):
                    angle = time_ms * speed
                    ring_radius = 25 + (i * 8)
                    # Find a point on the ring to draw a "power node"
                    node_x = center_x + math.cos(angle) * ring_radius
                    node_y = center_y + math.sin(angle) * ring_radius

                    # Draw the faint orbital path
                    pygame.draw.circle(screen, (150, 0, 0, 100), (center_x, center_y), ring_radius, 1)
                    # Draw the bright node
                    pygame.draw.circle(screen, (255, 50, 50), (int(node_x), int(node_y)), 3)

                # 3. Expanding Shockwave (Slow and Heavy)
                # Every 2 seconds, a shockwave expands outward
                wave_time = (time_ms % 2000) / 2000.0  # 0.0 to 1.0
                wave_radius = int(wave_time * 60)
                wave_alpha = int(255 * (1.0 - wave_time))

                wave_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(wave_surf, (255, 100, 0, wave_alpha), (60, 60), wave_radius, 2)
                screen.blit(wave_surf, (center_x - 60, center_y - 60))

            elif u.name in ["Frigate", "Destroyer", "Corvette"]:
                # --- Blinking Ammo Icon beside the unit ---
                # Pulse every 500ms
                if (time_ms // 500) % 2 == 0:
                    # Position it slightly to the right of the ship's center
                    ammo_x = center_x + 12
                    ammo_y = center_y - 8

                    # Draw a simple "Bullet/Shell" shape
                    # Body of the shell
                    pygame.draw.rect(screen, (255, 215, 0), (ammo_x, ammo_y, 6, 10))

                    # Tip of the shell (Triangle)
                    pygame.draw.polygon(screen, (255, 215, 0), [
                        (ammo_x, ammo_y),
                        (ammo_x + 6, ammo_y),
                        (ammo_x + 3, ammo_y - 4)
                    ])
                    # Small white highlight to make it look metallic
                    pygame.draw.line(screen, WHITE, (ammo_x + 1, ammo_y + 2), (ammo_x + 1, ammo_y + 8), 1)

            elif u.name == "Scout":
                # Radar Pulse Logic
                radius = (time_ms // 15) % 40
                alpha = max(0, 255 - (radius * 6))
                radar_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(radar_surf, (0, 255, 0, alpha), (40, 40), radius, 2)
                screen.blit(radar_surf, (center_x - 40, center_y - 40))
    # --- END OF ADDITION ---

    for smoke in active_smoke[:]:
        if not smoke.update():
            active_smoke.remove(smoke)
        else:
            smoke.draw(screen)
    for u in player_units + ai_units:
        if (u.side == "player" or u.is_revealed) and not u.is_destroyed:
            for i, healthy in enumerate(u.health_map):
                if not healthy and random.random() > 0.95: active_fires.append(
                    BurningPixel(u.rects[i].x + random.randint(0, CELL_SIZE),
                                 u.rects[i].y + random.randint(0, CELL_SIZE)))
    for fire in active_fires[:]:
        if not fire.update():
            active_fires.remove(fire)
        else:
            fire.draw(screen)
    screen.blit(header_font.render("AI TERRITORY", True, (AI_COLOR[0], AI_COLOR[1], AI_COLOR[2], 120)),
                (SIDE_PANEL_WIDTH + 15, (BOARD_SIZE // 2) - 35))
    label = header_font.render("PLAYER SECTOR", True, (PLAYER_COLOR[0], PLAYER_COLOR[1], PLAYER_COLOR[2], 120))
    screen.blit(label, ((SIDE_PANEL_WIDTH + BOARD_SIZE) - label.get_width() - 15, (BOARD_SIZE // 2) + 15))
    current_time = time.time()
    for trail in active_trails[:]:
        age = current_time - trail["time"]
        if age > (1.2 if trail.get("type") == "FLIGHT" else 0.6): active_trails.remove(trail); continue
        alpha = int(255 * (1 - (age / (1.2 if trail.get("type") == "FLIGHT" else 0.6))))
        trail_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        if trail.get("type") == "SONAR":
            rad = int(trail["max_radius"] * (age / 0.6))
            pygame.draw.circle(trail_surf, (0, 255, 80, alpha), trail["center"], rad, 3)
        elif trail.get("type") == "FLIGHT":
            prog = age / 1.2
            t = prog * 2 if prog <= 0.5 else 2 - (prog * 2)
            look_t = min(1.0, t + 0.05) if prog <= 0.5 else max(0.0, t - 0.05)
            pos, look = get_bezier(trail["start"], trail["control"], trail["end"], t), get_bezier(trail["start"],
                                                                                                  trail["control"],
                                                                                                  trail["end"], look_t)
            draw_aircraft(trail_surf, pos, look, (180, 190, 210), alpha)
        else:
            pygame.draw.line(trail_surf, (255, 255, 100, alpha), trail["start"], trail["end"], 2)
        screen.blit(trail_surf, (0, 0))
    pygame.draw.line(screen, (0, 100, 255), (SIDE_PANEL_WIDTH, 40 * CELL_SIZE),
                     (WINDOW_WIDTH - SIDE_PANEL_WIDTH, 40 * CELL_SIZE), 2)


game_state = "WELCOME"
admirals_log, player_stats, ai_stats = [], {"shots": 0, "hits": 0}, {"shots": 0, "hits": 0}
winner, player_units, ai_units = None, [], []
turn, selected_unit, shots_remaining = "player", None, 0
current_score, final_score = 0, 0
ai_fog = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
player_map = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
active_fires, active_smoke, active_wind, active_clouds, active_trails = [], [], [], [], []
ai_water_offset, player_water_offset = 0, 0
ship_intel_img = load_image("ship.png", (INTEL_W, INTEL_H))
ship_intel_img2 = load_image("ship2.png", (INTEL_W, INTEL_H))  # Add this line
shot_queue = []
next_shot_time = 0


# --- Load New Asset Images ---
ASSET_IMAGES = {
    "AI": load_image("AI_avatar.png", (INTEL_W, INTEL_H)),
    "Scout": load_image("scout.png", (INTEL_W, INTEL_H)),
    "Corvette": load_image("corvette.png", (INTEL_W, INTEL_H)),
    "Frigate": load_image("frigate.png", (INTEL_W, INTEL_H)),
    "Destroyer": load_image("destroyer.png", (INTEL_W, INTEL_H)),
    "Carrier": load_image("carrier.png", (INTEL_W, INTEL_H)),
    "Dreadnought": load_image("dreadnought.png", (INTEL_W, INTEL_H))
}


def get_current_intel_image():
    # 1. Check if it is AI's turn
    if turn == "ai":
        return ASSET_IMAGES.get("AI")

    # 2. Check if a player unit is selected
    if selected_unit:
        return ASSET_IMAGES.get(selected_unit.name)

    # Fallback to the original generic ship image
    return ship_intel_img2


log_pulses = []
next_pulse_time = 0
# Variables for the random sweep logic
log_sweep_y = -10.0  # Current vertical position (starts off-screen)
log_sweep_speed = 5.0  # Pixels per frame
log_next_sweep_time = 0  # When the next sweep should start (in ms)

difficulty = "EASY"  # Default
tier_y_base = WINDOW_HEIGHT // 2 + 50  # Lowered from original center
tier_buttons = {
    "EASY": pygame.Rect(WINDOW_WIDTH // 2 - 160, tier_y_base, 100, 40),
    "MEDIUM": pygame.Rect(WINDOW_WIDTH // 2 - 50, tier_y_base, 100, 40),
    "HARD": pygame.Rect(WINDOW_WIDTH // 2 + 60, tier_y_base, 100, 40)
}
# Start button now follows the tier buttons with a 70px gap
start_btn = pygame.Rect(WINDOW_WIDTH // 2 - 100, tier_y_base + 70, 200, 60)

def calculate_final_score():
    global final_score
    # Avoid division by zero and calculate accuracy
    eff_multiplier = (player_stats["hits"] / max(1, player_stats["shots"]))
    # 200 points for every remaining HP point in your fleet
    survival_bonus = sum(u.current_hp for u in player_units) * 200
    # Final formula: (Combat Points * Accuracy * Survival) / 300
    final_score = int((current_score * eff_multiplier * survival_bonus) / 300)


while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
    if game_state == "WELCOME":
        screen.fill(BLACK)
        if splash_img:
            screen.blit(splash_img, (0, 0))

        # Optional: Difficulty Label
        label = font.render("MISSION INTENSITY:", True, (180, 180, 180))
        screen.blit(label, (WINDOW_WIDTH // 2 - label.get_width() // 2, tier_y_base - 30))

        # Draw Tier Buttons
        for tier, rect in tier_buttons.items():
            is_selected = (difficulty == tier)
            # Glow effect for selected tier
            btn_col = PLAYER_COLOR if is_selected else (30, 30, 35)
            pygame.draw.rect(screen, btn_col, rect, border_radius=5)
            pygame.draw.rect(screen, WHITE if is_selected else (100, 100, 100), rect, 1, border_radius=5)

            txt_col = WHITE if is_selected else (150, 150, 150)
            txt = font.render(tier, True, txt_col)
            screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        # Start Button with Hover Effect
        s_hover = start_btn.collidepoint(pygame.mouse.get_pos())
        s_col = (0, 200, 100) if s_hover else (0, 150, 80)
        pygame.draw.rect(screen, s_col, start_btn, border_radius=8)

        # Draw a thin border for the start button
        pygame.draw.rect(screen, WHITE, start_btn, 1, border_radius=8)

        btn_text = header_font.render("START MISSION", True, WHITE)
        screen.blit(btn_text,
                    (start_btn.centerx - btn_text.get_width() // 2, start_btn.centery - btn_text.get_height() // 2))

        # Interaction handling inside the 'for event in events:' loop
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for tier, rect in tier_buttons.items():
                    if rect.collidepoint(event.pos):
                        difficulty = tier
                        if move_sound: move_sound.play()

                if start_btn.collidepoint(event.pos):
                    count = {"EASY": 5, "MEDIUM": 8, "HARD": 12}[difficulty]
                    if start_sound: start_sound.play()
                    reset_game(num_enemies=count)

    elif game_state == "PLAYING":



        # --- Process Delayed Battery Shots ---
        now = pygame.time.get_ticks()
        if shot_queue and now >= next_shot_time:
            s = shot_queue.pop(0)

            # 1. Sound and Visuals
            if s["sound"]: s["sound"].play()
            active_trails.append(
                {"start": s["source"], "end": (s["tx"] * CELL_SIZE + SIDE_PANEL_WIDTH + 5, s["ty"] * CELL_SIZE + 5),
                 "time": time.time()})

            # 2. Marking and Calculation
            if s["side"] == "PLAYER":
                ai_fog[s["ty"]][s["tx"]] = 2
                res, u_name = fire_at(s["tx"], s["ty"], ai_units, "PLAYER",
                                      ignore_evasion=(s["unit_name"] == "Corvette"))
                if res != "ALREADY_HIT": log_attack_results("PLAYER", s["unit_name"], [(res, u_name)])

            # 3. Random Realism Delay (0.2s - 0.6s)
            next_shot_time = now + random.randint(200, 600)

        draw_game_elements()
        m_pos = pygame.mouse.get_pos()
        mx, my = (m_pos[0] - SIDE_PANEL_WIDTH) // CELL_SIZE, m_pos[1] // CELL_SIZE
        hovered_unit = next((u for u in player_units if any(r.collidepoint(m_pos) for r in u.rects)), None)
        unit_to_show = hovered_unit or (selected_unit if selected_unit else None)
        if unit_to_show and unit_to_show.side == "player":
            patterns = {"Scout": ["Type: RECON", "Effect: Reveal 16x16 Area", "CD: 6 Turns"],
                        "Destroyer": ["Type: AOE", "Effect: 4x4 with 8 random shot placement", "CD: 4 Turns"],
                        "Carrier": ["Type: HEAVY STRIKE", "Effect: 2x2 Square", "CD: 6 Turns"],
                        "Frigate": ["Type: LIGHT STRIKE", "Effect: 2x2 Square", "CD: 2 Turns"],
                        "Corvette": ["Type: SCOUT STRIKE", "Effect: 1x1 Precise", "CD: 0 Turns"],
                        "Dreadnought": ["Type: AOE", "Effect: 4x4 Precise", "CD: 6 Turns"]}
            intel = [f"UNIT: {unit_to_show.name.upper()}"] + patterns.get(unit_to_show.name,
                                                                          ["Type: Standard", "Effect: 1x1 Precise"])
            draw_tooltip(screen, intel, m_pos)
        if turn == "player" and selected_unit and 0 <= mx < GRID_SIZE and 0 <= my < 40:
            preview_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            if selected_unit.name == "Destroyer":
                for dy in range(-1, 3):
                    for dx in range(-1, 3):
                        if 0 <= mx + dx < GRID_SIZE and 0 <= my + dy < 40: pygame.draw.rect(preview_surface,
                                                                                            PREVIEW_COLOR, pygame.Rect(
                                (mx + dx) * CELL_SIZE + SIDE_PANEL_WIDTH, (my + dy) * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif selected_unit.name == "Dreadnought":
                time_ms = pygame.time.get_ticks()
            # 4x4 Heavy Bombardment Preview
            # We use a slightly more intense red-tinted preview color for the Dreadnought
                dread_preview_col = (255, 50, 50, 80 + math.sin(time_ms * 0.01) * 30)

                for dy in range(-1, 3):
                    for dx in range(-1, 3):
                        px, py = mx + dx, my + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < 40:
                            pygame.draw.rect(preview_surface, dread_preview_col,
                                     pygame.Rect(px * CELL_SIZE + SIDE_PANEL_WIDTH,
                                                 py * CELL_SIZE, CELL_SIZE, CELL_SIZE))

                # Optional: Draw a thin border around the 4x4 area to define the strike zone
                border_rect = pygame.Rect((mx - 1) * CELL_SIZE + SIDE_PANEL_WIDTH,
                                  (my - 1) * CELL_SIZE, 4 * CELL_SIZE, 4 * CELL_SIZE)
                pygame.draw.rect(preview_surface, (255, 255, 255, 100), border_rect, 1)

            elif selected_unit.name == "Scout":
                pygame.draw.rect(preview_surface, (0, 255, 80, 40),
                                 pygame.Rect((mx - 8) * CELL_SIZE + SIDE_PANEL_WIDTH, (my - 8) * CELL_SIZE,
                                             16 * CELL_SIZE, 16 * CELL_SIZE))
            else:
                rad = 2 if selected_unit.name in ["Carrier", "Frigate"] else 1
                for dy in range(rad):
                    for dx in range(rad):
                        if 0 <= mx + dx < GRID_SIZE and 0 <= my + dy < 40: pygame.draw.rect(preview_surface,
                                                                                            PREVIEW_COLOR, pygame.Rect(
                                (mx + dx) * CELL_SIZE + SIDE_PANEL_WIDTH, (my + dy) * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            screen.blit(preview_surface, (0, 0))

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                add_log("PLAYER", "SURRENDER", "Admiral retreat initiated.")
                # Ensure score is calculated BEFORE moving to GAME_OVER screen
                calculate_final_score()
                winner = "AI"
                game_state = "GAME_OVER"

            if event.type == pygame.MOUSEBUTTONDOWN and turn == "player":
                clicked = next((u for u in player_units if any(r.collidepoint(m_pos) for r in u.rects)), None)
                if clicked and not clicked.is_destroyed and clicked.cooldown == 0:
                    if bell_sound: bell_sound.play()
                    if selected_unit: selected_unit.is_selected = False
                    selected_unit = clicked;
                    selected_unit.is_selected, shots_remaining = True, clicked.ammo_capacity
                elif selected_unit and 0 <= mx < GRID_SIZE and 0 <= my < 40:
                    source_pos = selected_unit.rects[1 if selected_unit.size > 1 else 0].center
                    results = []
                    fresh_strike = False

                    # Check if unit is a "Battery" type
                    is_battery = selected_unit.name in ["Corvette", "Frigate", "Destroyer"]

                    if is_battery:
                        # Determine targets for the queue
                        coords = []
                        if selected_unit.name == "Destroyer":
                            coords = random.sample([(mx + dx, my + dy) for dy in range(-1, 3) for dx in range(-1, 3)
                                                    if 0 <= mx + dx < GRID_SIZE and 0 <= my + dy < 40], 8)

                        else:  # Corvette/Frigate
                            rad = 2 if selected_unit.name == "Frigate" else 1
                            coords = [(mx + dx, my + dy) for dy in range(rad) for dx in range(rad)
                                      if 0 <= mx + dx < GRID_SIZE and 0 <= my + dy < 40]

                        # Add to sequential queue
                        for cx, cy in coords:
                            shot_queue.append({
                                "tx": cx, "ty": cy, "source": source_pos, "side": "PLAYER",
                                "unit_name": selected_unit.name,
                                "sound": shot_1_sound if selected_unit.name != "Destroyer" else shot_2_sound
                            })
                        fresh_strike = True
                    # Inside the event loop for MOUSEBUTTONDOWN
                    elif selected_unit.name == "Dreadnought":
                        # 4x4 Bombardment Logic
                        coords = [(mx + dx, my + dy) for dy in range(-1, 3) for dx in range(-1, 3)
                                  if 0 <= mx + dx < GRID_SIZE and 0 <= my + dy < 40]
                        # 2. Randomly shuffle the order of coordinates
                        random.shuffle(coords)

                        for cx, cy in coords:
                            shot_queue.append({
                                "tx": cx, "ty": cy, "source": source_pos, "side": "PLAYER",
                                "unit_name": "Dreadnought",
                                "sound": shot_2_sound  # Heavier sound effect
                            })
                        fresh_strike = True

                    else:  # Scout and Carrier (Instant Resolution)
                        if selected_unit.name == "Scout":
                            if sonar_sound: sonar_sound.play()
                            for ry in range(my - 8, my + 9):
                                for rx in range(mx - 8, mx + 9):
                                    if 0 <= rx < GRID_SIZE and 0 <= ry < 40 and ((rx - mx) ** 2 + (ry - my) ** 2) <= 64:
                                        if ai_fog[ry][rx] != 2: ai_fog[ry][rx] = 1
                            active_trails.append({"type": "SONAR", "center": (mx * CELL_SIZE + SIDE_PANEL_WIDTH + 5, my * CELL_SIZE + 5),
                                                  "max_radius": 10 * CELL_SIZE, "time": time.time()})
                            fresh_strike = True
                        elif selected_unit.name == "Carrier":
                            if plane_sound: plane_sound.play()
                            active_trails.append({"type": "FLIGHT", "start": source_pos,
                                                  "end": ((mx + 0.5) * CELL_SIZE + SIDE_PANEL_WIDTH, (my + 0.5) * CELL_SIZE), "control": (
                                (mx + 0.5) * CELL_SIZE + SIDE_PANEL_WIDTH + random.randint(-100, 100),
                                (source_pos[1] + (my + 0.5) * CELL_SIZE) // 2), "time": time.time()})
                            for dy in range(2):
                                for dx in range(2):
                                    if 0 <= mx + dx < GRID_SIZE and 0 <= my + dy < 40:
                                        res, u_name = fire_at(mx + dx, my + dy, ai_units, "PLAYER")
                                        if res != "ALREADY_HIT": results.append((res, u_name)); fresh_strike = True
                                        ai_fog[my + dy][mx + dx] = 2

                    if fresh_strike:
                        sfx = {"Corvette": shot_1_sound, "Frigate": shot_1_sound, "Destroyer": shot_2_sound,
                               "Carrier": plane_sound}
                        if sfx.get(selected_unit.name): sfx[selected_unit.name].play()
                        shots_remaining -= 1
                        if shots_remaining <= 0:
                            selected_unit.cooldown = {"Frigate": 2, "Destroyer": 4, "Carrier": 6, "Scout": 6, "Dreadnought": 6}.get(
                                selected_unit.name, 0)
                            selected_unit.is_selected = False;
                            selected_unit = None
                            for u in player_units:
                                if u.cooldown > 0: u.cooldown -= 1
                            random_pause_thinking();
                            turn = "ai"
        if turn == "ai":
            random_pause_thinking()

            # 1. Determine how many unique ships will attack this turn
            attack_count = {"EASY": 1, "MEDIUM": 2, "HARD": 3}.get(difficulty, 1)

            # 2. Get a list of all AI units that are still afloat and ready
            available_attackers = [u for u in ai_units if not u.is_destroyed and u.cooldown == 0]

            # 3. Limit the attack count to the number of ships actually available
            actual_attackers_this_turn = random.sample(available_attackers, min(len(available_attackers), attack_count))

            if actual_attackers_this_turn:
                for attacker in actual_attackers_this_turn:
                    results, ammo = [], attacker.ammo_capacity

                    # Execution of the specific ship's attack pattern
                    while ammo > 0:
                        # Adjust range to prevent 3x3 grids from going off-board
                        tx, ty = random.randint(0, GRID_SIZE - 3), random.randint(40, GRID_SIZE - 3)

                        if attacker.name == "Destroyer":
                            strikes = random.sample([(tx + dx, ty + dy) for dy in range(-1, 3) for dx in range(-1, 3) if
                                                     0 <= tx + dx < GRID_SIZE and 40 <= ty + dy < GRID_SIZE], 8)
                            for sx, sy in strikes:
                                res, u_name = fire_at(sx, sy, player_units, "AI")
                                results.append((res, u_name))
                                player_map[sy][sx] = 1

                        elif attacker.name == "Dreadnought":
                            # Dreadnought Firing Method: 3x3 Heavy Bombardment (9 cells)
                            for dy in range(4):
                                for dx in range(4):
                                    sx, sy = tx + dx, ty + dy
                                    if 0 <= sx < GRID_SIZE and 40 <= sy < GRID_SIZE:
                                        res, u_name = fire_at(sx, sy, player_units, "AI")
                                        results.append((res, u_name))
                                        player_map[sy][sx] = 1
                        else:
                            # Standard firing for other ships
                            rad = 2 if attacker.name in ["Carrier", "Frigate"] else 1
                            for dy in range(rad):
                                for dx in range(rad):
                                    if 0 <= tx + dx < GRID_SIZE and 40 <= ty + dy < GRID_SIZE:
                                        res, u_name = fire_at(tx + dx, ty + dy, player_units, "AI",
                                                              ignore_evasion=(attacker.name == "Corvette"))
                                        results.append((res, u_name))
                                        player_map[ty + dy][tx + dx] = 1
                        ammo -= 1
                    pygame.display.flip()  # Update the screen to show the hits
                    pygame.time.delay(200)  # Wait 0.4 seconds before the next ship fires

                    # Log each attacker's results separately
                    log_attack_results("AI", attacker.name, results)

                    # Set the cooldown for the ship that just fired
                    attacker.cooldown = {"Frigate": 2, "Destroyer": 4, "Carrier": 6, "Dreadnought": 6}.get(attacker.name, 0)

            # 4. Tick down cooldowns for all AI ships (even those that didn't fire)
            for u in ai_units:
                if u.cooldown > 0:
                    u.cooldown -= 1

            turn = "player"

        if sum(u.current_hp for u in ai_units) == 0:
            eff = (player_stats["hits"] / max(1, player_stats["shots"]))
            final_score = int((current_score * eff * (sum(u.current_hp for u in player_units) * 200)) / 300)
            winner, game_state = "PLAYER", "GAME_OVER"
        elif sum(u.current_hp for u in player_units) == 0:
            winner, game_state = "AI", "GAME_OVER"

    elif game_state == "GAME_OVER":
        screen.fill(BLACK)

        # --- DRAW WIN BACKGROUND ---
        if winner == "PLAYER" and player_win_img:
            screen.blit(player_win_img, (0, 0))
        elif winner == "AI" and ai_win_img:
            screen.blit(ai_win_img, (0, 0))
        # ---------------------------

        # Optional: Dimmer overlay for text readability
        dimmer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dimmer.fill((0, 0, 0, 150))  # Adjust 150 (0-255) for darkness
        screen.blit(dimmer, (0, 0))


        title_col = PLAYER_COLOR if winner == "PLAYER" else AI_COLOR
        header_surf = header_font.render(f"{winner} VICTORY", True, title_col)
        screen.blit(header_surf, (WINDOW_WIDTH // 2 - header_surf.get_width() // 2, WINDOW_HEIGHT // 2 - 140))

        # Calculate statistics for the display
        eff = (player_stats["hits"] / max(1, player_stats["shots"]))
        surv_points = sum(u.current_hp for u in player_units) * 200

        score_items = [
            f"[ FORMULA: (BASE COMBAT SCORE * MISSION ACCURACY * FLEET SURVIVAL) / 300 ]",
            "----------------------------------------------------------",
            f"BASE COMBAT SCORE:  {current_score:06}",
            f"MISSION ACCURACY:   {eff * 100:.1f}%",
            f"FLEET SURVIVAL:     {surv_points:06}",
            "----------------------------------------------------------",
            f"FINAL TOTAL SCORE:  {final_score:06}"
        ]

        # Draw the score breakdown
        item_y = WINDOW_HEIGHT // 2 - 40
        for i, line in enumerate(score_items):
            col = GLOW_COLOR if "TOTAL" in line else WHITE
            line_surf = font.render(line, True, col)
            line_x = WINDOW_WIDTH // 2 - line_surf.get_width() // 2
            screen.blit(line_surf, (line_x, item_y + (i * 25)))

        footer_surf = font.render("PRESS R TO RETURN TO HQ (MAIN MENU)", True, (150, 150, 150))
        screen.blit(footer_surf, (WINDOW_WIDTH // 2 - footer_surf.get_width() // 2, item_y + 200))

        for event in events:
            # Pressing R here returns you to the start menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game_state = "WELCOME"

    pygame.display.flip()
    clock.tick(FPS)