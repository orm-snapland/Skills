# Snapland Skills

ריפו הבית של Claude Agent Skills של Snapland. Snapland בונה בוטים וסוכנים לנדל"ן בישראל. Skills שנכתבים כאן רצים ב-claude.ai, ב-Claude Code וב-Claude API. Git הוא מקור האמת: Skills מותאמים אישית לא מסתנכרנים לבד בין המשטחים.

המדריך המלא (פורמט, frontmatter, progressive disclosure, בדיקות, הפצה, אבטחה) נמצא ב-[docs/anthropic-skills-guide.md](docs/anthropic-skills-guide.md). רעיונות למבנה Skills בתחום הנדל"ן, כהצעות בלבד, נמצאים ב-[docs/real-estate-ideas.md](docs/real-estate-ideas.md). המקורות כתובים ב-[docs/sources.md](docs/sources.md).

הסקילים מסודרים לפי סוג העבודה. בכל תיקיית סוג יושבים הסקילים שלה, ו-`shared/` מחזיק ידע שכמה סקילים קוראים.

| סוג | תיקייה | סקיל | מה הוא עושה |
|---|---|---|---|
| 1 · דוח כדאיות | `01-feasibility-report/` | `go-no-go-v3` · `planning-check` | Go / גבולי / No-Go ודוח חלופות, לכל שימוש וסוג עסקה · בדיקה תכנונית (4 מקורות, תקדימים) כסקיל עצמאי |
| 2 · בדיקת מצב קיים | `02-existing-state/` | `existing-state-check` · `permit-measurement` | מה בנוי היום מנתוני Snapland: יח"ד, ברוטו, גרעין, גודל ממוצע ומקדם קיים (●●○○) · מדידת היתר: פוליגונים לדירות, משותף ומרפסות (●●●○) → PDF + אקסל |
| 3 · סקר שוק | `03-market-survey/` | עוד לא נבנה | — |
| משותף | `shared/` | `israel-massing-rules` | חוקי הבינוי. דוח הכדאיות (שלב החלופות) קורא אותם |

תלויות: `go-no-go-v3` דורש את `israel-massing-rules` מותקן לצדו ואת ה-MCP של Snapland ישראל. `planning-check` ו-`existing-state-check` דורשים את אותו MCP, עומדים בפני עצמם וגם משמשים קלט לדוח הכדאיות (שלב 1, צעדים 3 ו-6). `permit-measurement` עובד עצמאית מעל Python, shapely, openpyxl ו-playwright, ומזין את `existing-state-check` כשיש תשריט.

אין תיקיית `skills/` כללית: כל סקיל יושב בתיקיית הסוג שלו. דוגמאות לבדיקת הכלים יושבות תחת `tests/`.

## מבנה

```
01-feasibility-report/       # תיקיית סוג. README קצר + הסקילים שלה
  README.md
  <skill-name>/              # סקיל אחד
    SKILL.md                 # חובה: frontmatter + הוראות
    scripts/                 # אופציונלי. מריצים, לא קוראים, אלא אם כתוב אחרת
    references/              # אופציונלי. נטען רק כשמפנים אליו
    assets/                  # אופציונלי. תבניות וקבצי עזר
    stages/                  # אופציונלי. סקיל רב-שלבי
    evals/                   # בדיקות. לא נכנס ל-ZIP
02-existing-state/           # תיקיית סוג
03-market-survey/            # תיקיית סוג. עוד בלי סקיל
shared/<skill-name>/         # סקיל שסקילים אחרים תלויים בו
docs/                        # המדריך, רעיונות, מקורות
templates/                   # תבנית SKILL.md + תיקיית your-skill-name/
tooling/                     # ולידטור ואורז
tests/                       # בדיקות הכלים ו-fixtures
dist/                        # ZIP שנוצרים מקומית. לא נכנס ל-git
```

