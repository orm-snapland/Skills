# Anthropic Agent Skills — Expert Authoring Guide

*Compiled 2026-09-30 from official Anthropic docs, the Agent Skills open spec (agentskills.io), and the `anthropics/skills` repo (commit `8a1541c`, 2026-09-28). Every key claim has an inline source. Anything marked **[UNCERTAIN]** or **[CONFLICT]** is either ambiguous or contradicted between official sources. Anything marked **[OPINION]** is my own recommendation and not an Anthropic statement.*

Source short-names used below:
- **[OV]** Overview: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- **[BP]** Best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **[API]** Skills in the API: https://platform.claude.com/docs/en/build-with-claude/skills-guide
- **[ENT]** Skills for enterprise: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise
- **[CC]** Claude Code skills: https://code.claude.com/docs/en/skills
- **[CCF]** Claude Code "Extend Claude Code" (feature comparison): https://code.claude.com/docs/en/features-overview
- **[SDK]** Agent SDK skills: https://code.claude.com/docs/en/agent-sdk/skills
- **[SPEC]** Open spec: https://agentskills.io/specification
- **[AS-BP] / [AS-DESC] / [AS-EVAL] / [AS-SCR]**: agentskills.io best practices / optimizing descriptions / evaluating skills / using scripts
- **[BLOG]** Engineering blog: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- **[BEA]** Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- **[HC-CREATE] / [HC-USE]** Help Center: https://support.claude.com/en/articles/12512198-creating-custom-skills / https://support.claude.com/en/articles/12512180-using-skills-in-claude
- **[REPO]** https://github.com/anthropics/skills (incl. `skills/skill-creator`)

---

