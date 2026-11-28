import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.animation import FuncAnimation, FFMpegWriter

SPRAY = 45
STORMS = [55, 80, 103]
SEASON_OFF = 183
SWAP_START = 120

def atrazine(d):
    return 0.1 + (np.exp(-(d - SPRAY) / 20) if d > SPRAY else 0)

def raining(d):
    return any(s <= d < s + 3 for s in STORMS)

def flow(d):
    return 2.5 if raining(d) else 1.0

def twin(d):
    if d < 15:
        return "Start", "gold", (68, 59)
    if SPRAY <= d < SPRAY + 3:
        return "Spray day", "gold", (30, 60)
    for s in STORMS:
        if s - 2 <= d < s:
            return "Raise boards", "gold", (68, 59)
        if s <= d < s + 6:
            return "Hold water", "gold", (30, 47)
    if swap_day <= d < swap_day + 7:
        return "Swap filter", "red", (112, 42)
    if SEASON_OFF <= d < SEASON_OFF + 7:
        return "Bypass", "gold", (68, 59)
    return "All good", "green", None

fill = np.zeros((366, 3))
swap_day = 999
f = np.zeros(3)
for d in range(365):
    if 15 <= d < SEASON_OFF:
        load = atrazine(d) * flow(d)
        f += load * np.array([1 / 42, 1 / 150, 1 / 700])
    if d >= SWAP_START and f[0] >= 0.85 and swap_day == 999:
        swap_day = d
        f[0] = 0
    f = np.clip(f, 0, 1)
    fill[d] = f

TREAT = [(3, 41), (66, 41), (66, 36), (80, 36), (105, 41), (112, 41), (112, 33), (112, 50), (120, 50),
         (120, 33), (128, 33), (128, 50), (134, 47), (142, 47), (142, 52), (152, 52)]
BYPASS = [(3, 41), (66, 41), (66, 36), (80, 36), (105, 41), (107, 41), (107, 25), (142, 25), (142, 52), (152, 52)]

def point(path, t):
    p = np.array(path, float)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    pos = t * seg.sum()
    i = min(np.searchsorted(np.cumsum(seg), pos), len(seg) - 1)
    start = np.cumsum(seg)[i] - seg[i]
    return p[i] + (pos - start) / seg[i] * (p[i + 1] - p[i])

dots = np.random.default_rng(0).random(40)
fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])

def box(x, y, w, h, name, color="#d9d6cc"):
    ax.add_patch(Rectangle((x, y), w, h, fc=color, ec="#555", lw=1.5))
    ax.text(x + w / 2, y - 2.6, name, ha="center", fontsize=11, fontweight="bold", color="white")

