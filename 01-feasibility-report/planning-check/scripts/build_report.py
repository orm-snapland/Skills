#!/usr/bin/env python3
"""planning.json → PDF בעברית + planning_for_gng.json.

    python3 build_report.py planning.json <outdir> [--no-gate]

מריץ gate.py, בונה HTML בסגנון דוחות Snapland (assets/report.css), bidi.py, render.py.
"""
import sys, json, pathlib, html as H, re
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate, bidi, render

TAG = {"מערכת": "t-sys", "מסמך": "t-doc", "חישוב": "t-cal", "הנחה": "t-asm", "חסר": "t-mis", "סותר": "t-con", "קלט משתמש": "t-usr"}
e = lambda s: H.escape(str(s if s is not None else "—"))


def tag(s):
    return f'<span class="tag {TAG.get(s, "t-sys")}">{e(s)}</span>' if s else ""


def sec(n, title, inner, brk=False):
    st = ' style="page-break-before:always"' if brk else ""
    return f'<section{st}><div class="shead"><span class="snum">{n:02d}</span><h2>{e(title)}</h2></div><div class="body">{inner}</div></section>'


def table(head, rows, widths=None):
    w = widths or [None] * len(head)
    th = "".join(f'<th{f" style=\"width:{x}\"" if x else ""}>{h}</th>' for h, x in zip(head, w))
    return f'<table class="gng"><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def plan_row(t, dist=False):
    d = f'<td class="num">{e(t.get("distance_m"))}</td>' if dist else ""
    alt = f'<div class="note">ערך שני: {e(t["alt"])} ({e(t.get("alt_source"))})</div>' if t.get("source") == "סותר" else ""
    return f'<tr>{d}<td><b>{e(t.get("plan"))}</b>{" — " + e(t["name"]) if t.get("name") else ""}</td><td>{e(t.get("gives"))}{alt}</td><td>{e(t.get("status"))}</td><td>{e(t.get("level"))}</td><td>{tag(t.get("source"))}</td></tr>'


