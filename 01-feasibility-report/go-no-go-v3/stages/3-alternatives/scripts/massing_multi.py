#!/usr/bin/env python3
"""Multi-building basic alternative (israel-massing-rules §4/§5/§9/§10).
massing.py places ONE bar; on lots above ~1 dunam that under-reports the envelope (Bruria 15: 1 bar = 43% of rights,
3 bars = 97%). This script packs up to `max_bld` bars (W 7–15 × L ≤ max_len) in the typed envelope with ≥ spacing m
between them, then sets floors = min(cap, floor(rights / Σ footprint)) — rounded DOWN, never above rights.
    python3 stages/3-alternatives/scripts/massing_multi.py cfg.json massing.json
cfg: same keys as massing.py + floors (cap), rights_gross, unit_target, spacing (12), max_bld (4), trials (400).
Output: buildings[] with geo (mass/core/units), floors, gross, util_of_rights, blocking, floors_for_rights,
fp_needed_at_cap and geo (parcel, envelope, parcel_edges, existing) — readable by maps.py."""
import json, math, random, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from shapely import affinity
from shapely.prepared import prep
from massing import proj, edges_of, classify


def envelope(cfg):
    to_xy, to_ll = proj(cfg['parcel'])
    poly = Polygon(to_xy(cfg['parcel'])).buffer(0)
    E = edges_of(list(poly.exterior.coords)); fi = cfg['front_edges']; typ = classify(E, fi); sb = cfg['setbacks']
    cut = unary_union([E[i].buffer(sb[t], cap_style=2) for i, t in enumerate(typ)])
    env = poly.difference(cut)
    if env.geom_type != 'Polygon': env = max(env.geoms, key=lambda g: g.area)
    (x0, y0), (x1, y1) = E[fi[0]].coords[0], E[fi[0]].coords[-1]
    return poly, env, E, typ, sb, math.degrees(math.atan2(y1 - y0, x1 - x0)), to_xy, to_ll


def pack(env, ang, cfg):
    Wmax, Lmax, Wmin = cfg.get('max_wid', 15), cfg['max_len'], cfg.get('min_wid', 7)
    sp = cfg.get('spacing', 12.0); nmax = cfg.get('max_bld', 4); trials = cfg.get('trials', 400)
    best = None
    for da in (0.0, 2.0, -2.0):
        a = ang + da
        R = affinity.rotate(env, -a, origin=(0, 0)); pr = prep(R.buffer(0.01)); mnx, mny, mxx, mxy = R.bounds
        cands = []
        for W in range(int(Wmax), int(Wmin) - 1, -1):
            for L in sorted({Lmax, Lmax - 3, Lmax - 6}):
                if L < W: continue
                for dx, dy in ((L, W), (W, L)):
                    x = mnx
                    while x + dx <= mxx:
                        y = mny
                        while y + dy <= mxy:
                            b = box(x, y, x + dx, y + dy)
                            if pr.contains(b) and (b.area * 0.87) / 2 >= 55: cands.append(b)
                            y += 1
                        x += 1
        random.seed(7)
        cands.sort(key=lambda b: -b.area)
        for t in range(trials):
            order = cands if t == 0 else random.sample(cands, len(cands))
            ch = []
            for c in order:
                if all(c.distance(o) >= sp for o in ch): ch.append(c)
                if len(ch) == nmax: break
            fp = sum(c.area for c in ch)
            if best is None or fp > best[0] + 1e-6:
                best = (fp, a, [affinity.rotate(c, a, origin=(0, 0)) for c in ch])
    return best


