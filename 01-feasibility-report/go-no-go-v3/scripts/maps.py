#!/usr/bin/env python3
"""Vector maps for the report (v2: one or many buildings, several existing buildings, street labels).
    python3 scripts/maps.py envelope.json property neighbors.json [labels.json] > map_property.svg   # stage 1, section 03
    python3 scripts/maps.py massing.json planning neighbors.json [labels.json] > map_planning.svg    # stage 3 only
envelope.json: output of scripts/envelope.py (property mode uses geo.parcel / geo.existing only).
massing.json: output of stages/3-alternatives/scripts/massing.py (geo.mass/core/units) or massing_multi.py (buildings[].geo).
neighbors.json: list of rings [[lon,lat],...] (search_entity parcels, geo bbox) — include road parcels.
labels.json: [[lon, lat, "יגאל אלון"], ...] street names, drawn RTL outside the parcel.
Unit labels are LTR ("69 m²"): Hebrew inside SVG text reorders unpredictably. Captions go in HTML, not in the SVG."""
import json, math, sys
from shapely.geometry import Polygon, LineString

COL = {'front': '#2563EB', 'rear': '#C81E3A', 'side': '#2F8F57'}


def svg(m, mode, neighbors, labels=(), pad=12):
    g = m['geo']; ring = g['parcel']
    lat0 = sum(p[1] for p in ring) / len(ring); lon0 = sum(p[0] for p in ring) / len(ring)
    kx = 111320 * math.cos(math.radians(lat0)); ky = 110574
    P = lambda c: [((x - lon0) * kx, (y - lat0) * ky) for x, y in c]
    path = lambda pts, close=True: "M" + " L".join(f"{x:.2f},{-y:.2f}" for x, y in pts) + (" Z" if close else "")
    poly = Polygon(P(ring)); mnx, mny, mxx, mxy = poly.bounds
    W = (mxx - mnx) + 2 * pad; Hh = (mxy - mny) + 2 * pad; x0, y1 = mnx - pad, mxy + pad
    o = [f'<svg viewBox="{x0:.1f} {-y1:.1f} {W:.1f} {Hh:.1f}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" '
         f'style="width:100%;height:100%;background:#EEF2F5;direction:ltr">',
         f'<rect x="{x0}" y="{-y1}" width="{W}" height="{Hh}" fill="#E9EDF0"/>']
    for nb in neighbors: o.append(f'<path d="{path(P(nb))}" fill="#FFFFFF" stroke="#B8C2CB" stroke-width="0.25"/>')
    o.append(f'<path d="{path(P(ring))}" fill="#FBE9EC" stroke="#C81E3A" stroke-width="0.6"/>')
    if mode == 'property':
        ex = g.get('existing') or []
        if ex and isinstance(ex[0][0], (int, float)): ex = [ex]
        for b in ex: o.append(f'<path d="{path(P(b))}" fill="#12263A" fill-opacity="0.82"/>')
        for lx, ly, t in labels:
            X, Y = P([[lx, ly]])[0]
            o.append(f'<text x="{X:.1f}" y="{-Y:.1f}" font-size="2.3" font-family="Heebo,DejaVu Sans" fill="#3D5163" '
                     f'text-anchor="middle" direction="rtl" unicode-bidi="embed">{t}</text>')
    if mode == 'planning':
        cx, cy = poly.centroid.x, poly.centroid.y
        env = Polygon(P(g['envelope']))
        edges = [(e['type'], LineString(P(e['line'])), e['length'], e['setback']) for e in g['parcel_edges']]
        ec = list(env.exterior.coords)
        for i in range(len(ec) - 1):
            seg = LineString([ec[i], ec[i + 1]])
            if seg.length < 0.3: continue
            mp = seg.interpolate(0.5, normalized=True); t = min(edges, key=lambda e: e[1].distance(mp))[0]
            o.append(f'<path d="{path([ec[i], ec[i + 1]], False)}" stroke="{COL[t]}" stroke-width="0.4" stroke-dasharray="1.2 0.8" fill="none"/>')
        blds = m.get('buildings') or [dict(geo=dict(mass=g['mass'], core=g.get('core'), units=g.get('units', [])))]
        for b in blds:
            G = b['geo']
            o.append(f'<path d="{path(P(G["mass"]))}" fill="#2E6E8E" fill-opacity="0.16" stroke="#2E6E8E" stroke-width="0.35"/>')
            for u in G.get('units', []): o.append(f'<path d="{path(P(u["poly"]))}" fill="none" stroke="#2E6E8E" stroke-width="0.2"/>')
            if G.get('core'): o.append(f'<path d="{path(P(G["core"]))}" fill="#12263A" fill-opacity="0.85"/>')
            for u in G.get('units', []):
                lx, ly = P([u['label']])[0]
                o.append(f'<text x="{lx:.2f}" y="{-ly + 0.55:.2f}" font-size="1.6" font-family="DejaVu Sans" font-weight="700" '
                         f'fill="#12263A" text-anchor="middle">{u["a"]} m²</text>')
        for t, ln, L, sb in edges:
            if L < 4: continue
            (ax, ay), (bx, by) = ln.coords[0], ln.coords[-1]; mx, my = (ax + bx) / 2, (ay + by) / 2; n_ = math.hypot(bx - ax, by - ay)
            nx, ny = -(by - ay) / n_, (bx - ax) / n_
            if (cx - mx) * nx + (cy - my) * ny > 0: nx, ny = -nx, -ny
            o.append(f'<text x="{mx + nx * 2.6:.2f}" y="{-(my + ny * 2.6) + 0.6:.2f}" font-size="1.7" font-family="DejaVu Sans" '
                     f'fill="#C81E3A" font-weight="700" text-anchor="middle">{L:.1f}</text>')
            ix, iy = mx - nx * sb, my - ny * sb
            o.append(f'<path d="M{mx:.2f},{-my:.2f} L{ix:.2f},{-iy:.2f}" stroke="{COL[t]}" stroke-width="0.2"/>')
            tx, ty = mx - nx * sb / 2 + ny * 1.6, my - ny * sb / 2 - nx * 1.6
            o.append(f'<text x="{tx:.2f}" y="{-ty + 0.5:.2f}" font-size="1.45" font-family="DejaVu Sans" fill="{COL[t]}" text-anchor="middle">{sb:g} m</text>')
    nx_, ny_ = x0 + W - 4, -y1 + 3
    o.append(f'<path d="M{nx_},{ny_} l-1.2,3 l1.2,-0.8 l1.2,0.8 Z" fill="#12263A"/><text x="{nx_}" y="{ny_ + 5.3}" font-size="1.8" '
             f'text-anchor="middle" font-family="DejaVu Sans" fill="#12263A">N</text>')
    sx, sy = x0 + 3, -(y1 - Hh) - 3
    o.append(f'<rect x="{sx}" y="{sy}" width="10" height="0.6" fill="#12263A"/><text x="{sx + 5}" y="{sy - 0.8}" font-size="1.6" '
             f'text-anchor="middle" font-family="DejaVu Sans" fill="#12263A">10 m</text>')
    o.append('</svg>')
    return "".join(o)


if __name__ == '__main__':
    m = json.load(open(sys.argv[1])); mode = sys.argv[2]
    nb = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else []
    lab = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else []
    sys.stdout.write(svg(m, mode, nb, lab))