def build_html(p):
    pc = p["parcel"]; n = 0; S = []
    title_place = f'{pc.get("address","")}' + (f' · {pc["neighborhood"]}' if pc.get("neighborhood") else "")
    gh = f'גוש {pc.get("gush","—")} חלקה {pc.get("helka","—")}'
    cover = (f'<div class="pg"><div class="cov"><div class="eyebrow">SNAPLAND</div><div class="t">בדיקה תכנונית</div>'
             f'<div class="s">מתאר · תוכנית אב · מדיניות · תב"עות ברדיוס 500 מ\'</div><div class="s">{e(p.get("as_of",""))}</div>'
             f'<div class="s">{e(gh)}</div><div class="s">{e(title_place)}</div></div></div>')
    intro = ('<div class="intro">המידע נאסף ממאגרים ממשלתיים ועירוניים באמצעות Snapland ומהנחות עבודה; מקור כל נתון מצוין לצידו. '
             'המידע מיועד להתמצאות בלבד ואינו מחייב — מידע תכנוני מחייב ניתן רק בתיק מידע מהוועדה המקומית.</div>'
             '<div class="legend" style="margin:8px 0 4px">' + " ".join(f'<span>{tag(k)}</span>' for k in ("מערכת", "מסמך", "חישוב", "הנחה", "חסר", "סותר")) + '</div>')
    # 01 bottom line
    n += 1
    miss = [k for k, v in p["sources"].items() if v.get("status") == "חסר"]
    bl = f'<div class="alert"><b>הזכות בת־המימוש:</b> {e(p["realizable"])}</div>'
    if p.get("potential"): bl += f'<p><b>פוטנציאל:</b> {e(p["potential"])}</p>'
    prec = p.get("precedents") or []
    bl += f'<p><b>תקדימים ברדיוס 500 מ\':</b> {len(prec)}' + (f' — המשמעותי: {e(prec[0]["plan"])} ({e(prec[0]["gap"])})' if prec else " — לא נמצא תקדים") + '.</p>'
    if miss: bl += f'<p><b>חסר:</b> {e(" · ".join(miss))} — ראה נספח.</p>'
    S.append(sec(n, "שורה תחתונה", bl))
    # 02 four sources
    n += 1
    rows = []
    for k in gate.SOURCES4:
        v = p["sources"].get(k, {})
        what = v.get("summary") or (" · ".join(v["items"]) if v.get("items") else "") or (f'איך משלימים: {v["how"]}' if v.get("how") else "—")
        rows.append(f'<tr><td><b>{e(k)}</b></td><td>{e(v.get("status"))}</td><td>{e(what)}</td><td>{tag(v.get("source") or ("חסר" if v.get("status") == "חסר" else ""))}</td></tr>')
    S.append(sec(n, "ארבעת המקורות", '<p>כל מקור נבדק; מקור שלא נמצא מסומן "חסר" עם הדרך להשלים.</p>' + table(["מקור", "סטטוס", "מה נמצא", "מקור"], rows, [None, "90px", None, "66px"])))
    # 03 plans on parcel (+ setbacks)
    n += 1
    inner = '<p>מאושר = זכות בת־מימוש · בהליך = פוטנציאל · שכבה = הקשר בלבד.</p>'
    inner += table(["תכנית", "מה קובעת כאן", "סטטוס", "מעמד", "מקור"], [plan_row(t) for t in p["plans_on_parcel"]], [None, None, "92px", "56px", "60px"])
    if p.get("setbacks"):
        inner += table(["קווי בניין", "ערך", "מקור"], [f'<tr><td>{e(s["side"])}</td><td>{e(s["value"])}</td><td>{tag(s.get("source"))}</td></tr>' for s in p["setbacks"]], [None, "80px", "66px"])
    S.append(sec(n, "תכניות החלות על החלקה", inner, brk=True))
    # 04 radius
    n += 1
    r5 = p.get("plans_500m") or []
    inner = (f'<p>{len(r5)} תכניות ברדיוס 500 מ\', לפי מרחק.</p>' + table(["מ'", "תכנית", "מה נותנת", "סטטוס", "מעמד", "מקור"], [plan_row(t, True) for t in r5], ["40px", None, None, "88px", "52px", "56px"])) if r5 else '<p>לא נמצאו תכניות ברדיוס 500 מ\'.</p>'
    S.append(sec(n, "תב\"עות ברדיוס 500 מ'", inner))
    # 05 precedents
    n += 1
    if prec:
        rows = [f'<tr><td><b>{e(x["plan"])}</b> · {e(x.get("distance_m"))} מ\'</td><td>{e(x["gives"])}</td><td>{e(x["baseline"])}</td><td><b>{e(x["gap"])}</b></td><td>{e(x.get("use"))}</td></tr>' for x in prec]
        inner = '<p>תכניות בסביבה שנותנות יותר מהמתאר כאן, באותו פרמטר — כלי מול העירייה.</p>' + table(["תכנית · מרחק", "מה נותנת", "מה המתאר נותן כאן", "הפער", "איך להשתמש"], rows)
    else:
        inner = '<p>לא נמצא תקדים ברדיוס 500 מ\'.</p>'
    S.append(sec(n, "תקדימים למשא ומתן", inner))
    # 06 regulatory
    n += 1
    reg = p.get("regulatory") or []
    S.append(sec(n, "התפתחויות רגולטוריות והחלטות", table(["נושא", "השפעה", "מעמד"], [f'<tr><td>{e(x["topic"])}</td><td>{e(x.get("impact"))}</td><td>{e(x.get("status"))}</td></tr>' for x in reg], [None, None, "96px"]) if reg else "<p>לא נמצאו.</p>"))
    # 07 ring
    n += 1
    ring = p.get("ring_50m") or []
    if ring:
        rows = [f'<tr><td>{e(x.get("parcel"))}</td><td>{e(x.get("address"))}</td><td class="num">{e(x.get("floors"))}</td><td>{e(x.get("use"))}</td><td class="num">{e(x.get("year"))}</td><td>{e(x.get("permit"))}</td></tr>' for x in ring]
        S.append(sec(n, "טבעת 50 מ'", '<p>מה בנוי צמוד לנכס — הקשר מיידי לגובה ולשימוש.</p>' + table(["חלקה", "כתובת", "קומות", "שימוש", "שנה", "היתר פעיל"], rows)))
    else:
        S.append(sec(n, "טבעת 50 מ'", "<p>לא נשלפה.</p>"))
    # appendix
    apx = ""
    if p.get("missing"):
        apx += table(["מה חסר", "למה משנה", "איך משיגים"], [f'<tr><td>{e(m["item"])}</td><td>{e(m.get("why"))}</td><td>{e(m.get("how"))}</td></tr>' for m in p["missing"]])
    if p.get("flags"):
        apx += '<ul>' + "".join(f"<li>{e(f)}</li>" for f in p["flags"]) + '</ul>'
    if p.get("refs"):
        apx += table(["נושא", "מקור", "מזהה"], [f'<tr><td>{e(r["topic"])}</td><td>{e(r["source"])}</td><td>{e(r.get("id"))}</td></tr>' for r in p["refs"]])
    if apx:
        S.append(f'<section><div class="shead"><span class="snum">נ</span><h2>נספח · מה חסר, דגלים ומקורות</h2></div><div class="body">{apx}</div></section>')
    body = "".join(S)
    return (f'<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>בדיקה תכנונית – {e(pc.get("address",""))}</title>'
            f'<style>/*FONTFACE*/\n/*STYLE*/\n</style></head><body>{cover}<div class="pg">{intro}{body}'
            '<div class="disclaimer">הבדיקה אינה תיק מידע, חוות דעת תכנונית או ייעוץ משפטי. סבירות אישור של תכנית בהליך היא הנחה, לא נתון.</div></div></body></html>')