def units_layout(b, ang, floors, ut, to_ll):
    core_pct = 0.11 if floors <= 9 else (0.12 if floors <= 19 else 0.13)
    br = affinity.rotate(b, -ang, origin=b.centroid); X0, Y0, X1, Y1 = br.bounds; bw, bl = X1 - X0, Y1 - Y0; fp = bw * bl
    long_y = bl >= bw; cx, cy = br.centroid.x, br.centroid.y
    core_a = core_pct * fp; cs = max(math.sqrt(core_a), 2.5) / 2; core = box(cx - cs, cy - cs, cx + cs, cy + cs)
    n = max(2, min(6, round((fp - core_a) / ut)))
    if n == 2:
        parts = [box(X0, Y0, X1, cy), box(X0, cy, X1, Y1)] if long_y else [box(X0, Y0, cx, Y1), box(cx, Y0, X1, Y1)]
    else:
        parts = []
        for a_, b_, k in (((X0, cx) if long_y else (Y0, cy)) + (math.ceil(n / 2),), ((cx, X1) if long_y else (cy, Y1)) + (n // 2,)):
            stp = (bl if long_y else bw) / k
            for i in range(k):
                parts.append(box(a_, Y0 + i * stp, b_, Y0 + (i + 1) * stp) if long_y else box(X0 + i * stp, a_, X0 + (i + 1) * stp, b_))
    U = [u for u in parts if u.difference(core).area >= 55]
    back = lambda g: affinity.rotate(g, ang, origin=b.centroid)
    LL = lambda g: [list(p) for p in to_ll(list(g.exterior.coords))]
    return dict(w=round(min(bw, bl), 1), l=round(max(bw, bl), 1), footprint=round(fp, 1), core=round(core_a, 1),
                core_pct=core_pct, units_per_floor=len(U), unit_areas=[round(u.difference(core).area) for u in U],
                geo=dict(mass=LL(back(br)), core=LL(back(core)),
                         units=[dict(a=round(u.difference(core).area), poly=LL(back(u)),
                                     label=list(to_ll([list(back(Point(u.centroid.x, u.centroid.y)).coords)[0]])[0])) for u in U]))


def run(cfg):
    poly, env, E, typ, sb, ang, to_xy, to_ll = envelope(cfg)
    fp, a, bars = pack(env, ang, cfg)
    cap, rights, lot = cfg['floors'], cfg['rights_gross'], cfg['lot_area_for_rights']
    floors = min(cap, int(rights // fp)) if fp else 0
    blds = [units_layout(b, a, floors, cfg.get('unit_target', 100), to_ll) for b in bars]
    units = floors * sum(b['units_per_floor'] for b in blds)
    gross = floors * fp; fh = cfg.get('floor_h', 3.0)
    gaps = [round(bars[i].distance(bars[j]), 1) for i in range(len(bars)) for j in range(i + 1, len(bars))]
    slender = [round(floors * fh / b['w'], 2) for b in blds]
    LLp = lambda g: [list(p) for p in to_ll(list(g.exterior.coords))]
    return dict(n_buildings=len(blds), buildings=blds, floors=floors, height=floors * fh, footprint_total=round(fp, 1),
                gross=round(gross), far=round(gross / lot, 2), util_of_rights=round(gross / rights, 3),
                coverage=round(fp / lot, 3), units=units, density_per_dunam=round(units / (lot / 1000), 1),
                blocking='זכויות (מ"ר)' if int(rights // fp) < cap else f'תקרת קומות ({cap})',
                floors_for_rights=round(rights / fp, 2), fp_needed_at_cap=round(rights / cap), min_gap=min(gaps) if gaps else None,
                slenderness_warn=[s for s in slender if s > 5], envelope_area=round(env.area, 1),
                edges=[dict(i=i, type=t, length=round(E[i].length, 1), setback=sb[t]) for i, t in enumerate(typ)],
                geo=dict(parcel=cfg['parcel'], existing=cfg.get('existing') or ([cfg['building']] if cfg.get('building') else []),
                         envelope=LLp(env), parcel_edges=[dict(type=t, length=round(E[i].length, 1), setback=sb[t],
                         line=[list(p) for p in to_ll(list(E[i].coords))]) for i, t in enumerate(typ)]))


if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1])); out = run(cfg)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k not in ('geo', 'buildings', 'edges')}, ensure_ascii=False))
