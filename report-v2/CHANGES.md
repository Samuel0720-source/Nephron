# NEPHRON report: changes from v1 to v2

v1 = `NEPHRON REPORT.pdf` / `WEC Bioengineering.pdf` (submitted Nov 21, 2026; not modified).
v2 = `NEPHRON_Report_v2.pdf` (Nov 25, 2026).
Authors unchanged: Thomas Kim (team captain), Samuel Koo. Refs [1]–[25] keep their v1 numbers. New sources are [26]–[50].

## Headline numbers

| | v1 | v2 (P50, with P10–P90) |
|---|---|---|
| Unit removal, steady state | 96% | 97% (94–99%) |
| Unit removal, season average under storms | not given (twin: 83%) | 94% (85–97%) |
| River load reduction | 90.2% | 47% (34–65%) NEPHRON alone; 67% (55–77%) with buffer strips |
| Cost | CAD 313/ha/yr | about CAD 750/ha/yr (500–1,050 depending on cartridge swaps) |
| Cost per kg atrazine | not stated (implied 162,000) | about CAD 180,000/kg |

The 90% river goal is no longer claimed. v2 says it needs NEPHRON plus runoff controls and continued use reduction.

## Changes by review item

1. **96% vs 83%.** v2 separates steady-state removal from season-average removal. A new simulation, `nephron_v2_sim.py`, keeps Samuel's weather model unchanged, so design A reproduces 67%/83% exactly. It then adds one design change at a time (Fig. 4): design flow 7 L/s, more DWM storm holding, a third biochar cartridge, a 4 m³ polish, and a swap threshold of 90% instead of 85%. Season average rises from 83% to 94%.
   *Why:* removal falls because storm flow bypasses the unit and the media fill up, and only the season average shows that.
2. **River reduction.** v2 uses one model in Sec. III-E: R = C·[T·U + (1−T)·B]. The tile share T is 30–90%, most likely 47%. That comes from a Quebec 22.5 ha field where tile drains carried 47% of measured pesticide mass [41], bounded by [42] and [43]. Buffer strips handle runoff (B = 20–70%, [44], [45]). The twin README's 70% falls inside this range.
3. **Design flow.** v2 uses one design flow of 7 L/s. With a Quebec drainage coefficient of 10 mm/day [28], peak flow is 23 L/s, and the NRCS 15% criterion gives 3.5 L/s [26], [27]. 7 L/s is 30% of peak and treats 97% of season water in the model. The trench is 26 × 6 × 1.2 m (187 m³), HRT 4.1 h. Porosity is 0.55 (hardwood chips under soil, 0.54–0.55 [27]), not 0.7, which makes the trench larger than the reviewer's 72 m³ / 290 m³ examples. The 6.1 mm/day of v1 was a carbon-box rating, not a drainage coefficient. Trench cost is checked against US$77–200/m³ [11].
4. **Polish contact time.** At 14.2 L/s the v1 polish had only 2.3 min. v2 uses a 4 m³ polish with 9.5 min EBCT, backed by GAC removing 47% of atrazine at 5.62 min [37]. Biochar EBCT is 54 min (≥30 min recommended [35]; 300 s vs 45 s data [34]).
5. **Cold water.** Tile water is mostly below 10 °C from late autumn to early spring [31]. Woodchip nitrate removal has Q10 2.2–2.9 [30], and atrazine half-life doubles for every 10 °C drop [32]. The 25% woodchip figure was a lab result at 4 h [13], and field woodchips removed atrazine by sorption with breakthrough in under 6 days [29]. v2 uses 5–40% (central 15%) as a season average.
6. **Media capacity and DOC.** v2 adds Freundlich log K_F 2.25–3.15 for 450 °C wood/crop biochars [33] and DOC fouling ([35], [36]). The resulting capacity of 12–142 g/season is comparable to the ~87 g load, so it does limit media life. Swaps average 2.3 per season. A DEA breakthrough estimate (C1 at about 6–13 days, C2 at about 12–27 days of average flow) is added.
7. **Biochar end of life.** v2 corrects the claim that spent biochar is regenerated. Heat regeneration of biochar is lab-scale [38], and the life-cycle study assessed thermal reactivation only for activated carbon [39]. v2 sends spent biochar to energy-recovery incineration or landfill (royalty $34/t in 2025 [40]) and spent GAC to reactivation. Both are costed.
8. **Cost-effectiveness.** v2 adds $/kg atrazine, the nitrate co-benefit (CAD 19–194/kg N vs US$2.50–20 [11]), woodchip replacement every 10 years ([26], ≈41% of install per [11]), settlement, disposal, polish renewal and design fees. It compares against municipal PAC (28–87% removal [37]) without claiming NEPHRON is cheaper per kg.
9. **Uncertainty.** Table IV gives ranges with sources. Table V and Figs. 2, 4 and 5 give P10/P50/P90 over 200 seasons. The twin's result and method are now in the report itself (Sec. III-C and Appendix B), not only as a code citation.
10. **Bioaugmentation law.** Added CEPA s. 106(1) [48] and NSNR(Organisms) [47]: native organisms are not exempt. Indigenous status waives some ecological data but still needs a notification for each ecozone. Schedule 1 needs 120 days, Schedule 3 (field study) 90 days, and Schedule 4 (organism grown at its site of isolation) 30 days.
11. **Frost and lids.** Average frost depth is 1.4 m for Montréal [49]. The code minimum in clay is 1.2 m, and the Montréal freezing index is 607 degree-days [50]. v1's "below the frost line" was only partly true, so v2 says the top of the trench and the box tops are within the frost zone. Insulated, locked lids are added. NRCS says to keep equipment off bioreactors [26], so the trench moves from under the field to a grassed edge strip.
12. **Drawing.** New Fig. 3 shows a dimensioned plan and section: 1.2 m precast inlet/outlet boxes, a 26 × 6 × 1.2 m trench, a 10.5 × 2.2 × 2.6 m carbon box with 3 × (2.5 × 1.5 × 2.0 m) biochar cartridges and a 2.0 × 1.5 × 1.33 m GAC polish, and a 200 mm bypass (≈27 L/s full at 0.5%, our Manning calculation). Sizes changed from the portfolio model as follows: trench 10 m → 26 m, carbon box 7 m → 10.5 m, one cartridge added, and the polish doubled.
13. **Typos.** Fixed "desisopropylatrazineine" → "desisopropylatrazine" and "the digital twin manage" → "manages". I could not find "c an be" in the v1 text layer, and v2 does not contain it.

