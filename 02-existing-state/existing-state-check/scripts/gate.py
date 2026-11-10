#!/usr/bin/env python3
"""שומר סף ל-existing.json. יציאה 0 = PASS.   python3 gate.py existing.json [--self-test]"""
import sys, json

TAGS = {"מערכת", "מסמך", "חישוב", "כלל אצבע", "הנחה", "חסר", "סותר", "קלט משתמש", "החלטה"}
STATUS = {"בנוי", "ריק", "חלקית"}
ROWS8 = ["טביעת רגל", "קומות · כניסות", "יח\"ד", "ברוטו בנוי", "שטח שירות (גרעין)",
         "גודל ממוצע נטו", "סבירות מול טאבו", "מדידה"]


def check(p):
    err, warn = [], []
    for k in ("parcel", "as_of", "headline", "status", "totals", "rows"):
        if not p.get(k): err.append(f"שדה חובה חסר: {k}")
    if p.get("status") and p["status"] not in STATUS:
        err.append(f"status חייב להיות אחד מ-{' / '.join(sorted(STATUS))}, התקבל \"{p['status']}\"")

    bs = p.get("buildings") or []
    if p.get("status") == "ריק":
        if bs: err.append("status \"ריק\" עם מבנים ברשימה")
        return err, warn
    if not bs: err.append("אין מבנים — נכס בנוי חייב לפחות מבנה אחד, או status \"ריק\"")

    t = p.get("totals") or {}
    gross = t.get("gross_sqm")
    if bs and gross:
        s = sum(float(b.get("gross_sqm") or 0) for b in bs)
        if s and abs(s - float(gross)) / float(gross) > 0.01:
            err.append(f"totals.gross_sqm ({gross}) לא מסתכם ממבנים ({round(s)})")
    if t.get("lot_area") and gross and not t.get("coefficient"):
        err.append("יש שטח מגרש וברוטו בלי מקדם קיים — סעיף \"קיים מול מותר\" צריך אותו")
    avg = t.get("avg_net_sqm")
    if avg is not None and not (20 <= float(avg) <= 300):
        err.append(f"גודל ממוצע נטו {avg} מ\"ר לא סביר — בדוק יח\"ד, קומות וטביעת רגל")
    if avg is None and not any("יח\"ד" in m.get("item", "") for m in p.get("missing") or []):
        err.append("אין גודל ממוצע ואין שורת \"חסר\" על יח\"ד")

    labels = [r.get("label") for r in p.get("rows") or []]
    for lbl in ROWS8:
        if lbl not in labels: err.append(f"חסרה שורה בטבלת היחידות הקיימות: {lbl}")
    for r in p.get("rows") or []:
        if r.get("source") not in TAGS: err.append(f"שורה \"{r.get('label')}\": תג מקור לא חוקי \"{r.get('source')}\"")
        if r.get("source") == "חסר" and not r.get("note"): err.append(f"שורה \"{r.get('label')}\": \"חסר\" בלי הסבר איך משלימים")
        if r.get("source") == "סותר" and not (r.get("alt") and r.get("alt_source")): err.append(f"שורה \"{r.get('label')}\": \"סותר\" בלי alt / alt_source")

    c = p.get("certainty")
    if c not in (1, 2, 3, 4): err.append("certainty חייב להיות 1–4 (●○○○ עד ●●●●)")
    if p.get("measurement") and c and int(c) < 3:
        err.append("יש מדידה אבל הוודאות נמוכה מ-3 — מדידה מהיתר שווה שלוש נקודות")

    tc = p.get("tabu_check")
    if tc and tc.get("gap_pct") is not None:
        g = float(tc["gap_pct"])
        if (g < 0 or g > 30) and not p.get("flags"):
            err.append(f"פער מול הטאבו {g:.0f}% חורג מ-0–30% בלי דגל")
    elif not tc:
        warn.append("אין בדיקת טאבו — הגודל הממוצע לא אומת מול מקור שני")

    if p.get("permit") and not p.get("built_vs_permit"):
        warn.append("יש היתר בלי משפט השוואה בין המאושר לבנוי")
    if "→" in json.dumps(p, ensure_ascii=False):
        err.append("חץ → בטקסט — נשבר ב-RTL; לנסח מחדש")
    return err, warn


def self_test():
    bad = {"parcel": {"address": "x"}, "as_of": "01.01.2026", "headline": "x", "status": "בנוי",
           "totals": {"lot_area": 400, "gross_sqm": 500, "avg_net_sqm": 5},
           "buildings": [{"gross_sqm": 100}], "rows": [{"label": "טביעת רגל", "source": "קסם"}],
           "certainty": 9}
    e, _ = check(bad)
    assert len(e) >= 6, e
    good = {"parcel": {"address": "x"}, "as_of": "01.01.2026", "headline": "x", "status": "בנוי",
            "totals": {"lot_area": 496, "gross_sqm": 564.0, "avg_net_sqm": 86.5, "coefficient": 1.14},
            "buildings": [{"gross_sqm": 564.0}],
            "rows": [{"label": l, "source": "חישוב", "note": "x"} for l in ROWS8],
            "tabu_check": {"gap_pct": 18}, "certainty": 2}
    e2, _ = check(good)
    assert not e2, e2
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test(); sys.exit(0)
    e, w = check(json.load(open(sys.argv[1], encoding="utf-8")))
    for x in w: print("⚠", x)
    for x in e: print("✗", x)
    print("PASS" if not e else f"FAIL ({len(e)})")
    sys.exit(1 if e else 0)
