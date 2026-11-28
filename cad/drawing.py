"""
The NEPHRON general-arrangement drawing (A3, 420 x 297 paper mm), from the CAD's hidden-line views.
Plan and section A-A at 1:200, the carbon box at 1:50, dimensions in mm, a parts list and a title block.
Run:  python drawing.py out/views.json out/nephron-ga.svg
"""
import json
import sys

views = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
INK = '#1b2430'
FAINT = '#8a94a3'
BLUE = '#0b63ba'
svg = []


def add(s):
    svg.append(s)


def path(polys, xf, cls, clip=None):
    d = []
    for poly in polys:
        pts = [xf(x, y) for x, y in poly]
        if clip and not any(clip(px, py) for px, py in pts):
            continue
        d.append('M' + ' L'.join(f'{px:.2f} {py:.2f}' for px, py in pts))
    add(f'<path class="{cls}" d="{" ".join(d)}"/>')


def text(x, y, s, size=2.6, anchor='middle', weight=400, fill=INK, rotate=None):
    r = f' transform="rotate({rotate} {x:.2f} {y:.2f})"' if rotate is not None else ''
    add(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}"{r}>{s}</text>')


def dim_h(x1, x2, y, ext_from, label, below=False):
    """A horizontal dimension at paper height y, extension lines down/up to ext_from."""
    add(f'<path class="dim" d="M{x1:.2f} {ext_from:.2f} L{x1:.2f} {y + (1 if below else -1):.2f} M{x2:.2f} {ext_from:.2f} L{x2:.2f} {y + (1 if below else -1):.2f}"/>')
    add(f'<path class="dim" d="M{x1:.2f} {y:.2f} L{x2:.2f} {y:.2f}" marker-start="url(#a)" marker-end="url(#a)"/>')
    text((x1 + x2) / 2, y - 0.9, label, 2.2)


def dim_v(y1, y2, x, ext_from, label, left=True):
    add(f'<path class="dim" d="M{ext_from:.2f} {y1:.2f} L{x + (-1 if left else 1):.2f} {y1:.2f} M{ext_from:.2f} {y2:.2f} L{x + (-1 if left else 1):.2f} {y2:.2f}"/>')
    add(f'<path class="dim" d="M{x:.2f} {y1:.2f} L{x:.2f} {y2:.2f}" marker-start="url(#a)" marker-end="url(#a)"/>')
    text(x - 0.9, (y1 + y2) / 2, label, 2.2, rotate=-90)


def callout(n, x, y, tx, ty):
    add(f'<path class="lead" d="M{x:.2f} {y:.2f} L{tx:.2f} {ty:.2f}"/><circle cx="{x:.2f}" cy="{y:.2f}" r="0.5" fill="{INK}"/>')
    add(f'<circle cx="{tx:.2f}" cy="{ty:.2f}" r="2.3" fill="#fff" stroke="{INK}" stroke-width="0.25"/>')
    text(tx, ty + 0.95, str(n), 2.4, weight=600)


add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" width="1680" height="1188" font-family="IBM Plex Mono, Consolas, monospace">')
add(f'''<defs><marker id="a" viewBox="0 0 6 6" refX="3" refY="3" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L6 3 L0 6 Z" fill="{INK}"/></marker>
<pattern id="soil" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0 L0 3" stroke="{FAINT}" stroke-width="0.25"/></pattern></defs>''')
add(f'<style>.vis{{fill:none;stroke:{INK};stroke-width:0.22;stroke-linejoin:round}} .hid{{fill:none;stroke:{FAINT};stroke-width:0.14;stroke-dasharray:1 0.7}} .dim{{fill:none;stroke:{INK};stroke-width:0.15}} .lead{{fill:none;stroke:{INK};stroke-width:0.15}} .cut{{fill:none;stroke:{BLUE};stroke-width:0.35;stroke-dasharray:4 1 0.6 1}}</style>')
add('<rect width="420" height="297" fill="#fff"/>')
add(f'<rect x="8" y="8" width="404" height="281" fill="none" stroke="{INK}" stroke-width="0.5"/>')

# --- PLAN, 1:200 ---------------------------------------------------------------------------
CX = json.load(open(sys.argv[1].replace('views.json', 'origin.json')))['cx']
S1 = 200
wx = lambda x: 18 + (x + 2600) / S1  # world x to paper  # noqa: E731
py = lambda Y: 40 + (3812 - Y) / S1  # noqa: E731
plan_xf = lambda X, Y: (wx(X + CX), py(Y))  # noqa: E731
text(18, 22, 'PLAN', 3.4, 'start', 700)
text(18, 26.5, '1:200 · lids removed', 2.3, 'start', fill=FAINT)
path(views['plan']['hidden'], plan_xf, 'hid')
path(views['plan']['visible'], plan_xf, 'vis')
add(f'<path class="cut" d="M{wx(-2400):.2f} {py(0):.2f} L{wx(43600):.2f} {py(0):.2f}"/>')
for x in (wx(-2400), wx(43600)):
    add(f'<path d="M{x:.2f} {py(0):.2f} L{x:.2f} {py(0) + 4:.2f}" stroke="{BLUE}" stroke-width="0.35" marker-end="url(#a)"/>')
    text(x, py(0) + 7.5, 'A', 3, weight=700, fill=BLUE)
