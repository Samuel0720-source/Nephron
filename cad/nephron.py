"""
NEPHRON, the treatment system as solid CAD (OpenCascade via build123d). Millimetres, z up, ground at z = 0,
flow along +x. Run:  python nephron.py <out_dir>
Writes:
  nephron.step                 the assembly, one named solid per part (opens in Fusion, Onshape, SolidWorks)
  mesh/<part>.mesh             each part tessellated, in the portfolio's TKM1 format
  views.json                   plan and section outlines (visible and hidden) for the drawing

Sizes come from the NEPHRON report, revised version 2 (Nov 25 2026), for one design flow of 7 L/s from a 20 ha field:
inlet control box; woodchip trench 26 x 6 x 1.2 m (187 m3, 4.1 h), media 0.45 to 1.65 m deep; precast carbon box
10.5 x 2.2 x 2.6 m with three 7.5 m3 biochar cartridges (54 min) and a 4 m3 GAC polish (9.5 min), 1.5 to 2.4 m deep;
outlet box with stop logs; 200 mm bypass; insulated, locked lids; flow, level and temperature sensors with a logger.
Wall thicknesses, box plans and pipe sizes are standard precast and drainage sizes.
"""
import json
import math
import os
import struct
import sys

import numpy as np
from build123d import Align, Box, Compound, Cylinder, Keep, Pos, Rot, Torus, export_step

OUT = sys.argv[1]
os.makedirs(f'{OUT}/mesh', exist_ok=True)
MIN = (Align.MIN, Align.MIN, Align.MIN)


def bx(x0, x1, y0, y1, z0, z1):
    return Pos(min(x0, x1), min(y0, y1), min(z0, z1)) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), align=MIN)


