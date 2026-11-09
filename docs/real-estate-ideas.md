# Applying Agent Skills to Real-Estate Bots (Snapland): Suggestions

> **Everything in this file is a SUGGESTION**, built by applying the official patterns in `anthropic-skills-guide.md` to a real-estate setting. Skill names, file layouts, and workflows here are proposals. They are not Anthropic guidance. Israeli legal, tax, and regulatory items are flagged **[VERIFY]**: confirm them with a current official source or a professional before encoding them in a skill. Rules like tax brackets change over time, so keep them out of the SKILL.md body (see guide §6, "no time-sensitive info").

## 0. Cross-cutting design decisions

### 0.1 Skills library layout (one Git repo = single source of truth)
Official guidance says custom skills don't sync across surfaces, so Git should be the source of truth ([ENT], guide §10).
```
snapland-skills/
├── README.md                    # registry: purpose, owner, version, deps, eval status per skill ([ENT] registry fields)
├── skills/                      # portable skills: spec-only frontmatter, safe for claude.ai + Skills API
│   ├── qualifying-real-estate-leads/
│   ├── writing-property-listings/
│   ├── analyzing-comparable-sales/
│   ├── reviewing-property-documents/
│   ├── scheduling-property-showings/
│   └── writing-market-reports/
├── shared-references/           # canonical copies (e.g. glossary-he-en.md); copy INTO each skill at build time,
│                                # because a skill can't reference files outside its own folder once uploaded
├── .claude/skills/  -> symlinks or build output for Claude Code (Claude Code-only frontmatter allowed here)
├── scripts/
│   ├── validate_all.sh          # runs skills-ref / quick_validate.py on every skill
│   └── deploy_api.sh            # `ant apply skills/<name>` per skill; commit claude-lock.json
└── evals/                       # optional central trigger-eval sets (per-skill evals/ also fine)
```
Notes:
- Claude Code supports symlinked skill folders in personal and project locations [CC]. Plugins handle symlinks differently.
- `ant apply` records skill IDs in `claude-lock.json`. Commit it so later runs upload new *versions* instead of new skills [Managed Agents skills doc].
- **Multi-tenant:** if Snapland uploads customer-specific skills via the API, use **one workspace per tenant**. Skills are workspace-wide, and any key in that workspace can read, invoke, or delete them [API].
- **Pin skill versions** in production bots. Don't use `latest` [API] [ENT].
- API container: **no network and no runtime pip install** [OV]. Pass live data (listings, CRM rows, comps) into the conversation or as uploaded files, or fetch it in your app/MCP layer. Don't fetch from inside the skill on the API.

### 0.2 Language (Hebrew/English) [OPINION]
- `name` must be ASCII kebab-case [SPEC]. The description can be English with **Hebrew trigger terms** added, e.g. "…Use when the user asks about a lead, ליד, פנייה, or קונה פוטנציאלי…". Nothing in the spec forbids Unicode in `description` (the rule is no XML tags). Measure Hebrew triggering with a Hebrew trigger-eval set.
- Write the body in English for precision. Put Hebrew output templates and example phrasing in `assets/` or `references/`, and state the output language rule explicitly ("Reply in the user's language; listing copy in Hebrew unless asked otherwise").
- Keep one terminology glossary per skill: `references/glossary-he-en.md` (e.g. גוש/חלקה/תת-חלקה = block/parcel/sub-parcel, נסח טאבו = land-registry extract, הערת אזהרה = caution note, משכנתא = mortgage, עיקול = attachment/lien). [BP] asks for consistent terminology.

### 0.3 Guardrails
- Side-effecting actions (book a showing, send WhatsApp/SMS/email, update the CRM) should be user-confirmed.
  - In Claude Code, use `disable-model-invocation: true` for manual workflows.
  - In production bots, **enforce this in app code or hooks, not in skill prose**. "An instruction… in a skill is a request, not a guarantee" [CCF].
- Credentials (CRM, Yad2/Madlan partner APIs if any) never go in skill files. Use env vars or MCP servers [HC-CREATE] [ENT].
- Legal/financial outputs: the skill should say "informational, not legal/tax advice" and set escalation rules (lawyer / שמאי / יועץ משכנתאות).
- Fair-housing / non-discrimination and privacy: add a Gotchas bullet that forbids profiling leads on protected characteristics. Minimize stored personal data. **[VERIFY]** Current Israeli Privacy Protection Law obligations (incl. the recent Amendment 13) and the Real Estate Brokers Law (חוק המתווכים במקרקעין) requirement for a signed written brokerage order before commission. Check both with counsel before encoding.

