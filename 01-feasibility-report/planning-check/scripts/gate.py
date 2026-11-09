#!/usr/bin/env python3
"""שומר סף ל-planning.json. יציאה 0 = PASS.   python3 gate.py planning.json [--self-test]"""
import sys, json, re

SOURCES4 = ["מתאר", "תוכנית אב", "מדיניות", "תב\"עות 500 מ'"]
LEVELS = {"מאושר", "בהליך", "שכבה"}
TAGS = {"מערכת", "מסמך", "חישוב", "הנחה", "חסר", "סותר", "קלט משתמש"}


def check(p):
    err, warn = [], []
    for k in ("parcel", "realizable", "sources", "plans_on_parcel"):
        if not p.get(k): err.append(f"שדה חובה חסר: {k}")
    src = p.get("sources", {})
    for k in SOURCES4:
        s = src.get(k)
        if not s or not s.get("status"): err.append(f"המקור \"{k}\" לא נבדק — status: נמצא / לא חל / חסר")
        elif s["status"] == "חסר" and not s.get("how"): err.append(f"המקור \"{k}\" חסר בלי how — איך משלימים")
    for grp in ("plans_on_parcel", "plans_500m"):
        for t in p.get(grp, []):
            if t.get("level") not in LEVELS: err.append(f"{grp}: {t.get('plan')} בלי level חוקי (מאושר / בהליך / שכבה)")
            if t.get("source") and t["source"] not in TAGS: err.append(f"{t.get('plan')}: תג מקור לא חוקי \"{t['source']}\"")
            if t.get("source") == "סותר" and not (t.get("alt") and t.get("alt_source")): err.append(f"{t.get('plan')}: \"סותר\" בלי alt / alt_source")
            if "ראה הערה" in json.dumps(t, ensure_ascii=False) and t.get("source") == "מערכת":
                err.append(f"{t.get('plan')}: \"ראה הערה\" מתויג מערכת — צריך חישוב")
    for t in p.get("plans_500m", []):
        if t.get("distance_m") is None: err.append(f"plans_500m: {t.get('plan')} בלי distance_m")
        elif t["distance_m"] > 500: err.append(f"plans_500m: {t.get('plan')} במרחק {t['distance_m']} מ' — מחוץ לרדיוס")
    if not any(t.get("level") == "מאושר" for t in p.get("plans_on_parcel", [])):
        warn.append("אין תכנית מאושרת על החלקה — ודא שהזכות בת־המימוש נכונה, או ציין שאין")
    for pr in p.get("precedents", []):
        for k in ("plan", "gives", "baseline", "gap"):
            if not pr.get(k): err.append(f"תקדים {pr.get('plan')}: חסר {k}")
    for r in p.get("regulatory", []):
        if re.search(r"77", r.get("topic", "")) and not re.search(r"צד|שני הצדדים|כל הרחוב|כל הרובע|כל האזור|לא רלוונטי", json.dumps(r, ensure_ascii=False)):
            warn.append(f"הודעה 77–78 בלי ציון צד הרחוב: {r.get('topic')}")
    if "→" in json.dumps(p, ensure_ascii=False): err.append("חץ → בטקסט — נשבר ב-RTL; לנסח מחדש")
    return err, warn


def self_test():
    bad = {"parcel": {"address": "x"}, "realizable": "x", "sources": {"מתאר": {"status": "חסר"}}, "plans_on_parcel": [{"plan": "1", "level": "x"}]}
    e, _ = check(bad); assert len(e) >= 4, e
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv: self_test(); sys.exit(0)
    e, w = check(json.load(open(sys.argv[1], encoding="utf-8")))
    for x in w: print("⚠", x)
    for x in e: print("✗", x)
    print("PASS" if not e else f"FAIL ({len(e)})"); sys.exit(1 if e else 0)
