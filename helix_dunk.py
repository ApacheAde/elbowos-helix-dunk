#!/usr/bin/env python3
"""Helix Dunk — neon gravity-basketball arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/HelixDunk_ElbowOS.mp4")
TITLE, HANDLE = "HELIX DUNK", "x.com/ElbowOS"
VOID, INK, COURT = (8, 4, 22), (28, 10, 36), (18, 8, 42)
CORAL, AMBER, LIME = (255, 92, 78), (255, 186, 48), (150, 255, 80)
MAG, CYAN, WHITE, ROSE = (255, 70, 180), (60, 230, 255), (250, 248, 255), (255, 110, 140)
ORANGE, NAVY, GOLD = (255, 120, 36), (16, 12, 48), (255, 214, 90)

class Game:
    def __init__(self):
        pygame.init(); pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit(); pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 62, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 38, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 26)
        self.clock = pygame.time.Clock()
        self.score = self.combo = self.t = self.flash = self.dunks = 0
        self.px, self.py = W // 2, 1640
        self.aim = -math.pi / 2
        self.charge = 0.0
        self.charging = False
        self.ball = None  # x,y,vx,vy
        self.hoop = [W // 2, 700, 3.4, 0.0]  # x,y,vx,phase
        self.wells = [
            [240, 1040, 62, 0.28],
            [860, 1180, 70, 0.30],
            [540, 900, 48, -0.22],
        ]
        self.sparks, self.stars, self.pop, self.pop_t = [], [], "", 0
        self.cooldown = 0
        for _ in range(80):
            self.stars.append([random.randint(0, W), random.randint(180, H),
                               random.choice([CORAL, AMBER, LIME, MAG, CYAN]),
                               random.randint(1, 3)])

    def burst(self, x, y, col, n=16):
        for _ in range(n):
            a = random.uniform(0, 6.2832); sp = random.uniform(2.0, 11)
            self.sparks.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 22, col])

    def shoot(self, power=None):
        if self.ball is not None or self.cooldown > 0:
            return
        p = 16.0 + (power if power is not None else self.charge) * 22.0
        self.ball = [self.px, self.py - 70, math.cos(self.aim) * p, math.sin(self.aim) * p]
        self.charge = 0.0
        self.charging = False
        self.burst(self.px, self.py - 70, AMBER, 10)

    def autoplay(self):
        hx, hy = self.hoop[0] + self.hoop[2] * 10, self.hoop[1]
        want_x = hx
        self.px += max(-9, min(9, (want_x - self.px) * 0.18))
        self.px = max(140, min(W - 140, self.px))
        want = math.atan2(hy - 80 - (self.py - 70), hx - self.px)
        self.aim += max(-0.12, min(0.12, (want - self.aim) * 0.45))
        if self.ball is None and self.cooldown == 0:
            self.charging = True
            self.charge = min(1.0, self.charge + 0.09)
            if self.charge > 0.42:
                self.shoot(0.62)

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.pop_t = max(0, self.pop_t - 1)
        self.cooldown = max(0, self.cooldown - 1)
        self.hoop[3] += 0.03
        self.hoop[0] += self.hoop[2] + math.sin(self.hoop[3]) * 1.4
        self.hoop[1] = 680 + 70 * math.sin(self.t * 0.028)
        if self.hoop[0] < 220 or self.hoop[0] > W - 220:
            self.hoop[2] *= -1
            self.hoop[0] = max(220, min(W - 220, self.hoop[0]))
        if self.charging:
            self.charge = min(1.0, self.charge + 0.035)
        if self.ball:
            bx, by, vx, vy = self.ball
            vy += 0.42
            for wx, wy, wr, pull in self.wells:
                dx, dy = wx - bx, wy - by
                d = math.hypot(dx, dy) + 8
                if d < wr * 3.2:
                    f = pull * 180.0 / (d * d)
                    vx += f * dx
                    vy += f * dy
            vx *= 0.998; vy *= 0.998
            bx += vx; by += vy
            if bx < 50 or bx > W - 50:
                vx *= -0.72; bx = max(50, min(W - 50, bx))
            if by > 1720:
                self.ball = None
                self.combo = 0
                self.pop, self.pop_t, self.flash = "AIRBALL", 14, 6
                self.cooldown = 8
                self.burst(bx, 1720, ROSE, 12)
            elif by < 240:
                vy = abs(vy) * 0.4; by = 240
                self.ball = [bx, by, vx, vy]
            else:
                self.ball = [bx, by, vx, vy]
            hx, hy = self.hoop[0], self.hoop[1]
            if self.ball and abs(bx - hx) < 78 and abs(by - hy) < 36 and vy > 0.4:
                self.combo += 1
                pts = 100 + self.combo * 25
                self.score += pts
                self.dunks += 1
                self.pop, self.pop_t, self.flash = "DUNK", 18, 8
                self.burst(hx, hy, LIME, 22)
                self.burst(hx, hy, GOLD, 12)
                self.ball = None
                self.cooldown = 10
        for p in self.sparks:
            p[0] += p[2]; p[1] += p[3]; p[3] += 0.18; p[4] -= 1
        self.sparks = [p for p in self.sparks if p[4] > 0]
        for s in self.stars:
            s[1] += 0.35
            if s[1] > H:
                s[1], s[0] = 180, random.randint(0, W)

    def draw(self, surf):
        surf.fill(VOID)
        for i in range(16):
            pygame.draw.rect(surf, (10 + i, 6 + i, 28 + i * 2), (0, 200 + i * 108, W, 112))
        for s in self.stars:
            pygame.draw.circle(surf, s[2], (int(s[0]), int(s[1])), s[3])
        pygame.draw.rect(surf, INK, (0, 0, W, 230))
        pygame.draw.rect(surf, CORAL, (0, 226, W, 6))
        pygame.draw.rect(surf, NAVY, (40, 1720, W - 80, 90), border_radius=18)
        pygame.draw.rect(surf, AMBER, (40, 1720, W - 80, 90), 3, border_radius=18)
        pygame.draw.circle(surf, (40, 20, 60), (W // 2, 1764), 46, 2)
        for wx, wy, wr, pull in self.wells:
            pulse = wr + 6 * math.sin(self.t * 0.12 + wx)
            col = CYAN if pull < 0 else ORANGE
            pygame.draw.circle(surf, col, (int(wx), int(wy)), int(pulse + 18), 2)
            pygame.draw.circle(surf, col, (int(wx), int(wy)), int(pulse * 0.45))
            pygame.draw.circle(surf, WHITE, (int(wx) - 6, int(wy) - 6), 6)
        hx, hy = int(self.hoop[0]), int(self.hoop[1])
        pygame.draw.rect(surf, (80, 40, 20), (hx + 62, hy - 90, 14, 130))
        pygame.draw.ellipse(surf, GOLD, (hx - 68, hy - 16, 136, 32), 8)
        pygame.draw.ellipse(surf, LIME, (hx - 54, hy - 10, 108, 22), 3)
        for k in range(7):
            nx = hx - 48 + k * 16
            pygame.draw.line(surf, WHITE, (nx, hy + 8), (hx + int((k - 3) * 8), hy + 48), 1)
        pygame.draw.circle(surf, CORAL, (int(self.px), int(self.py)), 36)
        pygame.draw.circle(surf, WHITE, (int(self.px) - 8, int(self.py) - 8), 8)
        pygame.draw.circle(surf, VOID, (int(self.px) - 6, int(self.py) - 8), 3)
        pygame.draw.rect(surf, AMBER, (int(self.px) - 18, int(self.py) + 30, 36, 28), border_radius=6)
        ax = self.px + math.cos(self.aim) * (90 + self.charge * 80)
        ay = self.py - 70 + math.sin(self.aim) * (90 + self.charge * 80)
        pygame.draw.line(surf, LIME if self.charging else AMBER,
                         (int(self.px), int(self.py - 70)), (int(ax), int(ay)), 4)
        if self.charging:
            pygame.draw.circle(surf, GOLD, (int(ax), int(ay)), 8 + int(self.charge * 10))
        if self.ball:
            bx, by = int(self.ball[0]), int(self.ball[1])
            pygame.draw.circle(surf, AMBER, (bx, by), 22)
            pygame.draw.circle(surf, GOLD, (bx, by), 22, 3)
            pygame.draw.circle(surf, WHITE, (bx - 6, by - 6), 6)
            pygame.draw.arc(surf, VOID, (bx - 14, by - 14, 28, 28), 0.4, 2.4, 2)
        for p in self.sparks:
            pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), max(2, p[4] // 5))
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((150, 255, 80, 30) if self.pop == "DUNK" else (255, 90, 120, 28))
            surf.blit(ov, (0, 0))
        if self.pop_t:
            lab = self.font_lg.render(self.pop, True, LIME if self.pop == "DUNK" else ROSE)
            surf.blit(lab, lab.get_rect(center=(W // 2, 780)))
        title = self.font_lg.render(TITLE, True, AMBER)
        surf.blit(title, title.get_rect(center=(W // 2, 72)))
        sub = self.font_sm.render(HANDLE, True, MAG)
        surf.blit(sub, sub.get_rect(center=(W // 2, 132)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        cb = self.font_sm.render(f"STREAK  x{self.combo}   DUNKS  {self.dunks}", True, LIME)
        hint = self.font_sm.render("A D aim   HOLD SPACE shoot", True, CORAL)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 150)))
        surf.blit(cb, cb.get_rect(center=(W // 2, H - 96)))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 48)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYUP and ev.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    if self.charging:
                        self.shoot()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.px -= 10; self.aim -= 0.03
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.px += 10; self.aim += 0.03
            self.px = max(80, min(W - 80, self.px))
            self.aim = max(-math.pi + 0.2, min(-0.15, self.aim))
            hold = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
            if hold and self.ball is None:
                self.charging = True
            self.tick(); self.draw(self.screen); pygame.display.flip(); self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "20", "-preset", "fast", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay(); self.tick(); self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT); pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