def for_gng(p):
    out = {}
    for k, v in p["sources"].items():
        out[k] = dict(v)
    out.setdefault("תב\"עות 500 מ'", {})["items"] = p.get("plans_500m", [])
    out["תב\"עות 500 מ'"]["precedents"] = p.get("precedents", [])
    return {"planning": out, "plans_on_parcel": p["plans_on_parcel"], "regulatory": p.get("regulatory", []),
            "ring_50m": p.get("ring_50m", []), "realizable": p["realizable"]}


if __name__ == "__main__":
    src, outdir = sys.argv[1], pathlib.Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    p = json.load(open(src, encoding="utf-8"))
    if "--no-gate" not in sys.argv:
        err, warn = gate.check(p)
        for w in warn: print("⚠", w)
        if err:
            for x in err: print("✗", x)
            sys.exit("gate FAIL — fix planning.json")
    pc = p["parcel"]
    slug = re.sub(r"[ ,]+", "-", str(pc.get("address") or f'{pc.get("gush")}-{pc.get("helka")}')).strip("-")
    html = bidi.process(build_html(p))
    tmp = outdir / f".planning-{slug}.html"; tmp.write_text(html, encoding="utf-8")
    pdf = outdir / f"בדיקה-תכנונית-{slug}.pdf"
    render.build(tmp, pdf, f'בדיקה תכנונית · גוש {pc.get("gush","—")} חלקה {pc.get("helka","—")} · {pc.get("address","")}',
                 f'בדיקה תכנונית – {pc.get("address","")}', "בדיקה תכנונית · מקור נתונים: Snapland")
    tmp.unlink(missing_ok=True)
    (outdir / f"planning_for_gng-{slug}.json").write_text(json.dumps(for_gng(p), ensure_ascii=False, indent=1), encoding="utf-8")