כלל טעינה שחשוב לכתיבה: Claude רואה תמיד רק `name` + `description` (בערך 100 טוקנים ל-Skill). את גוף `SKILL.md` הוא קורא כשה-Skill מופעל. קבצים אחרים נקראים רק אם ההוראות שולחות אליהם. לכן התיאור חייב לשאת את כל החלטת ההפעלה, והגוף נשאר קצר.

## יצירת Skill חדש

```bash
cp -R templates/your-skill-name <NN>-<type>/<שם>      # למשל 02-existing-state/tabu-reading
cp -R templates/your-skill-name shared/<שם>           # רק אם סקילים אחרים יקראו לו
```

בוחרים תיקיית סוג לפי העבודה שהסקיל עושה, לא לפי הלקוח. סוג חדש מקבל מספר רץ (`04-…`) ו-README קצר; הולידטור והאורז מזהים אותו לבד.

אחר כך:

1. שנו את שם התיקייה לשם הסופי, ואת `name` ב-frontmatter לאותו ערך.
2. מחקו את בלוק ההערות בתחילת הגוף.
3. כתבו תיאור לפי הסעיף הבא, כולל ביטויים בעברית שהצוות באמת מקליד.
4. השאירו בגוף רק מה ש-Claude יטעה בו בלי ההוראה: צ'קליסט, לולאת ולידציה, ברירת מחדל אחת, תבנית פלט, דוגמאות, Gotchas.
5. שימו ידע ארוך ב-`references/` (רמה אחת בלבד), וכתבו מתי לקרוא כל קובץ.
6. קבעו `metadata.version` (ראו "גרסאות").
7. מלאו לפחות שלושה evals ובדיקות טריגר.
8. הריצו את הולידטור, ואז ארזו.

`templates/SKILL.template.md` ו-`templates/your-skill-name/SKILL.md` הם אותו קובץ. מעתיקים את התיקייה, כי יש בה גם `evals/` ו-`LICENSE.txt`.

## שם ותיאור

`name`:

- זהה לשם התיקייה.
- רק `a-z`, `0-9` ומקף. 1–64 תווים.
- בלי מקף בהתחלה, בסוף, או כפול (`--`).
- בלי המילים `claude` או `anthropic`.
- עדיף צורת gerund (`qualifying-real-estate-leads`), לא שם מעורפל (`helper`).

`description` (עד 1024 תווים, בלי `<` או `>`):

- משפט יכולת בגוף שלישי: "Qualifies buyer leads…", לא "I can" ולא "You can".
- מיד אחר כך `Use when…` עם מונחים וניסוחים אמיתיים, כולל עברית. שמים את עיקר השימוש בהתחלה.
- סוגרים ב-`Do NOT use for…` כדי שלא ייגנב טריגר מ-Skill אח.
- דוגמה: `Qualifies real-estate leads from chat or a form and scores them. Use when the user mentions a lead, ליד, פנייה, or קונה פוטנציאלי, even if they do not ask to "qualify". Do NOT use for listing copy or pricing.`

מותרים רק שישה שדות, אחרת ההעלאה ל-claude.ai ול-API נכשלת: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. שדה של Claude Code בלבד (למשל `disable-model-invocation`) מותר רק אם בתיקייה יש קובץ `CLAUDE-CODE-ONLY`. האורז יסרב לארוז תיקייה כזאת ל-claude.ai.

גוף `SKILL.md`: מתחת ל-500 שורות. הולידטור מזהיר מעל זה, לא שובר את הבדיקה, אלא אם מריצים `--strict`.

כל ערכי `metadata` במירכאות. `metadata.version` הוא semver, למשל `"0.1.0"`.

## בדיקות

לפני שכותבים הוראות, מריצים את המשימה **בלי** ה-Skill ורושמים איפה Claude נכשל. אחר כך סוגרים רק את הפערים האלה.

לכל Skill, תחת `evals/` (התיקייה לא נכנסת ל-ZIP):

