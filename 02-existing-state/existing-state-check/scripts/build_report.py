#!/usr/bin/env python3
"""existing.json → PDF בעברית + existing_for_gng.json.

    python3 build_report.py existing.json <outdir> [--no-gate]

מריץ gate.py, בונה HTML בסגנון דוחות Snapland (assets/report.css), bidi.py, render.py.
"""
import sys, json, pathlib, html as H, re
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate, bidi, render

TAG = {"מערכת": "t-sys", "מסמך": "t-doc", "חישוב": "t-cal", "כלל אצבע": "t-cal", "הנחה": "t-asm",
       "חסר": "t-mis", "סותר": "t-con", "קלט משתמש": "t-usr", "החלטה": "t-skl"}
SQM = 'מ"ר'
e = lambda s: H.escape(str(s if s is not None else "—"))


def tag(s):
    return f'<span class="tag {TAG.get(s, "t-sys")}">{e(s)}</span>' if s else ""


def dots(n):
    n = int(n or 0)
    return "●" * n + "○" * (4 - n)


def num(x, unit=""):
    if x is None or x == "":
        return "—"
    if isinstance(x, (int, float)):
        s = f"{x:,.0f}" if abs(x) >= 100 else f"{x:,.1f}".rstrip("0").rstrip(".")
    else:
        s = str(x)
    return f"{s} {unit}".strip()


def sec(n, title, inner, brk=False):
    st = ' style="page-break-before:always"' if brk else ""
    return (f'<section{st}><div class="shead"><span class="snum">{n:02d}</span><h2>{e(title)}</h2></div>'
            f'<div class="body">{inner}</div></section>')