### 0.4 Mapping to "Building effective agents" patterns [BEA]
| Bot need | Pattern | Skill realization |
|---|---|---|
| Inbound message triage (buyer / seller / renter / spam / existing client) | Routing | A router in app code, or narrow skills with sharp, mutually exclusive descriptions + "Do NOT use for…" |
| Listing copy: facts → draft → style check → Hebrew/English variants | Prompt chaining + evaluator-optimizer | Checklist workflow + `references/style-guide.md` as the "validator" + `scripts/check_listing.py` |
| CMA: gather comps → clean → adjust → price range → report | Chaining with code gates | Low-freedom scripts for math, high-freedom prose for narrative |
| Market report across several neighborhoods | Orchestrator-workers / parallelization | Claude Code/SDK: subagent per neighborhood; API: sequential sections |

---

## 1. `qualifying-real-estate-leads`
**Goal:** Turn a conversation or form into a structured, scored lead plus next action.
```
qualifying-real-estate-leads/
├── SKILL.md                       # workflow, scoring summary, gotchas, output JSON schema
├── references/
│   ├── scoring-rubric.md          # BANT-style: budget, timeline, financing (pre-approval / אישור עקרוני), location, property type
│   ├── question-bank-he.md        # natural Hebrew follow-up questions per missing field
│   └── crm-field-map.md           # our field names ↔ CRM field names (a classic "gotcha" source)
├── scripts/
│   └── score_lead.py              # deterministic score from JSON; prints JSON {score, tier, missing_fields}
└── evals/evals.json
```
- **Description sketch:** "Qualifies real-estate buyer, seller, and renter leads from chat or form data: extracts budget, timeline, financing status, areas and property type, scores the lead, and proposes the next question or action. Use when handling a new inquiry, a lead, ליד, פנייה, or when asked whether a contact is serious. Do NOT use for writing listing copy or pricing a property."
- **Freedom:**
  - Low: scoring (script), so it's consistent and auditable.
  - High: conversational follow-ups.
- **Gotchas examples:**
  - Users state prices in "מיליון" or with ₪ or $, sometimes in thousands. Normalize to ILS integers.
  - "3 חדרים" in Israel conventionally includes the living room. **[VERIFY]** Confirm this convention for your market before encoding it.
- **Evals:**
  - Should trigger: casual Hebrew WhatsApp-style messages ("היי ראיתי דירה ברמת גן, יש לי אישור עקרוני ל-1.8").
  - Near-miss negative: "תכתוב לי מודעה לדירה ברמת גן".

## 2. `writing-property-listings`
**Goal:** Produce listing descriptions from structured property facts in Snapland's voice, ready for different portals.
```
writing-property-listings/
├── SKILL.md                       # workflow + output template + validation loop
├── references/
│   ├── style-guide.md             # tone, banned superlatives, accessibility wording
│   ├── portal-formats.md          # per-portal fields/length limits (Yad2, Madlan, website, Facebook): [VERIFY] limits yourself
│   └── examples.md                # 3–5 input→output pairs (he + en)
├── assets/
│   └── listing-template-he.md
└── scripts/
    └── check_listing.py           # length per portal, required fields present, no phone numbers in body, no banned words
```
- **Workflow:** facts JSON → draft → `check_listing.py` → fix → rerun until clean → variants (short/long, he/en).
- **Gotchas:**
  - Never invent facts that aren't in the input (floor, parking, מעלית, ממ"ד, מרפסת שמש).
  - Flag missing key Israeli features instead of assuming them.
- **Templates:** use the strict template for portal feeds and the flexible one for social posts [BP template pattern].

