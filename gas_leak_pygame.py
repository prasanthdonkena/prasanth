import pygame
import sys
import math
import random
import time
import threading
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import winsound

# ─── EMAIL CONFIG ─────────────────────────────────────────────
SENDER_EMAIL   = "prasanthdonkena@gmail.com"
RECEIVER_EMAIL = "prasanthdonkena387@gmail.com"
APP_PASSWORD   = "erbz rlak aint wyuv"

# ─── Init ─────────────────────────────────────────────────────
pygame.init()
pygame.font.init()

W, H = 1000, 680
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("GasSafe Pro — Smart Gas Leak Safety System")
clock  = pygame.time.Clock()

# ─── Fonts ────────────────────────────────────────────────────
F_BIG    = pygame.font.SysFont("Segoe UI", 32, bold=True)
F_MED    = pygame.font.SysFont("Segoe UI", 18, bold=True)
F_SM     = pygame.font.SysFont("Segoe UI", 13)
F_TINY   = pygame.font.SysFont("Segoe UI", 11)
F_MONO   = pygame.font.SysFont("Consolas", 22, bold=True)
F_MONO_S = pygame.font.SysFont("Consolas", 14)

# ─── Colors ───────────────────────────────────────────────────
BG       = (8,   15,  26)
CARD     = (13,  21,  37)
BORDER   = (30,  41,  59)
WHITE    = (226, 232, 240)
MUTED    = (100, 116, 139)
GREEN    = (34,  197, 94)
YELLOW   = (245, 158, 11)
RED      = (239, 68,  68)
BLUE     = (56,  189, 248)
ORANGE   = (249, 115, 22)
WALL     = (20,  35,  60)
FLOOR    = (15,  25,  45)
ROOF     = (10,  18,  35)

# ─── Gas Particle ─────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, phase="leak"):
        self.x     = x + random.randint(-10, 10)
        self.y     = y
        self.vx    = random.uniform(-0.8, 0.8)
        self.vy    = random.uniform(-1.5, -0.5)
        self.r     = random.randint(5, 14)
        self.alpha = random.randint(120, 200)
        self.phase = phase
        self.age   = 0

    def update(self, win_open, win_left_x, win_right_x):
        self.age += 1
        if win_open:
            # Suck toward nearest window
            if self.x < 500:
                self.vx -= 0.12
            else:
                self.vx += 0.12
            self.vy -= 0.08
            self.alpha -= 5
        else:
            self.vx *= 0.98
            self.vy += 0.03
        self.x += self.vx
        self.y += self.vy

    def draw(self, surface):
        if self.alpha <= 0:
            return
        col = (245,158,11) if self.phase=="leak" else \
              (239,68,68)  if self.phase=="danger" else \
              (56,189,248)
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, max(0,int(self.alpha))),
                           (self.r, self.r), self.r)
        surface.blit(s, (int(self.x)-self.r, int(self.y)-self.r))

    @property
    def alive(self):
        return (self.alpha > 5 and
                0 < self.x < W and
                self.y > 100)


# ─── Flame particle ───────────────────────────────────────────
class Flame:
    def __init__(self, x, y):
        self.x     = x + random.randint(-8, 8)
        self.y     = y
        self.vy    = random.uniform(-2.0, -0.8)
        self.vx    = random.uniform(-0.3, 0.3)
        self.r     = random.randint(3, 8)
        self.alpha = 200
        self.age   = 0

    def update(self):
        self.age += 1
        self.y  += self.vy
        self.x  += self.vx
        self.alpha -= 12

    def draw(self, surface):
        if self.alpha <= 0: return
        col = (255, 100+random.randint(0,80), 0)
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, max(0,int(self.alpha))),
                           (self.r, self.r), self.r)
        surface.blit(s, (int(self.x)-self.r, int(self.y)-self.r))

    @property
    def alive(self):
        return self.alpha > 0


def send_email_alert(level):
    try:
        msg = MIMEMultipart()
        msg["Subject"] = "GAS LEAK ALERT!"
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = RECEIVER_EMAIL
        ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = ("GAS LEAK DETECTED\n\nTime: "+ts+
                "\nLevel: "+str(level)+" ppm\n\n"
                "Windows opened\nElectricity cut off\n\n"
                "Evacuate immediately!\n-- GasSafe Pro")
        msg.attach(MIMEText(body, "plain"))
        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(SENDER_EMAIL, APP_PASSWORD)
        s.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        s.quit()
        return True
    except:
        return False