def table(head, rows, widths=None):
    w = widths or [None] * len(head)
    def _th(h, x):
        style = ' style="width:%s"' % x if x else ""
        return "<th%s>%s</th>" % (style, h)
    th = "".join(_th(h, x) for h, x in zip(head, w))
    return f'<table class="gng"><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def build_html(p):
    pc = p["parcel"]; t = p.get("totals") or {}; n = 0; S = []
    gh = f'גוש {pc.get("gush","—")} חלקה {pc.get("helka","—")}'
    place = pc.get("address", "") + (f' · {pc["neighborhood"]}' if pc.get("neighborhood") else "")
    cover = (f'<div class="pg"><div class="cov"><div class="eyebrow">SNAPLAND</div><div class="t">בדיקת מצב קיים</div>'
             f'<div class="s">מה בנוי כאן היום · יחידות, שטחים ומקדם קיים</div>'
             f'<div class="s">{e(p.get("as_of",""))}</div><div class="s">{e(gh)}</div><div class="s">{e(place)}</div></div></div>')
    intro = ('<div class="intro">המידע נאסף ממאגרים ממשלתיים ועירוניים באמצעות Snapland ומכללי אצבע; מקור כל נתון מצוין לצידו. '
             'השטחים כאן הם הערכה מנתוני מערכת ואינם מדידה. מדידה מחייבת נעשית על תשריט היתר או בידי מודד.</div>'
             '<div class="legend" style="margin:8px 0 4px">'
             + " ".join(f'<span>{tag(k)}</span>' for k in ("מערכת", "מסמך", "חישוב", "כלל אצבע", "חסר", "סותר"))
             + '</div>')

    # 01 שורה תחתונה
    n += 1
    bl = f'<div class="alert"><b>מצב קיים:</b> {e(p["headline"])}</div>'
    cards = [("ברוטו בנוי", num(t.get("gross_sqm"), 'מ"ר')), ("יח\"ד", num(t.get("units"))),
             ("גודל ממוצע נטו", num(t.get("avg_net_sqm"), 'מ"ר')), ("מקדם קיים", num(t.get("coefficient")))]
    bl += table(["", "ערך"], [f'<tr><td><b>{e(k)}</b></td><td class="num">{e(v)}</td></tr>' for k, v in cards],
                [None, "110px"])
    bl += f'<p><b>רמת דיוק:</b> {dots(p.get("certainty"))} — '
    bl += e("מדידה מתשריט" if int(p.get("certainty") or 0) >= 3 else "פוליגון מערכת וכלל אצבע") + ".</p>"
    if p.get("missing"):
        bl += f'<p><b>חסר:</b> {e(" · ".join(m["item"] for m in p["missing"]))} — ראה נספח.</p>'
    S.append(sec(n, "שורה תחתונה", bl))

    # 02 טבלת היחידות הקיימות
    n += 1
    rows = []
    for r in p.get("rows") or []:
        alt = (f'<div class="note">ערך שני: {e(r["alt"])} ({e(r.get("alt_source"))})</div>'
               if r.get("source") == "סותר" else "")
        rows.append(f'<tr><td><b>{e(r.get("label"))}</b></td>'
                    f'<td class="num">{e(num(r.get("value"), r.get("unit", "")))}</td>'
                    f'<td>{tag(r.get("source"))}</td><td>{e(r.get("note"))}{alt}</td></tr>')
    S.append(sec(n, "יחידות קיימות וגודלן",
                 '<p>הגודל הממוצע הוא ברוטו פחות גרעין המדרגות, חלקי מספר היחידות. כל שורה עם מקורה.</p>'
                 + table(["נתון", "ערך", "מקור", "הערה"], rows, [None, "96px", "74px", None])))

    # 03 מבנים
    n += 1
    bs = p.get("buildings") or []
    if bs:
        rows = [f'<tr><td><b>{e(b.get("id"))}</b></td>'
                f'<td class="num">{e(b.get("floors_above_ground"))}</td>'
                f'<td class="num">{e(b.get("residential_floors"))}</td>'
                f'<td class="num">{e(num(b.get("footprint_sqm")))}</td>'
                f'<td class="num">{e(num(b.get("gross_sqm")))}</td>'
                f'<td class="num">{e(b.get("units"))}</td>'
                f'<td>{e(b.get("primary_use"))}</td>'
                f'<td class="num">{e(b.get("year_built"))}</td>'
                f'<td class="num">{e(b.get("height_m"))}</td></tr>' for b in bs]
        inner = ('<p>קומות למגורים הן הקומות הבנויות פחות קומת עמודים, והן שמכפילות את טביעת הרגל.</p>'
                 + table(["מבנה", "קומות", "למגורים", "טביעת רגל", "ברוטו", 'יח"ד', "שימוש", "שנה", "גובה"], rows,
                         ["54px", "48px", "56px", "72px", "68px", "48px", None, "48px", "52px"]))
    else:
        inner = "<p>אין מבנים על החלקה.</p>"
    S.append(sec(n, "מבנים על החלקה", inner, brk=True))

    # 04 מאושר מול בנוי
    n += 1
    pm = p.get("permit")
    if pm:
        rows = [f'<tr><td>{e(k)}</td><td class="num">{e(v)}</td></tr>' for k, v in (
            ("מספר היתר", pm.get("permit_number")), ("שנה", pm.get("year")),
            ('יח"ד מאושרות', pm.get("authorized_units")), ("קומות מאושרות", pm.get("authorized_floors")),
            ("שטח מאושר", num(pm.get("authorized_area_sqm"), 'מ"ר')))]
        inner = table(["נתון", "ערך"], rows, [None, "120px"])
        inner += f'<p>{e(p.get("built_vs_permit") or "—")}</p>'
        inner += '<div class="note">היתר אינו מצב קיים: סגירות מרפסות, הרחבות ופיצולים מאוחרים אינם מופיעים בו.</div>'
    else:
        inner = '<p>לא נמצא היתר בנייה במערכת לנכס. מה שבנוי בפועל הוא המקור היחיד.</p>'
    S.append(sec(n, "מאושר מול בנוי", inner))

    # 05 אימות
    n += 1
    tc = p.get("tabu_check"); m = p.get("measurement")
    inner = ""
    if tc:
        inner += (f'<p>חציון שטח בטאבו {num(tc.get("tabu_median"), SQM)}, פער של '
                  f'{e(num(tc.get("gap_pct")))}% מול החישוב. נסח טאבו נמוך בדרך כלל ב-'
                  f'{e(tc.get("expected_pct", "15–20"))}% מהמציאות.</p>')
    else:
        inner += '<p>לא נמצא חציון שטח בטאבו לאימות הגודל הממוצע.</p>'
    if m:
        inner += (f'<p><b>מדידה:</b> גודל ממוצע {num(m.get("avg_net"), SQM)}'
                  + (f', ברוטו {num(m.get("gross"), SQM)}' if m.get("gross") else "")
                  + f' ({e(m.get("source"))}). המדידה גוברת על ההערכה.</p>')
    else:
        inner += '<p>אין מדידה. מדידה מתשריט היתר מעלה את רמת הדיוק לשלוש נקודות.</p>'
    S.append(sec(n, "אימות מול טאבו ומדידה", inner))

    # נספח
    apx = ""
    if p.get("missing"):
        apx += table(["מה חסר", "למה משנה", "איך משיגים"],
                     [f'<tr><td>{e(x["item"])}</td><td>{e(x.get("why"))}</td><td>{e(x.get("how"))}</td></tr>'
                      for x in p["missing"]])
    if p.get("flags"):
        apx += "<ul>" + "".join(f"<li>{e(f)}</li>" for f in p["flags"]) + "</ul>"
    if p.get("refs"):
        apx += table(["נושא", "מקור", "מזהה"],
                     [f'<tr><td>{e(r["topic"])}</td><td>{e(r["source"])}</td><td>{e(r.get("id"))}</td></tr>'
                      for r in p["refs"]])
    if apx:
        S.append('<section><div class="shead"><span class="snum">נ</span><h2>נספח · מה חסר, דגלים ומקורות</h2></div>'
                 f'<div class="body">{apx}</div></section>')

    return (f'<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
            f'<title>מצב קיים – {e(pc.get("address",""))}</title>'
            f'<style>/*FONTFACE*/\n/*STYLE*/\n</style></head><body>{cover}<div class="pg">{intro}{"".join(S)}'
            '<div class="disclaimer">השטחים כאן הם הערכה מנתוני מערכת וכללי אצבע, לא מדידה, ואינם תחליף למדידת מודד או '
            'לתשריט היתר. היתר אינו מעיד על המצב הבנוי בפועל.</div></div></body></html>')


