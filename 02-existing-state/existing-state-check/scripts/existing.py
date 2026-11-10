#!/usr/bin/env python3
"""מצב קיים מנתוני מערכת — טבלת היחידות הקיימות, מקדם קיים ודגלים.

    python3 existing.py inputs.json            # JSON ל-stdout
    python3 existing.py inputs.json --indent 1
    python3 existing.py --self-test

inputs.json (ראה references/contract.md §inputs):
    lot_area, stair_per_floor (ברירת מחדל 15), tabu_median, measurement{avg_net,gross,source},
    buildings[]: footprint_sqm, floors_above_ground, residential_floors?, has_pillar_floor,
                 height_m, year_built, primary_use, entrances, units

הסקריפט לא שולף כלום ולא שואל כלום. כל קלט מגיע מ-Snapland או ממסמך, והתיוג נקבע בסקיל.
"""
import argparse, json, sys

STAIR_PER_FLOOR = 15.0        # מ"ר לקומה לכל כניסה — חדר מדרגות בבניין קיים
TABU_LOW, TABU_HIGH = 0.15, 0.20   # נסח טאבו נמוך ב-15–20% מהמציאות
FLOOR_H_MIN, FLOOR_H_MAX = 2.6, 3.5


def _num(x):
    return None if x is None else round(float(x), 2)


def building_rows(b, stair_per_floor):
    floors = float(b.get("floors_above_ground") or 0)
    res = b.get("residential_floors")
    res = float(res) if res is not None else max(floors - (1 if b.get("has_pillar_floor") else 0), 0)
    fp = float(b.get("footprint_sqm") or 0)
    entrances = float(b.get("entrances") or 1)
    gross = fp * res
    core = stair_per_floor * res * entrances
    return {
        "id": b.get("id") or b.get("snap_id") or "—",
        "footprint_sqm": _num(fp),
        "floors_above_ground": _num(floors),
        "residential_floors": _num(res),
        "entrances": _num(entrances),
        "units": b.get("units"),
        "primary_use": b.get("primary_use"),
        "year_built": b.get("year_built"),
        "height_m": _num(b.get("height_m")),
        "gross_sqm": _num(gross),
        "core_sqm": _num(core),
        "net_sqm": _num(gross - core),
    }


