#!/usr/bin/env python3
"""Go/No-Go — building-line envelope only (no massing alternative in this version).

    python3 envelope.py config.json out.json

config.json:
  parcel          [[lon,lat],...]   Snapland parcel_geometry ring (search_cadastral_local_id)
  building        [[lon,lat],...] | [[[lon,lat],...],...]  existing footprint(s) (optional; property map only)
  front_edges     [i,...] | null    simplified-edge indices facing a street (corner lot = 2)
  street_point    [lon,lat]         used when front_edges is null: nearest edge = front
  setbacks        {"front":4,"rear":5,"side":3}   from build-rights
  floors          typical floors allowed (incl. ground)
  roof_floors     partial roof floors allowed (e.g. Rova "+2 ק' גג"); 0 if none
  roof_coverage   share of envelope used per roof floor (default 0.65)
  lot_area_for_rights  m² denominator for implied FAR (registered area)

Output: envelope_area, envelope_gross (envelope × floors + roof share), implied_far, edges, geo (parcel, existing, envelope).
Used when rights are envelope-based ("ראה הערה") and for the line-sensitivity note in section 05.
"""
import json, math, sys
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union


def proj(ring):
    lat0 = sum(p[1] for p in ring) / len(ring); lon0 = sum(p[0] for p in ring) / len(ring)
    kx = 111320 * math.cos(math.radians(lat0)); ky = 110574
    to_xy = lambda c: [((x - lon0) * kx, (y - lat0) * ky) for x, y in c]
    to_ll = lambda c: [(x / kx + lon0, y / ky + lat0) for x, y in c]
    return to_xy, to_ll


def edges_of(pxy, tol=0.5):
    simp = Polygon(pxy).simplify(tol, preserve_topology=True)   # GIS noise -> real edges
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
    for i in range(n):   # chamfer < 2 m inherits its neighbour
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
    if env.is_empty:
        return {'status': 'red', 'reason': 'אין שטח בקווי הבניין', 'envelope_area': 0}
    if env.geom_type != 'Polygon': env = max(env.geoms, key=lambda g: g.area)
    floors = cfg.get('floors', 6); roofs = cfg.get('roof_floors', 0)
    env_gross = env.area * floors + env.area * cfg.get('roof_coverage', 0.65) * roofs
    lot = cfg.get('lot_area_for_rights') or poly.area
    LL = lambda g: [list(p) for p in to_ll(list(g.exterior.coords))]
    return {
        'status': 'ok', 'parcel_area': round(poly.area, 1), 'envelope_area': round(env.area, 1),
        'envelope_share_of_lot': round(env.area / lot, 3), 'envelope_gross': round(env_gross),
        'implied_far': round(env_gross / lot, 2),
        'edges': [{'i': i, 'type': t, 'length': round(E[i].length, 1), 'setback': sb[t]} for i, t in enumerate(typ)],
        'geo': {'parcel': cfg['parcel'], 'existing': cfg.get('building'), 'envelope': LL(env)}}


if __name__ == '__main__':
    res = main(json.load(open(sys.argv[1])))
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'geo'}, ensure_ascii=False, indent=1))
