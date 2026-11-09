#!/usr/bin/env python3
"""
Go/No-Go — building-line envelope + basic massing option, per israel-massing-rules.

    python3 stages/3-alternatives/scripts/massing.py config.json out.json

config.json:
  parcel          [[lon,lat],...]   Snapland parcel_geometry ring (search_cadastral_local_id)
  building        [[lon,lat],...]   existing footprint (optional; maps only)
  front_edges     [i,...] | null    simplified-edge indices facing a street (corner lot = 2)
  street_point    [lon,lat]         used when front_edges is null: nearest edge = front
  setbacks        {"front":4,"rear":5,"side":3}   from build-rights; studio defaults 5/6/4 only if missing
  floors          typical floors allowed (incl. ground)
  roof_floors     partial roof floors allowed (e.g. Rova "+2 ק' גג"); 0 if none
  roof_setback    one-sided setback for roof floors (rules §7), default 4
  rights_gross    numeric gross cap from rights, or null when rights are envelope-based ("ראה הערה")
  roof_coverage   share of envelope used per roof floor when computing the envelope gross (default 0.65)
  unit_target     target gross unit m² (rules §9 handle), default 70
  lot_area_for_rights  m² denominator for coverage/FAR (registered area)
  max_len / max_wid / min_wid / floor_h   rules §4/§6 defaults 28 / 15 / 7 / 3.0

The rules in israel-massing-rules win over this file. Re-read them before each report;
if a rule changed (e.g. max length), pass the new value here rather than editing the logic.
"""
import json, math, sys
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import affinity


def proj(ring):
    lat0 = sum(p[1] for p in ring) / len(ring); lon0 = sum(p[0] for p in ring) / len(ring)
    kx = 111320 * math.cos(math.radians(lat0)); ky = 110574
    to_xy = lambda c: [((x - lon0) * kx, (y - lat0) * ky) for x, y in c]
    to_ll = lambda c: [(x / kx + lon0, y / ky + lat0) for x, y in c]
    return to_xy, to_ll


def edges_of(pxy, tol=0.5):
    simp = Polygon(pxy).simplify(tol, preserve_topology=True)   # GIS noise -> real edges (rules §1)
    pts = list(simp.exterior.coords)
    return [LineString([pts[i], pts[i + 1]]) for i in range(len(pts) - 1)]


def classify(E, front_idx):
    n = len(E); typ = ['side'] * n
    for i in front_idx: typ[i] = 'front'
    fu = unary_union([E[i] for i in front_idx])
    def ang(l):
        (x0, y0), (x1, y1) = l.coords[0], l.coords[-1]; return math.atan2(y1 - y0, x1 - x0)
    fa = ang(E[front_idx[0]])
    cand = [i for i in range(n) if typ[i] != 'front' and E[i].length >= 2]
    if cand:   # rear = most opposite and farthest from the front
        typ[max(cand, key=lambda i: E[i].distance(fu) + 5 * abs(math.cos(ang(E[i]) - fa)))] = 'rear'
    for i in range(n):   # chamfer < 2 m inherits its neighbour (rules §1)
        if E[i].length < 2 and typ[i] == 'side':
            j = (i - 1) % n if E[(i - 1) % n].length >= E[(i + 1) % n].length else (i + 1) % n
            typ[i] = typ[j]
    return typ