- `evals.json` — לפחות שלושה מקרים: מסלול שמח, קלט עברי מבולגן, ומקרה קצה. לכל אחד `prompt` ו-`expected_output`. מריצים כל מקרה עם ה-Skill ובלעדיו, בסשן נקי, כדי שההקשר של הכתיבה לא יסתיר פערים.
- `triggers.json` — שאילתות שצריכות להפעיל את ה-Skill ושאילתות near-miss שלא צריכות (למשל "תכתוב מודעה" לא מפעיל Skill של סינון לידים). בערך 20 שאילתות, חצי חיוביות וחצי שליליות, עם חלוקה ל-train/validation. לא מדביקים מילות מפתח של כישלון ישר לתוך התיאור.

בודקים גם דו-קיום: כל ה-Skills של Snapland טעונים יחד, ומוודאים שאף Skill לא גונב טריגרים. ב-Claude Code אפשר להיעזר ב-`skill-creator` או ב-`claude plugin eval`. אין בפלטפורמה מנגנון eval מובנה אחד לכל המשטחים.

## הפצה

מעלים לכל משטח בנפרד. אחרי כל העלאה ל-API רושמים את המזהים ב-[CHANGELOG.md](CHANGELOG.md).

### claude.ai

1. אורזים: `python tooling/package_skill.py <name>`. ה-ZIP נפתח כך: `dist/<name>.zip` → `<name>/SKILL.md` (שורש הארכיון הוא תיקיית ה-Skill, לא הקובץ עצמו).
2. Customize → Skills → "+" → Create skill → Upload a skill.
3. מפעילים את ה-Skill ובודקים כמה פרומפטים. Code execution צריך להיות דלוק (Settings → Capabilities).
4. ב-Team/Enterprise אפשר לשתף ולפרסם לספריית הארגון (לפי מרכז העזרה; דף ה-overview הישן עדיין אומר שאין ניהול מרכזי).

סנכרון מ-claude.ai אל Claude Code (`~/.claude/skills/synced/`) הוא חד-כיווני ודורס עריכות מקומיות. לא כותבים Skills שם.

### Claude Code

| רמה | נתיב |
| --- | --- |
| אישי | `~/.claude/skills/<name>/SKILL.md` |
| פרויקט | `.claude/skills/<name>/SKILL.md` |

אפשר להעתיק או לעשות symlink. קדימות: enterprise, אחר כך אישי, אחר כך פרויקט. שדות שקיימים רק ב-Claude Code לא נכנסים לעותק שעולה ל-claude.ai או ל-API.

### Claude API

- יוצרים Skill ב-`POST /v1/skills` (ה-API ב-GA, בלי כותרת beta). אפשר להעלות את ה-ZIP או קבצים. `SKILL.md` יכול לשבת בשורש ההעלאה או בתוך תיקייה אחת.
- בבקשת Messages מעבירים `container.skills` עם `skill_id` ו-`version`, יחד עם כלי code execution. עד 20 Skills לבקשה. עד 30MB לא דחוס.
- ב-production נועצים `version` למזהה `skver_…` מהטבלה ב-CHANGELOG. `latest` משנה התנהגות לכל מי שמעלה גרסה חדשה באותו workspace.
- גרסה חדשה היא snapshot מלא. `name` לא משתנה בין גרסאות.
- הקונטיינר בלי רשת ובלי התקנת חבילות בזמן ריצה. נתונים חיים (לידים, מודעות, עסקאות) מגיעים מהאפליקציה או מ-MCP, לא מתוך הסקריפט ב-API.
- Skills הם ברמת ה-workspace: כל מפתח ב-workspace יכול לקרוא, להפעיל ולמחוק. ללקוח נפרד, workspace נפרד.

Agent SDK טוען Skills ממערכת הקבצים (`~/.claude/skills` ו-`.claude/skills`) דרך `settingSources`, לא דרך רישום ב-API.

