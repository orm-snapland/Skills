#!/usr/bin/env python3
"""מדידת היתר – בונה את התוצרים מתוך spec.json.

    python3 build.py spec.json <outdir> [--check]

--check : רק בדיקות גאומטריה (חלוקה מלאה, חפיפות, מרפסות מחוץ למעטפת) – בלי קבצים.
פלט: <outdir>/<slug>-מדידת-דירות.pdf + .xlsx (+ overlay.png אם יש calibration).
מבנה ה-spec: ראה references/spec-format.md.
"""
import sys, json, re, base64, pathlib, subprocess
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
A = lambda p: Polygon(p).area / 1e4
PAL = [("#D6E6EF", "#2E6E8E", "#1F5570"), ("#F3E6CF", "#A9741A", "#7A5210"), ("#E8DDF0", "#6B4C8A", "#4E3566"),
       ("#DCEBDF", "#3F7F55", "#2C5C3D"), ("#F6DCDA", "#9E3B32", "#76261F"), ("#E4ECD2", "#6F8530", "#4F6020")]


def load(p):
    s = json.load(open(p, encoding="utf-8"))
    s.setdefault("common", []); s.setdefault("balconies", []); s.setdefault("voids", [])
    s.setdefault("other_common", []); s.setdefault("checks", []); s.setdefault("flags", [])
    return s


# ---------------------------------------------------------------- checks
def check(s):
    env = Polygon(s["envelope"]); ok = True
    assert env.is_valid, "envelope polygon invalid (self-intersection / order)"
    parts = [(u["id"], Polygon(u["poly"])) for u in s["units"]] + [(c["id"], Polygon(c["poly"])) for c in s["common"] if c.get("in_envelope", True)]
    for pid, p in parts:
        if not p.is_valid: print(f"✗ {pid}: invalid polygon"); ok = False
    for i, (a, pa) in enumerate(parts):
        for b, pb in parts[i + 1:]:
            ov = pa.intersection(pb).area / 1e4
            if ov > 0.005: print(f"✗ overlap {a}/{b}: {ov:.3f} m²"); ok = False
    gap = unary_union([p for _, p in parts]).symmetric_difference(env).area / 1e4
    print(f"{'✓' if gap < 0.01 else '✗'} partition vs envelope: diff {gap:.3f} m²"); ok &= gap < 0.01
    for b in s["balconies"]:
        ov = Polygon(b["poly"]).intersection(env).area / 1e4
        if ov > 0.005: print(f"✗ balcony {b['id']} overlaps envelope by {ov:.2f} m²"); ok = False
    print(f"envelope {A(s['envelope']):.2f} | " + " | ".join(f"{pid} {p.area/1e4:.2f}" for pid, p in parts))
    print(f"balconies {sum(A(b['poly']) for b in s['balconies']):.2f}")
    return ok


# ---------------------------------------------------------------- numbers
def numbers(s):
    F = s["meta"].get("typical_floors", 1)
    n = {"envelope": A(s["envelope"]), "F": F}
    for u in s["units"]: n["U:" + u["id"]] = A(u["poly"])
    for c in s["common"]: n["C:" + c["id"]] = A(c["poly"])
    for b in s["balconies"]: n["B:" + b["id"]] = A(b["poly"])
    for o in s["other_common"]: n["O:" + o["id"]] = A(o["poly"]) if "poly" in o else float(o["area"])
    n["units"] = sum(n["U:" + u["id"]] for u in s["units"])
    n["balconies"] = sum(n["B:" + b["id"]] for b in s["balconies"])
    n["bal_by_unit"] = {u["id"]: sum(n["B:" + b["id"]] for b in s["balconies"] if b["unit"] == u["id"]) for u in s["units"]}
    n["common_floor"] = sum(n["C:" + c["id"]] for c in s["common"])
    n["common_total"] = n["common_floor"] * F + sum(n["O:" + o["id"]] * o.get("floors", 1) for o in s["other_common"])
    return n


def ref(n, r):
    return float(r) if isinstance(r, (int, float)) else n[r]


