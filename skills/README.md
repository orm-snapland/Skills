# skills/

כאן גרים ה-Skills של Snapland, תיקייה אחת לכל Skill. הריפו מתחיל בלי Skills אמיתיים: אל תוסיפו לכאן fixture של בדיקות (אלה יושבים תחת `tests/`).

כדי להוסיף Skill:

1. העתיקו את `templates/your-skill-name/` אל `skills/<שם>/`.
2. שנו את שם התיקייה ואת השדה `name` לאותו kebab-case.
3. כתבו `description` לפי הכללים ב-README הראשי (כולל ביטויי טריגר בעברית).
4. החליפו את גוף `SKILL.md`, והוסיפו `scripts/`, `references/`, `assets/` רק אם צריך.
5. מלאו `evals/evals.json` (לפחות 3 מקרים) ו-`evals/triggers.json`.
6. הריצו `python tooling/validate_skills.py`.

`metadata.version` הוא semver במרכאות, למשל `"0.1.0"`. העלו אותו בכל שינוי שעולה ל-API.

---

Production skills live here, one folder per skill. This directory starts empty on purpose. Test fixtures belong under `tests/`, not here.

Copy `templates/your-skill-name/` to `skills/<name>/`, keep `name` identical to the folder, and follow the root README before uploading.
