"""NEPHRON v2 season simulation (extends dcbas_sim.py by S. Koo).

What this adds to the original twin model:
  * one design flow Q_D for the whole unit (trench, carbon box, polish),
  * a capacity for the biochar estimated from Freundlich data, cut by
    dissolved-organic-carbon (DOC) competition and stretched by biofilm,
  * a polish whose removal depends on its contact time (EBCT),
  * a storm-holding volume limited by how much water the soil can store,
  * uncertainty: every uncertain number is drawn from a range, and the
    results are reported as P10 / P50 / P90 over 200 storm seasons.

The weather generator is copied unchanged from dcbas_sim.py so that the
"v1" case reproduces the original 67 % / 83 % result exactly.

Run:  python nephron_v2_sim.py figures   (prints tables, writes the JSON results)
      python build_v2_figures.py figures figures   (redraws Figs. 2-5)
"""
import json
import os
import sys

import numpy as np

DAYS = 183
SEEDS = range(200)


# ---------------------------------------------------------------- weather
def weather(seed):
    """Same rain -> drain-flow -> atrazine model as dcbas_sim.py (unchanged)."""
    rng = np.random.default_rng(seed)
    rain = np.where(rng.random(DAYS) < 0.18, rng.gamma(2, 9, DAYS), 0)
    flow, soil = [], 0
    for r in rain:
        soil = soil * 0.75 + r * 0.35
        flow.append(0.4 + soil * 0.45)          # L/s from a 20 ha field
    flow = np.array(flow)
    days = np.arange(DAYS)
    spike = np.where(days >= 45, 25 * np.exp(-(days - 45) / 18), 0)
    conc = 0.3 + spike * np.clip(flow / 4, 0, 1.5)   # ug/L atrazine
    return rain, flow, conc


# ---------------------------------------------------------------- designs
# Each design is a dict of physical sizes. "v1" reproduces the original twin.
DESIGNS = {
    "A. v1 as submitted (original twin numbers)": dict(
        q_design=3.5, biochar_m3=15.0, polish_m3=2.0, hold_rate=1.5,
        hold_frac=0.45, store_m3=None, max_swaps=1, legacy=True),
    "B. v1 sizes, v2 literature ranges": dict(
        q_design=3.5, biochar_m3=15.0, polish_m3=2.0, hold_rate=1.5,
        hold_frac=0.45, store_m3=3000, max_swaps=3, legacy=False),
    "C. + design flow 7 L/s": dict(
        q_design=7.0, biochar_m3=15.0, polish_m3=2.0, hold_rate=1.5,
        hold_frac=0.45, store_m3=3000, max_swaps=3, legacy=False),
    "D. + more storm holding (DWM)": dict(
        q_design=7.0, biochar_m3=15.0, polish_m3=2.0, hold_rate=3.0,
        hold_frac=0.6, store_m3=3000, max_swaps=3, legacy=False),
    "E. v2 final: + 3rd cartridge, 4 m3 polish, swap at 90 %": dict(
        q_design=7.0, biochar_m3=22.5, polish_m3=4.0, hold_rate=3.0,
        hold_frac=0.6, store_m3=3000, max_swaps=5, swap_at=0.90, legacy=False),
}

BIOCHAR_BULK_T_PER_M3 = 0.30     # v1 report: 4.5 t in 15 m3
CARTRIDGE_M3 = 7.5               # one biochar cartridge


# ---------------------------------------------------------------- parameters
def nominal():
    """Central values (used for the 'nominal' line and the steady-state number)."""
    return dict(wood=0.15, carbon=0.90, polish_ref=0.47, polish_ebct_ref=5.62,
                logKf=2.70, inv_n=0.70, f_doc=0.55, f_bio=1.6,
                tile_share=0.47, buffer=0.45)


