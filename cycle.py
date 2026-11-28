"""NEPHRON over one year as an animation (design from the revised report, v2).

Tile water runs through the inlet box, the woodchip trench and the carbon box
(three biochar cartridges C1-C3, then a GAC polish) to the ditch. The bars show
how full each cartridge is. The twin swaps the lead cartridge when it is nearly
full (the others move up, fresh media goes in last) and holds water in the field
before storms. Off-season, the inlet box sends all water round the unit.

Run:  python cycle.py stills    six PNG frames
      python cycle.py           365-day video (needs ffmpeg)
"""
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
    for sd in swap_days:
        if sd <= d < sd + 5:
            return "Swap C1", "red", (CART_X[0], 42)
    if SPRAY <= d < SPRAY + 3:
        return "Spray day", "gold", (30, 60)
    for s in STORMS:
        if s - 2 <= d < s:
            return "Raise boards", "gold", (68, 59)
        if s <= d < s + 6:
            return "Hold water", "gold", (30, 47)
    if SEASON_OFF <= d < SEASON_OFF + 7:
        return "Bypass", "gold", (68, 59)
    return "All good", "green", None

CART_X = [113, 118.5, 124, 129.5]          # C1, C2, C3 (biochar), GAC polish
CART_NAMES = ["C1", "C2", "C3", "GAC"]
fill = np.zeros((366, 4))
swap_days = []
f = np.zeros(4)
for d in range(365):
    if 15 <= d < SEASON_OFF:
        load = atrazine(d) * flow(d)
        f += load * np.array([1 / 24, 1 / 90, 1 / 400, 1 / 2500])
    if 15 <= d < SEASON_OFF and f[0] >= 0.85 and (not swap_days or d - swap_days[-1] > 10):
        swap_days.append(d)                   # lead out, others move up, fresh media last
        f[:3] = [f[1], f[2], 0.0]
    f = np.clip(f, 0, 1)
    fill[d] = f
swap_day = swap_days[0] if swap_days else 999

TREAT = [(3, 41), (66, 41), (66, 36), (80, 36), (105, 41), (CART_X[0], 41)]
for k, x in enumerate(CART_X):
    TREAT += [(x, 33), (x, 50)] if k % 2 == 0 else [(x, 50), (x, 33)]
TREAT += [(134, 47), (142, 47), (142, 52), (152, 52)]
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
    box(62, 28, 12, 28, "Inlet box")
    box(79, 33, 26, 16, "Woodchip trench", "#c99a5c")
    box(110, 28, 24, 26, "Carbon box")
    box(138, 30, 8, 26, "Outlet")
    ax.add_patch(Rectangle((148, 49), 12, 4, color="#6fb6e8"))
    ax.text(153.5, 45, "Ditch", ha="center", fontsize=11, fontweight="bold", color="white")
    ax.add_patch(Rectangle((63.2, 51), 9.6, 3.2, color="green" if treating else "grey"))
    for x, w in [(61.5, 13), (109.5, 25), (137.5, 9)]:           # insulated, locked lids
        ax.add_patch(Rectangle((x, 55), w, 1.6, color="#3d4650"))

    for k, x in enumerate(CART_X):
        level = fill[d, k]
        w = 4.4 if k < 3 else 3.6
        ax.add_patch(Rectangle((x - w / 2, 31), w, 21, fc="#333" if k < 3 else "#15181c",
                               ec=plt.cm.RdYlGn_r(level), lw=3))
        ax.add_patch(Rectangle((x - w / 2, 31), w, 21 * level, color=plt.cm.RdYlGn_r(level), alpha=0.6))
        ax.text(x, 41.5, f"{level:.0%}", ha="center", fontsize=9, fontweight="bold", color="white")
        ax.text(x, 48, CART_NAMES[k], ha="center", fontsize=8, fontweight="bold", color="white")

    dots = (dots + 0.004 * flow(d)) % 1
    path = TREAT if treating else BYPASS
    for t in dots:
        x, y = point(path, t)
        clean = treating and x > 116
        dirty = atrazine(d) > 0.3 and not clean
        ax.add_patch(Circle((x, y), 0.8, color="orange" if dirty else "#4aa3e0" if clean else "#9fb7c9"))

    word, color, target = twin(d)
    for sx, sy in [(64, 45), (102, 46), (109, 43), (121.25, 53.8), (142, 40)]:
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
    for d in [10, 46, 56] + [sd + 2 for sd in swap_days] + [250]:
        draw(d)
        fig.savefig(f"still_{d:03d}.png", dpi=80)
else:
    FuncAnimation(fig, draw, frames=365).save("nephron_cycle.mp4", writer=FFMpegWriter(fps=24))