## Table of contents
1. What Skills are (and aren't)
2. Exact file format and frontmatter rules
3. Directory layout
4. Progressive disclosure: how Skills load
5. Writing descriptions that trigger correctly
6. Structuring the SKILL.md body
7. Bundling scripts, references, and assets
8. Degrees of freedom
9. Testing, evaluation, and iteration
10. Distribution per surface (Claude.ai, Claude Code, API, Agent SDK, Managed Agents)
11. Skills vs CLAUDE.md vs commands vs subagents vs hooks vs MCP
12. Workflow patterns from "Building effective agents" and how they map to Skills
13. Security
14. Common mistakes
15. Authoring checklist
16. Recent changes and ambiguities

---

## 1. What Skills are

- A Skill is "organized folders of instructions, scripts, and resources that agents can discover and load dynamically to perform better at specific tasks." Anthropic compares building one to writing "an onboarding guide for a new hire." [BLOG]
- Skills are "reusable, filesystem-based resources" that load **on demand**. Prompts, by contrast, are conversation-level instructions for one-off tasks. [OV]
- Skills run in an environment where Claude has **filesystem + bash/code execution**. Claude reads `SKILL.md` and other files with bash (e.g. `cat`). **Scripts are executed**, and only their output enters context. [OV]
- Anthropic ships pre-built Skills (`pptx`, `xlsx`, `docx`, `pdf`) on claude.ai, the API, Claude Platform on AWS, and Microsoft Foundry. **These are not available in Claude Code**, although Claude Code bundles the open-source `claude-api` skill. [OV]
- Agent Skills was published as an **open standard** (update dated 2025-12-18) [BLOG]. The spec now lives at agentskills.io. The repo's `spec/agent-skills-spec.md` only points there. [REPO] [SPEC]
- Composability: "While skills can't explicitly reference other skills, Claude can use multiple skills together automatically." [HC-CREATE]

## 2. Exact file format and frontmatter rules

`SKILL.md` = YAML frontmatter between `---` lines, followed by Markdown. [SPEC] In Claude Code, frontmatter is recognized **only if the opening `---` is the first line of the file**. If the YAML fails to parse, the skill still loads, but with no fields set. That means `/name` still works but auto-triggering doesn't. [CC]

### 2.1 Portable (spec) fields: the safe set for every surface

| Field | Required | Constraints | Source |
|---|---|---|---|
| `name` | Yes (spec/API/claude.ai) | 1–64 chars. Only lowercase `a-z`, `0-9`, and `-`. Can't start or end with `-`. No `--`. **Must match the parent directory name.** Anthropic adds: no XML tags, and must not contain the reserved words `anthropic` or `claude`. | [SPEC] [OV] [API] |
| `description` | Yes | 1–1024 chars, non-empty, no XML tags. Should say what the skill does **and** when to use it. | [SPEC] [OV] |
| `license` | No | Short license name or a pointer to a bundled file, e.g. `Proprietary. LICENSE.txt has complete terms`. | [SPEC] [REPO] |
| `compatibility` | No | 1–500 chars. Environment requirements (product, packages, network). "Most skills do not need" it. | [SPEC] |
| `metadata` | No | Map of string→string, e.g. `author`, `version: "1.0"`. Use unique key names. | [SPEC] |
| `allowed-tools` | No | Space-separated pre-approved tools, e.g. `Bash(git:*) Read`. **Experimental**, and support varies by client. | [SPEC] |

**Hard rule for uploads:** claude.ai uploads, the Skills API, and `package_skill.py` accept **only** these six keys. Any other key makes upload fail with `Unexpected key(s) in SKILL.md frontmatter: ... Allowed properties are: allowed-tools, compatibility, description, license, metadata, name`. [CC] The repo's `quick_validate.py` enforces the same allowlist. It also rejects `<` or `>` in the description and checks the name regex, hyphen rules, the 64/1024/500 limits, and that the name starts/ends correctly. [REPO `skills/skill-creator/scripts/quick_validate.py`]

Validators:
- `skills-ref validate ./my-skill` (the spec's reference library). [SPEC]
- `python -m scripts.quick_validate <dir>`, or `package_skill.py`, which validates before zipping. [REPO]
- `claude plugin validate .claude/skills` (Claude Code v2.1.233+) finds SKILL.md files whose frontmatter doesn't parse. [CC]

### 2.2 Claude Code–only extension fields

Claude Code accepts everything above plus the fields below. In Claude Code **all fields are optional**, and only `description` is "recommended". If `name` is omitted, the directory name is used. If `description` is omitted, the first non-empty body line is used. **Unknown fields are silently ignored.** [CC]

| Field | Purpose |
|---|---|
| `when_to_use` | Extra trigger context, appended to the description. The combined text of `description` + `when_to_use` is **truncated at 1,536 chars** in the skill listing (configurable via `skillListingMaxDescChars`). |
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]`. |
| `arguments` | Named positional args used in `$name` substitution. |
| `disable-model-invocation: true` | Only the user can invoke the skill (via `/name`). Its description is **removed from context**. Use for side-effecting workflows (deploy, send, commit). |
| `user-invocable: false` | Only Claude can invoke it. Hidden from the `/` menu. Use for background knowledge. |
| `disallowed-tools` | Tools removed while the skill is active. |
| `model`, `effort` | Per-skill model / effort override for the current turn. |
| `context: fork`, `agent`, `background` | Run the skill as the prompt of an isolated subagent (Explore, Plan, general-purpose, or a custom one). |
| `hooks` | Hooks registered when the skill is invoked. |
| `paths` | Glob patterns. Auto-load only when working on matching files. |
| `shell` | `bash` (default) or `powershell` for `!` injection. |

Claude Code body features, all Claude Code-only [CC]:
- `$ARGUMENTS`, `$0`/`$1` or `$ARGUMENTS[N]`, `$name`, and `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` substitutions.
- `` !`cmd` `` / ` ```! ` **dynamic context injection**. The command runs *before* Claude sees the skill. If it fails, the whole invocation aborts.

Per [CC], these features "don't function in claude.ai chat or through the API."

> **Portability rule of thumb [OPINION]:** For skills that must work on claude.ai or the API, use only the six spec fields and plain Markdown with relative paths. Keep Claude Code-only frontmatter in a separate variant, or add it only in the `.claude/skills` copy.

### 2.3 Naming conventions [BP]
- Prefer the gerund form: `processing-pdfs`, `analyzing-spreadsheets`. Noun phrases (`pdf-processing`) and action forms (`process-pdfs`) are also fine.
- Avoid vague names (`helper`, `utils`), overly generic ones (`documents`, `data`), reserved words (`claude-tools`), and inconsistent patterns across a collection.
- In Claude Code, don't name a folder `synced` or `anthropic-skills*`. Both are reserved for claude.ai sync. [CC]

## 3. Directory layout

Spec convention [SPEC]:
```
skill-name/            # must equal frontmatter `name`
├── SKILL.md           # required: metadata + instructions
├── scripts/           # optional: executable code (run, not read)
├── references/        # optional: docs loaded on demand (REFERENCE.md, FORMS.md, finance.md…)
├── assets/            # optional: templates, images, data files, schemas
└── ...                # anything else
```
- Reference files with **relative paths from the skill root**, e.g. `[guide](references/REFERENCE.md)` or `scripts/extract.py`. Script paths inside reference files are *also* relative to the skill root. [SPEC] [AS-SCR]
- Always use forward slashes. [BP]
- Name files descriptively (`form_validation_rules.md`, not `doc2.md`) and organize by domain or feature. [BP]
- `evals/` inside the skill holds `evals/evals.json` (the skill-creator and agentskills.io convention). `package_skill.py` **excludes a root-level `evals/`**, plus `__pycache__`, `node_modules`, `*.pyc`, and `.DS_Store`, when it builds the `.skill` zip. [AS-EVAL] [REPO]
- Eval run outputs go in a **sibling** folder, `<skill-name>-workspace/iteration-N/…`, not inside the skill. [AS-EVAL] [REPO]
- Upload size limit: the API caps the whole skill at **30 MB uncompressed**. [API]

Real examples in [REPO]: `pdf/` (SKILL.md + `forms.md` + `reference.md` + `scripts/`), `mcp-builder/` (`reference/` + `scripts/`), `skill-creator/` (`agents/`, `references/`, `scripts/`, `assets/`, `eval-viewer/`), and `claude-api/` (per-language subfolders + `shared/`, i.e. domain-organized references).

## 4. Progressive disclosure: how Skills load

| Level | When loaded | Typical cost | Content |
|---|---|---|---|
| 1 Metadata | Always, at startup, in the system prompt | ~100 tokens/skill | `name` + `description` |
| 2 Instructions | When triggered (Claude runs `cat SKILL.md`) | < 5k tokens recommended | SKILL.md body |
| 3+ Resources | Only when referenced and needed | 0 until read; scripts cost only their output | bundled files |
[OV] [SPEC]

Implications:
- You can install many skills cheaply. Bundled content is "effectively unbounded" because files only cost tokens when read. [BLOG] [OV]
- Keep the SKILL.md body **under 500 lines** (and under ~5,000 tokens per [SPEC]/[AS-BP]). Split content out as you approach that. [BP] [SPEC]
- Keep references **one level deep** from SKILL.md. With nested references Claude may only `head -100` a file and get partial info. [BP]
- Give reference files over 100 lines a **table of contents** at the top [BP]. skill-creator says >300 lines [REPO].
- Tell the agent *when* to load each file. "Read `references/api-errors.md` if the API returns a non-200 status code" works better than "see references/". [AS-BP]
- Claude Code specifics [CC]:
  - Once invoked, the rendered SKILL.md stays in the conversation across turns and isn't re-read. Write **standing instructions**, not one-time steps.
  - After auto-compaction, each re-attached skill keeps only its first 5,000 tokens, within a 25,000-token total budget.
  - The skill listing's budget is ~1% of the context window. Descriptions of rarely used skills get dropped first when it overflows.
- Too many skills hurts recall: "limit the number of Skills loaded simultaneously." [ENT]

## 5. Writing descriptions that trigger correctly

The description "carries the entire burden of triggering." [AS-DESC] Claude uses it "to choose the right Skill from potentially 100+ available Skills." [BP]

Rules:
1. Say **what it does + when to use it**, with concrete key terms: file types, domain nouns, user phrasings. [BP] [OV]
2. **Third person** for the "what" part ("Processes Excel files…", never "I can help…" or "You can use…"), because the description is injected into the system prompt. [BP]
3. Aim for user intent over implementation, and write an explicit "Use when…" clause. agentskills.io recommends imperative phrasing ("Use this skill when…"). [AS-DESC] (See the conflict note in §16. A good form that satisfies both: `"<Third-person capability sentence>. Use when <contexts/phrasings>, even if the user doesn't say <X>."` **[OPINION]**)
4. **Be a little "pushy."** "Currently Claude has a tendency to 'undertrigger' skills." skill-creator suggests adding things like "Make sure to use this skill whenever the user mentions…, even if they don't explicitly ask for…". [REPO skill-creator] [AS-DESC]
5. **State boundaries** to avoid stealing triggers. Official skills do this, e.g. `xlsx`: "Do NOT trigger when the primary deliverable is a Word document, HTML report…" and `docx`: "Do NOT use for PDFs, spreadsheets…". [REPO] [ENT: "Coexistence"]
6. Keep it concise: a few sentences to a short paragraph, under the 1024-char hard limit. [AS-DESC] In Claude Code, put the key use case first, because of the 1,536-char listing cap. [CC]
7. Simple one-step requests may not trigger a skill even with a perfect description, since Claude handles them itself. Skills trigger reliably on specialized, multi-step tasks. Design your trigger tests accordingly. [AS-DESC] [REPO skill-creator]
8. In Claude Code, fix over-triggering by narrowing the description or setting `disable-model-invocation: true`. [CC]

Good examples [BP]:
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.
```
Bad: `Helps with documents`, `Processes data`, `Does stuff with files`. [BP]

### Description optimization loop [AS-DESC] [REPO skill-creator]
- Write ~20 realistic queries: 8–10 should-trigger (varied phrasing, casual, typos, indirect) and 8–10 should-NOT-trigger. The negatives should be **near-misses**, not obviously unrelated.
- Run each ~3×, compute a trigger rate, and pass at a threshold of about 0.5.
- Split 60% train / 40% validation. Revise using train failures only, and pick the best iteration **by validation score**. Five iterations is usually enough. Don't paste failed-query keywords into the description; generalize the concept instead.
- In Claude Code, `skill-creator`'s `scripts/run_loop.py` automates this with `claude -p`. [REPO] agentskills.io gives a bash example that detects `tool_use` with `name == "Skill"` in `claude -p --output-format json`. [AS-DESC]

## 6. Structuring the SKILL.md body

The spec imposes no format [SPEC]. Recommended building blocks:
- **Quick start / core workflow.** Concise, stepwise, with one working example. [BP] [AS-BP]
- **Checklist for multi-step workflows** that Claude copies into its response and ticks off. [BP]
- **Feedback / validation loops**: do → validate (script or checklist) → fix → repeat, and "only proceed when validation passes." [BP]
- **Plan-validate-execute** for batch or destructive work: write `changes.json` → validate it with a script against the source of truth → apply → verify. [BP] [AS-BP]
- **Conditional workflow**: "Creating new? → A. Editing? → B." Move big branches into separate files. [BP]
- **Templates** for output format: strict ("ALWAYS use this exact template") or flexible ("sensible default, adapt"). [BP]
- **Examples** as input/output pairs. [BP]
- **Gotchas section.** Often the highest-value content: "concrete corrections to mistakes the agent will make without being told otherwise." Keep these in SKILL.md itself, not a reference file. [AS-BP]
- **Defaults, not menus.** Name one tool/approach, with an escape hatch. [BP] [AS-BP]
- **Procedures over declarations.** Teach the method, not the answer to one instance. [AS-BP]
- **Consistent terminology.** One term per concept. [BP]
- **No time-sensitive statements.** Put deprecated material in a collapsible "Old patterns" section. [BP]
- **Explain the why** rather than shouting MUST/NEVER. skill-creator calls all-caps ALWAYS/NEVER "a yellow flag" [REPO] [AS-EVAL]. Note that [BP] also shows using "MUST filter" to make a rule more prominent when Claude keeps missing it. Treat that as an escalation after testing, not a default. **[OPINION]**
- **Conciseness.** "Default assumption: Claude is already very smart." Only add what Claude lacks, and ask of each piece: "Would the agent get this wrong without this instruction?" [BP] [AS-BP]
- MCP tools: use fully-qualified `ServerName:tool_name` names. [BP]

## 7. Bundling scripts, references, and assets

Why scripts: they are more reliable than generated code, save tokens (the code never enters context), save time, and give consistency. [BP] Code "can serve as both executable tools and as documentation", so **say explicitly whether to run it or read it**. [BLOG] [BP]

Script design for agents [AS-SCR] [BP]:
- **No interactive prompts.** Agents can't answer TTY prompts, so accept flags, env vars, or stdin.
- `--help` with usage and examples. Clear error messages: what went wrong, what was expected, what to try.
- **Structured output** (JSON/CSV) on stdout and diagnostics on stderr. Keep output size predictable (support `--offset`/`--output`).
- Idempotent operations, `--dry-run` for destructive ones, meaningful exit codes, safe defaults (`--confirm`).
- "Solve, don't defer": handle errors in the script instead of failing and leaving it to Claude. No "voodoo constants"; document why each value was chosen.
- Self-contained dependencies: PEP 723 inline metadata + `uv run`, or Deno `npm:` imports, or Bun, or `bundler/inline`. **Pin versions.** State prerequisites, or use `compatibility`.
- Verbose validators with actionable messages, e.g. "Field 'signature_date' not found. Available fields: …".
- Claude Code: reference bundled scripts via `${CLAUDE_SKILL_DIR}/scripts/x.sh`. Optionally pre-approve exactly that command with `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/x.sh *)`. [CC]
- Signal to bundle a script: during evals, every run independently re-writes the same helper. [AS-BP] [REPO skill-creator]

**Runtime constraints differ by surface** [OV] [API] [BP]:

| Surface | Network | Package install |
|---|---|---|
| Claude API (code-execution container) | **None** | **None at runtime.** Pre-installed packages only (see code execution tool docs). |
| claude.ai | Full / partial / none depending on user and admin settings | Can install from PyPI/npm and pull from GitHub |
| Claude Code | Full (same as the user's machine) | Allowed, but install locally, not globally |

Assets: long templates, fonts, logos, lookup tables, and schemas live in `assets/` and are referenced from SKILL.md so they load only when needed. [AS-BP] [SPEC]

## 8. Degrees of freedom [BP] [AS-BP]
- **High freedom** (prose heuristics): many valid approaches, context-dependent. Example: code review.
- **Medium** (pseudocode or parameterized scripts): a preferred pattern with some variation.
- **Low** (exact script, "run exactly this, don't add flags"): fragile, consistency-critical, strict sequence. Example: migrations.
- The analogy: a narrow bridge with cliffs (low freedom) vs an open field (high freedom). Calibrate **each section** independently.
- Test with every model you'll use. Haiku may need more guidance, and Opus may be over-explained to. [BP] [ENT]

## 9. Testing, evaluation, and iteration

**Evaluation-driven development** [BP]:
1. Run Claude on representative tasks **without** the skill and document the failures.
2. Build ≥3 eval scenarios targeting those gaps.
3. Measure the baseline.
4. Write *minimal* instructions to close the gaps.
5. Iterate against the baseline.

"There is not currently a built-in way to run these evaluations" on the platform generally [BP]. Claude Code does now provide tools; see below.

Example eval (from [BP]):
```json
{"skills": ["pdf-processing"], "query": "Extract all text from this PDF file and save it to output.txt",
 "files": ["test-files/document.pdf"],
 "expected_behavior": ["Successfully reads the PDF…", "Extracts text from all pages…", "Saves to output.txt…"]}
