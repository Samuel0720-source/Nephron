// Builds NEPHRON_Report_v2.docx (IEEE-style, two columns, Times New Roman 12 pt).
// Usage: node build_v2_report.js <figures_dir> <out.docx>
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  AlignmentType, WidthType, BorderStyle, ShadingType, SectionType, PageBreak,
  Footer, PageNumber, ExternalHyperlink,
} = require("docx");

const FIG = process.argv[2];
const OUT = process.argv[3];
const FONT = "Times New Roman";
const COL = 4860;           // one column width (DXA) with 0.75 in margins and 0.25 in gap
const FULL = 10080;         // full text width (DXA)

// ---------------------------------------------------------------- helpers
// Inline markup: _italic_ and **bold**.
function runs(text, opts = {}) {
  const out = [];
  const re = /(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|~[^~]+~|_[^_]+_)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...opts }));
    const t = m[0];
    if (t.startsWith("~")) out.push(new TextRun({ text: t.slice(1, -1), subScript: true, font: FONT, ...opts }));
    else if (t.startsWith("***")) out.push(new TextRun({ text: t.slice(3, -3), bold: true, italics: true, font: FONT, ...opts }));
    else if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, ...opts }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, ...opts }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...opts }));
  return out;
}
const P = (text, o = {}) => new Paragraph({
  children: runs(text, o.run || {}), alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after ?? 80, line: 240 }, indent: o.indent ?? { firstLine: 240 }, keepNext: o.keepNext,
});
const PN = (text, o = {}) => P(text, { ...o, indent: { firstLine: 0 } });
const H1 = (num, title) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 }, keepNext: true,
  children: [new TextRun({ text: `${num}. `, font: FONT, size: 24 }),
             new TextRun({ text: title, font: FONT, size: 24, smallCaps: true })],
});
const H2 = (text) => new Paragraph({
  spacing: { before: 120, after: 60 }, keepNext: true,
  children: [new TextRun({ text, italics: true, font: FONT, size: 24 })],
});
const ITEM = (label, text) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 60 },
  indent: { left: 360, hanging: 360 },
  children: [new TextRun({ text: label + "\t", font: FONT, size: 24 }), ...runs(text, { size: 24 })],
  tabStops: [{ type: "left", position: 360 }],
});
const CAPTION = (text) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED, spacing: { before: 60, after: 160 },
  children: runs(text, { size: 20 }),
});
const TABLE_TITLE = (num, title) => [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 0 }, keepNext: true,
    children: [new TextRun({ text: `TABLE ${num}`, font: FONT, size: 20 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, keepNext: true,
    children: [new TextRun({ text: title, font: FONT, size: 20, smallCaps: true })] }),
];
function img(file, widthPx) {
  const buf = fs.readFileSync(path.join(FIG, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);   // PNG header
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 120, after: 0 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: buf,
      transformation: { width: widthPx, height: Math.round(widthPx * h / w) } })],
  });
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, header, rows, size = 18) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: head ? { fill: "E8E8E8", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: String(t).split("|").map((line) => new Paragraph({
      alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: runs(line, { size, bold: head || undefined }),
    })),
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, i, true)) }),
           ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((t, i) => cell(t, i, false)) }))],
  });
}
const space = () => new Paragraph({ spacing: { after: 60 }, children: [] });

// ---------------------------------------------------------------- page setup
const page = { size: { width: 12240, height: 15840 },
               margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } };
const twoCol = { count: 2, space: 360, equalWidth: true };
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] });