def rod_x(x0, x1, y, z, r):
    return Pos(min(x0, x1), y, z) * Rot(0, 90, 0) * Cylinder(r, abs(x1 - x0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def rod_y(y0, y1, x, z, r):
    return Pos(x, min(y0, y1), z) * Rot(-90, 0, 0) * Cylinder(r, abs(y1 - y0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def rod_z(z0, z1, x, y, r):
    return Pos(x, y, min(z0, z1)) * Cylinder(r, abs(z1 - z0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def pipe_x(x0, x1, y, z, od, wall):
    return rod_x(x0, x1, y, z, od / 2) - rod_x(x0 - 1, x1 + 1, y, z, od / 2 - wall)


def pipe_y(y0, y1, x, z, od, wall):
    return rod_y(y0, y1, x, z, od / 2) - rod_y(y0 - 1, y1 + 1, x, z, od / 2 - wall)


def pipe_z(z0, z1, x, y, od, wall):
    return rod_z(z0, z1, x, y, od / 2) - rod_z(z0 - 1, z1 + 1, x, y, od / 2 - wall)


def elbow(centre, bend_r, od, wall, start_deg):
    """A 90 degree elbow in the horizontal plane: a quarter of a hollow torus."""
    ring = Torus(bend_r, od / 2) - Torus(bend_r, od / 2 - wall)
    quarter = Rot(0, 0, start_deg) * bx(0, bend_r + od, 0, bend_r + od, -od, od)
    return Pos(*centre) * (ring & quarter)


def precast(x0, x1, y0, y1, z0, z1, wall, holes):
    """An open-topped precast box with round knock-outs where pipes pass through its walls."""
    body = bx(x0, x1, y0, y1, z0, z1) - bx(x0 + wall, x1 - wall, y0 + wall, y1 - wall, z0 + wall, z1 + 10)
    for axis, a, b, c, r in holes:  # ('x', y, z, x_at, r) cuts along x; ('y', x, z, y_at, r) along y
        if axis == 'x':
            body -= rod_x(c - wall - 20, c + wall + 20, a, b, r)
        else:
            body -= rod_y(c - wall - 20, c + wall + 20, a, b, r)
    return body


parts = {}  # name -> (solid, tone, apart, edges, title, role)


def part(name, solid, tone, apart, title, role, edges=True):
    solid.label = name
    parts[name] = (solid, tone, apart, edges, title, role)


# --- layout --------------------------------------------------------------------------------
INLET = (0, 1200)
TRENCH = (1800, 27800)
TW = 3000
VAULT = (28600, 39100)
VW = 1100
OUTLET = (39900, 41100)
OC = (OUTLET[0] + OUTLET[1]) / 2
Z_HEAD = -1560               # trench headers, inside the bed
Z_IN = -1600                 # tile-drain invert
OD, WALL = 170, 10           # 150 mm drainage pipe
OD_B = 225                   # 200 mm bypass

# 1. inlet control box: 1.2 m square precast, 150 mm walls, knock-outs for drain in, trench feed and bypass
inlet = precast(*INLET, -600, 600, -2100, -150, 150, [
    ('x', 0, Z_IN, INLET[0], OD / 2 + 10),
    ('x', 0, Z_HEAD, INLET[1], OD / 2 + 10),
    ('y', 600, -1500, 600, OD_B / 2 + 10),
])
part('inlet-box', inlet, 'shell', [-1800, 0, 0], 'Inlet control box', '1.2 m precast, 150 mm walls. Its Treat/Bypass board sends water through the unit in season and round it off-season; flow above 7 L/s spills to the bypass.')
guides = bx(530, 610, -450, -370, -1950, -300) + bx(530, 610, 370, 450, -1950, -300)
guides -= bx(550, 590, -430, -380, -1960, -290) + bx(550, 590, 380, 430, -1960, -290)  # U-channels
logs_in = None
for k in range(3):
    log = bx(555, 585, -425, 425, -1950 + k * 160, -1950 + k * 160 + 150)
    logs_in = log if logs_in is None else logs_in + log
part('inlet-logs', guides + logs_in, 0x9a7048, [-1800, 0, 2600], 'Inlet stop logs', 'Steel guide channels and boards: the seasonal switch that sends water through the unit in summer and round it in winter.')
lid = bx(INLET[0] - 50, INLET[1] + 50, -650, 650, -150, 0) - rod_z(-200, 50, 600, 0, 300)
lid += rod_z(-40, 0, 600, 0, 320) - rod_z(-50, 10, 600, 0, 40)  # hatch cover with a lifting hole
part('inlet-lid', lid, 'mid', [-1800, 0, 4200], 'Inlet lid', 'Insulated precast lid with a 600 mm hatch, locked, at grade.')

# 2. pipes: hollow, 150 mm
pipes = pipe_x(-1800, INLET[0] + 150, 0, Z_IN, OD, WALL)
pipes += pipe_x(INLET[1] - 150, TRENCH[0] + 300, 0, Z_HEAD, OD, WALL)
pipes += pipe_x(TRENCH[1] - 300, VAULT[0] + 200, 0, Z_HEAD, OD, WALL)
pipes += pipe_x(VAULT[1] - 200, OUTLET[0] + 150, 0, Z_IN - 300, OD, WALL)
pipes += pipe_x(OUTLET[1] - 150, 42700, 0, -1950, OD, WALL)
# perforated distribution header across the trench inlet, and a collection header across its outlet
for x, z in ((TRENCH[0] + 300, Z_HEAD), (TRENCH[1] - 300, Z_HEAD)):
    header = pipe_y(-TW + 300, TW - 300, x, z, OD, WALL)
    for k in range(-12, 13):
        header -= rod_z(z - 100, z, x, k * 210, 9)  # a row of 18 mm holes along the underside
    pipes += header
part('pipes', pipes, 'slate', [0, 0, 0], 'Drainage pipe, 150 mm', 'Tile drain in at 1.6 m, through the perforated trench headers and the carbon box, out to the ditch. Gravity all the way.')

# 3. bypass, 200 mm, round the trench and the carbon box, with long-radius elbows
R = 450
by = pipe_y(600 - 150, TW + 700 - R, 600, -1500, OD_B, 12)
by += elbow((600 + R, TW + 700 - R, -1500), R, OD_B, 12, 90)
by += pipe_x(600 + R, OC - R, TW + 700, -1500, OD_B, 12)
by += elbow((OC - R, TW + 700 - R, -1500), R, OD_B, 12, 0)
by += pipe_y(600 - 150, TW + 700 - R, OC, -1500, OD_B, 12)
part('bypass', by, 'mid', [0, 2200, 0], 'Measured bypass, 200 mm', 'Carries flow above 7 L/s, and all off-season flow, round the trench and the carbon box: about 27 L/s flowing full, more than the 23 L/s peak.')

# 4. woodchip trench
liner = bx(TRENCH[0], TRENCH[1], -TW, TW, -1690, -350) - bx(TRENCH[0] + 40, TRENCH[1] - 40, -TW + 40, TW - 40, -1650, -250)
part('liner', liner, 'slate', [0, 0, -1200], 'Trench liner', 'Holds the water in the bed for its 4.1 h retention at 7 L/s.')
rng = np.random.default_rng(7)
chips = bx(TRENCH[0] + 40, TRENCH[1] - 40, -TW + 40, TW - 40, -1650, -450)
part('chips', chips, 0xa8763f, [0, 0, 0], 'Woodchip bed, 187 m³', 'Weathered hardwood chips, 26 × 6 × 1.2 m, 0.45 to 1.65 m deep. Removes nitrate, which helps the biology downstream, and sorbs some atrazine: 5 to 40% over a season.', edges=True)

# 5. carbon box: 7 x 2.2 m precast vault, 200 mm walls, ledges for the cartridges, three lid sections with hatches
vault = precast(*VAULT, -VW, VW, -2800, -200, 200, [
    ('x', 0, Z_IN - 100, VAULT[0], OD / 2 + 10),
    ('x', 0, Z_IN - 300, VAULT[1], OD / 2 + 10),
])
BAFFLES = (VAULT[0] + 2850, VAULT[0] + 5550, VAULT[0] + 8250)
for x in BAFFLES:  # baffles between cartridges, open underneath for flow
    vault += bx(x - 40, x + 40, -VW + 200, VW - 200, -2400, -500)
part('vault', vault, 'shell', [0, 0, 0], 'Carbon box', 'Precast vault, 10.5 × 2.2 × 2.6 m, 200 mm walls, holding 22.5 m³ of biochar and 4 m³ of GAC in four lift-out cartridges.')
lids = None
cuts = [VAULT[0], *BAFFLES, VAULT[1]]
for a, b in zip(cuts, cuts[1:]):
    slab = bx(a + 10, b - 10, -VW, VW, -200, 0) - bx((a + b) / 2 - 350, (a + b) / 2 + 350, -350, 350, -250, 50)
    slab += bx((a + b) / 2 - 380, (a + b) / 2 + 380, -380, 380, -40, 0) - rod_z(-50, 10, (a + b) / 2, 0, 40)
    lids = slab if lids is None else lids + slab
part('lids', lids, 'mid', [0, 0, 5600], 'Carbon box lids', 'Four insulated precast sections, one over each cartridge, each with a 700 mm hatch.')

CARTS = [
    (VAULT[0] + 250, VAULT[0] + 2750, -600, 'biochar-1', 4100, 'Lead biochar cartridge', '7.5 m³ of wood biochar in a 60 mm square-tube frame with a perforated base and four lifting rings. Swapped when the twin predicts removal below 90%, or when DEA shows after cartridge 2: about 2.3 times a season.', 0x2a2725),
    (VAULT[0] + 2950, VAULT[0] + 5450, -600, 'biochar-2', 3600, 'Second biochar cartridge', '7.5 m³. Moves up to lead when the first is swapped.', 0x2a2725),
    (VAULT[0] + 5650, VAULT[0] + 8150, -600, 'biochar-3', 3100, 'Third biochar cartridge', '7.5 m³. Fresh media goes in last. The three give 54 min of contact at 7 L/s.', 0x2a2725),
    (VAULT[0] + 8350, VAULT[0] + 9750, -700, 'gac', 2600, 'GAC polish cartridge', '4 m³ of granular activated carbon, 9.5 min of contact: about two-thirds of what is left.', 0x15181c),
]
for x0, x1, top, name, lift, title, role, media_tone in CARTS:
    y0, y1, z0, t = -750, 750, -2600, 60
    frame = None

    def add(s):
        global frame
        frame = s if frame is None else frame + s

    for x in (x0, x1 - t):
        for y in (y0, y1 - t):
            add(bx(x, x + t, y, y + t, z0, top) - bx(x + 5, x + t - 5, y + 5, y + t - 5, z0 - 1, top + 1))  # hollow posts
    for z in (z0, top - t):
        add(bx(x0, x1, y0, y0 + t, z, z + t) - bx(x0 - 1, x1 + 1, y0 + 5, y0 + t - 5, z + 5, z + t - 5))
        add(bx(x0, x1, y1 - t, y1, z, z + t) - bx(x0 - 1, x1 + 1, y1 - t + 5, y1 - 5, z + 5, z + t - 5))
        add(bx(x0, x0 + t, y0 + t, y1 - t, z, z + t) - bx(x0 + 5, x0 + t - 5, y0 + t - 1, y1 - t + 1, z + 5, z + t - 5))
        add(bx(x1 - t, x1, y0 + t, y1 - t, z, z + t) - bx(x1 - t + 5, x1 - 5, y0 + t - 1, y1 - t + 1, z + 5, z + t - 5))
    plate = bx(x0 + t, x1 - t, y0 + t, y1 - t, z0, z0 + 10)
    for i in range(int((x1 - x0 - 2 * t) // 300)):
        for j in range(4):
            plate -= rod_z(z0 - 5, z0 + 15, x0 + t + 150 + i * 300, y0 + t + 170 + j * 340, 40)
    add(plate)
    for x in (x0 + 150, x1 - 150):
        for y in (y0 + 150, y1 - 150):
            add(bx(x - 10, x + 10, y - 40, y + 40, top, top + 90))
            add(Pos(x, y, top + 130) * Rot(0, 90, 0) * Torus(45, 10))
    media = bx(x0 + t, x1 - t, y0 + t, y1 - t, z0 + 10, top - t - 40)
    part(f'{name}-frame', frame, 'steel', [0, 0, lift], title, role)
    part(f'{name}-media', media, media_tone, [0, 0, lift], title + ' media', role)

# 6. outlet control box with stop logs up to 500 mm below grade, so the cartridges stay under water
outlet = precast(*OUTLET, -600, 600, -2100, -150, 150, [
    ('x', 0, Z_IN - 300, OUTLET[0], OD / 2 + 10),
    ('x', 0, -1950, OUTLET[1], OD / 2 + 10),
    ('y', 0, -1500, 600, OD_B / 2 + 10),
])
part('outlet-box', outlet, 'shell', [1800, 0, 0], 'Outlet control box', '1.2 m precast, out to the ditch.')
og = Pos(OUTLET[0], 0, 0) * (bx(530, 610, -450, -370, -1950, -300) + bx(530, 610, 370, 450, -1950, -300) - bx(550, 590, -430, -380, -1960, -290) - bx(550, 590, 380, 430, -1960, -290))
ologs = og
for k in range(10):
    ologs += bx(OUTLET[0] + 555, OUTLET[0] + 585, -425, 425, -1950 + k * 145, -1950 + k * 145 + 140)
part('outlet-logs', ologs, 0x9a7048, [1800, 0, 2600], 'Outlet stop logs', 'Ten boards up to 0.5 m below grade: they hold the water over the cartridges so the carbon and its biofilm never dry out.')
olid = Pos(OUTLET[0], 0, 0) * (bx(-50, 1250, -650, 650, -150, 0) - rod_z(-200, 50, 600, 0, 300) + rod_z(-40, 0, 600, 0, 320) - rod_z(-50, 10, 600, 0, 40))
part('outlet-lid', olid, 'mid', [1800, 0, 4200], 'Outlet lid', 'Insulated precast lid with a 600 mm hatch, locked, at grade.')

# 7. sensors and the logger
well_x = (TRENCH[0] + TRENCH[1]) / 2
sens = rod_x(INLET[1] - 330, INLET[1] - 160, 0, Z_IN, 120) - rod_x(INLET[1] - 340, INLET[1] - 150, 0, Z_IN, OD / 2 - WALL)  # inline flow meter
sens += pipe_z(-1950, 250, well_x, 0, 110, 6) + rod_z(250, 330, well_x, 0, 75)  # observation well with a cap
sens += rod_z(-2300, -250, BAFFLES[1], VW - 400, 22) + rod_z(-2400, -2300, BAFFLES[1], VW - 400, 35)  # level and temperature
sens += rod_z(-1900, -250, OUTLET[0] + 300, 0, 22) + rod_z(-2000, -1900, OUTLET[0] + 300, 0, 35)
part('sensors', sens, 'blue', [0, 0, 1400], 'Sensors', 'Inline flow meter at the inlet, a level well in the trench, level and temperature probes in the carbon box and outlet. Grab samples recalibrate the twin.')
px, py = VAULT[0] + 5000, -VW - 900
post = bx(px - 50, px + 50, py - 50, py + 50, -900, 2200) - bx(px - 44, px + 44, py - 44, py + 44, -901, 2201)
post += bx(px - 200, px + 200, py + 50, py + 250, 1100, 1600)
post += Pos(px, py - 60, 2320) * Rot(-35, 0, 0) * Box(700, 500, 35)
part('logger', post, 'steel', [0, -1600, 0], 'Logger and telemetry', 'Solar-powered logger on a post, sending readings to the digital twin.')

# --- STEP assembly --------------------------------------------------------------------------
assembly = Compound(label='NEPHRON', children=[p[0] for p in parts.values()])
export_step(assembly, f'{OUT}/nephron.step')

# --- meshes for the portfolio -------------------------------------------------------------------
def write_mesh(name, solid, tol):
    # curved detail (holes, rings) is coarser on the cartridge frames: they are seen small, and every triangle loads
    verts, tris = solid.tessellate(tol, 0.7 if 'frame' in name else 0.3)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], np.float32)
    f = np.array(tris, np.uint32)
    lo, hi = v.min(0), v.max(0)
    span = np.where(hi - lo > 0, hi - lo, 1)
    packed = np.round((v - lo) / span * 65535).astype(np.uint16)
    with open(f'{OUT}/mesh/nephron-{name}.mesh', 'wb') as out:
        out.write(b'TKM1')
        out.write(struct.pack('<II', len(v), len(f)))
        out.write(struct.pack('<3f', *lo))
        out.write(struct.pack('<3f', *hi))
        out.write(packed.tobytes())
        if (len(v) * 6) % 4:
            out.write(b'\0\0')
        out.write(f.astype(np.uint16 if len(v) <= 65535 else np.uint32).tobytes())
    return len(v), len(f)


manifest = []
for name, (solid, tone, apart, edges, title, role) in parts.items():
    nv, nf = write_mesh(name, solid, 8)
    vol = solid.volume / 1e9
    manifest.append({'name': name, 'tone': tone, 'apart': apart, 'edges': edges, 'title': title, 'role': role, 'volume_m3': round(vol, 3), 'tris': nf})
    print(f'{name:18s} {nf:7d} tris  {vol:8.3f} m3')
json.dump(manifest, open(f'{OUT}/manifest.json', 'w'), indent=1)
print('step', os.path.getsize(f'{OUT}/nephron.step') // 1024, 'KB')


# --- drawing views: plan, and section A-A along the flow --------------------------------------
from build123d import GeomType, Plane  # noqa: E402


def outline(shape, origin, up, look):
    visible, hidden = shape.project_to_viewport(origin, up, look)

    def pts(edges):
        out = []
        for e in edges:
            n = 2 if e.geom_type == GeomType.LINE else 18
            out.append([[round(p.X, 1), round(p.Y, 1)] for p in (e.position_at(i / (n - 1)) for i in range(n))])
        return out

    return {'visible': pts(visible), 'hidden': pts(hidden)}


plan_parts = ['inlet-box', 'pipes', 'bypass', 'liner', 'vault', 'outlet-box', 'logger', 'biochar-1-media', 'biochar-2-media', 'biochar-3-media', 'gac-media']
plan = Compound(children=[parts[n][0] for n in plan_parts])
cx = (-1800 + 42700) / 2
json.dump({'cx': cx}, open(f'{OUT}/origin.json', 'w'))
views = {'plan': outline(plan, (cx, 0, 50000), (0, 1, 0), (cx, 0, 0))}
section_parts = ['inlet-box', 'inlet-logs', 'inlet-lid', 'pipes', 'liner', 'chips', 'vault', 'lids', 'biochar-1-media', 'biochar-2-media', 'biochar-3-media', 'gac-media', 'biochar-1-frame', 'biochar-2-frame', 'biochar-3-frame', 'gac-frame', 'outlet-box', 'outlet-logs', 'outlet-lid']
cut = Compound(children=[parts[n][0] for n in section_parts]).split(Plane.XZ, keep=Keep.BOTTOM)
if isinstance(cut, (list, tuple)):
    cut = Compound(children=list(cut))
views['section'] = outline(cut, (cx, -50000, -1000), (0, 0, 1), (cx, 0, -1000))
json.dump(views, open(f'{OUT}/views.json', 'w'))
for k, v in views.items():
    allp = [p for poly in v['visible'] for p in poly]
    xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
    print(k, len(v['visible']), 'visible', len(v['hidden']), 'hidden', 'x', min(xs), max(xs), 'y', min(ys), max(ys))