```

**Claude A / Claude B loop** [BP]:
- Claude A helps you write and refine the skill. A fresh Claude B uses it on real tasks. You observe B and bring the specifics back to A.
- Watch for unexpected file-reading order, missed references, over-reliance on one file (maybe it belongs in SKILL.md), and never-read files (cut them or signal them better).

**Output-quality evals** (agentskills.io and skill-creator format) [AS-EVAL] [REPO]:
- `evals/evals.json`: `{skill_name, evals:[{id, prompt, expected_output, files, assertions[]}]}`. Start with 2–3 cases. Add assertions *after* the first run.
- Run each case **with_skill** and **without_skill** (or **old_skill** from a snapshot), each in a clean context (subagents). Capture `timing.json` (`total_tokens`, `duration_ms`).
- Grade into `grading.json`: `{text, passed, evidence}` per assertion. Require concrete evidence to PASS. Use scripts for mechanical checks.
- Aggregate into `benchmark.json` (pass-rate/time/tokens mean±stddev and the delta).
- Analyze:
  - Drop assertions that always pass in both configurations.
  - Investigate ones that always fail.
  - Study the ones that pass only with the skill.
  - High variance means ambiguity in the instructions.
- Human review goes in `feedback.json`, and **blind A/B comparison** is available for versions.
- Iterate by generalizing from feedback, keeping it lean, explaining the why, and bundling repeated work.

**Tooling**
- `skill-creator`:
  - In Claude Code: `/plugin install skill-creator@claude-plugins-official`.
  - Also available as `example-skills@anthropic-agent-skills` via `/plugin marketplace add anthropics/skills`.
  - It runs with/without-skill subagents, grading, benchmark, a blind A/B, description tuning, and an HTML review viewer. [CC] [REPO]
  - On claude.ai it runs in a reduced mode: no subagents, no baselines, no description optimization. [REPO]
- `claude plugin eval`, for skills shipped in a plugin: isolated with/without-plugin runs, graders (incl. `tool_used: Skill` for trigger rate), non-zero exit below a threshold (for CI gating). Its format is **not** interchangeable with skill-creator's `evals.json`. [CC]
- To A/B a personal/project skill in Claude Code, turn it off via `skillOverrides: {"name": "off"}` and use **fresh sessions** so authoring context doesn't mask gaps. [CC]
- `/skill-doctor` (v2.1.252+) shows each skill's context cost and usage, and flags never-invoked skills. [CC]

**Enterprise gates** [ENT]:
- Evaluate triggering accuracy, isolation, **coexistence** (does the new skill steal triggers?), instruction following, and output quality.
- 3–5 queries per skill (should / shouldn't / ambiguous), across Haiku/Sonnet/Opus.
- Separation of duties: authors don't review their own skills.
- Usage analytics are "not currently available through the Skills API", so log which skills each request includes. **[CONFLICT-ish]** The API index also lists a beta "Get Skill Usage" analytics endpoint; see §16.

## 10. Distribution per surface

**Custom Skills generally do not sync across surfaces.** Upload separately to each. [OV] [ENT] (There's a newer exception, claude.ai → Claude Code sync; see below and §16.) Keep **Git as the single source of truth**. [ENT]

### 10.1 claude.ai / Claude apps (incl. Cowork, Desktop, M365 add-ins)
- Requirements:
  - Code execution must be on: Settings > Capabilities, or for Team/Enterprise, Organization settings > Plugins & skills > Policy. [HC-USE]
  - Plans: Free, Pro, Max, Team, Enterprise per [HC-USE]. **[CONFLICT]** [OV] says Pro/Max/Team/Enterprise.
- Upload flow:
  1. Package the folder as a **ZIP whose root is the skill folder** (`my-skill.zip/my-skill/SKILL.md`), with the folder name equal to the skill name.
  2. Go to Customize > Skills > "+" > Create skill > Upload a skill.
  3. Toggle it on.
  4. Test several prompts and check Claude's thinking to confirm it loaded. [HC-CREATE] [HC-USE]
- skill-creator's `package_skill.py` produces a `.skill` file (a zip) after validation. [REPO]
- Upload errors: size limits, folder name ≠ skill name, missing SKILL.md, invalid characters in name/description. [HC-USE]
- Sharing (Team/Enterprise):
  - Share view-only with people or groups. Recipients get your updates automatically.
  - "Publish to org" (with optional review; offered as Available / Installed by default / Required).
  - Owners can provision skills org-wide. [HC-USE]
  - **[CONFLICT]** [OV] still says claude.ai custom Skills are individual-only and can't be centrally managed.
- Enterprise can enable **skill content scanning** for claude.ai and Cowork uploads. It does **not** cover the API or Console. [OV] [ENT]
- Cowork on Mac can "Record a skill" from a ~10-minute screen recording (Pro/Max/Team). [HC-CREATE]
- Enabled skills also apply in the Claude for Excel, PowerPoint, Word, and Outlook add-ins. [HC-USE]

### 10.2 Claude Code
- Locations [CC]:

| Level | Path |
|---|---|
| Enterprise (managed) | `.claude/skills/<name>/SKILL.md` in the managed settings dir |
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project | `.claude/skills/<name>/SKILL.md` (commit it) |
| Nested (monorepo) | `<subdir>/.claude/skills/...` |
| `--add-dir` | `<dir>/.claude/skills/...` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` → `/plugin-name:skill-name` |