def compute(inp):
    stair = float(inp.get("stair_per_floor") or STAIR_PER_FLOOR)
    lot = inp.get("lot_area")
    bs = [building_rows(b, stair) for b in inp.get("buildings") or []]
    if not bs:
        raise ValueError("inputs.buildings ריק — בלי מבנה אין מצב קיים. נכס ריק נרשם כך במפורש.")

    gross = sum(b["gross_sqm"] for b in bs)
    core = sum(b["core_sqm"] for b in bs)
    net = gross - core
    units = sum(float(b["units"]) for b in bs if b.get("units"))
    flags, missing = [], []

    avg_net = net / units if units else None
    if not units:
        missing.append({"item": "מספר יח\"ד",
                        "why": "בלי מספר היחידות אין גודל ממוצע ואין תמורה לבעלים",
                        "how": "נסח טאבו, יחידות דיוור או ספירת תיבות דואר. Snapland לרוב בלי units_count לבניין"})

    totals = {
        "lot_area": _num(lot),
        "footprint_sqm": _num(sum(b["footprint_sqm"] for b in bs)),
        "floors": _num(max(b["floors_above_ground"] for b in bs)),
        "entrances": _num(sum(b["entrances"] for b in bs)),
        "units": _num(units) if units else None,
        "gross_sqm": _num(gross),
        "core_sqm": _num(core),
        "net_sqm": _num(net),
        "avg_net_sqm": _num(avg_net),
        "service_ratio": round(core / gross, 4) if gross else None,
        "coefficient": _num(gross / float(lot)) if lot else None,
    }

    # סבירות מול טאבו: נסח נמוך ב-15–20% מהמציאות
    tabu = inp.get("tabu_median")
    tabu_check = None
    if tabu and avg_net:
        gap = (avg_net - float(tabu)) / avg_net
        tabu_check = {"tabu_median": _num(tabu), "gap_pct": _num(gap * 100),
                      "expected_pct": f"{int(TABU_LOW * 100)}–{int(TABU_HIGH * 100)}"}
        if gap < 0:
            flags.append("הטאבו גבוה מהחישוב — סימן לשטח שנספר פעמיים, למרפסות בפוליגון או לפיצול יחידות")
        elif gap > 0.30:
            flags.append("פער מול הטאבו מעל 30% — בדוק הרחבות, סגירות מרפסות או טביעת רגל שכוללת מרפסות")
    elif not tabu:
        missing.append({"item": "חציון שטח בטאבו",
                        "why": "מאמת את הגודל הממוצע מול מקור שני",
                        "how": "נסח רישום או עסקאות על החלקה"})

    for b in bs:
        if b["height_m"] and b["floors_above_ground"]:
            r = b["height_m"] / b["floors_above_ground"]
            if not (FLOOR_H_MIN <= r <= FLOOR_H_MAX):
                flags.append(f"מבנה {b['id']}: גובה חלקי קומות {r:.2f} מ' מחוץ לטווח "
                             f"{FLOOR_H_MIN}–{FLOOR_H_MAX} — קומת עמודים או מבנה גג; לא בונים על הגובה")
        if b["residential_floors"] != b["floors_above_ground"]:
            flags.append(f"מבנה {b['id']}: קומת עמודים הופחתה מהקומות למגורים "
                         f"({b['floors_above_ground']:.0f} בנויות, {b['residential_floors']:.0f} למגורים)")

    m = inp.get("measurement")
    certainty = 3 if m else 2
    if m:
        flags.append("מדידה קיימת גוברת על ההערכה מהמערכת; ההערכה נשארת בטבלה להשוואה")
    else:
        missing.append({"item": "מדידה מתשריט היתר",
                        "why": "מעלה את רמת הדיוק משתי נקודות לשלוש",
                        "how": "להעלות את ההיתר ולהריץ את הסקיל permit-measurement"})

    rows = [
        {"label": "טביעת רגל", "value": totals["footprint_sqm"], "unit": "מ\"ר", "source": "מערכת",
         "note": "פוליגון המבנה; לרוב כולל מרפסות"},
        {"label": "קומות · כניסות", "value": f"{totals['floors']:.0f} · {totals['entrances']:.0f}",
         "unit": "", "source": "מערכת", "note": "קומות למגורים אחרי הפחתת קומת עמודים"},
        {"label": "יח\"ד", "value": totals["units"], "unit": "", "source": "מערכת" if units else "חסר",
         "note": "" if units else "להשלים מנסח או מיחידות דיוור"},
        {"label": "ברוטו בנוי", "value": totals["gross_sqm"], "unit": "מ\"ר", "source": "חישוב",
         "note": "טביעת רגל כפול קומות למגורים"},
        {"label": "שטח שירות (גרעין)", "value": totals["core_sqm"], "unit": "מ\"ר", "source": "כלל אצבע",
         "note": f"{stair:.0f} מ\"ר לקומה לכל כניסה"},
        {"label": "גודל ממוצע נטו", "value": totals["avg_net_sqm"], "unit": "מ\"ר", "source": "חישוב",
         "note": "ברוטו פחות גרעין, חלקי יח\"ד"},
        {"label": "סבירות מול טאבו", "value": (f"{tabu_check['gap_pct']:.0f}%" if tabu_check else None),
         "unit": "", "source": "חישוב" if tabu_check else "חסר",
         "note": f"מצופה {tabu_check['expected_pct']}%" if tabu_check else "אין חציון טאבו"},
        {"label": "מדידה", "value": (m or {}).get("avg_net"), "unit": "מ\"ר",
         "source": "מסמך" if m else "חסר",
         "note": (m or {}).get("source") or "אין מדידה; ההערכה היא כלל אצבע"},
    ]

    return {"totals": totals, "buildings": bs, "rows": rows, "tabu_check": tabu_check,
            "certainty": certainty, "flags": flags, "missing": missing}


def self_test():
    inp = {"lot_area": 496, "tabu_median": 62,
           "buildings": [{"id": "A", "footprint_sqm": 188, "floors_above_ground": 4,
                          "has_pillar_floor": True, "height_m": 11.4, "entrances": 1, "units": 6,
                          "primary_use": "מגורים", "year_built": 1962}]}
    r = compute(inp)
    assert r["totals"]["gross_sqm"] == 564.0, r["totals"]
    assert r["totals"]["core_sqm"] == 45.0, r["totals"]
    assert r["totals"]["avg_net_sqm"] == 86.5, r["totals"]
    assert r["totals"]["coefficient"] == 1.14, r["totals"]
    assert r["certainty"] == 2
    assert any("קומת עמודים" in f for f in r["flags"])
    no_units = {"lot_area": 400, "buildings": [{"id": "A", "footprint_sqm": 100,
                                                "floors_above_ground": 3, "entrances": 1}]}
    r2 = compute(no_units)
    assert r2["totals"]["avg_net_sqm"] is None
    assert any("יח\"ד" in x["item"] for x in r2["missing"])
    try:
        compute({"buildings": []})
    except ValueError:
        pass
    else:
        raise AssertionError("מבנים ריקים היו צריכים להיכשל")
    print("self-test ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="?", help="נתיב ל-inputs.json")
    ap.add_argument("--indent", type=int, default=1)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test(); sys.exit(0)
    if not a.inputs:
        ap.error("חסר inputs.json")
    try:
        out = compute(json.load(open(a.inputs, encoding="utf-8")))
    except ValueError as exc:
        sys.exit(str(exc))
    print(json.dumps(out, ensure_ascii=False, indent=a.indent))