// ================================================================ CONTENT
// ---------------- title page
const title = [
  new Paragraph({ spacing: { before: 600 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: "NEPHRON: A Digital-Twin-Managed Bioreactor for Atrazine in Tile Drainage", font: FONT, size: 40 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Nitrate-Eliminating Pesticide-Hydrolyzing Reactor for On-farm Networks", font: FONT, size: 22, italics: true })] }),
  ...["Bio-Engineering Competition", "Team NEPHRON", "Thomas Kim (team captain), Samuel Koo",
      "Waterloo Engineering Competition, November 21, 2026", "Revised version 2, November 25, 2026"].map((t) =>
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
      children: [new TextRun({ text: t, font: FONT, size: 24 })] })),
  new Paragraph({ spacing: { after: 240 }, children: [] }),
];
const front = [
  PN("***Abstract—***Atrazine and its transformation product desethylatrazine (DEA) reach the Châteauguay River, a drinking-water source in Montérégie, Quebec, in pulses after spring spraying. We propose NEPHRON, a buried, gravity-fed unit at the tile-drain outlet: a woodchip denitrifying trench, three wood-biochar cartridges and a granular activated carbon (GAC) polish. A digital twin, fed by low-cost sensors and grab samples, tells the farmer when to hold storm water in the field and when to swap the lead cartridge. This revised version sizes every stage for one design flow (7 L/s from a 20 ha field), replaces single values with literature ranges, and re-runs the twin over 200 storm seasons. With fresh media and no bypass the unit removes 97% of the atrazine that reaches it (P10–P90: 94–99%); averaged over a stormy season it removes 94% (85–97%). Tile drains carry only part of the river’s atrazine (about half in a Quebec field study), so NEPHRON alone would cut the river load by 47% (34–65%), and by 67% (55–77%) with buffer strips on surface runoff. Meeting the 90% case goal therefore needs NEPHRON together with runoff controls and continued use reduction. The unit costs about CAD 750 per hectare per year and also removes nitrate.", { after: 160 }),
  PN("***Index Terms—***atrazine, biochar, bioremediation, digital twin, drinking water, tile drainage.", { after: 160 }),
  PN("***Key Results—***Unit removal of 97% at steady state and 94% averaged over a stormy season (P50; P10–P90 85–97%), up from 83% for the v1 design; river load reduction of 47% from NEPHRON alone and 67% with buffer strips; one design flow of 7 L/s with 4.1 h in the woodchips, 54 min in the biochar and 9.5 min in the polish; about CAD 750 per hectare per year (CAD 500–1,050 depending on how often cartridges are swapped).", { after: 160 }),
  PN("***Abbreviations—***AAFC, Agriculture and Agri-Food Canada; CEPA, Canadian Environmental Protection Act, 1999; DEA, desethylatrazine; DIA, desisopropylatrazine; DOC, dissolved organic carbon; DSL, Domestic Substances List; DWM, drainage water management; EBCT, empty-bed contact time; GAC, granular activated carbon; HRT, hydraulic retention time; MAPAQ, Quebec Ministry of Agriculture, Fisheries and Food; NRCS, USDA Natural Resources Conservation Service; P10/P50/P90, 10th, 50th and 90th percentiles over 200 simulated seasons; SCABRIC, Châteauguay River watershed organization; UV254, ultraviolet absorbance at 254 nm.", { after: 160 }),
];

// ---------------- I. Introduction
const intro = [
  H1("I", "Introduction"),
  H2("A. The Problem in the Châteauguay Watershed"),
  P("Pesticides were measured in the Châteauguay River, in an area dominated by corn and soybean growing in Montérégie, which produces 62% of Quebec’s grain corn. Biweekly measurements at a drinking-water treatment plant over 838 days (2021–2023) showed that pesticide concentrations peaked in June and July, that DEA was more concentrated than atrazine, and that conventional treatment did not significantly reduce total pesticides including transformation products [1]. In western Montérégie, transformation products made up on average 51% of total pesticide concentrations, and DEA was detected at all sites [2]."),
  H2("B. Why Atrazine"),
  P("Atrazine was chosen over S-metolachlor and linuron for three reasons. First, its biodegradation is well documented: the soil bacterium _Pseudomonas_ sp. ADP breaks it down completely to CO₂ and NH₃ through six genes (_atzA_ to _atzF_) [3], so a biological treatment can, in principle, remove atrazine and its chlorinated derivatives. Second, its transformation products are regulated: Health Canada’s limit is 5 µg/L for atrazine and its metabolites, including DEA [4], and Quebec’s is 3.5 µg/L [5]. Third, in Quebec atrazine may only be used on a prescription written by an agronomist [6]; since this rule came in in 2018, atrazine sales have dropped by 84% [7]. NEPHRON therefore targets the fields where atrazine is still used. Tile water from Canadian corn fields has contained 0.1–29 µg/L atrazine, up to 16 times the 1.8 µg/L aquatic-life guideline, with the highest values right after application [8], [9]."),
  H2("C. Why the Tile Outlet, and What It Misses"),
  P("Pesticides enter tile drains through cracks and root channels, mainly in the first rains after spraying [10]. All the water from a field leaves through one pipe, so concentrations are high and flows small; river water is up to 48 times more dilute (0.6 vs. 29 µg/L), which makes removal there more costly per gram. Field practices reduce but do not remove pesticides, and constructed wetlands take land out of production."),
  P("Tile drains are not the only path, and v1 did not say how large their share is. On a 22.5 ha corn–soybean field in Quebec, surface runoff and tile drainage carried similar shares, 53% and 47%, of the measured pesticide mass [41]; the published abstract does not split this by compound, so it is used here as the best Quebec estimate for atrazine. In a flat Illinois watershed, surface runoff rarely occurred and most water left through tiles [42], while a review found pesticide concentrations are usually higher in surface runoff than in drain water [43]. This version therefore uses one river model (Sec. III-E) in which tile drains carry 30–90% of the atrazine load (most likely 47%), and the rest is surface runoff that NEPHRON does not treat. Runoff is handled with vegetated buffer strips, which NEPHRON is designed to work with. The judging criteria are mapped in Appendix A."),
];

// ---------------- II. Design
const design = [
  H1("II", "NEPHRON Design"),
  H2("A. System Layout and Frost"),
  P("NEPHRON is a gravity-fed unit with no pump (Figs. 1 and 3). v1 said the field is farmed over it; NRCS asks that equipment be kept off a bioreactor or that it have adequate cover [26], so v2 places the trench and boxes in a grassed strip at the field edge, with only pipes under cropped land. The trench media sit 0.45–1.65 m deep, and the cartridges and pipes 1.5–2.4 m deep. A Quebec transport ministry study of frost action on roads gives an average frost depth of about 1.4 m for Montréal [49], and the Quebec building code sets footings in clay at least 1.2 m deep or below the frost line, with a Montréal freezing index of 607 degree-days [50]. Roads are kept clear of snow, which insulates the ground, so 1.4 m is conservative for a grassed strip. The cartridges and the lower trench are below it, but the top of the trench and the box tops are not, so all three boxes get insulated, locked lids, and the trench is relied on for treatment only from April to October."),
];
const fig1 = [img("fig1_twin_demo.png", 318),
  CAPTION("Fig. 1. NEPHRON as shown in the live demonstration. Sensors measure (1), the digital twin manages (2), and the farmer acts (3). At the end of the year shown here, the twin reports that all is well. The pipe under the carbon box is the bypass, the percentages give the capacity used in each cartridge, and the bar marks the operating year (Table I).")];
const design2 = [
  H2("B. One Design Flow"),
  P("v1 used three flows that did not match: the carbon box was rated at 14.2 L/s (17 m³ at 20 min contact, equal to 6.1 mm/day from 20 ha), the twin used 3.5 L/s, and the trench volume was never given. v2 uses one design flow for every stage."),
  P("Quebec tile systems have used drainage coefficients as low as 10 mm/day in tight clays, with laterals usually 13–16 m apart [28]. We could not open the CRAAQ design guide that sets current values, so we take 10 mm/day as a conservative peak: 20 ha × 10 mm/day = 2,000 m³/day, or 23 L/s. NRCS Standard 605 asks a bioreactor to treat at least 15% of the peak drain flow (or the 10-year, 24-hour flow, or 60% of average annual flow) with an HRT of at least 3 h [26], [27]. Fifteen percent of 23 L/s is 3.5 L/s, the twin’s original value. That is enough for nitrate, but in the twin model 19% of the season’s drain water arrives above 3.5 L/s and bypasses untreated, mostly in the storms that carry the atrazine pulse. v2 therefore uses **7 L/s** (30% of peak, 3.0 mm/day), which sends 97% of the season’s water through treatment in the model."),
  P("**Trench.** Four hours at 7 L/s is 101 m³ of water. Hardwood chips under 1–2 ft (0.3–0.6 m) of soil have a porosity of 0.54–0.55, not the 0.7 often assumed [27], so the trench needs 183 m³ of chips. We use 26 × 6 × 1.2 m (187 m³, HRT 4.1 h). Its length-to-width ratio of 4.3:1 allows one perforated header at each end [26]. For comparison, 4 h at 14.2 L/s would need 372 m³ of chips, and the 10 × 6 × 1.2 m trench in the portfolio model gives 3.1 h at 3.5 L/s. NRCS sets a media life of at least 10 years and asks that the surface allow for settlement [26]; v2 adds both to the costs (Sec. V)."),
  P("**Carbon box.** v1’s 20 min contact time applied to the whole 17 m³ box; the 2 m³ polish alone would get only 2.3 min at 14.2 L/s. v2 sizes each stage separately. Biochar needs time: in flow-through tests, 300 s removed much more atrazine than 45 s, while 600 s added little [34], and a study of biochar water treatment recommends an EBCT of at least 30 min [35]. Three 7.5 m³ biochar cartridges (22.5 m³) give 54 min at 7 L/s. For the polish, GAC removed 47% of atrazine at an EBCT of 5.62 min in river water [37]; a 4 m³ polish gives 9.5 min. The box is 10.5 × 2.2 m in plan and 2.6 m deep (Fig. 3). The 200 mm bypass carries about 27 L/s flowing full at 0.5% slope (our Manning calculation, n = 0.011), more than the 23 L/s peak. Table II compares v1 and v2."),
];
const t2 = [...TABLE_TITLE("II", "Design Sizes, v1 and v2"),
  table([1500, 1680, 1680], ["Item", "v1", "v2"], [
    ["Design flow", "3.5 L/s (twin)|14.2 L/s (box)", "7 L/s for all stages"],
    ["Woodchip trench", "not given", "26 × 6 × 1.2 m,|187 m³, HRT 4.1 h"],
    ["Biochar", "2 × 7.5 m³", "3 × 7.5 m³, EBCT 54 min"],
    ["GAC polish", "2 m³, 2.3 min at|14.2 L/s", "4 m³, EBCT 9.5 min"],
    ["Carbon box", "7 × 2.2 m", "10.5 × 2.2 × 2.6 m"],
    ["Control boxes", "1.2 m precast", "1.2 m precast,|insulated lids"],
    ["Bypass", "200 mm", "200 mm, ≈27 L/s full"],
  ]), space()];
const design3 = [
  H2("C. Stages"),
  ITEM("1.", "_Inlet control box._ A Treat/Bypass board sends water to the trench and carbon box in the treatment season and around the carbon box off-season. Flow above 7 L/s spills to a measured bypass."),
  ITEM("2.", "_Woodchip trench._ A standard denitrifying bioreactor; field units remove 20–40% of annual nitrate-N loss [11]. Removing nitrate helps the biology downstream, since preferred nitrogen sources repress atrazine degradation in _Pseudomonas_ sp. ADP and nitrate additions reduced atrazine mineralization in soil [12]. The woodchips also take up some atrazine, but by sorption, which fills up within days (Sec. II-D)."),
  ITEM("3.", "_Carbon box._ A precast box with four lift-out cartridges: three wood biochar (C1–C3) and a GAC polish. An adsorption stage after a woodchip bioreactor is recommended to capture what the woodchips release [14]. When the twin predicts removal below 90%, or DEA appears after C2, the lead cartridge is removed, the others move forward, and fresh media goes in last."),
  ITEM("4.", "_Outlet control box._ Stop logs keep water above the cartridges, so the carbon and its biofilm never dry out."),
  H2("D. Biology in the Carbon Box, and Cold Water"),
  P("When atrazine-degrading biofilms were combined with biochar, 20–36% of the atrazine was biodegraded, transformation products were under 2.5% of the parent compound, and filter life was 1.8–2.3 times longer [15]. GAC that adsorbs atrazine also supports better degrading biofilms than non-adsorbing media [16]. In pilot GAC columns fed river water at 0.5–20 µg/L, a degrading _Rhodococcus_ strain extended the time before effluent consistently exceeded 0.1 µg/L by at least 41 days [17]. Phase 2 of NEPHRON would seed the cartridges with a culture enriched from local corn soil and selected for the chlorine-first _atzA_–_atzF_ pathway [3], so DEA does not build up, but only after the federal notification in Sec. IV-B."),
  P("Spring tile water is cold. In a field bioreactor study in Lithuania, water below 10 °C was the usual tile-water condition from late autumn to early spring, and inflow ranged from 1.8 to 21.7 °C over the season [31]. Woodchip nitrate removal has a temperature coefficient (Q10) of 2.2–2.9 [30], and New York bioreactors removed less nitrate below 5 °C [11]. Atrazine biodegradation slows too: in a clay loam, its half-life roughly doubled for every 10 °C drop [32]. So in April–June the carbon box works mainly by sorption, and v2 credits the biofilm with only a 1.0–2.3 times life extension (Table IV)."),
  P("The v1 woodchip figure also needed correcting. The 25% removal at 4 h came from lab columns [13], and the removal is by sorption, not biology [13], [29]. In a field woodchip bioreactor, atrazine broke through in under 6 days (models predicted 6–10 days), although total mass was still cut by 53% at a 21 h HRT [29]. Over a whole season, v2 therefore assumes the trench removes 5–40% of atrazine (central value 15%). Fresh woodchips also release more organic carbon than weathered ones [30], and that carbon would foul the biochar, so v2 uses weathered chips or keeps the carbon box bypassed while a new trench flushes."),
  H2("E. Seasonal Operation"),
  P("Atrazine moves in the first drainage events after spraying [9], [10], so NEPHRON runs as a seasonal shield (Table I). Off-season the carbon box is bypassed, so winter organic matter does not use up carbon meant for the spray pulse. Before forecast storms in the six to eight weeks after spraying, the farmer raises the field-drain boards. Drainage water management (DWM) cut tile discharge by 46% on average across studies [18], so the field releases the storm slowly through the carbon. v2 holds more water than v1 (up to 3 L/s, limited to about 3,000 m³ of soil storage). Holding has a risk: controlled drainage with subirrigation increased surface runoff and herbicide loss when heavy rain came soon after application [46]. NEPHRON therefore raises the boards only before a forecast storm, never subirrigates, and lowers them as soon as the storm has passed. A co-op or SCABRIC owns a shared cartridge pool, and spring start-up takes five steps in an app."),
];
const t1 = [...TABLE_TITLE("I", "NEPHRON Operating Year"),
  table([1300, 1780, 1780], ["Season", "System setting", "Farmer and twin"], [
    ["Start-up (Apr)", "Treat; boards lowered", "Five-step start-up; baseline sample"],
    ["Spray (May–Jul)", "Treat; boards raised before storms", "Logs spray date; storm alerts"],
    ["Late summer (Aug–Sep)", "Treat; boards normal", "Crew swaps cartridges"],
    ["Off-season (Oct–Mar)", "Bypass; boards raised", "Ice and fault alerts"],
  ]), space()];
const design4 = [
  H2("F. Digital Twin"),
  P("The digital twin is a computer model of each unit that tracks how much atrazine has entered and how much carbon capacity is left (Fig. 1) [25]. Low-cost flow, level and temperature sensors feed it continuously, shared turbidity, nitrate and UV254 probes add water-quality signals, and each grab sample for atrazine, DEA, DIA and hydroxyatrazine recalibrates it, so no costly online analyzer is needed. UV254 matters because organic matter that absorbs at 254 nm is what fouls biochar, and its breakthrough has been proposed as a cheap field signal for biochar bed life [35]. The twin warns the farmer to hold water before storms, times cartridge swaps from predicted removal and DEA breakthrough, flags ice or clogging, and reports atrazine removed each season for cost-share programs."),
  P("These functions answer the four tests the case sets. Holding storm water sends the spray pulse through the carbon (treatment effectiveness). Swapping on DEA breakthrough catches the transformation product the case says must be considered. Tracking each spent cartridge to incineration or reactivation keeps captured atrazine out of soil and water (environmental safety). Replacing carbon only when its capacity is used, with early clogging and ice alerts, supports cost and long-term use."),
];

// ---------------- III. Performance
const perf = [
  H1("III", "Performance Analysis"),
  H2("A. Comparison with Alternatives"),
  P("A woodchip bioreactor alone removed 25% of atrazine at 4 h and 53% at 72 h in the lab, and adding biochar raised removal to 90%, but only at 72 h [13]. Holding a field’s drainage for 72 h would need a bed many times larger than NEPHRON’s. NEPHRON instead pairs a standard 4 h trench with a compact carbon box that has about an hour of contact (Fig. 2). Unlike v1, Fig. 2 shows NEPHRON as a range, and separates steady-state removal from removal averaged over a stormy season."),
];
const fig2 = [img("fig2_alternatives.png", 318),
  CAPTION("Fig. 2. Atrazine removal by NEPHRON v2 compared with woodchip and biochar-amended bioreactors in the lab at 4 h and 72 h [13]. NEPHRON bars are P50 over 200 seasons; whiskers are P10–P90.")];
const perf2 = [
  H2("B. Steady-State Removal"),
  P("With fresh media and no bypass, the stages act in series: removal = 1 − (1 − w)(1 − c)(1 − p), where w, c and p are the woodchip, biochar and polish removals. v1 used single values (25%, 90% and 50%) to get 96%. v2 draws each value from a range (Table IV); the polish removal is scaled by its contact time from the 47% measured at 5.62 min [37], which gives 66% (45–83%) at 9.5 min. Steady-state removal is then 97% (P10–P90 94–99%). This is the most the unit can do; storms and media filling up lower it."),
];
const t4 = [...TABLE_TITLE("IV", "Uncertain Inputs and Their Ranges"),
  table([2060, 1300, 1500], ["Input", "Range (central)", "Source"], [
    ["Woodchip atrazine removal, season mean", "5–40% (15%)", "[13], [29]"],
    ["Fresh biochar pair removal", "80–95% (90%)", "[13], [19]"],
    ["GAC removal at 5.62 min EBCT", "30–65% (47%)", "[37]"],
    ["Freundlich log K~F~, wood biochars", "2.25–3.15", "[33]"],
    ["Freundlich 1/n", "0.5–0.9 (0.7)", "assumed"],
    ["Capacity kept with DOC present", "30–80% (55%)", "assumed; [35], [36]"],
    ["Biofilm life extension", "1.0–2.3× (1.6×)", "[15], [32]"],
    ["Tile share of river atrazine", "30–90% (47%)", "[41]–[43]"],
    ["Buffer-strip removal of runoff atrazine", "20–70% (45%)", "[44], [45]"],
  ], 17), space()];
const perf3 = [
  H2("C. Season-Average Removal under Storms"),
  P("The twin’s season model [25] runs one 183-day season per random seed: rain falls on 18% of days, soil moisture turns rain into drain flow, atrazine rises after spraying and is flushed out by flow, and flow above the design flow bypasses untreated. Over 200 seasons, the v1 design removed 67% on a fixed calendar and 83% with the twin. Fig. 4 shows the design changes that close the gap, re-run with the ranges in Table IV (method in Appendix B):"),
  ITEM("A.", "v1 as submitted: 83% with the twin (67% fixed)."),
  ITEM("B.", "v1 sizes with the literature ranges: 81%. The steady-state removal is similar, but the biochar holds less than v1 assumed (Sec. III-D)."),
  ITEM("C.", "Design flow 7 L/s: 89%. Bypass falls from about 3,100 m³ to 270 m³ per season."),
  ITEM("D.", "More storm holding through DWM: 89%, with bypass down to 56 m³. Holding now matters less than media capacity."),
  ITEM("E.", "v2 final, with a third biochar cartridge, a 4 m³ polish, and the twin swapping when predicted removal drops below 90% instead of 85%: **94% (P10 85%, P90 97%)**. A fixed calendar with the same hardware gives 89%."),
  P("The twin adds 5 points at P50 and 13 at P10 for the final design, because it swaps when the media are full rather than on a set date. Even so, 23% of seasons fall below 90%, mostly when the biochar draws a low capacity; Sec. VI makes measuring that capacity the first pilot task."),
];
const fig4 = [img("fig4_design_steps.png", 640),
  CAPTION("Fig. 4. Season-average atrazine removal at one unit for each design step, over 200 simulated storm seasons with the input ranges of Table IV. Lines are P10–P90; dots and numbers are P50. Orange: cartridges swapped once on a fixed date. Blue: swaps timed by the digital twin.")];
const perf4 = [
  H2("D. Media Capacity, Competition and DEA"),
  P("v1 argued that capacity would never limit media life, because the expected load (0.009 mg/g) was far below the more than 10 mg/g GAC held at 7 µg/L [23]. That compared biochar with GAC and ignored competition. For tree, corncob and corn-straw biochars made at 450 °C, Freundlich log K~F~ values of 2.25–3.15 have been reported (q in mg/kg, C in mg/L; summarized in [33]). With 1/n of 0.5–0.9 (assumed, since it was not reported with those values), biochar holds about 0.7–60 mg/kg in equilibrium with 2 µg/L, with a central value of 6.5 mg/kg (0.0065 mg/g), the same order as v1’s load, not a thousand times larger."),
  P("Dissolved organic matter is typically present at 1,000 to 100,000 times the concentration of micropollutants and fouls adsorbents, shortening bed life [35]; organic matter also displaces atrazine from activated carbon over time [36], and v1 already cited this effect [23]. Woodchips release DOC, so this applies directly. We found no data for DOC competition on wood biochar, so v2 assumes 30–80% of the clean-water capacity remains, plus the biofilm extension above. The three cartridges then hold 12–142 g of atrazine per season (P10–P90; central 41 g), compared with about 87 g arriving in a typical model season. Capacity, not only contact time, sets how often cartridges are swapped: 2.3 lead-cartridge swaps per season on average (none in 28% of seasons, five in 30%)."),
  P("DEA sorbs less than atrazine on activated carbon [20], and we found no Freundlich data for DEA on wood biochar, so its breakthrough is an estimate. At the central capacity with DOC and no biofilm (3.6 mg/kg), a 7.5 m³ cartridge (2.25 t) treats about q·ρ/C = 3.6 × 300 / 2 ≈ 530 bed volumes, or 4,000 m³, about 19 days of average flow (2.4 L/s) before atrazine passes it. If DEA is held at 30–70% of atrazine’s capacity, DEA passes C1 after about 6–13 days of average flow and C2 after 12–27 days, and sooner during the spray pulse. This is why the twin watches DEA after C2 and swaps the lead cartridge a few times each season, and why Sec. VI measures DEA isotherms on the chosen biochar before a full-scale build."),
  H2("E. River Reduction: One Model"),
  P("v1 calculated river reduction two ways (96% unit removal in the abstract, 95% × 95% coverage = 90.2% in Sec. III-E), and both assumed all river atrazine comes through tile drains. v2 uses one model for the whole report:"),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: runs("R = C × [T × U + (1 − T) × B]", { size: 24 }) }),
  P("where C is the share of atrazine-treated tile fields fitted with NEPHRON (95%), T the tile-drain share of the river load (Sec. I-C), U the season-average unit removal (Sec. III-C), and B the removal of runoff atrazine by buffer strips on the same fields (0 if no buffers are added). Grass and multi-species buffers cut atrazine in runoff by 58–72% under simulated rain [44], but on a Quebec sandy loam, dissolved tracers passed beneath a well-vegetated buffer strip [45], so v2 uses B = 20–70%.", { indent: { firstLine: 0 } }),
  P("NEPHRON alone reduces the river load by 47% (P10–P90 34–65%), from 0.6 to about 0.32 µg/L at P50. With buffer strips it reduces it by 67% (55–77%), to about 0.20 µg/L (Fig. 5). Neither meets the case goal of 90% (0.06 µg/L). Reaching it would need tile drains to carry nearly all the atrazine and NEPHRON to treat nearly all of it, or runoff controls that remove more than 90%. Our honest conclusion is that NEPHRON is the tile-drain part of a watershed plan, alongside buffer strips and the prescription system that has already cut atrazine sales by 84% [7]."),
];
const fig5 = [img("fig5_river.png", 318),
  CAPTION("Fig. 5. River atrazine load reduction with 95% of treated tile fields fitted, over 200 seasons with the ranges of Table IV. Dots are P50; lines are P10–P90.")];