- Precedence: enterprise > personal > project. A same-name skill replaces a bundled one. A skill beats a `.claude/commands` file. Plugin skills are namespaced. [CC]
- **Custom slash commands have been merged into skills.** `.claude/commands/deploy.md` still works, but prefer `.claude/skills/deploy/SKILL.md`, which supports extra files. [CC]
- Live reload: edits to SKILL.md are picked up mid-session. Use `/reload-skills` for a newly created top-level skills dir. [CC]
- Invocation: `/skill-name [args]`, or automatic. You can stack up to 6 skills in one message. [CC]
- Permissions:
  - `Skill(name)` / `Skill(name *)` allow/deny rules.
  - `allowed-tools` grants tools **for the invoking turn only**. It isn't gated by workspace trust, so review checked-in skills.
  - `skillOverrides` (`on` / `name-only` / `user-invocable-only` / `off`). [CC]
- **claude.ai → Claude Code sync** (v2.1.273+, claude.ai login only, not API-key or Bedrock sessions):
  - Skills download into `~/.claude/skills/synced/` about every 10 minutes. The sync is one-way, and local edits there get overwritten.
  - Names are `/anthropic-skills:<name>`.
  - `!` injection does **not** run for synced skills on your machine.
  - Opt out with `syncClaudeAiSkills: false`. [CC] [HC-USE]