def draw(rng):
    """One random set of the uncertain parameters (ranges in CHANGES.md / Table IV)."""
    return dict(
        wood=rng.uniform(0.05, 0.40),        # woodchip atrazine removal, season mean
        carbon=rng.uniform(0.80, 0.95),      # fresh biochar pair removal
        polish_ref=rng.uniform(0.30, 0.65),  # GAC removal at 5.62 min EBCT
        polish_ebct_ref=5.62,
        logKf=rng.uniform(2.25, 3.15),       # Freundlich log Kf, wood biochars
        inv_n=rng.uniform(0.5, 0.9),         # Freundlich 1/n (assumed range)
        f_doc=rng.uniform(0.3, 0.8),         # capacity kept with DOC competition
        f_bio=rng.uniform(1.0, 2.3),         # biofilm life extension
        tile_share=rng.triangular(0.3, 0.47, 0.9),
        buffer=rng.uniform(0.2, 0.7),        # buffer-strip removal of runoff load
    )


def biochar_capacity_g(design, p, c_eq_ugl=2.0):
    """Grams of atrazine the biochar can hold in one season.

    Freundlich: q (mg/kg) = Kf * C(mg/L)^(1/n), at the flow-weighted mean
    inflow concentration (about 2 ug/L in this model).
    """
    q_mg_per_kg = 10 ** p["logKf"] * (c_eq_ugl / 1000) ** p["inv_n"]
    mass_kg = design["biochar_m3"] * BIOCHAR_BULK_T_PER_M3 * 1000
    return q_mg_per_kg * mass_kg / 1000 * p["f_doc"] * p["f_bio"]


def polish_removal(design, p):
    """GAC polish removal scaled by contact time (first-order in EBCT)."""
    ebct_min = design["polish_m3"] / (design["q_design"] / 1000) / 60
    return 1 - (1 - p["polish_ref"]) ** (ebct_min / p["polish_ebct_ref"])


# ---------------------------------------------------------------- one season
def season(seed, design, p, twin=True):
    """Return season-average removal and bookkeeping for one storm season."""
    rain, flow, conc = weather(seed)
    q_d = design["q_design"]
    if design["legacy"]:
        cap = 50.0                              # original twin's assumption
        wood, carbon, polish_max = 0.25, 0.90, 0.50
    else:
        cap = biochar_capacity_g(design, p)
        wood, carbon, polish_max = p["wood"], p["carbon"], polish_removal(design, p)
    cap_lead = cap * CARTRIDGE_M3 / design["biochar_m3"]
    store_cap = (design["store_m3"] / 86.4) if design["store_m3"] else np.inf  # L/s-days
    stored = used = 0.0
    swaps = 0
    tot_in = tot_out = bypass_m3 = 0.0
    for d in range(DAYS):
        q = flow[d]
        if twin:                                     # storm holding with boards raised
            storm_coming = d < DAYS - 1 and rain[d + 1] > 15
            if storm_coming or q > q_d:
                keep = min(q * design["hold_frac"], design["hold_rate"], store_cap - stored)
                keep = max(keep, 0.0)
                q -= keep
                stored += keep
            elif stored > 0 and q < 0.7 * q_d:       # release slowly after the storm
                give = min(stored, 0.7 * q_d - q)
                q += give
                stored -= give
        treated = min(q, q_d)
        bypass = q - treated
        full = min(used / cap, 1)
        r_c = carbon * (1 - full ** 3)
        if design["legacy"]:
            r_p = polish_max * (1 - full)
        else:
            r_p = polish_max
        removal = 1 - (1 - wood) * (1 - r_c) * (1 - r_p)
        grams = conc[d] * treated * 86400 / 1e6
        used += grams * (1 - wood) * r_c
        if twin:
            swap_now = removal < design.get("swap_at", 0.85) and swaps < design["max_swaps"]
        else:
            swap_now = d == 140 and swaps < 1
        if swap_now:
            used = 0.0 if design["legacy"] else max(0.0, used - cap_lead)
            swaps += 1
        tot_in += conc[d] * q * 86400 / 1e6
        tot_out += grams * (1 - removal) + conc[d] * bypass * 86400 / 1e6
        bypass_m3 += bypass * 86.4
    # water still held in the field at season end drains later through the unit
    return dict(removal=1 - tot_out / tot_in, swaps=swaps, bypass_m3=bypass_m3,
                load_g=tot_in, cap_g=cap)