const t5 = [...TABLE_TITLE("V", "Headline Results, P10 / P50 / P90"),
  table([2260, 2600], ["Quantity (final design)", "P10 / P50 / P90"], [
    ["Unit removal, steady state", "94% / 97% / 99%"],
    ["Unit removal, season average, twin", "85% / 94% / 97%"],
    ["Unit removal, season average, fixed calendar", "72% / 89% / 95%"],
    ["River reduction, NEPHRON alone", "34% / 47% / 65%"],
    ["River reduction, with buffer strips", "55% / 67% / 77%"],
    ["Lead-cartridge swaps per season", "0 / 2 / 5 (mean 2.3)"],
    ["Bypassed volume per season", "0 / 56 / 710 m³"],
  ], 17), space()];

// ---------------- IV. Impacts
const impacts = [
  H1("IV", "Health, Environmental and Community Impacts"),
  H2("A. Human Health and Drinking Water"),
  P("Municipalities along the Châteauguay draw drinking water from the river, where conventional treatment did not significantly lower pesticides and transformation products [1]. Levels meet Quebec’s standard today, but transformation products may carry higher health risks than their parents [1]. Removing atrazine and DEA at the field edge cuts the load the plant must handle and widens the margin below the 3.5 µg/L provincial and 5 µg/L federal limits during June and July peaks [4], [5]."),
  H2("B. Safety and Regulation of Phase 2 Bacteria"),
  P("NEPHRON uses no added chemicals and no pump, sits below grade under locked, insulated lids, and keeps spent media in closed cartridges handled by a trained crew, never by the farmer."),
  P("v1 said native bacteria would be released only after regulatory review; v2 names the review. Under CEPA, no one may manufacture or import a living organism that is not on the Domestic Substances List until the prescribed information has been given to the Minister and the assessment period has expired (s. 106(1)) [48]. Being native is not an exemption. The New Substances Notification Regulations (Organisms) require Schedule 1 information at least 120 days before manufacture or import. For a micro-organism indigenous to the ecozone where it is released, some ecological-effects data are waived, but a separate notification is still needed for each ecozone, with data showing the organism is indigenous there [47]. An experimental field study uses Schedule 3, with a 90-day period, and an organism grown at its site of isolation for release at that same site uses Schedule 4, with 30 days [47]. Phase 2 therefore starts with a DSL check and, if needed, a Schedule 3 notification at least 90 days before the pilot."),
  H2("C. Environment, Wildlife and End of Life"),
  P("As a herbicide, atrazine mostly affects aquatic plants and algae, which the 1.8 µg/L guideline protects [8]; treating tile water removes short peaks of up to 29 µg/L [9] that the river average hides. Woodchip bioreactors can release nitrous oxide, methane and DOC [14]; the carbon box captures the DOC, and the twin flags long retention times."),
  P("v1 said spent media would be regenerated at high temperature. That is standard for GAC, but not yet for biochar. A semi-oxic heat treatment regenerated fouled biochar in the lab [38], and a life-cycle study found that regeneration and incineration with energy recovery both lowered the impacts of spent adsorbents; it assessed thermal reactivation only for activated carbon, and incineration, landfill and elution regeneration for biochar [39]. v2 therefore sends spent biochar to incineration with energy recovery, or to an engineered landfill if none is available (Quebec’s disposal royalty was CAD 34 per tonne in 2025 [40]), and sends spent GAC to commercial reactivation. Spent media never go onto fields, so captured atrazine is not moved into soil."),
  H2("D. Communities"),
  P("Farmers keep their land in production and gain nitrate removal [11]. The cartridge pool creates local service work, and the twin’s season reports give municipalities and SCABRIC measured data on atrazine removed."),
];