## כלים

תלות אחת, נעולה: `PyYAML==6.0.2`.

```bash
python -m pip install -r tooling/requirements.txt
python tooling/validate_skills.py                             # כל תיקיות הסוג, shared/ והתבנית
python tooling/validate_skills.py 01-feasibility-report       # סוג אחד
python tooling/validate_skills.py shared/israel-massing-rules # Skill אחד
python tooling/validate_skills.py --strict         # גם אזהרות נכשלות
python tooling/package_skill.py <name>             # dist/<name>.zip. מחפש בכל תיקיות הסוג
python tooling/package_skill.py all
python tooling/package_skill.py --path templates/your-skill-name
```

הולידטור בודק: frontmatter קיים וניתן לפענוח ומתחיל בשורה 1; רק השדות המותרים להעלאה (אלא אם יש `CLAUDE-CODE-ONLY`); כללי `name` והתאמה לתיקייה; אורך התיאור ובלי סוגריים משולשים; `metadata.version` ב-semver. אזהרות: מעל 500 שורות, תיאור בלי `Use when` / `השתמש בסקיל הזה כש…`, בלי `Do NOT use` / `אל תפעיל כש…`, תיאור בגוף ראשון, ותיאור בלי עברית ל-Skill שיושב בתיקיית סוג או ב-`shared/`.

האורז רץ אחרי ולידציה. הוא משמיט `evals/` בשורש ה-Skill, `__pycache__`, `node_modules`, `*.pyc`, `.DS_Store`, `.gitkeep` ואת קובץ הסימון `CLAUDE-CODE-ONLY`.

GitHub Actions (`.github/workflows/validate-skills.yml`) מריץ את הולידטור ואת בדיקות הכלים על pull requests ועל push ל-`main`.

## גרסאות

- כל Skill נושא `metadata.version`. מעלים את המספר בכל שינוי שעולה למשטח.
- אחרי העלאה ל-API רושמים ב-CHANGELOG את `skill_id` ואת מזהה הגרסה שאותו נועצים ב-production.
- היסטוריית הריפו עצמו (כלים ומבנה) גם היא ב-CHANGELOG.

## אבטחה

בלי סודות, מפתחות, או נתוני לקוחות בקבצים. סקריפטים לא פונים החוצה ל-URL שרירותי. מתקינים רק Skills מהריפו הזה או מאנתרופיק, וסוקרים כל קובץ לפני העלאה.

## רישום Skills

| Skill | מטרה | בעלים | metadata.version | משטחים | סטטוס eval |
| --- | --- | --- | --- | --- | --- |
| _אין עדיין_ | | | | | |

---

# English

Home of Snapland's custom Claude Agent Skills. Snapland builds real-estate bots and agents for Israel. Skills authored here are used in claude.ai, Claude Code, and the Claude API. Git is the source of truth: custom skills do not sync themselves across those surfaces.

The full authoring guide is [docs/anthropic-skills-guide.md](docs/anthropic-skills-guide.md). Suggested real-estate skill shapes (not Anthropic guidance, and not skills to build until someone asks) are in [docs/real-estate-ideas.md](docs/real-estate-ideas.md). Source URLs are in [docs/sources.md](docs/sources.md).

Skills are grouped by the kind of work they do, with `shared/` for skills other skills depend on. Tooling fixtures live under `tests/`.

| Type | Folder | Skills | What they do |
|---|---|---|---|
| 1 · Feasibility report | `01-feasibility-report/` | `go-no-go-v3` · `planning-check` | Go / borderline / No-Go plus the alternatives report, for every use and deal type · the planning check (4 sources, precedents) as a skill of its own |
| 2 · Existing state | `02-existing-state/` | `existing-state-check` · `permit-measurement` | What stands there today from Snapland data: units, gross, core, average size and the existing coefficient (●●○○) · measures a building permit into per-apartment, shared-space and balcony polygons (●●●○) → PDF + Excel |
| 3 · Market survey | `03-market-survey/` | not built yet | — |
| Shared | `shared/` | `israel-massing-rules` | Massing rules. The feasibility report reads them in its alternatives stage |