- Cowork and cloud sessions don't read `~/.claude/skills`. Use claude.ai-enabled skills or repo `.claude/skills`. [CC]
- Distribution: commit `.claude/skills/`, ship as a **plugin** (marketplace), or deploy via managed settings. [CC]
- Anthropic's example skills: `/plugin marketplace add anthropics/skills`, then `/plugin install document-skills@anthropic-agent-skills` or `example-skills@…`. [REPO]

### 10.3 Claude API (Messages + Skills API)
- Skills need the **code execution tool** (`{"type":"code_execution_20250825","name":"code_execution"}`). [API]
- Pass skills in `container.skills`: `{"type":"anthropic"|"custom","skill_id":…, "version":…}`, **max 20 per request**. [API]
  - Anthropic skill IDs: `pptx|xlsx|docx|pdf`, with date versions like `20251013` or `latest`.
  - Custom skill IDs look like `skill_01…`, with versions `skver_01…` or `latest`. [API]
- **Skills API (`/v1/skills`) is GA; no beta header is needed** [API]:
  - Legacy `anthropic-beta: skills-2025-10-02` still works but returns the old shapes.
  - The old field names were `display_title` and `latest_version`. They're now `display_name` (≤255 chars, not unique) and `latest_version_id`.
  - `DELETE /v1/skills/{id}` now deletes all versions.