// ---------------- V. Cost
const cost = [
  H1("V", "Cost and Return on Investment"),
  P("Table III is revised for the larger v2 unit. It adds woodchip replacement, settlement, spent-media disposal, polish renewal and design costs, which v1 left out. The woodchip trench is priced within the US$77–200 per m³ reported for installed bioreactors [11]; the other capital items, media prices and crew costs are engineering estimates."),
];
const t3 = [...TABLE_TITLE("III", "Estimated Costs for One 20 ha Field (CAD)"),
  table([3460, 1400], ["Item", "Cost (CAD)"], [
    ["Capital: woodchip trench, 26 × 6 × 1.2 m, lined, installed", "26,000"],
    ["Capital: two 1.2 m precast control boxes, stop logs, insulated lids", "6,000"],
    ["Capital: precast carbon box 10.5 × 2.2 × 2.6 m, frames, installation", "17,000"],
    ["Capital: media (6.75 t biochar at $600/t; 1.8 t GAC at $3,000/t)", "9,450"],
    ["Capital: sensors and logger (flow, level, temperature)", "3,000"],
    ["Capital: engineering design and approvals (design can add 50–100% of installation cost [11])", "10,000"],
    ["**Total capital (about $3,570/ha)**", "**71,450**"],
    ["Annual: capital over 20 years at 4%", "5,257"],
    ["Annual: woodchips replaced every 10 years (≈41% of trench cost [11]), sinking fund at 4%", "891"],
    ["Annual: settlement top-up of chips and soil cap [26]", "300"],
    ["Annual: lead biochar swaps, mean 2.3 per season at $1,850 (2.25 t plus crew visit)", "4,255"],
    ["Annual: spent biochar, 5.2 t at $150/t incl. $34/t royalty [40]", "780"],
    ["Annual: GAC polish renewed every 3 years", "1,800"],
    ["Annual: laboratory (6 samples at $250, atrazine and DEA)", "1,500"],
    ["Annual: telemetry and twin hosting", "300"],
    ["**Total annual (about $750/ha)**", "**15,083**"],
  ], 17), space()];
