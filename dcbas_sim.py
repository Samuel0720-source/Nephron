import numpy as np
import matplotlib.pyplot as plt

CAPACITY = 3.5
WOOD, CARBON, POLISH = 0.25, 0.90, 0.50
CARBON_HOLDS = 50
RIVER_FLOW = 1217e6 / 31.536e6
RIVER_CONC = 0.6
TILE_SHARE = 0.70
COVERAGE = 0.95

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
    return rain, flow, conc

def season(seed, twin):
    rain, flow, conc = weather(seed)
    stored = 0
    used = 0
    swapped = False
    total_in = 0
    total_out = 0
    for d in range(183):
        q = flow[d]
        if twin:
            storm_coming = d < 182 and rain[d + 1] > 15
            if storm_coming or q > CAPACITY:
                keep = min(q * 0.45, 1.5)
                q -= keep
                stored += keep
            elif stored > 0 and q < 2.5:
                give = min(stored, 2.5 - q)
                q += give
                stored -= give
        treated = min(q, CAPACITY)
        bypass = q - treated
        full = min(used / CARBON_HOLDS, 1)
        carbon = CARBON * (1 - full ** 3)
        removal = 1 - (1 - WOOD) * (1 - carbon) * (1 - POLISH * (1 - full))
        grams = conc[d] * treated * 86400 / 1e6
        used += grams * (1 - WOOD) * carbon
        swap_now = (twin and removal < 0.85) or (not twin and d == 140)
        if swap_now and not swapped:
            used = 0
            swapped = True
        total_in += conc[d] * q * 86400 / 1e6
        total_out += grams * (1 - removal) + conc[d] * bypass * 86400 / 1e6
    return 1 - total_out / total_in

no_twin = np.median([season(s, False) for s in range(200)])
with_twin = np.median([season(s, True) for s in range(200)])
kg = RIVER_CONC * RIVER_FLOW * 86400 / 1e6

print(f"River: {RIVER_FLOW:.1f} m3/s at {RIVER_CONC} ug/L = {kg:.1f} kg atrazine per day")
print(f"No sensors: unit removes {no_twin:.0%} -> river drops {no_twin * COVERAGE * TILE_SHARE:.0%}")
print(f"With twin:  unit removes {with_twin:.0%} -> river drops {with_twin * COVERAGE * TILE_SHARE:.0%}")

plt.bar(["No sensors", "With twin"], [no_twin * 100, with_twin * 100], color=["orange", "#2a78d6"])
plt.axhline(95, ls=":", color="red", label="design target 95%")
plt.ylabel("atrazine removed at one unit (%)")
plt.title("What the digital twin adds (200 seasons)")
plt.legend()
plt.savefig("twin_benefit.png", dpi=200)
