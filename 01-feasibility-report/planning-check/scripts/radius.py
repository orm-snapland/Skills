#!/usr/bin/env python3
"""תכניות / חלקות ברדיוס — מרחק מהמרכז, כפילויות, מיון.

    python3 radius.py items.json --lat 32.09 --lon 34.79 [--radius 500] [--key plan_number] > out.json

items.json: רשימה (או {"results"/"items"/"data": [...]}) של רשומות Snapland. מיקום לפי סדר עדיפות:
lat/lon · centroid · geometry (GeoJSON Point/Polygon/MultiPolygon). distance_m קיים → משתמשים בו.
כפילות לפי --key: נשארת הרשומה במעמד הגבוה (מאושר > בהליך > שכבה), ה-ids של השאר נשמרים ב-dupes.
"""
import sys, json, math, argparse

RANK = {"מאושר": 3, "מאושרת": 3, "בתוקף": 3, "מופקדת": 2, "הערות ציבור": 2, "בבדיקה": 2, "בהליך": 2, "טיוטה": 1, "שכבה": 0}


def hav(lat1, lon1, lat2, lon2):
    R = 6371000; p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def coords(g):
    t = g.get("type"); c = g.get("coordinates")
    if t == "Point": return [c]
    if t == "Polygon": return c[0]
    if t == "MultiPolygon": return [p for poly in c for p in poly[0]]
    return []


def where(r):
    for a, b in (("lat", "lon"), ("latitude", "longitude")):
        if a in r and b in r: return float(r[a]), float(r[b]), None
    if isinstance(r.get("centroid"), dict): return float(r["centroid"]["lat"]), float(r["centroid"]["lon"]), None
    g = r.get("geometry") or r.get("parcel_geometry")
    if isinstance(g, dict):
        pts = coords(g)
        if pts: return None, None, pts
    return None, None, None


def dist(r, lat, lon):
    if r.get("distance_m") is not None: return float(r["distance_m"])
    la, lo, pts = where(r)
    if la is not None: return hav(lat, lon, la, lo)
    if pts: return min(hav(lat, lon, y, x) for x, y in pts)   # GeoJSON = [lon, lat]; הקודקוד הקרוב
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("items"); ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True); ap.add_argument("--radius", type=float, default=500)
    ap.add_argument("--key", default="plan_number"); a = ap.parse_args()
    raw = json.load(open(a.items, encoding="utf-8"))
    rows = raw if isinstance(raw, list) else next((raw[k] for k in ("results", "items", "data") if k in raw), [])
    out, nopos = {}, []
    for r in rows:
        d = dist(r, a.lat, a.lon)
        if d is None: nopos.append(r.get(a.key)); continue
        if d > a.radius: continue
        r = dict(r, distance_m=round(d))
        k = r.get(a.key) or id(r)
        if k in out:
            keep, drop = (r, out[k]) if RANK.get(str(r.get("status")), -1) > RANK.get(str(out[k].get("status")), -1) else (out[k], r)
            keep.setdefault("dupes", []).append(drop.get("snap_id") or drop.get("id")); out[k] = keep
        else:
            out[k] = r
    res = sorted(out.values(), key=lambda r: r["distance_m"])
    json.dump(res, sys.stdout, ensure_ascii=False, indent=1)
    print(f"\n{len(res)} within {a.radius:.0f} m · {len(nopos)} without position: {nopos[:10]}", file=sys.stderr)


if __name__ == "__main__":
    main()