const cost2 = [
  P("The total is about CAD 15,100 per year, or **CAD 750 per hectare per year** ($0.40 per m³ treated), more than twice v1’s CAD 313. The largest uncertainty is media capacity: with no swaps the cost is about CAD 500/ha, and with five swaps about CAD 1,050/ha."),
  P("**Cost-effectiveness.** Per kilogram, atrazine removal is expensive at any point because the problem is in micrograms per litre. The unit removes about 84 g per season in the model (mean), so the cost is about CAD 180,000 per kg; v1’s own numbers already implied about CAD 162,000 per kg (6,250 / 0.0385). Conventional drinking-water treatment does little for pesticides, while powdered activated carbon at full-scale plants removed 28–87% of atrazine at doses of 2.8–33 mg/L [37]. We could not find a verified cost per kilogram for municipal carbon upgrades, so we do not claim NEPHRON is cheaper per kilogram. Its case rests on three other points: it removes the peaks that reach tributaries before any plant; it targets only the fields that still use atrazine; and it removes nitrate."),
  P("**Nitrate co-benefit.** NRCS-designed field bioreactors removed 0.8–8.3 kg N/ha per year [11], or 16–166 kg N per year from 20 ha. The trench’s share of the annual cost (capital, replacement and settlement, about CAD 3,100) works out to CAD 19–194 per kg N, about CAD 34 per kg N at the middle of the range. That is above the US$2.50–20 per kg N (up to US$48) reported for bioreactors sized for nitrate alone [11], because this trench is sized for 7 L/s rather than the 15% criterion."),
  P("**Who pays.** The farmer gains nitrate removal and keeps atrazine available under prescription, and MAPAQ’s Prime-Vert program pays up to 70% of eligible costs of on-farm trials of agri-environmental practices, capped at $15,000 per trial [24]. That could fund the pilot in Sec. VI but not a full installation. For AAFC and the province, the return is a protected drinking-water source: with 832 atrazine prescriptions issued in Quebec in 2019 [7], one 20 ha unit per prescription would cost about CAD 12.5 million per year, a targeted program rather than a watershed-wide one."),
];

// ---------------- VI, VII
const impl = [
  H1("VI", "Implementation and Ethics"),
  P("NEPHRON uses standard drainage hardware and takes no cropland out of production. The rollout is: (1) a demonstration unit on a Châteauguay farm with SCABRIC; (2) column tests at 4–10 °C with real tile water to measure woodchip and biochar removal, DOC release, and Freundlich isotherms for atrazine and DEA on the chosen biochar, the inputs Table IV could only bound; (3) DEA breakthrough tests to set the twin’s swap rule; and (4) phase 2 strains only after a DSL check and any notification under the organisms regulations [47], [48]."),
  P("Three trade-offs remain: the woodchips release some nitrous oxide; spent biochar is incinerated or landfilled, not yet regenerated; and holding water in the field could increase runoff if the boards are misused [46]. Sec. II-E and IV-C explain how each is managed, and we think they are worth accepting to keep atrazine and DEA out of a drinking-water source. The design handles four practical barriers. Cold water slows biology, so the unit treats water only from April to October and relies on sorption in spring. Farmers have little spare time, so start-up takes five steps in an app and a trained crew does every swap. Organic matter competes with atrazine for carbon [23], [35], so the carbon box is bypassed off-season and while a new trench flushes. Finally, the farm pays while downstream users benefit, and Prime-Vert [24] can cover part of the pilot."),
  H1("VII", "Conclusion"),
  P("NEPHRON turns a standard nitrate bioreactor into a field kidney for atrazine: woodchips remove the nitrate that blocks biodegradation, biochar and GAC capture atrazine and DEA, and a digital twin runs the unit with five spring steps. This revision sizes the whole unit for one design flow and tests it against storms and literature ranges. The unit removes 97% at steady state and 94% averaged over a stormy season, at about CAD 750 per hectare per year. Because tile drains carry about half of the river’s atrazine, NEPHRON alone cuts the river load by about half, and by about two thirds with buffer strips. Reaching the 90% goal needs NEPHRON as the tile-drain part of a watershed plan. Farmers get a low-effort addition to drainage they already have, and AAFC and Quebec get a targeted way to protect a drinking-water source."),
];