# ---------------------------------------------------------------- overlay
def overlay(s, outdir):
    cal = s.get("calibration")
    if not cal: return None
    from PIL import Image, ImageDraw
    Image.MAX_IMAGE_PIXELS = None
    sys.path.insert(0, str(HERE)); from scan_tools import cm2px
    im = Image.open(cal["scan"]).convert("RGB")
    allp = [p for g in (s["units"], s["common"], s["balconies"]) for x in g for p in x["poly"]] + s["envelope"]
    xs = [cm2px(cal, x, y)[0] for x, y in allp]; ys = [cm2px(cal, x, y)[1] for x, y in allp]
    pad = 60; box = (int(min(xs)) - pad, int(min(ys)) - pad, int(max(xs)) + pad, int(max(ys)) + pad)
    base = im.crop(box).convert("RGBA"); ov = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    P = lambda poly: [(cm2px(cal, x, y)[0] - box[0], cm2px(cal, x, y)[1] - box[1]) for x, y in poly]
    hexrgb = lambda h, a: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
    for b in s["balconies"]: d.polygon(P(b["poly"]), fill=(76, 160, 90, 60), outline=(60, 130, 70, 255))
    for i, u in enumerate(s["units"]): d.polygon(P(u["poly"]), fill=hexrgb(PAL[i % 6][1], 65))
    for c in s["common"]: d.polygon(P(c["poly"]), fill=(90, 90, 90, 80))
    out = Image.alpha_composite(base, ov).convert("RGB"); d2 = ImageDraw.Draw(out)
    for i, u in enumerate(s["units"]):
        pts = P(u["poly"]); d2.line(pts + [pts[0]], fill=hexrgb(PAL[i % 6][1], 255)[:3], width=3)
    for c in s["common"]:
        pts = P(c["poly"]); d2.line(pts + [pts[0]], fill=(40, 40, 40), width=3)
    for v in s["voids"]:
        pts = P(v["poly"]); d2.line(pts + [pts[0]], fill=(158, 59, 50), width=2)
    p = outdir / "overlay.png"; out.save(p); return p


