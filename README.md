# Snapland Skills

סקילים של Claude לעבודת נדל"ן בישראל. כאן נמצאת רק הגרסה הסופית של כל סקיל. גרסאות קודמות ופלטי דוגמה שמורים ב-Drive (Snapland Skills - דוחות וגרסאות).

| סוג | תיקייה | סקיל | מה הוא עושה |
|---|---|---|---|
| 1 · דוח כדאיות | `01-feasibility-report/` | `go-no-go-v3` · `planning-check` | Go / גבולי / No-Go ודוח חלופות, לכל שימוש וסוג עסקה · בדיקה תכנונית (4 מקורות, תקדימים) כסקיל עצמאי |
| 2 · בדיקת מצב קיים | `02-existing-state/` | `permit-measurement` | מדידת היתר: פוליגונים לדירות, משותף ומרפסות → PDF + אקסל |
| 3 · סקר שוק | `03-market-survey/` | עוד לא נבנה | — |
| משותף | `shared/` | `israel-massing-rules` | חוקי הבינוי. דוח הכדאיות (שלב חלופות) קורא אותם |

## תלויות
- `go-no-go-v3` דורש את `israel-massing-rules` מותקן לצדו, ואת ה-MCP של Snapland ישראל.
- `planning-check` דורש את ה-MCP של Snapland ישראל; עומד בפני עצמו וגם משמש קלט לדוח הכדאיות.
- `permit-measurement` עובד עצמאית: Python, shapely, openpyxl, playwright.

## התקנה
כל תיקיית סקיל (התיקייה שיש בה `SKILL.md`) נארזת ל-`.skill` ומותקנת ב-Claude.