// ---------------- References
const REFS = [
  "X. Feng, Z. Liu, S. Vo Duy, L. Parent, B. Barbeau, and S. Sauvé, “Temporal trends of 46 pesticides and 8 transformation products in surface and drinking water in Québec, Canada (2021–2023): Potential higher health risks of transformation products than parent pesticides,” _Water Res._, vol. 277, Art. no. 123339, 2025, doi: 10.1016/j.watres.2025.123339.",
  "X. Feng, Z. Liu, S. Vo Duy, G. Munoz, L. Parent, and S. Sauvé, “Pesticides and transformation products in surface waters of western Montérégie, Canada: Occurrence, spatial distribution and ecotoxicological risks,” _Environ. Sci.: Adv._, vol. 3, no. 6, 2024, doi: 10.1039/d3va00231d.",
  "B. Martinez, J. Tomkins, L. P. Wackett, R. Wing, and M. J. Sadowsky, “Complete nucleotide sequence and organization of the atrazine catabolic plasmid pADP-1 from _Pseudomonas_ sp. strain ADP,” _J. Bacteriol._, vol. 183, no. 19, pp. 5684–5697, 2001, doi: 10.1128/JB.183.19.5684-5697.2001.",
  "Health Canada, _Guidelines for Canadian Drinking Water Quality: Guideline Technical Document – Atrazine_. Ottawa, ON, Canada: Health Canada, 1993.",
  "Gouvernement du Québec, “Contrôles de l’eau distribuée,” _Règlement sur la qualité de l’eau potable_ (RLRQ, c. Q-2, r. 40), Oct. 14, 2026. [Online]. Available: https://www.quebec.ca/agriculture-environnement-et-ressources-naturelles/eau/potable-usees-pluviales/eau-potable/obligations-qualite-eau-potable/controles-eau-distribuee. Accessed: Nov. 21, 2026.",
  "_Pesticides Management Code_, CQLR c. P-9.3, r. 1, s. 74.1 (Québec).",
  "Ministère de l’Environnement et de la Lutte contre les changements climatiques, “La justification agronomique : état d’avancement de sa mise en œuvre,” Gouvernement du Québec, Québec, QC, Canada. [Online]. Available: https://cdn-contenu.quebec.ca/cdn-contenu/environnement/pesticides/justification-agronomique-etat-avancement.pdf. Accessed: Nov. 21, 2026.",
  "Canadian Council of Ministers of the Environment, “Canadian water quality guidelines for the protection of aquatic life: Atrazine,” in _Canadian Environmental Quality Guidelines_. Winnipeg, MB, Canada: CCME, 1999.",
  "P. Milburn, D. A. Leger, H. O’Neill, K. MacQuarrie, and J. E. Richards, “Point and nonpoint source leaching of atrazine from a corn field: Effects on tile drainage water quality,” _Can. Agric. Eng._, vol. 37, no. 4, pp. 269–277, 1995.",
  "E. J. Kladivko, L. C. Brown, and J. L. Baker, “Pesticide transport to subsurface tile drains in humid regions of North America,” _Crit. Rev. Environ. Sci. Technol._, vol. 31, no. 1, pp. 1–62, 2001.",
  "L. E. Christianson et al., “Effectiveness of denitrifying bioreactors on water pollutant reduction from agricultural areas,” _Trans. ASABE_, vol. 64, no. 2, pp. 641–658, 2021, doi: 10.13031/trans.14011.",
  "V. García-González, F. Govantes, L. J. Shaw, R. G. Burns, and E. Santero, “Nitrogen control of atrazine utilization in _Pseudomonas_ sp. strain ADP,” _Appl. Environ. Microbiol._, vol. 69, no. 12, pp. 6987–6993, 2003, doi: 10.1128/AEM.69.12.6987-6993.2003.",
  "B. Hassanpour, L. D. Geohring, A. R. Klein, S. Giri, L. Aristilde, and T. S. Steenhuis, “Application of denitrifying bioreactors for the removal of atrazine in agricultural drainage water,” _J. Environ. Manage._, vol. 239, pp. 48–56, 2019, doi: 10.1016/j.jenvman.2019.03.029.",
  "M. G. Healy et al., “Optimizing nitrate removal and evaluating pollution swapping trade-offs from laboratory denitrification bioreactors,” _Ecol. Eng._, vol. 74, pp. 290–301, 2015, doi: 10.1016/j.ecoleng.2014.10.005.",
  "A. C. Portmann, G. H. LeFevre, R. Hankawa, D. Werner, and C. P. Higgins, “The regenerative role of biofilm in the removal of pesticides from stormwater in biochar-amended biofilters,” _Environ. Sci.: Water Res. Technol._, vol. 8, no. 5, pp. 1092–1110, 2022, doi: 10.1039/d1ew00870f.",
  "M. Herzberg, C. G. Dosoretz, S. Tarre, M. Beliavski, and M. Green, “Biological granulated activated carbon fluidized bed reactor for atrazine remediation,” _Water Sci. Technol._, vol. 49, no. 11–12, pp. 215–222, 2004.",
  "L. R. Jones, S. A. Owens, P. Horrell, and R. G. Burns, “Bacterial inoculation of granular activated carbon filters for the removal of atrazine from surface water,” _Water Res._, vol. 32, no. 8, pp. 2542–2549, 1998.",
  "J. A. Ross et al., “A synthesis and comparative evaluation of factors influencing the effectiveness of drainage water management,” _Agric. Water Manage._, vol. 178, pp. 366–376, 2016.",
  "B. M. Phillips, L. B. McCalla Fuller, K. Siegler, X. Deng, and R. S. Tjeerdema, “Treating agricultural runoff with a mobile carbon filtration unit,” _Arch. Environ. Contam. Toxicol._, vol. 82, no. 4, pp. 455–466, 2022, doi: 10.1007/s00244-022-00925-8.",
  "C. D. Adams and T. L. Watson, “Treatability of s-triazine herbicide metabolites using powdered activated carbon,” _J. Environ. Eng._, vol. 122, no. 4, pp. 327–330, 1996, doi: 10.1061/(ASCE)0733-9372(1996)122:4(327).",
  "W. R. Roy and I. G. Krapac, “Adsorption and desorption of atrazine and deethylatrazine by low organic carbon geologic materials,” _J. Environ. Qual._, vol. 23, no. 3, pp. 549–556, 1994, doi: 10.2134/jeq1994.00472425002300030021x.",
  "S. J. Feakin, B. Gubbins, I. McGhee, L. J. Shaw, and R. G. Burns, “Inoculation of granular activated carbon with s-triazine-degrading bacteria for water treatment at pilot-scale,” _Water Res._, vol. 29, no. 7, pp. 1681–1688, 1995.",
  "G.-S. Wang, “Effects of natural organic matter on adsorption capacity for atrazine by activated carbon,” _J. Chin. Inst. Environ. Eng._, vol. 15, no. 2, pp. 81–89, 2005.",
  "Ministère de l’Agriculture, des Pêcheries et de l’Alimentation, “Programme Prime-Vert 2026-2027,” Gouvernement du Québec, Québec, QC, Canada, 2026. [Online]. Available: https://www.quebec.ca/agriculture-environnement-et-ressources-naturelles/agriculture/aide-financiere/prime-vert/volet1. Accessed: Nov. 21, 2026.",
  "S. Koo, “NEPHRON digital-twin simulation (dcbas_sim.py),” GitHub, Nov. 21, 2026. [Online]. Available: https://github.com/Samuel0720-source/Nephron/blob/main/dcbas_sim.py. Accessed: Nov. 25, 2026.",
  "USDA Natural Resources Conservation Service, “Conservation practice standard: Denitrifying bioreactor, Code 605,” NRCS Ohio, Jan. 2017. [Online]. Available: https://efotg.sc.egov.usda.gov/api/CPSFile/20038/605_OH_CPS_Denitrifying_Bioreactor_2017. Accessed: Nov. 25, 2026.",
  "USDA Natural Resources Conservation Service, “Conservation practice guidance: 605 – Denitrifying bioreactor,” NRCS Illinois, Apr. 2021. [Online]. Available: https://efotg.sc.egov.usda.gov/api/CPSFile/30345/605_IL_GD_Denitrifying_Bioreactor_2021. Accessed: Nov. 25, 2026.",
  "M. Gagnon, A. Weill, É. Thibault, and V. Bouthillier Grenier, _Guide d’évaluation des systèmes de drainage : une approche renouvelée_. Agri-Réseau, 2015. [Online]. Available: https://www.agrireseau.net/documents/document_89233.pdf. Accessed: Nov. 25, 2026.",
  "A. Ranaivoson, P. Rice, J. F. Moncrief, G. W. Feyereisen, and M. Dittrich, “Acetochlor and atrazine dissipation in a woodchip denitrifying bioreactor: A comparison of experimental results with model estimates,” _Int. J. Hydrol._, vol. 3, no. 4, pp. 286–306, 2019, doi: 10.15406/ijh.2019.03.00191.",
  "N. L. Hoover, A. Bhandari, M. L. Soupir, and T. B. Moorman, “Woodchip denitrification bioreactors: Impact of temperature and hydraulic retention time on nitrate removal,” _J. Environ. Qual._, vol. 45, no. 3, pp. 803–812, 2016, doi: 10.2134/jeq2015.03.0161.",
  "R. Vismontienė and A. Povilaitis, “Effect of biochar amendment in woodchip denitrifying bioreactors for nitrate and phosphate removal in tile drainage flow,” _Water_, vol. 13, Art. no. 2883, 2021, doi: 10.3390/w13202883.",
  "I. F. Chowdhury, M. Rohan, B. J. Stodart, C. Chen, H. Wu, and G. S. Doran, “Persistence of atrazine and trifluralin in a clay loam soil undergoing different temperature and moisture conditions,” _Environ. Pollut._, vol. 276, Art. no. 116687, 2021, doi: 10.1016/j.envpol.2021.116687.",
  "J. M. Gonzalez, M. J. Shipitalo, D. R. Smith, E. Warnemuende-Pappas, and S. J. Livingston, “Atrazine sorption by biochar, tire chips, and steel slag as media for blind inlets: A kinetic and isotherm sorption approach,” _J. Water Resour. Prot._, vol. 8, no. 13, pp. 1266–1282, 2016, doi: 10.4236/jwarp.2016.813097.",
  "C. J. Penn, J. M. Gonzalez, and I. Chagas, “Investigation of atrazine sorption to biochar with titration calorimetry and flow-through analysis: Implications for design of pollution-control structures,” _Front. Chem._, vol. 6, Art. no. 307, 2018, doi: 10.3389/fchem.2018.00307.",
  "J. Kearns, E. Dickenson, M. T. Aung, S. M. Joseph, S. R. Summers, and D. Knappe, “Biochar water treatment for control of organic micropollutants with UVA surrogate monitoring,” _Environ. Eng. Sci._, vol. 38, no. 5, pp. 298–309, 2021, doi: 10.1089/ees.2020.0173.",
  "Q. Li, V. L. Snoeyink, C. Campos, and B. J. Mariñas, “Displacement effect of NOM on atrazine adsorption by PACs with different pore size distributions,” _Environ. Sci. Technol._, vol. 36, no. 7, pp. 1510–1515, 2002, doi: 10.1021/es010870w.",
  "U.S. Environmental Protection Agency, Office of Pesticide Programs, “Summary of pesticide removal/transformation efficiencies from various drinking water treatment processes,” CARAT Background Document 3, Oct. 3, 2000. [Online]. Available: https://archive.epa.gov/pesticides/carat/web/pdf/dw4.pdf. Accessed: Nov. 25, 2026.",
  "M. A. Greiner, K. K. Shimabuku, and R. S. Summers, “Influence of biochar thermal regeneration on sulfamethoxazole and dissolved organic matter adsorption,” _Environ. Sci.: Water Res. Technol._, vol. 4, no. 2, pp. 169–174, 2018, doi: 10.1039/C7EW00379J.",
  "I. Kozyatnyk, D. M. M. Yacout, J. Van Caneghem, and S. Jansson, “Comparative environmental assessment of end-of-life carbonaceous water treatment adsorbents,” _Bioresour. Technol._, vol. 302, Art. no. 122866, 2020, doi: 10.1016/j.biortech.2020.122866.",
  "Ministère de l’Environnement, de la Lutte contre les changements climatiques, de la Faune et des Parcs, _Rapport annuel 2025 : guide pour remplir la déclaration annuelle à l’intention des exploitants d’installations d’élimination_. Québec, QC, Canada, 2025. [Online]. Available: https://www.environnement.gouv.qc.ca/matieres/redevances/Guide-rapp-annuel.pdf. Accessed: Nov. 25, 2026.",
  "F. Chrétien, I. Giroux, G. Thériault, P. Gagnon, and J. Corriveau, “Surface runoff and subsurface tile drain losses of neonicotinoids and companion herbicides at edge-of-field,” _Environ. Pollut._, vol. 224, pp. 255–264, 2017, doi: 10.1016/j.envpol.2017.02.002.",
  "P. K. Kalita, A. S. Algoazany, J. K. Mitchell, R. A. C. Cooke, and M. C. Hirschi, “Subsurface water quality from a flat tile-drained watershed in Illinois, USA,” _Agric. Ecosyst. Environ._, vol. 115, no. 1–4, pp. 183–193, 2006, doi: 10.1016/j.agee.2006.01.006.",
  "A. Gramlich, S. Stoll, C. Stamm, T. Walter, and V. Prasuhn, “Effects of artificial land drainage on hydrology, nutrient and pesticide fluxes from agricultural fields – A review,” _Agric. Ecosyst. Environ._, vol. 266, pp. 84–99, 2018, doi: 10.1016/j.agee.2018.04.005.",
  "C.-H. Lin, R. N. Lerch, K. W. Goyne, and H. E. Garrett, “Reducing herbicides and veterinary antibiotics losses from agroecosystems using vegetative buffers,” _J. Environ. Qual._, vol. 40, no. 3, pp. 791–799, 2011, doi: 10.2134/jeq2010.0141.",
  "S. E. Allaire, C. Sylvain, S. F. Lange, G. Thériault, and P. Lafrance, “Potential efficiency of riparian vegetated buffer strips in intercepting soluble compounds in the presence of subsurface preferential flows,” _PLoS ONE_, vol. 10, no. 7, Art. no. e0131840, 2015, doi: 10.1371/journal.pone.0131840.",
  "J. D. Gaynor, C. S. Tan, C. F. Drury, T. W. Welacky, H. Y. Ng, and W. D. Reynolds, “Runoff and drainage losses of atrazine, metribuzin, and metolachlor in three water management systems,” _J. Environ. Qual._, vol. 31, no. 1, pp. 300–308, 2002, doi: 10.2134/jeq2002.3000.",
  "_New Substances Notification Regulations (Organisms)_, SOR/2005-248 (Canada), current to Oct. 29, 2026. [Online]. Available: https://laws-lois.justice.gc.ca/eng/regulations/SOR-2005-248/FullText.html. Accessed: Nov. 25, 2026.",
  "_Canadian Environmental Protection Act, 1999_, S.C. 1999, c. 33, ss. 104, 106. [Online]. Available: https://laws-lois.justice.gc.ca/eng/acts/C-15.31/. Accessed: Nov. 25, 2026.",
  "A. Lacasse, “Étude de l’action du gel sur les routes,” Service des sols et chaussées, Ministère des Transports du Québec, Québec, QC, Canada, May 1988. [Online]. Available: http://www.bv.transports.gouv.qc.ca/mono/1177376.pdf. Accessed: Nov. 25, 2026.",
  "Garantie de construction résidentielle, “Caractéristiques du sol – mouvements du sol dû au gel,” Fiche technique FT-9.4.4.4-01, Montréal, QC, Canada, Feb. 2024. [Online]. Available: https://www.garantiegcr.com/app/uploads/2024/02/ft-9-4-4-4--01-240227.pdf. Accessed: Nov. 25, 2026.",
];
const refs = [new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 }, keepNext: true,
    children: [new TextRun({ text: "References", font: FONT, size: 24, smallCaps: true })] }),
  ...REFS.map((r, i) => new Paragraph({
    alignment: AlignmentType.LEFT, spacing: { after: 40 }, indent: { left: 480, hanging: 480 },
    children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT, size: 18 }), ...runs(r, { size: 18 })],
    tabStops: [{ type: "left", position: 480 }],
  }))];