def for_gng(p):
    t = p.get("totals") or {}
    bs = p.get("buildings") or []
    return {
        "existing_buildings": bs,
        "rows": p.get("rows") or [],
        "rights_rows": {"existing_gross": t.get("gross_sqm"), "existing_coefficient": t.get("coefficient")},
        "economics": {"existing": {"buildings": bs, "units": t.get("units"),
                                   "tabu_median": (p.get("tabu_check") or {}).get("tabu_median")},
                      "demolish_sqm": t.get("gross_sqm")},
        "certainty": p.get("certainty"),
        "flags": p.get("flags") or [],
        "missing": p.get("missing") or [],
    }


if __name__ == "__main__":
    src, outdir = sys.argv[1], pathlib.Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    p = json.load(open(src, encoding="utf-8"))
    if "--no-gate" not in sys.argv:
        err, warn = gate.check(p)
        for w in warn: print("⚠", w)
        if err:
            for x in err: print("✗", x)
            sys.exit("gate FAIL — fix existing.json")
    pc = p["parcel"]
    slug = re.sub(r"[ ,]+", "-", str(pc.get("address") or f'{pc.get("gush")}-{pc.get("helka")}')).strip("-")
    html = bidi.process(build_html(p))
    tmp = outdir / f".existing-{slug}.html"
    tmp.write_text(html, encoding="utf-8")
    pdf = outdir / f"מצב-קיים-{slug}.pdf"
    render.build(tmp, pdf,
                 f'מצב קיים · גוש {pc.get("gush","—")} חלקה {pc.get("helka","—")} · {pc.get("address","")}',
                 f'מצב קיים – {pc.get("address","")}', "בדיקת מצב קיים · מקור נתונים: Snapland")
    tmp.unlink(missing_ok=True)
    (outdir / f"existing_for_gng-{slug}.json").write_text(
        json.dumps(for_gng(p), ensure_ascii=False, indent=1), encoding="utf-8")
