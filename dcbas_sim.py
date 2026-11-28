import numpy as np
import matplotlib.pyplot as plt

RIVER_FLOW = 1217e6 / 31.536e6
RIVER_CONC = 0.6
COVERAGE = 0.95
SURF_K = 0.28

V1 = dict(wood=0.25, cap=3.5, holds=50, store=0, swap_at=0.85, inlet=0, buffer=0)
V2 = dict(wood=0.40, cap=5.0, holds=100, store=60, swap_at=0.93, inlet=0.9, buffer=0.5)


def weather(seed):
    rng = np.random.default_rng(seed)
    rain = np.where(rng.random(183) < 0.18, rng.gamma(2, 9, 183), 0)
    flow = []
    soil = 0
    for r in rain:
        soil = soil * 0.75 + r * 0.35
        flow.append(0.4 + soil * 0.45)
    flow = np.array(flow)
    days = np.arange(183)
    spike = np.where(days >= 45, 25 * np.exp(-(days - 45) / 18), 0)
    conc = 0.3 + spike * np.clip(flow / 4, 0, 1.5)
    surface = np.clip(rain - 12, 0, None) * SURF_K
    return rain, flow, conc, surface


def grams(conc, q):
    return conc * q * 86400 / 1e6


def season(seed, twin, wood, cap, holds, store, swap_at, inlet, buffer):
    rain, flow, conc, surface = weather(seed)
    total_in = grams(conc, flow).sum() + grams(conc * 2, surface).sum()
    lost = dict(runoff=0, bypass=0, leak=0, stored=0)
    water = mass = used = 0
    swapped = False
    for d in range(183):
        runoff = grams(conc[d] * 2, surface[d])
        lost["runoff"] += runoff * (1 - inlet) * (1 - buffer)
        q = flow[d] + surface[d] * inlet
        m = grams(conc[d], flow[d]) + runoff * inlet

        if twin and not store:
            if (d < 182 and rain[d + 1] > 15) or q > cap:
                keep = min(q * 0.45, 1.5)
                water += keep
                mass += m * keep / q
                m -= m * keep / q
                q -= keep
            elif water > 0 and q < 2.5:
                give = min(water, 2.5 - q)
                m += mass * give / water
                mass -= mass * give / water
                water -= give
                q += give
        if twin and store:
            if (d < 182 and rain[d + 1] > 15) or q > cap:
                keep = min(max(q - cap * 0.6, 0), store - water)
                water += keep
                mass += m * keep / q
                m -= m * keep / q
                q -= keep
            elif water > 0 and q < cap * 0.9:
                give = min(water, cap * 0.9 - q)
                m += mass * give / water
                mass -= mass * give / water
                water -= give
                q += give

        treated = min(q, cap)
        full = min(used / holds, 1)
        contact = (holds / cap) / (50 / 3.5)
        carbon = (1 - 0.1 ** contact) * (1 - full ** 3)
        removal = 1 - (1 - wood) * (1 - carbon) * (1 - 0.5 * (1 - full))
        g = m * treated / q
        lost["bypass"] += m - g
        lost["leak"] += g * (1 - removal)
        used += g * (1 - wood) * carbon
        if twin and removal < swap_at and (store or not swapped):
            used = 0
            swapped = True
        if not twin and d == 140:
            used = 0
    lost["stored"] = mass
    return {k: v / total_in for k, v in lost.items()}


def median_run(twin, design):
    runs = [season(s, twin, **design) for s in range(200)]
    lost = {k: np.median([r[k] for r in runs]) for k in runs[0]}
    field = 1 - np.median([sum(r.values()) for r in runs])
    return field, lost


kg = RIVER_CONC * RIVER_FLOW * 86400 / 1e6
print(f"River: {RIVER_FLOW:.1f} m3/s at {RIVER_CONC} ug/L = {kg:.1f} kg atrazine per day")
print(f"Nephron on {COVERAGE:.0%} of fields, 200 random seasons each\n")

steps = [
    ("Nephron 1.0\nno sensors", False, V1),
    ("+ digital\ntwin", True, V1),
    ("+ biochar in\nwoodchips", True, dict(V1, wood=0.40)),
    ("+ 2x carbon\nbox", True, dict(V1, wood=0.40, cap=5.0, holds=100)),
    ("+ twin holds\nwater in field", True, dict(V2, inlet=0, buffer=0)),
    ("+ surface\ninlet", True, dict(V2, buffer=0)),
    ("+ grass\nbuffer strip", True, V2),
]
drops = []
for name, twin, design in steps:
    field, lost = median_run(twin, design)
    river = field * COVERAGE
    drops.append(river * 100)
    print(f"{name.replace(chr(10), ' '):28s} river drops {river:.1%}  ({RIVER_CONC} -> {RIVER_CONC * (1 - river):.3f} ug/L)")
    print("    lost to: " + ", ".join(f"{k} {max(v, 0):.1%}" for k, v in lost.items()))

plt.figure(figsize=(11, 5))
bars = plt.bar([s[0] for s in steps], drops, color=["orange", "#2a78d6"] + ["#1b9e77"] * 5)
plt.bar_label(bars, fmt="%.0f%%")
plt.axhline(90, ls=":", color="red", label="case goal 90%")
plt.ylabel("atrazine drop in the river (%)")
plt.ylim(0, 100)
plt.title("Nephron 1.0 to 2.0, one upgrade at a time (200 seasons each)")
plt.legend()
plt.tight_layout()
plt.savefig("nephron2_ladder.png", dpi=200)