// ---------------- Appendices (single column)
const appA = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "Appendix A", font: FONT, size: 24, smallCaps: true })] }),
  ...TABLE_TITLE("VI", "How NEPHRON Meets Each Judging Criterion"),
  table([2200, 2600, 5280], ["Judging criterion", "Where to find it", "What the report shows"], [
    ["Evidence-based solution (20)", "Secs. I-C, II-B to II-D, III; Figs. 2, 4, 5; Tables IV, V", "Every stage rests on peer-reviewed field or pilot results; every uncertain input is a range with a source or is marked as assumed; results are P10/P50/P90 over 200 seasons; the river model includes surface runoff."],
    ["Practical and feasible (20)", "Secs. II-A, II-B, II-E, V, VI; Tables I–III; Fig. 3", "One 7 L/s design flow checked against NRCS 605 and a Quebec drainage coefficient; dimensioned plan and section; frost and insulated lids; five-step start-up; crew-run cartridge pool; full costs including replacement and disposal."],
    ["Innovative (10)", "Secs. II-D, II-F, III-C", "Removing nitrate first lets the biofilm break atrazine down; the twin holds storm water and swaps cartridges on predicted removal, DEA and UV254 rather than a calendar, adding 5–13 points of removal."],
    ["Ethical and environmental (10)", "Secs. IV, VI", "No added chemicals; DEA tracked; spent biochar incinerated with energy recovery, GAC reactivated, never spread on fields; CEPA notification named for phase 2 bacteria; the 90% goal is shown honestly as needing runoff controls too."],
    ["Report requirements", "Secs. I to V", "Background and safety (I, IV-B); environment, wildlife and communities (IV-C, IV-D); quantitative analysis (III); cost and return (V); human health and drinking water (IV-A)."],
    ["Professional report and sources (15)", "Whole report; References", "Times New Roman 12 pt, IEEE format, 50 peer-reviewed, government and standards sources; v2 changes listed in a separate change log."],
  ], 18),
  space(),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 60 },
    children: [new TextRun({ text: "Appendix B: v2 Season Model", font: FONT, size: 24, smallCaps: true })] }),
  PN("The v2 model extends the twin’s season model [25] and keeps its weather unchanged, so design A reproduces the original 67% and 83%. Each of 200 seeds draws one storm season and one set of the inputs in Table IV. Each day, the model (1) holds water in the field before a forecast storm of more than 15 mm, or when flow exceeds the design flow, up to the holding rate and about 3,000 m³ of soil storage, and releases it once flow falls below 70% of the design flow; (2) treats flow up to the design flow and bypasses the rest; (3) removes atrazine in series, with biochar removal falling as (1 − f³) as the fraction used, f, rises toward the season capacity from Sec. III-D, and polish removal scaled by EBCT; and (4) swaps the lead cartridge, freeing one cartridge’s capacity, when predicted removal drops below the swap threshold (85% in A–D, 90% in E; at most one swap per season in A and five in E). The fixed-calendar case swaps once on day 140. Unit removal is the season’s atrazine out (treated plus bypassed) divided by atrazine in. Limitations: daily steps; atrazine in held water takes the concentration of the day it is released; capacity uses the flow-weighted mean concentration; DEA is not simulated directly; and water still held at season end is not counted. The model compares designs and operating rules. It does not predict actual river concentrations.", { run: { size: 22 } }),
];