- Create a skill by uploading a zip or individual files [API]:
  - SDKs: Python `files_from_dir()`; CLI `ant apply <dir>`.
  - `SKILL.md` may sit at the upload root or inside a single top folder.
  - Limit: 30 MB uncompressed.
- **Versions are full snapshots**: re-upload all files, and the `name` must stay the same. [API]
- **Pin versions in production.** With `latest`, anyone in the workspace uploading a new version changes prod behavior immediately. [API] [ENT]
- In the container, files are copied to `/skills/{skill-name}/`. [API]
- Custom skills are **workspace-wide**: any key with workspace access can read, invoke, and delete them. For multi-tenant SaaS, use **one workspace per tenant** (default max 100 workspaces/org). [API] ← important for Snapland if you host skills per customer.
- Runtime: no network, no runtime installs, fresh container unless you reuse `container.id`. Handle `pause_turn` for long operations. Download outputs via the Files API (`file_id`). [API]
- Not covered by ZDR. Compliance API Activity Feed logs create/delete events. [API] [OV]

### 10.4 Claude Agent SDK
- Skills are **filesystem-only**; there's no programmatic registration. They're discovered via `settingSources`/`setting_sources` (`"user"`, `"project"`): `~/.claude/skills`, `<cwd>/.claude/skills` and parent dirs up to the repo root, `add_dirs`/`additionalDirectories`, or the `plugins` option. [SDK]
- The `skills` option can be `"all"`, a list of exact names, or `[]`. Setting it auto-adds the `Skill` tool. If you pass an explicit `tools` list, include `"Skill"`. [SDK]
- Confirm loading via the `system/init` message's `skills` and `slash_commands` arrays. You can dispatch by sending `/<name>` in the prompt. [SDK]
- A common failure: `setting_sources=[]` loads no skills. Also check that `cwd` is at or under the directory holding `.claude/skills`. [SDK]

### 10.5 Claude Managed Agents (beta, `managed-agents-2026-04-01`)
- Attach skills via the agent's `skills` array (up to 500 per session), or mount a GitHub repo. Its root `.claude/skills` is auto-discovered, which makes the repo part of your **trust boundary**. [MA: https://platform.claude.com/docs/en/managed-agents/skills]

## 11. Skills vs CLAUDE.md vs commands vs subagents vs hooks vs MCP

| Use… | When | Source |
|---|---|---|
| **CLAUDE.md** | "Always do X" rules every session needs. Keep it under 200 lines. | [CCF] |
| **Skill** | Reference material needed *sometimes*, or a repeatable workflow (`/name`). Also: "you paste the same playbook… for the third time." | [CCF] [CC] |
| **Slash command** | Legacy. Now just a user-invocable skill. Use `disable-model-invocation: true` for manual-only. | [CC] |
| **Subagent** | Context isolation: reading many files, parallel work, returning only a summary. Can preload skills (`skills:` field, full content injected at startup). A skill can run *as* a subagent via `context: fork`. | [CCF] [CC] |
| **Hook** | Must happen **deterministically** on every event (lint after edit, block unsafe commands). "An instruction… in a skill is a request, not a guarantee." Put guardrails in hooks. | [CCF] |
| **MCP** | Connection and auth to external systems (tools/data). A skill teaches *how* to use those tools well. The pattern is **Skill + MCP**. | [CCF] [BLOG] |
| **Plugin** | Packaging layer for sharing skills + hooks + subagents + MCP across repos and teams. | [CCF] |

## 12. Workflow patterns from "Building effective agents" [BEA]
The post is from Dec 2024. It now carries a note that "much of the tooling landscape… has changed" and points to Managed Agents. The core patterns still hold:
- **Workflows** (predefined code paths) vs **agents** (the LLM directs its own process). Start with the simplest thing, and add complexity only when it measurably helps.
- **Prompt chaining**: fixed sequential steps with programmatic "gates". → In a skill: a checklist workflow with validation gates between steps.
- **Routing**: classify, then send to a specialized path. → A conditional-workflow section in SKILL.md pointing to per-branch reference files. Or several narrow skills whose descriptions do the routing.
- **Parallelization** (sectioning or voting). → In Claude Code, a skill that spawns subagents (`/audit` spawning security/perf/style subagents [CCF]), or `context: fork`.
- **Orchestrator-workers**: a central LLM decomposes dynamically. → An agent loop, subagents, or dynamic workflows.
- **Evaluator-optimizer**: generate, critique, refine. → A skill "feedback loop" with a checklist or validation script as the evaluator.
- Agent principles: simplicity, transparency (show planning), and a careful **agent-computer interface**. Document tools as you would for a junior dev, and "poka-yoke" them. This applies directly to scripts inside skills.
- Customer-support agents are called out as a strong fit: conversation plus tools plus a measurable resolution. That maps to real-estate lead bots.