def steady_state(design, p):
    """Removal with fresh media and no bypass (the old '96 %' type number)."""
    if design["legacy"]:
        return 1 - (1 - 0.25) * (1 - 0.90) * (1 - 0.50)
    return 1 - (1 - p["wood"]) * (1 - p["carbon"]) * (1 - polish_removal(design, p))


def river(unit, p, coverage=0.95, with_buffers=False):
    """River load reduction: one model for the whole report.

    R = coverage * [T * U + (1 - T) * B]   (B = 0 if no buffer-strip upgrade)
    """
    t = p["tile_share"]
    b = p["buffer"] if with_buffers else 0.0
    return coverage * (t * unit + (1 - t) * b)


# ---------------------------------------------------------------- Monte Carlo
def run_design(name, design):
    out = {"fixed": [], "twin": []}
    for s in SEEDS:
        p = draw(np.random.default_rng(10_000 + s))
        for mode in ("fixed", "twin"):
            r = season(s, design, p, twin=(mode == "twin"))
            r["steady"] = steady_state(design, p)
            r["river_alone"] = river(r["removal"], p)
            r["river_buffers"] = river(r["removal"], p, with_buffers=True)
            out[mode].append(r)
    return out


def pct(values):
    return [float(np.percentile(values, q)) for q in (10, 50, 90)]


def summarise(results):
    table = {}
    for name, res in results.items():
        row = {}
        for mode, runs in res.items():
            row[mode] = {k: pct([r[k] for r in runs])
                         for k in ("removal", "steady", "river_alone", "river_buffers",
                                   "swaps", "bypass_m3", "cap_g", "load_g")}
            row[mode]["median_simple"] = float(np.median([r["removal"] for r in runs]))
        table[name] = row
    return table


def ebct_table():
    rows = {}
    for name, d in DESIGNS.items():
        q = d["q_design"] / 1000
        rows[name] = dict(q_lps=d["q_design"],
                          biochar_ebct_min=d["biochar_m3"] / q / 60,
                          polish_ebct_min=d["polish_m3"] / q / 60)
    return rows


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    results = {name: run_design(name, d) for name, d in DESIGNS.items()}
    table = summarise(results)
    # nominal (central-value) steady state for the headline
    nominal_steady = {n: steady_state(d, nominal()) for n, d in DESIGNS.items()}
    summary = dict(table=table, ebct=ebct_table(), nominal_steady=nominal_steady)
    with open(os.path.join(outdir, "v2_sim_results.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    # raw per-season removals for figures
    raw = {n: {m: [r["removal"] for r in res[m]] for m in res} for n, res in results.items()}
    raw_river = {n: {m: [r["river_alone"] for r in res[m]] for m in res} for n, res in results.items()}
    raw_riverb = {n: {m: [r["river_buffers"] for r in res[m]] for m in res} for n, res in results.items()}
    with open(os.path.join(outdir, "v2_sim_raw.json"), "w") as fh:
        json.dump(dict(unit=raw, river=raw_river, river_buffers=raw_riverb), fh)
    for name, row in table.items():
        print(f"\n== {name}")
        for mode in ("fixed", "twin"):
            r = row[mode]
            f = lambda v: "/".join(f"{x*100:.0f}" for x in v)
            print(f"  {mode:5s} unit P10/50/90 {f(r['removal'])} %  steady {f(r['steady'])} %"
                  f"  river alone {f(r['river_alone'])} %  +buffers {f(r['river_buffers'])} %"
                  f"  swaps {r['swaps'][1]:.0f}  bypass {r['bypass_m3'][1]:.0f} m3"
                  f"  cap {r['cap_g'][1]:.0f} g  load {r['load_g'][1]:.0f} g"
                  f"  (median {row[mode]['median_simple']*100:.1f})")
    print("\nEBCT:", json.dumps(ebct_table(), indent=1))
    print("nominal steady:", {k: round(v, 3) for k, v in nominal_steady.items()})


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v2_out")