dim_h(wx(0), wx(41100), py(-3000) + 10, py(-600) + 1, '41 100')
dim_h(wx(1800), wx(27800), py(-3000) + 5, py(-3000) + 0.5, '26 000 (187 m³, 4.1 h at 7 L/s)')
dim_h(wx(28600), wx(39100), py(-3000) + 5, py(-1100) + 0.5, '10 500')
dim_v(py(3000), py(-3000), wx(3600), wx(1800) + 0.5, '6 000')
dim_v(py(1100), py(-1100), wx(39100) + 6, wx(39100) + 0.5, '2 200', left=False)
callout(1, wx(600), py(300), wx(600) + 5, 33)
callout(3, wx(14800), py(1500), wx(14800), 33)
callout(8, wx(22000), py(3700), wx(24000), 33)
callout(4, wx(33800), py(600), wx(33800), 33)
callout(7, wx(40500), py(300), wx(40500) + 6, 33)
callout(10, wx(33600), py(-2000), wx(31500), 91)

# --- SECTION A-A, 1:200 ---------------------------------------------------------------------
G = 114  # paper y of grade
wz = lambda z: G - z / S1  # world z to paper  # noqa: E731
sec_xf = lambda X, Y: (wx(X + CX), wz(Y - 1000))  # noqa: E731
text(18, 101, 'SECTION A–A', 3.4, 'start', 700)
text(18, 105.5, '1:200', 2.3, 'start', fill=FAINT)
add(f'<rect x="{wx(-1800):.2f}" y="{wz(0):.2f}" width="{wx(42700) - wx(-1800):.2f}" height="{wz(-3100) - wz(0):.2f}" fill="url(#soil)" opacity="0.5"/>')
add(f'<path d="M{wx(-2400):.2f} {wz(0):.2f} L{wx(43600):.2f} {wz(0):.2f}" stroke="{INK}" stroke-width="0.35"/>')
text(wx(-2400), wz(0) - 1.2, 'GRADE ±0', 2.1, 'start')
path(views['section']['hidden'], sec_xf, 'hid')
path(views['section']['visible'], sec_xf, 'vis')
add(f'<path d="M{wx(-1800):.2f} {wz(-1400):.2f} L{wx(42700):.2f} {wz(-1400):.2f}" stroke="{BLUE}" stroke-width="0.2" stroke-dasharray="1.6 1"/>')
text(wx(42700), wz(0) - 1.2, 'FROST 1.4 m (MONTRÉAL AVG), DASHED', 1.9, 'end', fill=BLUE)
dim_v(wz(0), wz(-1600), wx(-1800) - 3, wx(-1800), '1600')
dim_v(wz(0), wz(-2800), wx(42700) + 5, wx(39100), '2800', left=False)
dim_v(wz(-450), wz(-1650), wx(27800) + 3.5, wx(27800), '1200', left=False)
callout(2, wx(590), wz(-1300), wx(590) + 4, 135)
callout(3, wx(14800), wz(-1050), wx(14800), 135)
callout(5, wx(32300), wz(-1500), wx(32300), 135)
callout(6, wx(37650), wz(-1800), wx(37650), 135)
callout(9, wx(41900), wz(-1950), wx(41900) + 3, 135)

# --- DETAIL B: the carbon box, 1:50 -----------------------------------------------------------
X0, S2, B0 = 28300, 50, 22   # world x at the detail's left edge, scale, paper x
by0 = 170                    # paper y of grade in the detail
dxx = lambda x: B0 + (x - X0) / S2  # noqa: E731
dzz = lambda z: by0 - z / S2  # noqa: E731
dxf = lambda X, Y: (dxx(X + CX), dzz(Y - 1000))  # noqa: E731
W = (39400 - X0) / S2
inside = lambda x, y: B0 - 1 < x < B0 + W and by0 - 8 < y < by0 + 60  # noqa: E731
text(18, 152, 'DETAIL B — CARBON BOX', 3.4, 'start', 700)
text(18, 156.5, '1:50 · section A–A · insulated lids', 2.3, 'start', fill=FAINT)
add(f'<clipPath id="cb"><rect x="{B0 - 1}" y="{by0 - 8}" width="{W + 1}" height="70"/></clipPath><g clip-path="url(#cb)">')
path(views['section']['hidden'], dxf, 'hid', inside)
path(views['section']['visible'], dxf, 'vis', inside)
add('</g>')
add(f'<path d="M{dxx(X0):.2f} {dzz(0):.2f} L{dxx(39400):.2f} {dzz(0):.2f}" stroke="{INK}" stroke-width="0.35"/>')
for a, b, lab in ((28850, 31350, '2 500'), (31550, 34050, '2 500'), (34250, 36750, '2 500'), (36950, 38350, '1 400')):
    dim_h(dxx(a), dxx(b), dzz(-2800) + 5, dzz(-2600), lab)