`go-no-go-v3` needs `israel-massing-rules` installed beside it and the Snapland Israel MCP. `planning-check` and `existing-state-check` need that MCP, stand alone, and also feed the feasibility report (stage 1, steps 3 and 6). `permit-measurement` is self-contained on Python, shapely, openpyxl and playwright, and feeds `existing-state-check` when a permit drawing exists.

## Layout

One folder per skill, inside its type folder: `<NN>-<type>/<kebab-case-name>/`, or `shared/<kebab-case-name>/` for a dependency. Each holds a required `SKILL.md` and optional `scripts/`, `references/`, `assets/`, `stages/`, and `evals/`. Also `docs/`, `templates/`, and `tooling/`. Packaged zips go to `dist/` and are gitignored.

Claude always sees `name` and `description` (~100 tokens per skill). It reads the `SKILL.md` body when the skill triggers, and other files only when the instructions say to. The description carries triggering. The body stays short.

## Create a skill

```bash
cp -R templates/your-skill-name <NN>-<type>/<kebab-case-name>
cp -R templates/your-skill-name shared/<kebab-case-name>     # only if other skills will read it
```

Pick the type folder by the work the skill does, not by the client. A new type gets the next number (`04-…`) and a short README; the validator and packager pick it up on their own. Rename the folder and set `name` to the same value. Delete the HTML comment at the top of the body. `templates/SKILL.template.md` and `templates/your-skill-name/SKILL.md` are the same file; copy the folder so `evals/` and `LICENSE.txt` come with it.

Agents working in this repo should follow [CLAUDE.md](CLAUDE.md) (and [AGENTS.md](AGENTS.md)).

## Name and description

`name` equals the folder. Lowercase letters, digits, and hyphens only, 1–64 characters, no leading, trailing, or doubled hyphen, and it must not contain `claude` or `anthropic`. Prefer a gerund (`qualifying-real-estate-leads`) over a vague name (`helper`).

`description` is at most 1024 characters and must not contain `<` or `>`. Write a third-person capability sentence, then `Use when…` with the real phrases people type, including Hebrew, then `Do NOT use for…` so sibling skills keep their triggers. Put the main use case first (Claude Code truncates the listing).

```yaml
description: Qualifies real-estate leads from chat or a form and scores them. Use when the user mentions a lead, ליד, פנייה, or קונה פוטנציאלי, even if they do not ask to "qualify". Do NOT use for listing copy or pricing.
```

Only six frontmatter fields upload to claude.ai and the Skills API: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Claude Code-only fields are allowed only when the folder contains a `CLAUDE-CODE-ONLY` marker. The packager will not zip that folder for upload unless you pass `--allow-claude-code-only`.

Keep the `SKILL.md` body under about 500 lines. The validator warns above that, and `--strict` turns the warning into a failure. Quote every `metadata` value. `metadata.version` is semver, for example `"0.1.0"`.

## Testing

Run the task without the skill first and record the failures. Write the minimum instructions that close those gaps.

Inside `evals/` (left out of the zip):

- `evals.json` — at least three cases: happy path, messy Hebrew input, and an edge case. Each has a `prompt` and an `expected_output`. Run every case with the skill and without it, in a fresh session.
- `triggers.json` — should-trigger queries and near-miss queries that must not trigger. About twenty queries, split between train and validation. Do not paste failed-query keywords straight into the description.

Also run a coexistence check with the other Snapland skills loaded. Claude Code can use `skill-creator` or `claude plugin eval`. There is no single platform eval runner that covers every surface.

## Distribute

Upload to each surface separately. After an API upload, record the ids in [CHANGELOG.md](CHANGELOG.md).