def main(cfg):
    to_xy, to_ll = proj(cfg['parcel'])
    poly = Polygon(to_xy(cfg['parcel'])).buffer(0)
    E = edges_of(list(poly.exterior.coords))
    if cfg.get('front_edges') is not None:
        fi = cfg['front_edges']
    else:
        sp = Point(to_xy([cfg['street_point']])[0]); fi = [min(range(len(E)), key=lambda i: E[i].distance(sp))]
    typ = classify(E, fi)
    sb = cfg['setbacks']
    cut = unary_union([E[i].buffer(sb[t], cap_style=2) for i, t in enumerate(typ)])
    env = poly.difference(cut)
    if env.geom_type != 'Polygon': env = max(env.geoms, key=lambda g: g.area)

    # inscribed working rectangle, axis parallel to the street (±12° for skewed lots). Never a bbox.
    (x0, y0), (x1, y1) = E[fi[0]].coords[0], E[fi[0]].coords[-1]
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0)); c = poly.centroid
    Wmax, Lmax, Wmin = cfg.get('max_wid', 15), cfg.get('max_len', 28), cfg.get('min_wid', 7)
    best = None
    for rot in [r * 0.5 for r in range(-24, 25)]:
        er = affinity.rotate(env, -(ang + rot), origin=c); mnx, mny, mxx, mxy = er.bounds; eb = er.buffer(0.01)
        for W in [Wmax - 0.5 * k for k in range(int((Wmax - Wmin) / 0.5) + 1)]:
            for L in [Lmax - 0.5 * k for k in range(int((Lmax - W) / 0.5) + 1)]:
                for bw, bl in ((W, L), (L, W)):
                    if best and bw * bl <= best[0]: continue
                    hit = None; dx = 0
                    while dx <= mxx - mnx - bw and not hit:
                        dy = 0
                        while dy <= mxy - mny - bl:
                            bb = box(mnx + dx, mny + dy, mnx + dx + bw, mny + dy + bl)
                            if eb.contains(bb): hit = bb; break
                            dy += 0.25
                        dx += 0.25
                    if hit: best = (bw * bl, rot, hit)
    if not best:
        return {'status': 'red', 'reason': "רוחב אפקטיבי אחרי קווי הבניין קטן מ-7 מ' — אין בינוי",
                'envelope_area': round(env.area, 1)}
    _, rot, b = best; R = ang + rot
    back = lambda g: affinity.rotate(g, R, origin=c)
    X0, Y0, X1, Y1 = b.bounds; bw, bl = X1 - X0, Y1 - Y0; fp = bw * bl
    long_y = bl >= bw; cx, cy = b.centroid.x, b.centroid.y
    floors = cfg.get('floors', 6); roofs = cfg.get('roof_floors', 0); H = cfg.get('floor_h', 3.0)
    tf = floors + roofs
    core_pct = 0.11 if tf <= 9 else (0.12 if tf <= 19 else 0.13)            # rules §8
    core_a = core_pct * fp; cs = max(math.sqrt(core_a), 2.5) / 2
    core = box(cx - cs, cy - cs, cx + cs, cy + cs)
    n = max(2, min(6, round((fp - core_a) / cfg.get('unit_target', 70))))  # rules §9

    def layout(clip=None):
        if n == 2:   # split across the long axis, each unit full depth
            parts = [box(X0, Y0, X1, cy), box(X0, cy, X1, Y1)] if long_y else [box(X0, Y0, cx, Y1), box(cx, Y0, X1, Y1)]
        else:        # two back-to-back rows along the long axis: ceil(n/2) vs floor(n/2)
            parts = []
            for a, bq, k in (((X0, cx) if long_y else (Y0, cy)) + (math.ceil(n / 2),),
                             ((cx, X1) if long_y else (cy, Y1)) + (n // 2,)):
                st = (bl if long_y else bw) / k
                for i in range(k):
                    parts.append(box(a, Y0 + i * st, bq, Y0 + (i + 1) * st) if long_y
                                 else box(X0 + i * st, a, X0 + (i + 1) * st, bq))
        U = []
        for r in parts:
            if clip is not None: r = r.intersection(clip)
            if r.is_empty or r.area < 1: continue
            if r.difference(core).area >= 55: U.append(r)   # < 55 m² deleted (rules §7, §9)
        return U

    typU = layout()
    pr = affinity.rotate(poly, -R, origin=c); v = (cx - pr.centroid.x, cy - pr.centroid.y)
    s = cfg.get('roof_setback', 4)
    if abs(v[1]) >= abs(v[0]): clip = box(X0, Y0, X1, Y1 - s) if v[1] > 0 else box(X0, Y0 + s, X1, Y1)
    else: clip = box(X0, Y0, X1 - s, Y1) if v[0] > 0 else box(X0 + s, Y0, X1, Y1)
    topU = layout(clip) if roofs else []
    if roofs and not topU: roofs = 0                                          # whole floor cancelled
    roof_area = sum(u.area for u in topU)
    gross = floors * fp + roofs * roof_area
    blocking = 'קווי הבניין — מידות המעטפת'
    cap = cfg.get('rights_gross')
    if cap and gross > cap:
        while floors > 1 and floors * fp + roofs * roof_area > cap: floors -= 1   # round down, never exceed
        gross = floors * fp + roofs * roof_area; blocking = 'זכויות (מ"ר)'
    elif max(bw, bl) >= Lmax - 0.01:
        blocking = f"אורך מבנה מרבי {Lmax} מ' (כלל הסטודיו)"
    units = floors * len(typU) + roofs * len(topU)
    lot = cfg.get('lot_area_for_rights') or poly.area
    env_gross = env.area * cfg.get('floors', 6) + env.area * cfg.get('roof_coverage', 0.65) * cfg.get('roof_floors', 0)
    rect = poly.area / poly.minimum_rotated_rectangle.area
    LL = lambda g: [list(p) for p in to_ll(list(g.exterior.coords))]
    lab = lambda u: list(to_ll([list(back(Point(u.centroid.x + (0.9 if u.centroid.x > cx else -0.9), u.centroid.y)).coords)[0]])[0])
    return {
        'status': 'green' if rect >= 0.85 else 'yellow', 'rectangularity': round(rect, 2),
        'parcel_area': round(poly.area, 1), 'envelope_area': round(env.area, 1), 'envelope_gross': round(env_gross),
        'edges': [{'i': i, 'type': t, 'length': round(E[i].length, 1), 'setback': sb[t]} for i, t in enumerate(typ)],
        'building': {'w': round(min(bw, bl), 1), 'l': round(max(bw, bl), 1), 'footprint': round(fp, 1),
                     'coverage': round(fp / lot, 3), 'floors': floors, 'roof_floors': roofs,
                     'height': (floors + roofs) * H, 'core_pct': core_pct, 'core': round(core_a, 1),
                     'units_per_floor': len(typU), 'roof_units': len(topU),
                     'unit_areas': [round(u.difference(core).area) for u in typU],
                     'roof_unit_areas': [round(u.difference(core).area) for u in topU],
                     'units': units, 'gross': round(gross), 'far': round(gross / lot, 2),
                     'density_per_dunam': round(units / (lot / 1000), 1),
                     'util_of_envelope': round(gross / env_gross, 3) if env_gross else None,
                     'blocking': blocking},
        'geo': {'parcel': cfg['parcel'], 'existing': cfg.get('building'), 'envelope': LL(env),
                'mass': LL(back(b)), 'core': LL(back(core)),
                'units': [{'a': round(u.difference(core).area), 'poly': LL(back(u)), 'label': lab(u)} for u in typU],
                'parcel_edges': [{'type': t, 'length': round(E[i].length, 1), 'setback': sb[t],
                                  'line': [list(p) for p in to_ll(list(E[i].coords))]} for i, t in enumerate(typ)]}}


if __name__ == '__main__':
    res = main(json.load(open(sys.argv[1])))
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'geo'}, ensure_ascii=False, indent=1))
