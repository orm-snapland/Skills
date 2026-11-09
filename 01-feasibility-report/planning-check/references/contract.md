# planning.json — החוזה

```jsonc
{
  "parcel": {"address": "סנהדרין 7, תל אביב-יפו", "gush": 6106, "helka": 399, "neighborhood": "בבלי",
             "lot_area": 496, "snap_id": "…", "lat": 32.09, "lon": 34.79},
  "as_of": "09.11.2026",
  "realizable": "תכנית רובע 4 (3729א) היא הזכות בת־המימוש: מעטפת — תכסית בקווי הבניין × 6 קומות + 2 קומות גג.",
  "potential":  "תא/5500 בהערות ציבור: מקדם 4.0 ו-9 קומות — אם תאושר, בסיס לתב\"ע עתידית.",
  "sources": {                                   // ארבעתם חובה, כל אחד עם status
    "מתאר":        {"status": "נמצא", "summary": "…", "source": "מערכת"},
    "תוכנית אב":   {"status": "חסר",  "how": "לבקש מהעירייה"},
    "מדיניות":     {"status": "נמצא", "items": ["9112"], "source": "מערכת"},
    "תב\"עות 500 מ'": {"status": "נמצאו 4", "source": "מערכת"}
  },
  "plans_on_parcel": [ {"plan": "3729א", "name": "רובע 4", "gives": "…", "status": "מאושר", "level": "מאושר", "source": "מערכת"} ],
  "setbacks": [ {"side": "אחורי (מערב)", "value": "5 מ'", "source": "מערכת"} ],          // אופציונלי
  "plans_500m": [ {"plan": "507-…", "name": "…", "status": "מופקדת", "level": "בהליך", "distance_m": 150, "gives": "…"} ],
  "precedents": [ {"plan": "507-…", "distance_m": 150, "gives": "24 קומות", "baseline": "20 קומות", "gap": "+4 קומות", "use": "…"} ],
  "regulatory": [ {"topic": "הודעה לפי 77–78 …", "impact": "…", "status": "20.01.2025"} ],
  "ring_50m":   [ {"parcel": "6106/400", "address": "…", "floors": 4, "use": "מגורים", "year": 1962, "permit": "—"} ],
  "missing":    [ {"item": "תוכנית אב", "why": "כיוון עירוני", "how": "לבקש מהעירייה"} ],
  "flags":      ["…"],
  "refs":       [ {"topic": "זכויות", "source": "Snapland linked-build-rights", "id": "…"} ]
}
```
- `level` חייב להיות אחד: `מאושר` · `בהליך` · `שכבה`.
- `source` (תג): `מערכת` · `מסמך` · `חישוב` · `הנחה` · `חסר` · `סותר` (עם `alt` ו-`alt_source`).
- `precedents` ריק = אין תקדים (נכתב בדוח במפורש).
- `planning_for_gng.json` (נוצר בבנייה) = `sources` + `plans_500m` + `precedents` במבנה ש-`data.json["planning"]` של דוח הכדאיות מצפה לו.
