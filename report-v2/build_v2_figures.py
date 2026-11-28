"""Figures for NEPHRON report v2 (print, light background).\n\nUsage: python build_v2_figures.py <sim_results_dir> <figure_out_dir>\n"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

SIM, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

BLUE, ORANGE = "#2a78d6", "#eb6834"      # categorical slots 1 and 2
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 10,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2})

res = json.load(open(os.path.join(SIM, "v2_sim_results.json")))["table"]
E = [k for k in res if k.startswith("E")][0]


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------------- Fig 2: alternatives
def fig_alternatives():
    rows = [("Woodchip bioreactor, 4 h [13]", 25, None),
            ("Woodchip bioreactor, 72 h [13]", 53, None),
            ("Woodchip + biochar, 72 h [13]", 90, None),
            ("NEPHRON v2, season average", *[v * 100 for v in res[E]["twin"]["removal"][1:2]],
             [v * 100 for v in res[E]["twin"]["removal"]]),
            ("NEPHRON v2, steady state", res[E]["twin"]["steady"][1] * 100,
             [v * 100 for v in res[E]["twin"]["steady"]])]
    fig, ax = plt.subplots(figsize=(3.4, 2.3), dpi=300)
    for i, (lab, val, rng) in enumerate(rows):
        color = BLUE if lab.startswith("NEPHRON") else "#b9b8b2"
        ax.barh(i, val, height=0.55, color=color, edgecolor="white", lw=0)
        if rng:
            ax.plot([rng[0], rng[2]], [i, i], color=INK, lw=1.2)
            ax.plot([rng[0]] * 2, [i - 0.12, i + 0.12], color=INK, lw=1.2)
            ax.plot([rng[2]] * 2, [i - 0.12, i + 0.12], color=INK, lw=1.2)
            ax.text(101, i, f"{val:.0f}%  ({rng[0]:.0f}–{rng[2]:.0f})", va="center", fontsize=8, color=INK)
        else:
            ax.text(val + 1.5, i, f"{val:.0f}%", va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Atrazine removed (%)", fontsize=8.5)
    ax.tick_params(axis="x", labelsize=8)
    clean(ax)
    fig.savefig(os.path.join(OUT, "fig2_alternatives.png"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------- Fig 4: design steps
def fig_design_steps():
    names = list(res.keys())
    short = ["A  v1 as submitted\n(original twin numbers)", "B  v1 sizes,\nliterature ranges",
             "C  + design flow\n7 L/s", "D  + more storm\nholding (DWM)",
             "E  v2 final: 3rd cartridge,\n4 m³ polish, swap at 90%"]
    fig, ax = plt.subplots(figsize=(6.8, 2.7), dpi=300)
    for i, n in enumerate(names):
        for j, (mode, col, lab) in enumerate((("fixed", ORANGE, "Fixed calendar (one swap)"),
                                              ("twin", BLUE, "Digital twin"))):
            p10, p50, p90 = [v * 100 for v in res[n][mode]["removal"]]
            y = i + (0.17 if mode == "fixed" else -0.17)
            ax.plot([p10, p90], [y, y], color=col, lw=2, solid_capstyle="round",
                    label=lab if i == 0 else None)
            ax.plot(p50, y, "o", ms=6, color=col, mec="white", mew=1.2)
            ax.text(p90 + 0.8, y, f"{p50:.0f}", va="center", fontsize=8, color=INK)
    ax.axvline(95, color=MUTED, ls=(0, (3, 3)), lw=1)
    ax.text(95.3, -0.55, "95% target", fontsize=8, color=INK2, va="center")
    ax.set_yticks(range(len(names)), short, fontsize=8)
    ax.set_xlim(45, 102)
    ax.set_xlabel("Season-average atrazine removed at one unit (%), P10–P90 line, P50 dot", fontsize=8.5)
    ax.tick_params(axis="x", labelsize=8)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=8, frameon=False)
    ax.set_ylim(len(names) - 0.5, -0.8)
    clean(ax)
    fig.savefig(os.path.join(OUT, "fig4_design_steps.png"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------- Fig 5: river
def fig_river():
    rows = [("NEPHRON only\n(tile water)", res[E]["twin"]["river_alone"]),
            ("NEPHRON + buffer\nstrips (runoff)", res[E]["twin"]["river_buffers"])]
    fig, ax = plt.subplots(figsize=(3.4, 1.7), dpi=300)
    for i, (lab, (p10, p50, p90)) in enumerate(rows):
        ax.plot([p10 * 100, p90 * 100], [i, i], color=BLUE, lw=2.2, solid_capstyle="round")
        ax.plot(p50 * 100, i, "o", ms=6.5, color=BLUE, mec="white", mew=1.2)
        ax.text(p50 * 100, i - 0.28, f"P50 {p50*100:.0f}%  (P10 {p10*100:.0f}, P90 {p90*100:.0f})",
                ha="center", fontsize=7.5, color=INK)
    ax.axvline(90, color=MUTED, ls=(0, (3, 3)), lw=1)
    ax.text(89, 1.45, "case goal 90%", fontsize=7.5, color=INK2, ha="right")
    ax.set_yticks([0, 1], [r[0] for r in rows], fontsize=8)
    ax.set_ylim(1.6, -0.6)
    ax.set_xlim(0, 100)
    ax.set_xlabel("River atrazine load reduction (%)", fontsize=8.5)
    ax.tick_params(axis="x", labelsize=8)
    clean(ax)
    fig.savefig(os.path.join(OUT, "fig5_river.png"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------- Fig 3: drawing
def dim(ax, x1, y1, x2, y2, text, off=0.0, vertical=False, fs=6.5):
    """Dimension line with end ticks and a label."""
    ax.annotate("", xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle="<->", lw=0.6, color=INK2, shrinkA=0, shrinkB=0))
    xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
    if vertical:
        ax.text(xm + off, ym, text, fontsize=fs, color=INK, va="center", ha="left", rotation=90)
    else:
        ax.text(xm, ym + off, text, fontsize=fs, color=INK, ha="center", va="bottom")


def fig_drawing():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 6.2), dpi=300,
                                   gridspec_kw=dict(height_ratios=[1.0, 1.0], hspace=0.12))
    chip, box, gac, soil = "#d9c3a0", "#9db8d9", "#6f6f6f", "#efe9dc"
    W = 2.0                                   # plan widths drawn x2
    tx = 2.5                                  # trench start (m)
    cx = tx + 26 + 2.5                        # carbon box start
    ox = cx + 10.5 + 3.0                      # outlet box start
    xmax = ox + 5
    # ---------------- PLAN
    ax = ax1
    ax.set_title("(a) Plan (lengths to scale, widths drawn ×2)", fontsize=9, loc="left", color=INK)
    yc = 3 * W                                # flow-line centre
    ax.plot([-4.3, 0], [yc, yc], color=INK, lw=1.4)
    ax.text(-4.3, yc - 0.9, "tile main\n(from 20 ha)", fontsize=6.5, color=INK2, va="top")
    ax.add_patch(Rectangle((0, yc - 0.6 * W), 1.2, 1.2 * W, fc="#cfcfcf", ec=INK, lw=0.8, zorder=3))
    ax.text(-1.6, yc + 0.6 * W + 0.4, "inlet box, 1.2 m\nprecast, stop logs,\nTreat/Bypass board",
            fontsize=6, ha="center", va="bottom")
    ax.add_patch(Rectangle((tx, 0), 26, 6 * W, fc=chip, ec=INK, lw=0.8, zorder=2))
    ax.text(tx + 13, yc, "woodchip trench, hardwood chips, 187 m³\nHRT 4.1 h at 7 L/s (porosity 0.55)",
            fontsize=7, ha="center", va="center", zorder=4)
    ax.plot([1.2, tx], [yc, yc], color=INK, lw=1.2)
    for xx, lab in ((tx + 0.5, "inlet header"), (tx + 25.5, "outlet header")):
        ax.plot([xx, xx], [0.5, 6 * W - 0.5], color=INK2, lw=0.8, ls=(0, (2, 1.5)), zorder=3)
        ax.text(xx + (0.4 if xx < tx + 5 else -0.4), 0.7, lab, fontsize=5.6, color=INK2, rotation=90,
                va="bottom", ha="left" if xx < tx + 5 else "right", zorder=4)
    dim(ax, tx, -1.0, tx + 26, -1.0, "26.0 m", off=0.2)
    dim(ax, tx + 2.6, 0, tx + 2.6, 6 * W, "6.0 m", off=0.2, vertical=True)
    ax.plot([tx + 26, cx], [yc, yc], color=INK, lw=1.2)
    ax.add_patch(Rectangle((cx, yc - 1.1 * W), 10.5, 2.2 * W, fc="#f4f4f2", ec=INK, lw=0.9, zorder=2))
    x = cx + 0.25
    for lab in ("C1", "C2", "C3"):
        ax.add_patch(Rectangle((x, yc - 0.75 * W), 2.5, 1.5 * W, fc=box, ec=INK, lw=0.6, zorder=3))
        ax.text(x + 1.25, yc, lab, fontsize=6.5, ha="center", va="center", zorder=4)
        x += 2.75
    ax.add_patch(Rectangle((x, yc - 0.75 * W), 2.0, 1.5 * W, fc=gac, ec=INK, lw=0.6, zorder=3))
    ax.text(x + 1.0, yc, "GAC", fontsize=6.5, ha="center", va="center", color="white", zorder=4)
    ax.text(cx + 5.25, -2.9,
            "carbon box: C1–C3 wood biochar, 2.5 × 1.5 × 2.0 m (7.5 m³) each;\n"
            "GAC polish 2.0 × 1.5 × 1.33 m (4 m³)", fontsize=6, ha="center", va="top")
    dim(ax, cx, yc - 1.1 * W - 1.0, cx + 10.5, yc - 1.1 * W - 1.0, "10.5 m", off=0.2)
    dim(ax, cx + 10.5 + 0.7, yc - 1.1 * W, cx + 10.5 + 0.7, yc + 1.1 * W, "2.2 m", off=0.2, vertical=True)
    ax.plot([cx + 10.5, ox], [yc, yc], color=INK, lw=1.2)
    ax.add_patch(Rectangle((ox, yc - 0.6 * W), 1.2, 1.2 * W, fc="#cfcfcf", ec=INK, lw=0.8, zorder=3))
    ax.text(ox + 0.6, yc + 0.6 * W + 0.4, "outlet box, 1.2 m\nprecast, stop logs", fontsize=6,
            ha="center", va="bottom")
    ax.annotate("", xy=(ox + 3.6, yc), xytext=(ox + 1.2, yc),
                arrowprops=dict(arrowstyle="-|>", lw=1.0, color=BLUE))
    ax.text(ox + 3.7, yc, "ditch", fontsize=6.5, va="center")
    by = -2.6
    ax.plot([0.6, 0.6, ox + 0.6, ox + 0.6], [yc - 0.6 * W, by, by, yc - 0.6 * W], color=ORANGE, lw=1.3)
    ax.text(tx + 8, by - 0.3, "200 mm bypass: flow above 7 L/s, and the carbon box"
            " off-season", fontsize=6.3, ha="center", va="top", color=INK)
    ax.set_xlim(-4.5, xmax)
    ax.set_ylim(-4.6, 6 * W + 3.6)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---------------- SECTION
    ax = ax2
    ax.set_title("(b) Section along the flow path (depths drawn ×3)", fontsize=9, loc="left", color=INK)
    V = 3.0

    def y(d):
        return -d * V

    ax.add_patch(Rectangle((-4.5, y(3.0)), xmax + 4.5, 3.0 * V, fc=soil, ec="none", zorder=0))
    ax.plot([-4.5, xmax], [0, 0], color=INK, lw=1.0)
    ax.text(-4.4, 0.25, "ground", fontsize=6.5)
    ax.plot([-4.5, xmax], [y(1.4)] * 2, color=BLUE, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.text(tx + 13, y(1.72), "dashed blue line: average frost depth, Montréal, 1.4 m [49]", fontsize=6.2, color=BLUE, va="top", ha="center")
    # bypass drawn first so the boxes hide it (it runs beside them in plan)
    ax.plot([1.2, ox], [y(2.1)] * 2, color=ORANGE, lw=1.1, ls=(0, (5, 2)), zorder=1)
    ax.text(tx + 13, y(2.1) - 0.25, "200 mm bypass (beside the units in plan): ≈27 L/s flowing full "
            "at 0.5 % slope", fontsize=6.2, ha="center", va="top", color=INK)
    ax.add_patch(Rectangle((0, y(2.3)), 1.2, 2.3 * V, fc="#cfcfcf", ec=INK, lw=0.8, zorder=3))
    ax.add_patch(Rectangle((tx, y(1.65)), 26, 1.2 * V, fc=chip, ec=INK, lw=0.8, zorder=3))
    ax.text(tx + 12, y(1.05), "woodchips in a liner; 0.45 m soil cap,\ngrassed and kept out of traffic [26]", fontsize=6.4, ha="center", va="center", zorder=4)
    dim(ax, tx + 24.6, y(0.45), tx + 24.6, y(1.65), "1.2 m", off=0.15, vertical=True)
    dim(ax, tx + 1.2, 0, tx + 1.2, y(0.45), "0.45 m", off=0.15, vertical=True, fs=5.8)
    for xs in ((-4.3, 0), (1.2, tx), (tx + 26, cx)):
        ax.plot(xs, [y(1.6)] * 2, color=INK, lw=1.2, zorder=2)
    ax.add_patch(Rectangle((cx, y(2.6)), 10.5, 2.6 * V, fc="#f4f4f2", ec=INK, lw=0.9, zorder=3))
    ax.plot([cx + 0.1, cx + 10.4], [y(0.2)] * 2, color=BLUE, lw=0.9, zorder=5)
    ax.text(cx + 10.3, y(0.2) - 0.1, "water level", fontsize=5.4, color=BLUE, ha="right", va="top",
            zorder=5)
    x = cx + 0.25
    for lab in ("C1", "C2", "C3"):
        ax.add_patch(Rectangle((x, y(2.4)), 2.5, 2.0 * V, fc=box, ec=INK, lw=0.6, zorder=4))
        ax.text(x + 1.25, y(1.4), lab, fontsize=6.5, ha="center", va="center", zorder=5)
        x += 2.75
    ax.add_patch(Rectangle((x, y(2.4)), 2.0, 1.33 * V, fc=gac, ec=INK, lw=0.6, zorder=4))
    ax.text(x + 1.0, y(1.75), "GAC", fontsize=6.5, ha="center", va="center", color="white", zorder=5)
    dim(ax, cx + 10.5 + 0.7, 0, cx + 10.5 + 0.7, y(2.6), "2.6 m", off=0.2, vertical=True)
    for x0, w in ((0, 1.2), (cx, 10.5), (ox, 1.2)):
        ax.add_patch(Rectangle((x0 - 0.15, -0.02), w + 0.3, 0.3, fc="#fff3b0", ec=INK, lw=0.6, zorder=6))
    ax.text(cx + 5.25, 0.5, "insulated, locked lids on all three boxes", fontsize=6.3, ha="center")
    ax.add_patch(Rectangle((ox, y(2.3)), 1.2, 2.3 * V, fc="#cfcfcf", ec=INK, lw=0.8, zorder=3))
    ax.plot([cx + 10.5, ox], [y(1.9)] * 2, color=INK, lw=1.2, zorder=2)
    ax.plot([ox + 1.2, ox + 3.6], [y(1.9)] * 2, color=INK, lw=1.2, zorder=2)
    ax.set_xlim(-4.5, xmax)
    ax.set_ylim(y(3.0), 1.3)
    ax.axis("off")
    fig.savefig(os.path.join(OUT, "fig3_drawing.png"), bbox_inches="tight")
    plt.close(fig)


fig_alternatives()
fig_design_steps()
fig_river()
fig_drawing()
print("figures written to", OUT)