def draw(d):
    global dots
    ax.clear()
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 90)
    ax.axis("off")
    treating = 15 <= d < SEASON_OFF
    sky = "#9fb0bd" if raining(d) else "#b8dcf5" if d < SEASON_OFF else "#e3e8ec"
    ax.add_patch(Rectangle((0, 56), 160, 34, color=sky))
    ax.add_patch(Rectangle((0, 12), 160, 44, color="#8b6a4a"))
    grass = "#6aa84f" if d < SEASON_OFF else "#c9b25a"
    ax.add_patch(Rectangle((0, 55), 146, 1.5, color=grass))
    ax.scatter(np.arange(1, 146, 1.5), [57] * 97, marker="^", s=25, color=grass)
    if raining(d):
        r = np.random.default_rng(d).random((80, 2))
        ax.scatter(r[:, 0] * 140, 57 + r[:, 1] * 30, marker="|", s=40, color="#3b6e9b")
    if twin(d)[0] == "Hold water":
        ax.add_patch(Rectangle((0, 42), 60, 7, color="#6fb6e8", alpha=0.75))

    ax.plot([2, 66], [41, 41], color="#333", lw=7)
    ax.text(20, 37.5, "Tile drain", ha="center", fontsize=11, fontweight="bold", color="white")
    ax.plot([107, 107, 142], [41, 25, 25], color="#333", lw=5)
    ax.plot([48, 48], [41, 56], color="#333", lw=5)
    ax.add_patch(Rectangle((45.5, 55.5), 5, 2, color="#333"))
    ax.text(48, 59.5, "Surface inlet", ha="center", fontsize=10, fontweight="bold")
    box(62, 28, 12, 28, "Inlet box")
    box(79, 33, 26, 16, "Woodchip + biochar", "#c99a5c")
    box(110, 28, 24, 26, "Carbon box")
    box(138, 30, 8, 26, "Outlet")
    ax.add_patch(Rectangle((148, 49), 12, 4, color="#6fb6e8"))
    ax.text(153.5, 45, "Ditch", ha="center", fontsize=11, fontweight="bold", color="white")
    ax.add_patch(Rectangle((63.2, 51), 9.6, 3.2, color="green" if treating else "grey"))

    for k, x in enumerate([112.5, 120, 127.5]):
        level = fill[d, k]
        ax.add_patch(Rectangle((x - 2.8, 31), 5.6, 21, fc="#333", ec=plt.cm.RdYlGn_r(level), lw=3))
        ax.add_patch(Rectangle((x - 2.8, 31), 5.6, 21 * level, color=plt.cm.RdYlGn_r(level), alpha=0.6))
        ax.text(x, 41.5, f"{level:.0%}", ha="center", fontsize=10, fontweight="bold", color="white")

    dots = (dots + 0.004 * flow(d)) % 1
    path = TREAT if treating else BYPASS
    for t in dots:
        x, y = point(path, t)
        clean = treating and x > 117
        dirty = atrazine(d) > 0.3 and not clean
        ax.add_patch(Circle((x, y), 0.8, color="orange" if dirty else "#4aa3e0" if clean else "#9fb7c9"))

    word, color, target = twin(d)
    for sx, sy in [(64, 45), (102, 46), (109, 43), (124, 53), (142, 40)]:
        ax.add_patch(Circle((sx, sy), 1.6, fc="#1e88e5", ec="white", lw=2))
        ax.plot([sx, 142], [sy, 68], color="white", lw=1.8, ls="--")
    ax.add_patch(Rectangle((141, 67), 16, 21, color="#222"))
    ax.add_patch(Rectangle((142, 69), 14, 17, color="white"))
    ax.add_patch(Circle((149, 81), 2.5, color=color))
    ax.text(149, 73, word, ha="center", fontsize=10, fontweight="bold")
    ax.text(149, 64, "Digital twin", ha="center", fontsize=11, fontweight="bold")
    if target:
        ax.annotate("", xy=target, xytext=(140.5, 74),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.5, ls="--", connectionstyle="arc3,rad=0.25"))
        ax.add_patch(Circle(target, 3.5, fill=False, ec=color, lw=2.5))
    for i, (c, txt) in enumerate([("#1e88e5", "1  Sensors measure"), ("#222", "2  Twin decides"), (color, "3  Farmer acts")]):
        ax.add_patch(Circle((3.5, 86 - i * 3.4), 1, color=c))
        ax.text(5.5, 86 - i * 3.4, txt, va="center", fontsize=10, fontweight="bold")

    ax.add_patch(Rectangle((0, 0), 160, 12, color="#2a2a28"))
    for name, a, b, c in [("Start-up", 0, 30, "#7fb8e0"), ("Atrazine season", 30, 122, "orange"),
                          ("Late summer", 122, 183, "#e8c25a"), ("Off-season / winter", 183, 365, "#9aa5ad")]:
        x0, x1 = 4 + 152 * a / 365, 4 + 152 * b / 365
        ax.add_patch(Rectangle((x0, 4), x1 - x0, 2.2, color=c))
        ax.text((x0 + x1) / 2, 7.6, name, ha="center", fontsize=12, fontweight="bold", color="white")
    ax.plot([4 + 152 * d / 365] * 2, [3, 7], color="white", lw=3)

if len(sys.argv) > 1:
    for d in [10, 46, 56, 100, swap_day + 2, 250]:
        draw(d)
        fig.savefig(f"still_{d:03d}.png", dpi=80)
else:
    FuncAnimation(fig, draw, frames=365).save("dcbas_cycle.mp4", writer=FFMpegWriter(fps=24))