def play_alarm():
    for _ in range(6):
        winsound.Beep(1500, 200)
        winsound.Beep(800,  200)

def play_safe():
    winsound.Beep(600, 400)

# ══════════════════════════════════════════════════════════════
# MAIN GAME LOOP
# ══════════════════════════════════════════════════════════════
def draw_rounded_rect(surf, color, rect, radius=10, alpha=255):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (color[0], color[1], color[2], alpha), (0,0,rect[2],rect[3]), border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))

def draw_text_center(surf, text, font, color, cx, cy):
    t = font.render(text, True, color)
    surf.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2))

def draw_text(surf, text, font, color, x, y):
    t = font.render(text, True, color)
    surf.blit(t, (x, y))

# ─── House drawing ────────────────────────────────────────────
HOUSE_X  = 50
HOUSE_Y  = 120
HOUSE_W  = 580
HOUSE_H  = 400

# Rooms
KITCHEN_RECT  = pygame.Rect(HOUSE_X,            HOUSE_Y+200, HOUSE_W//2,   200)
LIVING_RECT   = pygame.Rect(HOUSE_X+HOUSE_W//2, HOUSE_Y+200, HOUSE_W//2,   200)
BEDROOM_RECT  = pygame.Rect(HOUSE_X,            HOUSE_Y,     HOUSE_W//2,   200)
HALLWAY_RECT  = pygame.Rect(HOUSE_X+HOUSE_W//2, HOUSE_Y,     HOUSE_W//2,   200)

# Windows (left wall and right wall)
WIN_L = pygame.Rect(HOUSE_X+20,       HOUSE_Y+30,  80, 60)
WIN_R = pygame.Rect(HOUSE_X+HOUSE_W-100, HOUSE_Y+30, 80, 60)
WIN_L2= pygame.Rect(HOUSE_X+20,       HOUSE_Y+230, 80, 50)
WIN_R2= pygame.Rect(HOUSE_X+HOUSE_W-100, HOUSE_Y+230, 80, 50)

# Stove position
STOVE_X = HOUSE_X + 60
STOVE_Y = HOUSE_Y + 340

# Sensor position
SENSOR_X = HOUSE_X + HOUSE_W//2 - 15
SENSOR_Y  = HOUSE_Y + 210

def draw_house(surf, win_open, elec_on, gas_level, sensor_blink):
    # ── Roof ──────────────────────────────────────────────────
    pts = [(HOUSE_X-10, HOUSE_Y),
           (HOUSE_X + HOUSE_W//2, HOUSE_Y-80),
           (HOUSE_X + HOUSE_W+10, HOUSE_Y)]
    pygame.draw.polygon(surf, (15, 28, 50), pts)
    pygame.draw.polygon(surf, BORDER, pts, 2)

    # ── Rooms ─────────────────────────────────────────────────
    for rect, col, label in [
        (KITCHEN_RECT,  (14,24,44),  "KITCHEN"),
        (LIVING_RECT,   (12,22,40),  "LIVING ROOM"),
        (BEDROOM_RECT,  (13,23,42),  "BEDROOM"),
        (HALLWAY_RECT,  (11,20,38),  "HALLWAY"),
    ]:
        pygame.draw.rect(surf, col, rect)
        pygame.draw.rect(surf, (*BORDER, 255), rect, 1)
        lbl = F_TINY.render(label, True, MUTED)
        surf.blit(lbl, (rect.x+6, rect.y+4))

    # ── House border ──────────────────────────────────────────
    pygame.draw.rect(surf, (*BORDER, 255),
                     (HOUSE_X, HOUSE_Y, HOUSE_W, HOUSE_H), 2)

    # ── Windows ───────────────────────────────────────────────
    for wr in [WIN_L, WIN_R, WIN_L2, WIN_R2]:
        if win_open:
            pygame.draw.rect(surf, (20,60,100), wr)
            pygame.draw.rect(surf, BLUE, wr, 2)
            # Window panes open (lines moved apart)
            mid = wr.centerx
            pygame.draw.line(surf, BLUE,
                             (wr.x+4, wr.y+4),
                             (mid-4, wr.bottom-4), 1)
            pygame.draw.line(surf, BLUE,
                             (mid+4, wr.y+4),
                             (wr.right-4, wr.bottom-4), 1)
            # Air flow arrows
            for ay in range(wr.y+8, wr.bottom-4, 10):
                arrow = F_TINY.render(">>", True, (*BLUE, 160))
                surf.blit(arrow, (wr.x+6, ay))
            open_lbl = F_TINY.render("OPEN", True, GREEN)
            surf.blit(open_lbl, (wr.x+wr.width//2 -
                                  open_lbl.get_width()//2,
                                  wr.bottom+2))
        else:
            pygame.draw.rect(surf, (10,30,55), wr)
            pygame.draw.rect(surf, (30,60,100), wr, 2)
            # Cross panes (closed window)
            pygame.draw.line(surf, (30,60,100),
                             (wr.centerx, wr.top),
                             (wr.centerx, wr.bottom), 1)
            pygame.draw.line(surf, (30,60,100),
                             (wr.left, wr.centery),
                             (wr.right, wr.centery), 1)

    # ── Stove ─────────────────────────────────────────────────
    stove_rect = pygame.Rect(STOVE_X-30, STOVE_Y-10, 70, 35)
    pygame.draw.rect(surf, (20,35,55), stove_rect, border_radius=4)
    pygame.draw.rect(surf, (40,70,110), stove_rect, 2, border_radius=4)
    # Burner circles
    for bx in [STOVE_X-15, STOVE_X+15]:
        pygame.draw.circle(surf, (30,50,80), (bx, STOVE_Y+8), 8)
        pygame.draw.circle(surf, (40,70,110), (bx, STOVE_Y+8), 8, 1)
    stove_lbl = F_TINY.render("GAS STOVE", True, MUTED)
    surf.blit(stove_lbl, (STOVE_X - stove_lbl.get_width()//2 + 5,
                           STOVE_Y + 28))

    # ── Electricity panel ─────────────────────────────────────
    ep = pygame.Rect(HOUSE_X + HOUSE_W//2 - 30,
                     HOUSE_Y + 260, 60, 45)
    panel_col = (20,35,20) if elec_on else (35,10,10)
    pygame.draw.rect(surf, panel_col, ep, border_radius=4)
    border_col = GREEN if elec_on else RED
    pygame.draw.rect(surf, border_col, ep, 2, border_radius=4)
    # Lightning bolt
    bolt_col = YELLOW if elec_on else (80,20,20)
    draw_text_center(surf, "⚡" if elec_on else "✖",
                     F_MED, bolt_col,
                     ep.centerx, ep.centery-4)
    elec_lbl = F_TINY.render(
        "ON" if elec_on else "OFF", True,
        GREEN if elec_on else RED)
    surf.blit(elec_lbl,
              (ep.centerx - elec_lbl.get_width()//2, ep.bottom+2))

    # ── Gas sensor ────────────────────────────────────────────
    s_col = GREEN if gas_level < 50 else \
            YELLOW if gas_level < 75 else RED
    if sensor_blink and gas_level >= 75:
        s_col = RED if (pygame.time.get_ticks()//300)%2==0 else (80,0,0)
    pygame.draw.circle(surf, s_col, (SENSOR_X, SENSOR_Y), 12)
    pygame.draw.circle(surf, WHITE,  (SENSOR_X, SENSOR_Y), 12, 2)
    draw_text_center(surf, "S", F_TINY, WHITE, SENSOR_X, SENSOR_Y)
    sen_lbl = F_TINY.render("SENSOR", True, s_col)
    surf.blit(sen_lbl, (SENSOR_X - sen_lbl.get_width()//2,
                        SENSOR_Y + 14))

    # ── People icon ───────────────────────────────────────────
    person_col = WHITE if gas_level < 75 else RED
    draw_text_center(surf, "🧑", F_MED, person_col,
                     HOUSE_X + HOUSE_W//2 + 80,
                     HOUSE_Y + 290)
    draw_text_center(surf, "👩", F_MED, person_col,
                     HOUSE_X + HOUSE_W//2 + 110,
                     HOUSE_Y + 290)

    # ── Room gas overlay (tint room when gassy) ───────────────
    if gas_level > 40:
        alpha = min(int((gas_level-40)*2.5), 100)
        ov = pygame.Surface(
            (KITCHEN_RECT.width, KITCHEN_RECT.height),
            pygame.SRCALPHA)
        ov.fill((245, 158, 11, alpha))
        surf.blit(ov, (KITCHEN_RECT.x, KITCHEN_RECT.y))


def main():
    # ── State ─────────────────────────────────────────────────
    gas_level     = 22
    sim_running   = False
    sim_done_flag = False
    win_open      = False
    elec_on       = True
    email_status  = "STANDBY"
    particles     = []
    flames        = []
    graph_vals    = [22,25,30,28,24,20,19,23,27,22,18,20]
    log_entries   = [
        ("2026-06-10 08:14", 42,  "SAFE",    "No actions"),
        ("2026-06-10 09:02", 78,  "WARNING", "Alert sent"),
        ("2026-06-10 11:55", 95,  "DANGER",  "Windows+Power+Email"),
        ("2026-06-10 14:30", 31,  "SAFE",    "No actions"),
    ]
    sim_seq       = [22,30,42,55,64,72,81,90,96,98,94,85,72,58,42,30,22]
    sim_idx       = 0
    sim_timer     = 0
    peaked        = False
    warn_beeped   = False
    sensor_blink  = False
    show_log      = False
    notification  = ""
    notif_timer   = 0
    alarm_played  = False

    # ── Login screen ──────────────────────────────────────────
    login_done  = False
    login_user  = ""
    login_pass  = ""
    login_field = "user"
    login_error = ""

    while not login_done:
        screen.fill(BG)
        draw_rounded_rect(screen, CARD, (W//2-180, H//2-200, 360, 380), 14)

        draw_text_center(screen, "GasSafe Pro",
                         F_BIG, RED, W//2, H//2-150)
        draw_text_center(screen, "Smart Gas Leak Safety System",
                         F_SM, MUTED, W//2, H//2-115)

        # Username box
        ub_col = BLUE if login_field=="user" else BORDER
        draw_rounded_rect(screen, (20,35,60),
                          (W//2-140, H//2-80, 280, 38), 6)
        pygame.draw.rect(screen, ub_col,
                         (W//2-140, H//2-80, 280, 38), 2,
                         border_radius=6)
        draw_text(screen, "Username:", F_TINY, MUTED,
                  W//2-138, H//2-100)
        u_disp = login_user if login_user else "admin"
        draw_text(screen, u_disp, F_SM, WHITE, W//2-132, H//2-68)

        # Password box
        pb_col = BLUE if login_field=="pass" else BORDER
        draw_rounded_rect(screen, (20,35,60),
                          (W//2-140, H//2-20, 280, 38), 6)
        pygame.draw.rect(screen, pb_col,
                         (W//2-140, H//2-20, 280, 38), 2,
                         border_radius=6)
        draw_text(screen, "Password:", F_TINY, MUTED,
                  W//2-138, H//2-40)
        p_disp = "*"*len(login_pass) if login_pass else "gas123"
        draw_text(screen, p_disp, F_SM, WHITE, W//2-132, H//2-8)

        if login_error:
            draw_text_center(screen, login_error,
                             F_SM, RED, W//2, H//2+38)

        # Login button
        draw_rounded_rect(screen, (180,20,20),
                          (W//2-140, H//2+58, 280, 42), 8)
        draw_text_center(screen, "LOGIN",
                         F_MED, WHITE, W//2, H//2+79)

        draw_text_center(screen, "Default: admin / gas123",
                         F_TINY, MUTED, W//2, H//2+118)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if (W//2-140 <= mx <= W//2+140 and
                        H//2-80 <= my <= H//2-42):
                    login_field = "user"
                elif (W//2-140 <= mx <= W//2+140 and
                          H//2-20 <= my <= H//2+18):
                    login_field = "pass"
                elif (W//2-140 <= mx <= W//2+140 and
                          H//2+58 <= my <= H//2+100):
                    u = login_user if login_user else "admin"
                    p = login_pass if login_pass else "gas123"
                    if u == "admin" and p == "gas123":
                        login_done = True
                    else:
                        login_error = "Invalid username or password"
                        login_pass  = ""
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    login_field = "pass" if login_field=="user" else "user"
                elif event.key == pygame.K_RETURN:
                    u = login_user if login_user else "admin"
                    p = login_pass if login_pass else "gas123"
                    if u == "admin" and p == "gas123":
                        login_done = True
                    else:
                        login_error = "Wrong credentials"
                        login_pass  = ""
                elif event.key == pygame.K_BACKSPACE:
                    if login_field == "user":
                        login_user = login_user[:-1]
                    else:
                        login_pass = login_pass[:-1]
                else:
                    ch = event.unicode
                    if login_field == "user":
                        login_user += ch
                    else:
                        login_pass += ch
        clock.tick(30)

    # ══════════════════════════════════════════════════════════
    # MAIN DASHBOARD LOOP
    # ══════════════════════════════════════════════════════════
    while True:
        dt = clock.tick(30)
        sim_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Start button
                if (660 <= mx <= 960 and 370 <= my <= 410
                        and not sim_running):
                    sim_running  = True
                    sim_idx      = 0
                    peaked       = False
                    warn_beeped  = False
                    alarm_played = False
                    win_open     = False
                    elec_on      = True
                    particles.clear()
                    email_status = "STANDBY"
                    sim_done_flag= False
                # Reset button
                if (660 <= mx <= 960 and 420 <= my <= 458
                        and not sim_running):
                    gas_level    = 22
                    win_open     = False
                    elec_on      = True
                    particles.clear()
                    email_status = "STANDBY"
                    notification = "System reset!"
                    notif_timer  = 3000
                # Log toggle
                if (660 <= mx <= 960 and 460 <= my <= 498):
                    show_log = not show_log
                # Export
                if (660 <= mx <= 960 and 500 <= my <= 538):
                    import csv, os
                    path = os.path.join(
                        os.path.expanduser("~"),
                        "Downloads", "gas_log.csv")
                    with open(path,"w",newline="") as f:
                        w2 = csv.writer(f)
                        w2.writerow(["Time","Level","Status","Actions"])
                        for r in log_entries: w2.writerow(r)
                    notification = "Exported to Downloads!"
                    notif_timer  = 3000

        # ── Simulation step ───────────────────────────────────
        if sim_running and sim_timer >= 600:
            sim_timer = 0
            if sim_idx < len(sim_seq):
                gas_level = sim_seq[sim_idx]
                graph_vals.append(gas_level)
                if len(graph_vals) > 20: graph_vals.pop(0)
                sim_idx  += 1
                sensor_blink = gas_level >= 75

                if gas_level >= 50 and not warn_beeped:
                    warn_beeped = True
                    threading.Thread(
                        target=lambda: (
                            winsound.Beep(1000,300),
                            time.sleep(0.1),
                            winsound.Beep(1000,300)),
                        daemon=True).start()

                if gas_level >= 75 and not peaked:
                    peaked      = True
                    win_open    = True
                    elec_on     = False
                    email_status = "SENDING..."
                    if not alarm_played:
                        alarm_played = True
                        threading.Thread(target=play_alarm, daemon=True).start()
                    threading.Thread(
                        target=lambda: (
                            send_email_alert(gas_level),
                            ),
                        daemon=True).start()
                    notification = "DANGER! Windows opened + Power cut!"
                    notif_timer  = 5000

            else:
                # Done
                if not sim_done_flag:
                    sim_done_flag = True
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    log_entries.insert(0,(ts,98,"DANGER",
                                         "Windows+Power+Email"))
                    threading.Thread(target=play_safe, daemon=True).start()
                    notification = "Simulation done! Incident logged."
                    notif_timer  = 4000
                sim_running = False

        # ── Spawn particles ───────────────────────────────────
        if gas_level > 30:
            rate = max(1, int((gas_level-30)/15))
            for _ in range(rate):
                phase = "danger" if gas_level>=75 else \
                        "vent"   if win_open      else "leak"
                particles.append(Particle(STOVE_X, STOVE_Y, phase))

        # Spawn flames on stove
        if elec_on or gas_level < 75:
            for _ in range(2):
                for bx in [STOVE_X-15, STOVE_X+15]:
                    flames.append(Flame(bx, STOVE_Y))

        # Update particles
        particles = [p for p in particles if p.alive]
        for p in particles:
            p.update(win_open, WIN_L.x, WIN_R.x)
            if win_open: p.phase = "vent"
            elif gas_level>=75: p.phase = "danger"

        # Update flames
        flames = [f for f in flames if f.alive]
        for f in flames: f.update()

        if notif_timer > 0: notif_timer -= dt

        # ══════════════════════════════════════════════════════
        # DRAW
        # ══════════════════════════════════════════════════════
        screen.fill(BG)

        # ── Top bar ───────────────────────────────────────────
        pygame.draw.rect(screen, CARD, (0,0,W,52))
        pygame.draw.line(screen, BORDER, (0,52),(W,52), 1)
        draw_text(screen, "🔴  GasSafe Pro",
                  F_MED, WHITE, 16, 14)
        st_col = YELLOW if sim_running else GREEN
        st_txt = "● Monitoring..." if sim_running else "● Standby"
        draw_text(screen, st_txt, F_SM, st_col, W-200, 18)
        draw_text(screen, "admin", F_TINY, MUTED, W-60, 20)

        # ── House ─────────────────────────────────────────────
        draw_house(screen, win_open, elec_on,
                   gas_level, sensor_blink)

        # ── Flames ────────────────────────────────────────────
        for f in flames: f.draw(screen)

        # ── Particles ─────────────────────────────────────────
        for p in particles: p.draw(screen)

        # ── Right panel ───────────────────────────────────────
        px = 650
        # Panel BG
        draw_rounded_rect(screen, CARD,
                          (px-10, 60, 360, 580), 10)
        pygame.draw.rect(screen, BORDER,
                         (px-10,60,360,580), 1, border_radius=10)

        # Gas level display
        s_col, s_txt = (
            (GREEN,  "SAFE")    if gas_level < 50 else
            (YELLOW, "WARNING") if gas_level < 75 else
            (RED,    "DANGER")
        )
        draw_text(screen, "GAS LEVEL", F_TINY, MUTED, px, 72)
        lvl_surf = F_BIG.render(str(gas_level)+" ppm", True, s_col)
        screen.blit(lvl_surf, (px, 88))
        draw_rounded_rect(screen, (*s_col,40),
                          (px, 126, 120, 24), 4)
        draw_text_center(screen, s_txt, F_TINY, s_col,
                         px+60, 138)

        # Progress bar
        draw_text(screen, "Level indicator:", F_TINY, MUTED, px, 162)
        pygame.draw.rect(screen, BORDER, (px, 178, 300, 12),
                         border_radius=6)
        bw = int((gas_level/100)*300)
        if bw > 0:
            pygame.draw.rect(screen, s_col, (px, 178, bw, 12),
                             border_radius=6)

        # Action cards
        for i, (icon, lbl, active, col) in enumerate([
            ("🪟", "WINDOWS",     win_open,      BLUE),
            ("⚡", "ELECTRICITY", not elec_on,   ORANGE),
            ("📧", "EMAIL",       peaked,         GREEN),
        ]):
            cx = px + i*104
            ac = (*col,40) if active else (*BORDER,255)
            draw_rounded_rect(screen, CARD,
                              (cx, 202, 96, 70), 8)
            bc = col if active else BORDER
            pygame.draw.rect(screen, bc,
                             (cx,202,96,70), 2, border_radius=8)
            draw_text_center(screen, icon, F_MED, WHITE,
                             cx+48, 226)
            st = ("OPEN"  if active else "CLOSED")  if i==0 else \
                 ("OFF"   if active else "ON")       if i==1 else \
                 (email_status if active else "STANDBY")
            draw_text_center(screen, lbl, F_TINY,
                             col if active else MUTED, cx+48, 248)
            draw_text_center(screen, st,  F_TINY,
                             col if active else MUTED, cx+48, 262)

        # ── Live graph ────────────────────────────────────────
        draw_text(screen, "📈 LIVE PPM GRAPH",
                  F_TINY, MUTED, px, 284)
        gx, gy, gw, gh = px, 300, 320, 80
        pygame.draw.rect(screen, (10,18,35),
                         (gx,gy,gw,gh), border_radius=4)
        pygame.draw.rect(screen, BORDER,
                         (gx,gy,gw,gh), 1, border_radius=4)
        # Danger line
        dl_y = gy + gh - int((75/100)*gh)
        pygame.draw.line(screen, (*RED,100),
                         (gx,dl_y),(gx+gw,dl_y), 1)
        # Graph line
        if len(graph_vals) >= 2:
            pts2 = []
            for i2, v in enumerate(graph_vals):
                gpt_x = gx + int((i2/(len(graph_vals)-1))*gw)
                gpt_y = gy + gh - int((min(v,100)/100)*gh)
                pts2.append((gpt_x, gpt_y))
            # Area fill
            poly2 = [(gx,gy+gh)] + pts2 + [(gx+gw,gy+gh)]
            s2 = pygame.Surface((gw,gh), pygame.SRCALPHA)
            adj = [(x-gx, y-gy) for x,y in poly2]
            pygame.draw.polygon(s2, (56,189,248,30), adj)
            screen.blit(s2,(gx,gy))
            # Line
            for i2 in range(len(pts2)-1):
                _, lc = (
                    (None,GREEN)  if graph_vals[i2+1]<50 else
                    (None,YELLOW) if graph_vals[i2+1]<75 else
                    (None,RED)
                )
                pygame.draw.line(screen, lc,
                                 pts2[i2], pts2[i2+1], 2)
            for i2,(gx2,gy2) in enumerate(pts2):
                _, dc = (
                    (None,GREEN)  if graph_vals[i2]<50 else
                    (None,YELLOW) if graph_vals[i2]<75 else
                    (None,RED)
                )
                pygame.draw.circle(screen, dc, (gx2,gy2), 3)

        # ── Stats ─────────────────────────────────────────────
        d_count = sum(1 for r in log_entries if r[2]=="DANGER")
        w_count = sum(1 for r in log_entries if r[2]=="WARNING")
        for si,(slbl,sval,sc) in enumerate([
            ("Incidents", str(d_count), RED),
            ("Warnings",  str(w_count), YELLOW),
            ("Uptime",    "99.8%",      BLUE),
        ]):
            sx = px + si*108
            draw_rounded_rect(screen, (10,18,35),
                              (sx, 392, 100, 52), 6)
            draw_text_center(screen, sval, F_MONO_S, sc,
                             sx+50, 408)
            draw_text_center(screen, slbl, F_TINY, MUTED,
                             sx+50, 428)

        # ── Buttons ───────────────────────────────────────────
        for bi,(btxt,by,bcol,enabled) in enumerate([
            ("▶  START SIMULATION", 370, RED,            not sim_running),
            ("↺  RESET",            420, (30,50,80),     not sim_running),
            ("📋  LOG  "+("▲" if show_log else "▼"), 460,(20,40,20), True),
            ("💾  EXPORT CSV",      500, (20,40,20),     True),
        ]):
            bc2 = bcol if enabled else (20,30,45)
            tc2 = WHITE if enabled else MUTED
            draw_rounded_rect(screen, bc2,
                              (px-10+10, by, 300, 34), 6)
            draw_text_center(screen, btxt, F_SM, tc2,
                             px-10+10+150, by+17)

        # ── Log panel ─────────────────────────────────────────
        if show_log:
            log_y = 540
            draw_rounded_rect(screen, CARD,
                              (px-10, log_y, 360, 150), 8)
            pygame.draw.rect(screen, BORDER,
                             (px-10,log_y,360,150), 1,
                             border_radius=8)
            draw_text(screen, "INCIDENT LOG",
                      F_TINY, MUTED, px, log_y+6)
            for li, row in enumerate(log_entries[:4]):
                ly = log_y + 26 + li*28
                rc = GREEN if row[2]=="SAFE" else \
                     YELLOW if row[2]=="WARNING" else RED
                draw_text(screen, row[0], F_TINY, MUTED, px, ly)
                draw_text(screen, str(row[1])+"ppm",
                          F_TINY, rc, px+120, ly)
                draw_text(screen, row[2], F_TINY, rc, px+175, ly)

        # ── Notification toast ────────────────────────────────
        if notification and notif_timer > 0:
            is_danger = "DANGER" in notification or \
                        "danger" in notification
            nc = (100,20,20) if is_danger else (20,60,20)
            draw_rounded_rect(screen, nc,
                              (W//2-200, H-60, 400, 44), 8)
            draw_text_center(screen, notification,
                             F_SM, WHITE, W//2, H-38)

        # ── House label ───────────────────────────────────────
        draw_text_center(screen,
                         "REAL-TIME HOUSE SIMULATION",
                         F_TINY, MUTED,
                         HOUSE_X + HOUSE_W//2,
                         HOUSE_Y + HOUSE_H + 14)

        pygame.display.flip()

main()
