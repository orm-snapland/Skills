#!/usr/bin/env python3
"""בדיקות הסקיל: חישוב, שומר סף ובניית הדוח.   python3 tests/run_tests.py

אין תלות חיצונית: ה-PDF עצמו לא נבנה כאן (דורש playwright), רק ה-HTML וקובץ ההעברה.
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
import existing, gate, build_report  # noqa: E402


def test_calc():
    inp = json.load(open(HERE / "sanhedrin7_inputs.json", encoding="utf-8"))
    t = existing.compute(inp)["totals"]
    # אומת מול אקסל המזמין (סנהדרין 7, 06.10.2026)
    assert t["gross_sqm"] == 1004.0, t
    assert t["units"] == 16.0, t
    assert t["avg_net_sqm"] == 59.0, t
    assert t["coefficient"] == 1.31, t
    assert t["service_ratio"] == 0.0598, t
    print("calc ok")


def test_gate():
    p = json.load(open(HERE / "sanhedrin7_existing.json", encoding="utf-8"))
    err, _ = gate.check(p)
    assert not err, err
    broken = json.loads(json.dumps(p, ensure_ascii=False))
    broken["totals"]["gross_sqm"] = 2000
    assert gate.check(broken)[0], "ברוטו שלא מסתכם ממבנים היה צריך להיכשל"
    broken2 = json.loads(json.dumps(p, ensure_ascii=False))
    broken2["rows"] = broken2["rows"][:4]
    assert gate.check(broken2)[0], "טבלה חסרת שורות הייתה צריכה להיכשל"
    print("gate ok")


def test_report():
    p = json.load(open(HERE / "sanhedrin7_existing.json", encoding="utf-8"))
    html = build_report.build_html(p)
    for must in ("מצב קיים", "יחידות קיימות וגודלן", "מאושר מול בנוי", "1,004"):
        assert must in html, must
    assert "→" not in html, "חץ בטקסט נשבר ב-RTL"
    assert "/*FONTFACE*/" in html and "/*STYLE*/" in html
    g = build_report.for_gng(p)
    assert g["economics"]["demolish_sqm"] == 1004.0, g
    assert g["rights_rows"]["existing_coefficient"] == 1.31, g
    assert g["economics"]["existing"]["units"] == 16.0, g
    print("report ok")


if __name__ == "__main__":
    existing.self_test()
    gate.self_test()
    test_calc()
    test_gate()
    test_report()
    print("all ok")