Other changes:
- The program cost is updated to CAD 12.5 M/yr (832 prescriptions × CAD 15,083).
- Appendix A is updated. Appendix B (model method) is new.
- The DWM pollution-swapping risk [46] and the fresh-woodchip DOC flush [30] are added.

## What I could not verify (stated as assumptions or left out)

- **NRCS national CPS 605 (2020) PDF.** The nrcs.usda.gov server timed out on every attempt. I cited the Ohio adoption of the standard [26] and the Illinois guidance [27], which I opened. Christianson [11] confirms the national 15%/3 h criteria.
- **Current Quebec drainage coefficient.** I could not open the CRAAQ guide (2005/2022). I used 10 mm/day from [28], which says it was "formerly" used in tight clays, and labelled it a conservative peak.
- **Atrazine-specific tile share.** The Chrétien et al. [41] abstract gives 53/47% for "measured mass losses" without splitting by compound. I could not open the full text. The Little Vermilion "96% via tiles" figure from a search snippet could not be confirmed, so it is not used.
- **Freundlich 1/n** for the 2.25–3.15 log K_F biochars, and **DOC capacity loss on wood biochar**: no data found. Assumed ranges 0.5–0.9 and 30–80%, marked "assumed" in Table IV.
- **DEA isotherms on wood biochar**: none found. The DEA breakthrough is an estimate that assumes 30–70% of atrazine's capacity. Adams & Watson [20] (DEA < atrazine on PAC) was not reopened, because the repository blocked the download. It was already cited in v1.
- **Biofilm factor in cold water** (1.0–2.3×) combines [15] and [32]. It is not a measured value.
- **Costs.** Carbon box, control boxes, media prices, crew visits, the $150/t disposal (only the $34/t royalty is verified), the GAC renewal interval and the design fee are engineering estimates. The USD→CAD conversion (~1.37) is assumed.
- **Municipal treatment cost per kg atrazine**: no verified figure found, so none is given.
- **Quebec tile-water temperatures**: no Quebec dataset found. The Lithuanian field data [31] and the New York rates in [11] are used as cold-climate analogues.
- **CEPA wording.** The regulations were read online. Schedule 4 is paraphrased, and quotes were limited. Any Quebec provincial authorization for releasing microbes was not checked.
- **Manning bypass capacity and polish EBCT scaling** (first-order from 47% at 5.62 min) are our own calculations or assumptions.

## Sources opened for v2

Every new reference [26]–[50] was opened, either as full text, the official page, or the publisher/Europe PMC abstract: [26], [27], [28], [29], [31], [33], [34], [35], [37], [39], [40], [43], [47], [48], [49], [50], and Christianson [11] were read in full or in the relevant section. [30], [32], [36], [38], [41], [42], [44], [45] and [46] were checked from their abstracts (Europe PMC or Crossref), and the report uses only what those abstracts state. Ross [18] was re-checked from its abstract (46% discharge reduction).

## Files (this folder)

- `NEPHRON_Report_v2.pdf`: the report.
- `nephron_v2_sim.py`: v2 Monte Carlo (`python nephron_v2_sim.py figures`).
- `build_v2_figures.py`: Figs. 2-5 from the results (`python build_v2_figures.py figures figures`).
- `build_v2_report.js`, `docx_to_pdf.ps1`: report source (docx-js) and Word PDF export.
- `figures/`: figures and simulation results (`v2_sim_results.json`, `v2_sim_raw.json`).
- The original model, `../dcbas_sim.py`, is unchanged; the v2 simulation copies its weather generator.