dim_h(dxx(28600), dxx(39100), dzz(-2800) + 11, dzz(-2800), '10 500')
dim_v(dzz(-600), dzz(-2600), dxx(28600) - 4, dxx(28850), '2 000')
dim_v(dzz(-700), dzz(-2600), dxx(39100) + 4, dxx(38350), '1 900', left=False)
for x, lab in ((30100, 'C1'), (32800, 'C2'), (35500, 'C3')):
    text(dxx(x), dzz(-1500), f'BIOCHAR {lab}', 2.5, weight=600)
    text(dxx(x), dzz(-1500) + 3.4, '7.5 m³', 2.4, weight=600)
text(dxx(37650), dzz(-1650), 'GAC', 2.4, weight=600)
text(dxx(37650), dzz(-1650) + 3.4, '4 m³', 2.4, weight=600)

# --- parts list ------------------------------------------------------------------------------
PARTS = [
    ('1', 'Inlet control box', '1', 'Precast 1 200 × 1 200, Treat/Bypass board'),
    ('2', 'Stop logs and guides', '2 sets', 'Steel U-channel, timber boards 150'),
    ('3', 'Woodchip bed', '187 m³', '26 000 × 6 000 × 1 200, lined, 4.1 h'),
    ('4', 'Carbon box', '1', 'Precast 10 500 × 2 200 × 2 600, 200 walls'),
    ('5', 'Biochar cartridge', '3', '2 500 × 1 500 × 2 000, 7.5 m³, 54 min'),
    ('6', 'GAC polish cartridge', '1', '1 400 × 1 500 × 1 900, 4 m³, 9.5 min'),
    ('7', 'Outlet control box', '1', 'Precast, as 1; crest 500 below grade'),
    ('8', 'Bypass', '1', '200 pipe, about 27 L/s full at 0.5%'),
    ('9', 'Drainage pipe', '—', '150 pipe; perforated trench headers'),
    ('10', 'Logger, solar, sensors', '1', 'Flow, level, temperature'),
]
tx0, ty0 = 288, 22
text(tx0, ty0, 'PARTS', 3.4, 'start', 700)
add(f'<path d="M{tx0} {ty0 + 2.5} L{tx0 + 118} {ty0 + 2.5}" stroke="{INK}" stroke-width="0.3"/>')
for i, (n, name, qty, spec) in enumerate(PARTS):
    y = ty0 + 8 + i * 9
    add(f'<circle cx="{tx0 + 2.5}" cy="{y - 0.9}" r="2.2" fill="#fff" stroke="{INK}" stroke-width="0.25"/>')
    text(tx0 + 2.5, y, n, 2.2, weight=600)
    text(tx0 + 7, y, name, 2.5, 'start', 600)
    text(tx0 + 118, y, qty, 2.3, 'end')
    text(tx0 + 7, y + 3.4, spec, 2.1, 'start', fill='#44505f')
    add(f'<path d="M{tx0} {y + 5.4} L{tx0 + 118} {y + 5.4}" stroke="#d5dae1" stroke-width="0.2"/>')

notes = [
    'NOTES',
    '1. Dimensions in mm. Do not scale.',
    '2. Sizes from the NEPHRON report, revised',
    '   version 2 (25 Nov 2026): one design flow,',
    '   7 L/s from a 20 ha field, for every stage.',
    '3. Trench and boxes in a grassed strip at the',
    '   field edge; only pipes under cropped land.',
    '4. Stop logs hold water over the cartridges.',
    '5. Cartridges lift out through the lid hatches.',
]
for i, line in enumerate(notes):
    text(tx0, 125 + i * 4.6, line, 2.4 if i else 3.0, 'start', 700 if i == 0 else 400)

# --- title block ----------------------------------------------------------------------------
tb = [(288, 236, 124, 53)]
add(f'<rect x="288" y="236" width="124" height="53" fill="none" stroke="{INK}" stroke-width="0.5"/>')
for y in (252, 262, 272):
    add(f'<path d="M288 {y} L412 {y}" stroke="{INK}" stroke-width="0.25"/>')
add(f'<path d="M350 252 L350 289" stroke="{INK}" stroke-width="0.25"/>')
text(292, 243, 'NEPHRON', 5.2, 'start', 700)
text(292, 249, 'Atrazine treatment unit · general arrangement', 2.4, 'start')
cells = [
    (292, 256, 'PROJECT', 'WEC 2026 · Bio-Engineering'),
    (354, 256, 'RESULT', '1st place'),
    (292, 266, 'SCALE', '1:200 · detail 1:50 (A3)'),
    (354, 266, 'UNITS', 'mm'),
    (292, 276, 'DRAWING', 'NEP-GA-001 · rev B'),
    (354, 276, 'MODEL', 'nephron.step'),
]
for x, y, k, v in cells:
    text(x, y, k, 1.8, 'start', fill=FAINT)
    text(x, y + 3.6, v, 2.4, 'start')
add('</svg>')
open(OUT, 'w', encoding='utf-8').write('\n'.join(svg))
print('wrote', OUT)