# ---------------------------------------------------------------- excel
def excel(s, n, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    Fn = "Arial"; H = Font(name=Fn, bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="12263A")
    B = Font(name=Fn, bold=True); N = Font(name=Fn); BL = Font(name=Fn, color="0000FF")
    T = Font(name=Fn, bold=True, size=14); SUB = PatternFill("solid", fgColor="EAF1F5"); TOT = PatternFill("solid", fgColor="F4E9D6")
    NOTE = Font(name=Fn, size=9, color="3D5163"); th = Side(style="thin", color="C8D0D8"); BOX = Border(top=th, bottom=th, left=th, right=th)
    m = s["meta"]; wb = Workbook()
    pg = wb.active; pg.title = "פוליגונים"; pg.sheet_view.rightToLeft = True
    pg["A1"] = f"קואורדינטות פוליגונים – {m['address']}"; pg["A1"].font = T
    pg["A2"] = "ס\"מ. " + m.get("origin_note", "ראשית (0,0) בפינה הדרום-מערבית של המעטפת; X מזרחה, Y צפונה.") + " השטח בנוסחת שרוך – שינוי קואורדינטה מעדכן הכול."
    pg["A2"].font = Font(name=Fn, italic=True, color="3D5163")
    for c, w in zip("ABCDE", [10, 12, 12, 4, 50]): pg.column_dimensions[c].width = w
    aref = {}; r = 4
    blocks = [("envelope", "ENV", "מעטפת קומה (בנוי, ללא מרפסות)", s["envelope"])]
    blocks += [("U:" + u["id"], u["id"], u["name"] + " – ברוטו", u["poly"]) for u in s["units"]]
    blocks += [("C:" + c["id"], c["id"], c["name"], c["poly"]) for c in s["common"]]
    blocks += [("B:" + b["id"], b["id"], f"{b['name']} – {unit_name(s, b['unit'])}", b["poly"]) for b in s["balconies"]]
    blocks += [("V:" + v["id"], v["id"], v["name"], v["poly"]) for v in s["voids"]]
    blocks += [("O:" + o["id"], o["id"], o["name"], o["poly"]) for o in s["other_common"] if "poly" in o]
    for key, pid, name, poly in blocks:
        pg.cell(r, 1, pid).font = B; pg.cell(r, 2, name).font = B
        for c in range(1, 6): pg.cell(r, c).fill = SUB
        r += 1
        for c, h in enumerate(["#", "X (ס\"מ)", "Y (ס\"מ)"], 1):
            x = pg.cell(r, c, h); x.font = H; x.fill = HF
        r += 1; first = r
        for i, (x, y) in enumerate(poly):
            pg.cell(r, 1, i + 1); pg.cell(r, 2, x).font = BL; pg.cell(r, 3, y).font = BL; r += 1
        pg.cell(r, 1, "סגירה"); pg.cell(r, 2, f"=B{first}"); pg.cell(r, 3, f"=C{first}"); last = r; r += 1
        pg.cell(r, 1, "שטח מ\"ר").font = B
        c = pg.cell(r, 2, f"=ROUND(ABS(SUMPRODUCT(B{first}:B{last-1},C{first+1}:C{last})-SUMPRODUCT(B{first+1}:B{last},C{first}:C{last-1}))/2/10000,2)")
        c.font = B; c.fill = TOT; aref[key] = f"'פוליגונים'!B{r}"; r += 2

    s1 = wb.create_sheet("סיכום", 0); s1.sheet_view.rightToLeft = True
    for c, w in zip("ABCDEF", [40, 14, 12, 16, 10, 48]): s1.column_dimensions[c].width = w
    s1["A1"] = f"{m['address']} – מדידת דירות ושטחי שירות מתוך היתר"; s1["A1"].font = T
    s1["A2"] = f"מקור: {m.get('source','תשריט היתר')}. שיטה: {m.get('method','ברוטו לפי היתר')}."
    s1["A2"].font = Font(name=Fn, italic=True, color="3D5163"); s1.merge_cells("A2:F2"); s1["A2"].alignment = Alignment(wrap_text=True); s1.row_dimensions[2].height = 30
    s1["A4"] = f"מספר קומות טיפוסיות ({m.get('floors_label','')})"; s1["A4"].font = B; s1["B4"] = n["F"]; s1["B4"].font = BL
    hdr = ["רכיב", "לקומה (מ\"ר)", "קומות", "בבניין (מ\"ר)", "חדרים", "הערה"]

    def header(row):
        for c, h in enumerate(hdr, 1):
            x = s1.cell(row, c, h); x.font = H; x.fill = HF; x.alignment = Alignment(horizontal="center")

    def line(row, label, f, floors, rooms="", note="", bold=False, fill=None):
        s1.cell(row, 1, label).font = B if bold else N; s1.cell(row, 2, f).font = B if bold else N
        s1.cell(row, 3, floors); s1.cell(row, 4, f"=B{row}*C{row}").font = B if bold else N
        s1.cell(row, 5, rooms); s1.cell(row, 6, note).font = NOTE; s1.cell(row, 6).alignment = Alignment(wrap_text=True)
        for c in range(1, 7):
            s1.cell(row, c).border = BOX
            if fill: s1.cell(row, c).fill = fill
        for c in (2, 4): s1.cell(row, c).number_format = "0.00"

    sec = lambda row, t: setattr(s1.cell(row, 1, t), "font", Font(name=Fn, bold=True, size=12))
    r = 6; sec(r, "א. דירות – שטח ברוטו"); r += 1; header(r); r += 1; u0 = r
    for u in s["units"]:
        line(r, u["name"], f"={aref['U:'+u['id']]}", "=$B$4", u.get("rooms", ""), u.get("note", "")); r += 1
    line(r, "סה\"כ דירות", f"=SUM(B{u0}:B{r-1})", "=$B$4", bold=True, fill=TOT); rU = r; r += 2
    sec(r, "ב. מרפסות – שטח שירות"); r += 1; header(r); r += 1; b0 = r
    for b in s["balconies"]:
        line(r, f"{b['id']} · {b['name']} · {unit_name(s, b['unit'])}", f"={aref['B:'+b['id']]}", "=$B$4", note=f"מידות {b.get('dims','')} ס\"מ"); r += 1
    b1 = r - 1
    for u in s["units"]:
        line(r, f"מרפסות – {u['name']}", f'=SUMIF(A{b0}:A{b1},"*{u["name"]}",B{b0}:B{b1})', "=$B$4", bold=True, fill=SUB); r += 1
    line(r, "סה\"כ מרפסות", f"=SUM(B{b0}:B{b1})", "=$B$4", bold=True, fill=TOT); r += 2
    sec(r, "ג. שטחים משותפים"); r += 1; header(r); r += 1; c0 = r
    for c in s["common"]:
        line(r, c["name"], f"={aref['C:'+c['id']]}", "=$B$4", note=c.get("note", "")); r += 1
    for o in s["other_common"]:
        f = f"={aref['O:'+o['id']]}" if "poly" in o else (o.get("formula") or o["area"])
        line(r, o["name"], f, o.get("floors", 1), note=o.get("note", "")); r += 1
    s1.cell(r, 1, "סה\"כ משותף בבניין").font = B; s1.cell(r, 4, f"=SUM(D{c0}:D{r-1})").font = B
    s1.cell(r, 4).number_format = "0.00"
    for c in range(1, 7): s1.cell(r, c).fill = TOT; s1.cell(r, c).border = BOX
    r += 2
    if s["checks"]:
        sec(r, "ד. בקרה מול חישוב האדריכל"); r += 1
        for c, h in enumerate(["בדיקה", "מדידה", "אדריכל", "הפרש", "", "ממצא"], 1):
            x = s1.cell(r, c, h); x.font = H; x.fill = HF
        r += 1
        for ch in s["checks"]:
            s1.cell(r, 1, ch["label"]); s1.cell(r, 2, round(ref(n, ch["ours"]), 2)); s1.cell(r, 3, ref(n, ch["architect"]))
            s1.cell(r, 4, f"=B{r}-C{r}"); s1.cell(r, 6, ch.get("note", "")).font = NOTE
            for c in (2, 3, 4): s1.cell(r, c).number_format = "0.00"
            for c in range(1, 7): s1.cell(r, c).border = BOX
            r += 1
    nt = wb.create_sheet("הנחות ודגלים"); nt.sheet_view.rightToLeft = True
    nt.column_dimensions["A"].width = 4; nt.column_dimensions["B"].width = 120
    for i, t in enumerate(s["flags"], 1):
        nt.cell(i, 1, i).font = B; c = nt.cell(i, 2, re.sub("<[^>]+>", "", t)); c.font = N; c.alignment = Alignment(wrap_text=True); nt.row_dimensions[i].height = 32
    wb.save(path)
    rc = pathlib.Path("/mnt/skills/public/xlsx/scripts/recalc.py")
    if rc.exists():
        print(subprocess.run([sys.executable, str(rc), str(path)], capture_output=True, text=True).stdout[:200])


def unit_name(s, uid):
    return next(u["name"] for u in s["units"] if u["id"] == uid)


# ---------------------------------------------------------------- svg plan
def svg_plan(s, n):
    pts = [p for g in (s["units"], s["common"], s["balconies"], s["voids"]) for x in g for p in x["poly"]] + s["envelope"]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    W = x1 - x0; Hh = y1 - y0; k = max(W, Hh) / 1900          # קנה מידה לטקסט
    T = lambda x, y: (x, y1 + y0 - y)
    path = lambda p: "M" + " L".join(f"{T(x,y)[0]:.0f},{T(x,y)[1]:.0f}" for x, y in p) + " Z"
    fs = lambda v: v * k
    o = [f'<svg viewBox="{x0-260*k:.0f} {y0-200*k:.0f} {W+520*k:.0f} {Hh+330*k:.0f}" xmlns="http://www.w3.org/2000/svg" font-family="Heebo">',
         f'<defs><pattern id="hb" width="{28*k:.0f}" height="{28*k:.0f}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="{28*k:.0f}" stroke="#4C8B5A" stroke-width="{5*k:.1f}" opacity=".45"/></pattern>'
         f'<pattern id="hs" width="{22*k:.0f}" height="{22*k:.0f}" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="{22*k:.0f}" stroke="#555" stroke-width="{4*k:.1f}" opacity=".5"/></pattern></defs>']
    for b in s["balconies"]:
        o.append(f'<path d="{path(b["poly"])}" fill="#E3F0E5" stroke="#4C8B5A" stroke-width="{6*k:.1f}"/><path d="{path(b["poly"])}" fill="url(#hb)"/>')
    for i, u in enumerate(s["units"]):
        o.append(f'<path d="{path(u["poly"])}" fill="{PAL[i%6][0]}" stroke="{PAL[i%6][1]}" stroke-width="{12*k:.1f}"/>')
    for c in s["common"]:
        o.append(f'<path d="{path(c["poly"])}" fill="#E4E4E4" stroke="#333" stroke-width="{10*k:.1f}"/><path d="{path(c["poly"])}" fill="url(#hs)"/>')
    for v in s["voids"]:
        P = Polygon(v["poly"]); bx = P.bounds; a, b = T(bx[0], bx[1]), T(bx[2], bx[3])
        o.append(f'<path d="{path(v["poly"])}" fill="#fff" stroke="#9E3B32" stroke-width="{5*k:.1f}" stroke-dasharray="{14*k:.0f} {8*k:.0f}"/>'
                 f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#9E3B32" stroke-width="{4*k:.1f}"/><line x1="{a[0]}" y1="{b[1]}" x2="{b[0]}" y2="{a[1]}" stroke="#9E3B32" stroke-width="{4*k:.1f}"/>')

    def where(x):
        if "label_at" in x: return x["label_at"]
        c = Polygon(x["poly"]).representative_point(); return (c.x, c.y)

    def lab(xy, t1, t2, col, s1=58, s2=46, bg=False):
        X, Y = T(*xy); r = ""
        if bg: r = f'<rect x="{X-fs(170)}" y="{Y-fs(62)}" width="{fs(340)}" height="{fs(140)}" fill="#fff" opacity=".85"/>'
        return r + (f'<text x="{X}" y="{Y}" text-anchor="middle" font-size="{fs(s1):.0f}" font-weight="700" fill="{col}">{t1}</text>'
                    f'<text x="{X}" y="{Y+fs(s2+14):.0f}" text-anchor="middle" font-size="{fs(s2):.0f}" fill="{col}">{t2}</text>')
    for i, u in enumerate(s["units"]):
        rooms = f" · {u['rooms']} חד׳" if u.get("rooms") else ""
        o.append(lab(where(u), u["name"], f'{n["U:"+u["id"]]:.2f} מ"ר{rooms}', PAL[i % 6][2]))
    for c in s["common"]:
        o.append(lab(where(c), c.get("short", c["name"]), f'{n["C:"+c["id"]]:.2f} מ"ר', "#222", 44, 40, True))
    for b in s["balconies"]:
        X, Y = T(*where(b)); bx = Polygon(b["poly"]).bounds
        rot = f' transform="rotate(-90 {X:.0f} {Y:.0f})"' if (bx[3] - bx[1]) > 1.6 * (bx[2] - bx[0]) else ""
        o.append(f'<text x="{X:.0f}" y="{Y:.0f}" text-anchor="middle" dominant-baseline="middle" font-size="{fs(38):.0f}" font-weight="700" fill="#2F6B3C"{rot}>{b["id"]} · {n["B:"+b["id"]]:.2f}</text>')
    for v in s["voids"]:
        X, Y = T(*where(v)); o.append(f'<text x="{X:.0f}" y="{Y:.0f}" text-anchor="middle" font-size="{fs(34):.0f}" font-weight="700" fill="#9E3B32">{v["id"]}</text>')
    for g, col in [(s["units"], None), (s["common"], "#333")]:
        for i, x in enumerate(g):
            for px, py in x["poly"]:
                X, Y = T(px, py); o.append(f'<circle cx="{X}" cy="{Y}" r="{9*k:.1f}" fill="{col or PAL[i%6][1]}"/>')
    ex = Polygon(s["envelope"]).bounds; c = "#3D5163"; sw = 3 * k
    a, b = T(ex[0], ex[1] - 110 * k), T(ex[2], ex[1] - 110 * k)
    o.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{c}" stroke-width="{sw}"/><text x="{(a[0]+b[0])/2}" y="{a[1]-fs(14)}" text-anchor="middle" font-size="{fs(40):.0f}" fill="{c}">{ex[2]-ex[0]:.0f}</text>')
    a, b = T(ex[0] - 170 * k, ex[1]), T(ex[0] - 170 * k, ex[3])
    o.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{c}" stroke-width="{sw}"/><text x="{a[0]-fs(14)}" y="{(a[1]+b[1])/2}" text-anchor="middle" font-size="{fs(40):.0f}" fill="{c}" transform="rotate(-90 {a[0]-fs(14)} {(a[1]+b[1])/2})">{ex[3]-ex[1]:.0f}</text>')
    nx, ny = T(x1 + 120 * k, y1 - 120 * k)
    o.append(f'<g transform="translate({nx},{ny}) scale({k})"><path d="M0,-70 L28,30 L0,10 L-28,30 Z" fill="#12263A"/><text x="0" y="80" text-anchor="middle" font-size="44" font-weight="700">צ</text></g></svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- pdf
def pdf(s, n, ovpath, path):
    m = s["meta"]; F = n["F"]; f2 = lambda v: f"{v:,.2f}"
    vtx = lambda poly: " · ".join(f"{i+1}:({x:g},{y:g})" for i, (x, y) in enumerate(poly))
    kpis = "".join(f'<div class="kpi" style="--c:{PAL[i%6][1]}"><div class="n">{f2(n["U:"+u["id"]])}</div><div class="l">מ"ר · {u["name"]}{" (" + u["rooms"] + " חד׳)" if u.get("rooms") else ""}</div></div>' for i, u in enumerate(s["units"]))
    kpis += f'<div class="kpi" style="--c:#555"><div class="n">{f2(n["common_floor"])}</div><div class="l">מ"ר · משותף לקומה</div></div>'
    kpis += f'<div class="kpi" style="--c:#4C8B5A"><div class="n">{f2(n["balconies"])}</div><div class="l">מ"ר · מרפסות לקומה (שירות)</div></div>'
    legend = "".join(f'<span><i style="background:{PAL[i%6][0]};border-color:{PAL[i%6][1]}"></i>{u["name"]}</span>' for i, u in enumerate(s["units"]))
    legend += '<span><i style="background:#E4E4E4;border-color:#333"></i>משותף</span><span><i style="background:#E3F0E5;border-color:#4C8B5A"></i>מרפסת</span><span><i style="background:#fff;border-color:#9E3B32"></i>שקע/פיר X</span><span>מידות בס"מ</span>'
    rows_u = "".join(f'<tr><td>{u["name"]} – ברוטו</td><td class="n">{f2(n["U:"+u["id"]])}</td><td class="n">{F}</td><td class="n">{f2(n["U:"+u["id"]]*F)}</td></tr>' for u in s["units"])
    rows_c = "".join(f'<tr><td>{c["name"]}</td><td class="n">{f2(n["C:"+c["id"]])}</td><td class="n">{F}</td><td class="n">{f2(n["C:"+c["id"]]*F)}</td></tr>' for c in s["common"])
    rows_b = "".join(f'<tr><td>{b["id"]}</td><td>{b["name"]}</td><td>{unit_name(s,b["unit"])}</td><td class="n">{b.get("dims","")}</td><td class="n">{f2(n["B:"+b["id"]])}</td><td class="n">{f2(n["B:"+b["id"]]*F)}</td></tr>' for b in s["balconies"])
    rows_b += "".join(f'<tr class="st"><td></td><td>מרפסות {u["name"]}</td><td></td><td></td><td class="n">{f2(n["bal_by_unit"][u["id"]])}</td><td class="n">{f2(n["bal_by_unit"][u["id"]]*F)}</td></tr>' for u in s["units"])
    rows_o = "".join(f'<tr><td>{o["name"]}</td><td>{o.get("note","")}</td><td class="n">{o.get("floors",1)}</td><td class="n">{f2(n["O:"+o["id"]])}</td></tr>' for o in s["other_common"])
    rows_ch = "".join(f'<tr><td>{c["label"]}</td><td class="n">{f2(ref(n,c["ours"]))}</td><td class="n">{f2(ref(n,c["architect"]))}</td><td>{c.get("note","")}</td></tr>' for c in s["checks"])
    rows_v = "".join(f'<tr><td>{x["name"]}</td><td class="n">{f2(A(x["poly"]))}</td><td class="vx">{vtx(x["poly"])}</td></tr>' for x in s["units"] + s["common"])
    rows_v += "".join(f'<tr><td>{b["id"]} · {b["name"]}</td><td class="n">{f2(A(b["poly"]))}</td><td class="vx">{vtx(b["poly"])}</td></tr>' for b in s["balconies"])
    flags = "".join(f"<li>{f}</li>" for f in s["flags"])
    ov_sec = f'<section class="pb"><h2>אימות: הפוליגונים על גבי התשריט המקורי</h2><img src="__OVERLAY__"><div class="note">הגבולות נבנו ממידות כתובות; ההנחה על הסריקה ויזואלית בלבד (עיוות נייר/סריקה).</div></section>' if ovpath else ""
    meta = "".join(f'<div><div class="k">{k}</div><div class="v">{v}</div></div>' for k, v in [
        ("מקור", m.get("source", "תשריט היתר")), ("תאריך היתר", m.get("permit_date", "—")),
        ("שיטת מדידה", m.get("method", "ברוטו לפי היתר")), ("קומות טיפוסיות", f'{F} ({m.get("floors_label","")}) · {len(s["units"])*F} דירות')])
    css = (ASSETS / "report.css").read_text(encoding="utf-8")
    html = f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>/*FONTFACE*/{css}</style></head><body>
<div class="cover"><div class="eb">מדידת דירות מתוך היתר בנייה · SNAPLAND</div><h1>{m["address"]}</h1>
<div class="sub">{m.get("subtitle", "")}</div><div class="meta">{meta}</div></div>
<div class="kpis">{kpis}</div>
<div class="plan">{svg_plan(s, n)}<div class="legend">{legend}</div></div>
<section class="pb"><h2>1 · שטחים לקומה ולבניין</h2><table><tr><th>רכיב</th><th class="n">לקומה מ"ר</th><th class="n">קומות</th><th class="n">בבניין מ"ר</th></tr>{rows_u}
<tr class="st"><td>סה"כ דירות</td><td class="n">{f2(n["units"])}</td><td class="n">{F}</td><td class="n">{f2(n["units"]*F)}</td></tr>{rows_c}
<tr class="t"><td>שטח קומה טיפוסית (מעטפת)</td><td class="n">{f2(n["envelope"])}</td><td class="n">{F}</td><td class="n">{f2(n["envelope"]*F)}</td></tr></table>
<section><h2>2 · מרפסות – שטח שירות</h2><table><tr><th>#</th><th>מרפסת</th><th>דירה</th><th class="n">מידות ס"מ</th><th class="n">לקומה מ"ר</th><th class="n">בבניין מ"ר</th></tr>{rows_b}
<tr class="t"><td></td><td>סה"כ מרפסות</td><td></td><td></td><td class="n">{f2(n["balconies"])}</td><td class="n">{f2(n["balconies"]*F)}</td></tr></table></section>
{f'<section><h2>3 · שטחים משותפים מחוץ לקומה הטיפוסית</h2><table><tr><th>רכיב</th><th>פירוט</th><th class="n">קומות</th><th class="n">מ"ר</th></tr>{rows_o}<tr class="t"><td>סה"כ משותף בבניין</td><td>כולל משותף בקומות הטיפוסיות</td><td></td><td class="n">{f2(n["common_total"])}</td></tr></table></section>' if s["other_common"] else ""}
{f'<section><h2>4 · בקרה מול חישוב האדריכל</h2><table><tr><th>בדיקה</th><th class="n">מדידה</th><th class="n">אדריכל</th><th>ממצא</th></tr>{rows_ch}</table></section>' if s["checks"] else ""}</section>
{ov_sec}
<section class="pb"><h2>הנחות ודגלים</h2>{f'<div class="flag">{m["headline_flag"]}</div>' if m.get("headline_flag") else ""}<ol>{flags}</ol></section>
<section><h2>קואורדינטות (ס"מ · {m.get("origin_note","ראשית בפינה הדרום-מערבית, X מזרחה, Y צפונה")})</h2>
<table><tr><th style="width:24%">פוליגון</th><th class="n" style="width:9%">מ"ר</th><th>קודקודים</th></tr>{rows_v}</table><div class="note">הקואורדינטות וחישובי השטח חיים בקובץ האקסל.</div></section></body></html>'''
    i = html.index("</svg>")   # בידוד ביטויי חשבון (594×632) כדי שה-RTL לא יהפוך אותם
    pat = re.compile(r"(?<![\w(#])([+\u200e]?\d[\d.,]*(?:\s*[×=+]\s*\d[\d.,]*)+)")
    html = html[:i] + pat.sub(lambda mm: f'<span dir="ltr" style="unicode-bidi:isolate">{mm.group(1)}</span>', html[i:])
    if ovpath:
        html = html.replace("__OVERLAY__", "data:image/png;base64," + base64.b64encode(open(ovpath, "rb").read()).decode())
    R = {"hebrew": "U+0590-05FF, U+200C-2010, U+20AA, U+25CC, U+FB1D-FB4F", "latin": "U+0000-00FF, U+2000-206F, U+2212"}
    fonts = "".join(f'@font-face{{font-family:Heebo;font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode((ASSETS/"fonts"/f"heebo-{sub}-{w}-normal.woff2").read_bytes()).decode()}) format("woff2");unicode-range:{rng};}}' for w in (400, 500, 700) for sub, rng in R.items())
    tmp = pathlib.Path(path).with_suffix(".build.html"); tmp.write_text(html.replace("/*FONTFACE*/", fonts), encoding="utf-8")
    from playwright.sync_api import sync_playwright
    foot = f'<div style="width:100%;font-size:7pt;color:#3D5163;padding:0 15mm;display:flex;justify-content:space-between;direction:rtl;font-family:sans-serif"><span>{m["address"]} · מדידת היתר · Snapland</span><span><span class="pageNumber"></span>/<span class="totalPages"></span></span></div>'
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); pg.goto(tmp.resolve().as_uri()); pg.wait_for_timeout(1200)
        pg.pdf(path=str(path), format="A4", print_background=True, display_header_footer=True, header_template="<div></div>", footer_template=foot,
               margin={"top": "13mm", "bottom": "15mm", "left": "14mm", "right": "14mm"})
        b.close()
    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    spec, out = sys.argv[1], pathlib.Path(sys.argv[2]); s = load(spec)
    ok = check(s)
    if "--check" in sys.argv: sys.exit(0 if ok else 1)
    if not ok: print("⚠ הבדיקות נכשלו – מתקנים את ה-spec לפני הפקה (או --force)"); "--force" in sys.argv or sys.exit(1)
    out.mkdir(parents=True, exist_ok=True); n = numbers(s)
    slug = s["meta"].get("slug", re.sub(r"[ ,]+", "-", s["meta"]["address"]).strip("-"))
    ov = overlay(s, pathlib.Path("/tmp"))
    excel(s, n, out / f"{slug}-מדידת-דירות.xlsx")
    pdf(s, n, ov, out / f"{slug}-מדידת-דירות.pdf")
    print("wrote", out / f"{slug}-מדידת-דירות.pdf", "+ .xlsx")