// ================================================================ ASSEMBLE
const twoColProps = (type) => ({ page, column: twoCol, type });
const oneColProps = (type) => ({ page, type });
const doc = new Document({
  creator: "Thomas Kim, Samuel Koo",
  title: "NEPHRON: A Digital-Twin-Managed Bioreactor for Atrazine in Tile Drainage (v2)",
  styles: { default: { document: { run: { font: FONT, size: 24 } } } },
  sections: [
    { properties: oneColProps(SectionType.NEXT_PAGE), footers: { default: footer }, children: [...title, ...front] },
    { properties: twoColProps(SectionType.NEXT_PAGE), footers: { default: footer },
      children: [...intro, ...design, ...fig1, ...design2, ...t2] },
    { properties: oneColProps(SectionType.CONTINUOUS), footers: { default: footer }, children: [
      img("fig3_drawing.png", 640),
      CAPTION("Fig. 3. NEPHRON v2 for a 20 ha field at a 7 L/s design flow. (a) Plan: inlet box, woodchip trench, carbon box with three biochar cartridges and a GAC polish, outlet box and 200 mm bypass. (b) Section: depths below grade, the 1.4 m average frost depth for Montréal [49], and insulated lids. Dimensions in metres."),
    ] },
    { properties: twoColProps(SectionType.CONTINUOUS), footers: { default: footer },
      children: [...design3, ...t1, ...design4, ...perf, ...fig2, ...perf2, ...t4, ...perf3] },
    { properties: oneColProps(SectionType.CONTINUOUS), footers: { default: footer }, children: [...fig4] },
    { properties: twoColProps(SectionType.CONTINUOUS), footers: { default: footer },
      children: [...perf4, ...fig5, ...t5, ...impacts, ...cost, ...t3, ...cost2, ...impl, ...refs] },
    { properties: oneColProps(SectionType.NEXT_PAGE), footers: { default: footer }, children: appA },
  ],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("wrote", OUT, b.length, "bytes"); });
