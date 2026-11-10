# החוזים — inputs.json ו-existing.json

## inputs.json — הקלט ל-`scripts/existing.py`
רק מספרים. כל ערך כבר נשלף או נמסר; הסקריפט לא פונה לשום מקור.

```jsonc
{
  "lot_area": 765,              // מ"ר. בלעדיו אין מקדם קיים
  "stair_per_floor": 15,        // אופציונלי. ברירת מחדל 15 מ"ר לקומה לכל כניסה
  "tabu_median": 49,            // אופציונלי. חציון שטח יחידה בנסח / בעסקאות
  "measurement": {"avg_net": 71.5, "gross": 1004, "source": "permit-measurement, היתר 1966"},
  "buildings": [
    {"id": "A", "snap_id": "bui-…", "footprint_sqm": 251, "floors_above_ground": 4,
     "residential_floors": 4,   // אופציונלי. ברירת מחדל: קומות פחות קומת עמודים
     "has_pillar_floor": false, "height_m": 11.5, "year_built": 1966,
     "primary_use": "מגורים", "entrances": 1, "units": 16}
  ]
}
```

הסקריפט מחזיר `totals`, `buildings`, `rows` (שמונה השורות), `tabu_check`, `certainty`, `flags`, `missing`.
`certainty` יוצא 2 בלי מדידה ו-3 איתה.

## existing.json — החוזה של הסקיל
מה ש-`scripts/gate.py` בודק ו-`scripts/build_report.py` מפיק ממנו. דוגמה מלאה: `tests/sanhedrin7_existing.json`.

```jsonc
{
  "parcel": {"address": "סנהדרין 7, תל אביב-יפו", "gush": 6106, "helka": 399,
             "neighborhood": "פלורנטין", "lot_area": 765, "snap_id": "…"},
  "as_of": "10.11.2026",
  "status": "בנוי",                       // בנוי · ריק · חלקית
  "headline": "משפט אחד עם המספרים: כמה מבנים, קומות, ברוטו, יח\"ד, גודל ממוצע ומקדם קיים.",
  "buildings": [ /* פלט existing.py + source לכל מבנה */ ],
  "totals":    { /* פלט existing.py כמות שהוא */ },
  "rows":      [ /* שמונה השורות, כל אחת value, unit, source, note */ ],
  "tabu_check": {"tabu_median": 49, "gap_pct": 16.95, "expected_pct": "15–20"},
  "permit":    {"permit_number": "…", "year": 1966, "authorized_units": 16,
                "authorized_floors": 4, "authorized_area_sqm": 1004, "source": "מערכת"},
  "built_vs_permit": "משפט: מה תואם, מה חורג, ומה ההיתר לא מראה.",
  "measurement": null,                    // או {avg_net, gross, source} כשיש מדידה
  "certainty": 2,                         // 1–4, מוצג ●●○○
  "missing":  [ {"item": "…", "why": "…", "how": "…"} ],
  "flags":    ["…"],
  "refs":     [ {"topic": "מבנה", "source": "Snapland buildings", "id": "bui-…"} ]
}
```

- תגי מקור מותרים: `מערכת` · `מסמך` · `חישוב` · `כלל אצבע` · `הנחה` · `חסר` · `סותר` (עם `alt` ו-`alt_source`) · `קלט משתמש` · `החלטה`.
- שמונה השורות חייבות להופיע כולן, גם כשהערך `null` — אז המקור `חסר` וה-`note` אומר איך משלימים.
- `status: "ריק"` — בלי מבנים, בלי טבלה; הדוח אומר שהחלקה ריקה ומה המקור לכך.
- `existing_for_gng.json` (נוצר בבנייה) = `existing_buildings`, `rows`, `rights_rows`
  (`existing_gross`, `existing_coefficient`), `economics` (`existing`, `demolish_sqm`), `certainty`, `flags`, `missing` —
  במבנה שדוח הכדאיות צורך.