## 3. `analyzing-comparable-sales` (CMA)
**Goal:** Estimate a price range from comparable transactions and explain it.
```
analyzing-comparable-sales/
├── SKILL.md                       # plan-validate-execute workflow; when to widen radius/time window
├── references/
│   ├── methodology.md             # comp selection, adjustments (floor, size, condition, parking, ממ"ד), outlier rules
│   └── data-sources.md            # schemas of the comp data we feed in (see below)
├── scripts/
│   ├── clean_comps.py             # normalize sqm, price/sqm, dedupe, drop outliers, output JSON
│   ├── adjust_and_range.py        # deterministic adjustments → low/mid/high + price/sqm stats
│   └── validate_plan.py           # checks comp_plan.json (enough comps, date window, same property type)
└── assets/cma-report-template.md
```
- **Data sources (Israel)**, for your app or an MCP layer, not inside an API skill (no network):
  - The Israel Tax Authority real-estate transactions database is free and public, searchable by address or block/parcel (https://www.gov.il/en/service/real_estate_information).
  - A bulk open dataset of ~3.8M transactions was reportedly published in Sept 2026 by the "מידע לעם" project (https://www.odata.org.il/dataset/nadlan). **[VERIFY]** Check its license and freshness.
  - Govmap transaction endpoints are wrapped by a community MCP server (https://github.com/nitzpo/nadlan-mcp). This is **third-party code, so audit it first** [ENT].
  - Madlan/Yad2 data: **[VERIFY]** terms of use before any scraping. Prefer official partner feeds.
- **Pattern:** Claude writes `comp_plan.json` → `validate_plan.py` → run scripts → Claude writes the narrative. All numbers come from scripts [BP "verifiable intermediate outputs"].
- **Gotchas:**
  - Reported transaction dates vs. signing dates.
  - Distinguish net vs. gross sqm ("מ"ר ברוטו/נטו").
  - New-build (קבלן) vs. second-hand prices.
  - Partial-rights sales (e.g. selling ½ of a unit) skew price/sqm.
  - All of these are **[VERIFY]** against your data.
- **Output disclaimer:** "Not an appraisal (שומה). A licensed appraiser is required for official valuation."

## 4. `reviewing-property-documents` (contracts, Tabu extracts)
**Goal:** Extract and flag key facts and risks from a נסח טאבו, purchase or lease agreement, or building permit. **Not legal advice.**
```
reviewing-property-documents/
├── SKILL.md                       # doc-type routing + checklist + escalation rules
├── references/
│   ├── tabu-extract.md            # sections of a נסח: owners, mortgages, attachments (עיקולים), caution notes (הערות אזהרה), restrictions
│   ├── purchase-agreement.md      # clause checklist (payments schedule, possession date, penalties, bank guarantee/ערבות חוק מכר for new builds [VERIFY])
│   └── lease-agreement.md         # rent, term, indexation, guarantees, maintenance, exit clauses
├── scripts/
│   └── extract_pdf_text.py        # text + OCR fallback; outputs JSON pages[]
└── assets/review-report-template.md
```
- Per the Ministry of Justice service page, a Tabu extract lists registered owners, liens, mortgages, attachments, court orders, and restrictions. You request it by גוש/חלקה (+ תת-חלקה in a condominium). It is "official… only in its digital format" and accurate as of its generation date (https://www.gov.il/en/service/land_registration_extract).
- **Gotchas:**
  - Always report the extract's generation date and warn if it's stale.
  - Name mismatches between the seller and the registered owner are a red flag.
  - Not all properties are registered in Tabu. Some are at רמ"י or a management company. **[VERIFY]**
- **Composes with** the pre-built `pdf` skill on claude.ai/API. Don't duplicate PDF mechanics; reference your own script only for Hebrew/OCR specifics.
- **Security:** documents contain personal data. Don't send them to external URLs from scripts [OV].

## 5. `scheduling-property-showings`
**Goal:** Propose and confirm viewing slots and send reminders.
- The value here is mostly **integration**, so use **MCP / app tools** (calendar, WhatsApp, CRM). The skill teaches *how*:
  - Buffer rules, travel time between listings, owner/tenant availability, and confirmation message templates in Hebrew.
  - Reference tools by fully qualified name (`Calendar:create_event`) [BP].
- Minimal layout:
```
scheduling-property-showings/
├── SKILL.md            # rules: business hours, Shabbat/holiday blackout, buffers, confirmation-before-booking
├── references/messages-he.md
└── scripts/find_slots.py   # deterministic slot finder from availability JSON
```
- **Gotchas:**
  - Israel's Friday/Saturday weekend and holiday calendar.
  - DST changes.
  - Always confirm with the lead **and** the owner/tenant before booking.
- Make booking a confirmed action in app code. In Claude Code, set `disable-model-invocation: true` on any "send/book" skill.

## 6. `writing-market-reports`
**Goal:** A neighborhood/city market update (price/sqm trends, inventory, days-on-market) for clients or content marketing.
- Chaining: data pull (outside the skill) → `scripts/compute_stats.py` → charts (`scripts/make_charts.py`, or the pre-built `xlsx`/`pptx`/`docx` skills on API/claude.ai) → narrative in the template → a fact-check loop against the stats JSON.
- **Gotchas:**
  - State the period and source of every number.
  - Never extrapolate a trend from fewer than N transactions. Pick N yourself and document why [BP "no voodoo constants"].

## 7. Reference-only (knowledge) skills worth considering
- `israeli-real-estate-glossary`: `user-invocable: false` in Claude Code, so it's background knowledge only.
- `snapland-brand-voice`: tone and formatting, modeled on the official `brand-guidelines` skill [REPO].
- `israeli-purchase-costs`: purchase tax (מס רכישה), betterment tax (מס שבח), lawyer/broker fees.
  - Keep rates in `references/rates-YYYY.md`, **each with its source URL and effective date**.
  - Put a Gotcha in SKILL.md: "rates change, so always cite the file date and recommend verification". **[VERIFY]** every figure.

## 8. Starter eval plan per skill (from guide §9)
- 3 output evals per skill:
  - 1 happy path
  - 1 messy real-world input (Hebrew slang/typos, missing fields)
  - 1 edge case (e.g. partial-rights sale, stale Tabu extract)
- 20 trigger queries: 10 should-trigger and 10 near-miss negatives across the sibling skills. For example, the lead skill should NOT fire on "write me a listing", and the CMA skill should NOT fire on "what's the purchase tax?".
- **Coexistence run** with all Snapland skills loaded [ENT]. Test on every model the bots use.