### claude.ai

1. `python tooling/package_skill.py <name>` writes `dist/<name>.zip`. The zip root is the skill folder: `<name>/SKILL.md`, not a bare `SKILL.md`.
2. Customize → Skills → "+" → Create skill → Upload a skill.
3. Turn the skill on and try several prompts. Code execution has to be enabled (Settings → Capabilities).
4. On Team and Enterprise, the Help Center describes sharing and publishing to the org library. The older overview page still says custom skills are individual-only; follow the Help Center.

claude.ai → Claude Code sync downloads into `~/.claude/skills/synced/` and overwrites local edits. Do not author skills there.

### Claude Code

| Level | Path |
| --- | --- |
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project | `.claude/skills/<name>/SKILL.md` |

Copy or symlink the folder. Precedence is enterprise, then personal, then project. Keep Claude Code-only frontmatter out of any copy you upload.

### Claude API

- Create the skill with `POST /v1/skills` (GA; no beta header). Upload the zip or individual files. `SKILL.md` may sit at the upload root or inside one top-level folder.
- On Messages requests, pass `container.skills` (`skill_id` plus `version`) and the code execution tool. At most 20 skills per request. The skill must be at most 30 MB uncompressed.
- Pin `version` to the `skver_…` id recorded in the changelog. `latest` changes production behavior for the whole workspace as soon as anyone uploads a new version.
- A new version is a full snapshot. `name` stays the same across versions.
- The API container has no network and cannot install packages at runtime. Pass live listings, leads, and comps in from the app or from MCP.
- Skills are workspace-wide: any key in the workspace can read, invoke, and delete them. Use one workspace per tenant.

The Agent SDK discovers skills from the filesystem (`~/.claude/skills` and `.claude/skills`) via `settingSources`. It does not register them through the Skills API.

## Tooling

One pinned dependency: `PyYAML==6.0.2`.

```bash
python -m pip install -r tooling/requirements.txt
python tooling/validate_skills.py                             # every type folder, shared/, and the template
python tooling/validate_skills.py 01-feasibility-report       # one type
python tooling/validate_skills.py shared/israel-massing-rules # one skill
python tooling/validate_skills.py --strict         # warnings fail the run
python tooling/package_skill.py <name>             # writes dist/<name>.zip. Looks the name up in every type folder
python tooling/package_skill.py all
python tooling/package_skill.py --path templates/your-skill-name
```

The validator checks that frontmatter exists, parses, and starts on line 1; that only upload-safe fields are present unless the skill is marked Claude Code-only; that `name` follows the rules and matches the folder; that `description` is within 1024 characters and has no angle brackets; and that `metadata.version` is semver. Warnings cover a `SKILL.md` over 500 lines, a description missing `Use when` / `השתמש בסקיל הזה כש…`, missing `Do NOT use` / `אל תפעיל כש…`, or written in the first person, and a skill in a type folder or `shared/` whose description has no Hebrew.

The packager validates first. It omits root-level `evals/`, `__pycache__`, `node_modules`, `*.pyc`, `.DS_Store`, `.gitkeep`, and the `CLAUDE-CODE-ONLY` marker.

GitHub Actions (`.github/workflows/validate-skills.yml`) runs the validator and the tooling tests on pull requests and on pushes to `main`.

## Versions

Each skill carries `metadata.version`. Bump it whenever you upload a change. After an API upload, add `skill_id` and the version id you will pin in production to the table in `CHANGELOG.md`. Repo-level notes (tooling and layout) go in that file too.

## Security

No secrets, keys, or customer data in the tree. Scripts must not fetch arbitrary URLs. Install only skills from this repo or from Anthropic, and review every file before upload.

## Skill registry

| Skill | Purpose | Owner | metadata.version | Surfaces | Eval status |
| --- | --- | --- | --- | --- | --- |
| _none yet_ | | | | | |