## 13. Security
- **Only use skills from trusted sources** (your own or Anthropic's). A malicious skill can direct tool use, run code, or exfiltrate data. "Treat like installing software." [OV] [BLOG]
- Audit every file: SKILL.md, scripts, images, resources. Look for network calls, unexpected file access, and instructions to hide actions or ignore safety rules. [OV] [ENT]
- **External URL fetching is risky.** Fetched content can carry prompt injection, and dependencies can change later. [OV]
- Risk tiers [ENT]:
  - **High**: scripts, instruction manipulation, MCP references, network patterns, hardcoded credentials.
  - **Medium**: filesystem scope beyond the skill dir or `../`, tool invocations.
- **Never hardcode secrets** in skills. Use env vars or a secret store, and "Use appropriate MCP connections for external service access." [HC-CREATE] [ENT]
- "Principle of Lack of Surprise": a skill's contents shouldn't surprise the user if described. [REPO skill-creator]
- Claude Code specifics [CC]:
  - `allowed-tools` in a repo skill applies even in untrusted folders and `-p` runs, so review it.
  - `disableSkillShellExecution` blocks `!` injection (useful in managed settings).
- Integrity: checksums plus signed commits; version pinning in the API. [ENT]
- Data: Skills are not covered by ZDR. [OV]

## 14. Common mistakes
1. Vague or first-person description, or no "when to use". [BP]
2. Non-spec frontmatter keys (e.g. `dependencies`, `argument-hint`) in a skill uploaded to claude.ai or the API → hard upload error. [CC]
3. `name` doesn't match the folder, has uppercase or spaces, or contains `claude`/`anthropic`. [SPEC] [OV]
4. Angle brackets or XML in the description (rejected by `quick_validate.py`). [REPO]
5. SKILL.md over 500 lines, or explaining things Claude already knows. [BP]
6. Deeply nested references, or long references without a TOC. [BP]
7. Too many options with no default. [BP]
8. Scripts that are interactive, fail silently, print huge unstructured output, or leave it unclear whether to run or read. [AS-SCR] [BP]
9. Assuming network or package installs on the API. [OV]
10. Windows backslash paths. [BP]
11. Time-sensitive text ("before Aug 2025 use…"). [BP]
12. Testing only in the authoring session (context masks gaps). Use fresh sessions and baselines. [CC] [AS-EVAL]
13. Overfitting the description to test queries. [AS-DESC]
14. One mega-skill that does everything (hard to trigger precisely), or micro-skills that always co-load. [AS-BP] [HC-CREATE]
15. `latest` version in API production. [API]
16. Relying on a skill instruction for a hard guardrail. Use a hook, or a code-level check in your app. [CCF]
17. `context: fork` on a guidelines-only skill: the subagent gets no actionable task. [CC]

## 15. Authoring checklist (merge of [BP] checklist + extras)
**Metadata**
- [ ] `name`: kebab-case, ≤64 chars, equals the folder name, no reserved words
- [ ] `description`: ≤1024 chars (and front-loaded for the 1,536 Claude Code cap), third-person "what" + "Use when…", key terms, boundaries ("Do NOT use for…"), no `<>`
- [ ] Only spec fields if the skill will be uploaded to claude.ai or the API
**Body**
- [ ] Under 500 lines / ~5k tokens; only what Claude lacks
- [ ] Clear workflow steps / checklist; validation loop for quality-critical steps
- [ ] Gotchas section; concrete examples; output template
- [ ] Defaults, not menus; consistent terminology; no time-sensitive info
- [ ] References one level deep, each with a "read this when…" trigger; TOC on long files
**Code**
- [ ] Scripts: non-interactive, `--help`, structured stdout, helpful errors, no magic numbers, pinned deps
- [ ] Run vs read intent is explicit; forward-slash relative paths
- [ ] Dependencies verified for the target surface (API: no network, no installs)
**Testing**
- [ ] ≥3 evals (should/shouldn't/edge) + baseline without the skill
- [ ] ~20-query trigger set with near-miss negatives; train/validation split
- [ ] Tested on each target model (Haiku/Sonnet/Opus); fresh sessions
- [ ] Coexistence test with the other skills in the same environment
**Security & ops**
- [ ] No secrets; network access justified; audited scripts
- [ ] In Git; version pinned in prod; registry entry (purpose, owner, version, deps, eval status)

## 16. Recent changes and ambiguities (as of 2026-09-30)
- **Skills API is GA.** The `skills-2025-10-02` beta header is no longer needed, and several fields and behaviors changed (`display_name`, `latest_version_id`, `skver_` IDs, delete cascades). SDK `client.skills` replaces `client.beta.skills`. [API] Help Center pages still say "in beta for API users". **[CONFLICT, stale]** [HC-USE] [HC-CREATE]
- **Help Center "create custom skills" is out of step with the platform docs** [HC-CREATE]:
  - It says `name` is "human-friendly" ("Brand Guidelines"), `description` has a "200 characters maximum", and there's an optional `dependencies` field. It also uses a lowercase `skill.md`.
  - The platform docs and spec require lowercase-hyphen names, allow up to 1024 chars, and **reject** unknown keys like `dependencies` on upload [OV] [SPEC] [CC]. The official repo uses `SKILL.md`.
  - **[OPINION]** Follow the spec: `SKILL.md`, kebab-case name. The 200-char figure may be a UI display limit or just stale. Keep descriptions tight, but don't treat 200 as the hard limit.
- **Sharing on claude.ai:**
  - [OV] says custom skills are individual-only and can't be centrally managed.
  - [HC-USE] (updated ~Sep 2026) describes sharing, publishing to an org library, review workflows, and owner provisioning on Team/Enterprise.
  - The Help Center is newer; treat [OV] as stale on this point.
- **Cross-surface sync:**
  - [OV] and [ENT] say skills don't sync across surfaces.
  - Claude Code v2.1.273+ now **downloads claude.ai-enabled skills** (one-way) when you're signed in with a claude.ai account [CC] [HC-USE]. API skills still don't sync anywhere.
- **Plan availability**: [HC-USE] includes the Free plan; [OV] lists Pro/Max/Team/Enterprise.
- **Description voice**:
  - [BP] says "Always write in third person."
  - [AS-DESC] says "Use imperative phrasing… 'Use this skill when…'".
  - Official repo skills mix both ("Use this skill whenever…", "Applies Anthropic's brand…").
  - They're compatible if you use the pattern third-person capability + "Use when…". Avoid "I" and "you can".
- **Size guidance**: [BP] says a TOC for references over 100 lines; skill-creator says over 300 lines. [BP] says SKILL.md under 500 lines; [SPEC] adds a <5,000-token recommendation.
- **Emphasis words**: [BP] suggests "MUST" can fix ignored rules; skill-creator and [AS-EVAL] prefer explaining the reasoning over all-caps rules.
- **Usage analytics**:
  - [ENT] says they're not available via the Skills API.
  - The API index lists a beta "Get Skill Usage" org-analytics endpoint (`/docs/en/api/beta/organization/analytics/skills/list`). **[UNCERTAIN]** I didn't read that page.
- **Claude Code grew many Claude Code-only frontmatter fields and features in 2026**: `when_to_use`, `arguments`, `background`, `paths`, `shell`, `disallowed-tools`, `effort`, `hooks`, `metadata`, stacking, `/skill-doctor`, `claude plugin eval`, reserved `anthropic-skills:` namespace. Version-gated behaviors are listed in [CC].
- API examples now show model id `claude-opus-5-5` [API]. The [BEA] routing example still mentions Haiku 4.5 / Sonnet 4.5 (older text).
- **[UNCERTAIN]** The exact package list in the API container isn't reproduced here. Check the Code execution tool docs before relying on a library.

---

## סיכום קצר בעברית

- **מה זה Skill:** תיקייה עם קובץ `SKILL.md` (frontmatter בפורמט YAML ואחריו הוראות ב-Markdown), ואפשר לצרף אליה סקריפטים, קבצי reference ו-assets. Claude טוען אותה רק כשהיא רלוונטית. זה נקרא progressive disclosure: קודם רק השם והתיאור (~100 טוקנים), אחר כך גוף ה-SKILL.md, ובסוף רק הקבצים שבאמת נדרשים.
- **שדות חובה:** `name` באותיות לועזיות קטנות, ספרות ומקפים, עד 64 תווים, זהה לשם התיקייה ובלי המילים claude/anthropic. `description` עד 1024 תווים, בלי תגיות XML או סוגריים משולשים.
  - ב-claude.ai וב-API מותרים רק שישה שדות: name, description, license, compatibility, metadata, allowed-tools. כל שדה אחר גורם לכישלון בהעלאה.
- **התיאור (description) קובע מתי ה-Skill יופעל:** לכתוב בגוף שלישי מה ה-Skill עושה, להוסיף "Use when…" עם ביטויים ומילות מפתח שמשתמשים באמת כותבים (אפשר גם בעברית), ולציין מתי *לא* להשתמש בו. כדאי שיהיה קצת "אגרסיבי", כי Claude נוטה להפעיל Skills פחות מדי.
- **גוף הקובץ:** עד כ-500 שורות. לכתוב רק מה ש-Claude לא יודע בעצמו. לתת צ'קליסט של שלבים, לולאת ולידציה, תבנית פלט, דוגמאות וסעיף Gotchas. הפניות לקבצים נוספים ברמה אחת בלבד. להגדיר ברירת מחדל אחת ולא תפריט של אפשרויות.
- **סקריפטים:** לפעולות דטרמיניסטיות (חישובים, ולידציה). בלי קלט אינטראקטיבי, פלט JSON והודעות שגיאה ברורות. ב-API אין רשת ואין התקנת חבילות בזמן ריצה.
- **בדיקות:** קודם מריצים בלי Skill כדי לקבל baseline, ואז בונים לפחות 3 evals עם ה-Skill ובלעדיו. בנוסף, סט של כ-20 שאילתות טריגר (חיוביות ו-near-miss שליליות) עם חלוקה ל-train/validation. בודקים על כל מודל שבשימוש. הכלים: `skill-creator` ו-`claude plugin eval`.
- **הפצה:**
  - claude.ai: קובץ ZIP דרך Customize > Skills. ב-Team/Enterprise אפשר לשתף ולפרסם לארגון.
  - Claude Code: `~/.claude/skills` או `.claude/skills`, או דרך plugins.
  - API: דרך `/v1/skills`. ה-API יצא מבטא ולא צריך יותר beta header. לנעוץ גרסה ב-production. Workspace נפרד לכל לקוח.
  - Agent SDK: טעינה ממערכת הקבצים דרך `settingSources`.
- **Skill מול שאר הכלים:**
  - CLAUDE.md: כללים שתמיד חלים.
  - Skill: ידע ותהליכים לפי צורך.
  - Subagent: בידוד קונטקסט.
  - Hook: אכיפה דטרמיניסטית, כלומר guardrails אמיתיים.
  - MCP: חיבור למערכות חיצוניות, כשה-Skill מלמד איך להשתמש בו.
- **אבטחה:** להתקין Skills רק ממקורות מהימנים ולבדוק כל קובץ. בלי סודות בקבצים, ולהיזהר משליפת תוכן מ-URL חיצוני (prompt injection).
- **שימו לב:** יש סתירות בין מרכז העזרה לבין התיעוד הרשמי, למשל תיאור של 200 תווים מול 1024, שדה `dependencies`, ושיתוף ב-claude.ai. פירוט בסעיף 16.
