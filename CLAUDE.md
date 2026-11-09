# Snapland skills — instructions for Claude Code

This repository is the source of truth for Snapland's custom Agent Skills (real-estate bots, Israel). Skills do not sync across claude.ai, Claude Code, and the API, so Git is canonical. The researched spec is `docs/anthropic-skills-guide.md`. Domain sketches in `docs/real-estate-ideas.md` are suggestions, not skills to implement unless asked. Legal and tax figures stay out of skill bodies until someone verifies them.

`skills/` is for portable skills only. Do not add a production skill that nobody asked for. Put validator fixtures in `tests/fixtures/`.

## Layout

```
skills/<kebab-case-name>/
  SKILL.md          # required
  scripts/          # run, don't read, unless the skill says otherwise
  references/       # one level deep from SKILL.md
  assets/
  evals/            # not uploaded; evals.json + triggers.json
```

Copy `templates/your-skill-name/` (same text as `templates/SKILL.template.md`) and rename it. Delete the HTML comment in `SKILL.md` before shipping.

## Frontmatter

Opening `---` is line 1, no BOM. Upload-safe keys only:

`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.

Any other key fails claude.ai and `POST /v1/skills`. Claude Code-only keys (`when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`) require a `CLAUDE-CODE-ONLY` file in that folder. The packager then refuses a claude.ai zip.

- `name`: 1–64 chars, `a-z`, `0-9`, hyphens; no leading, trailing, or double hyphen; must not contain `claude` or `anthropic`; must equal the folder name.
- `description`: 1–1024 chars, no `<` or `>`. Third person, key use case first. Pattern: capability sentence, then `Use when…` (real phrasings, including Hebrew), then `Do NOT use for…`.
- `metadata.version`: quoted semver (`"0.1.0"`). Bump it on every change you upload. Record `skill_id` and the pinned `skver_…` in `CHANGELOG.md`. Do not pin `latest`.
- Quote every metadata value. `allowed-tools` is a space-separated string and is experimental.

## Body

Under 500 lines. Only facts Claude would get wrong: workflow checklist, validation loop, one default, output template, examples, gotchas. Forward-slash paths from the skill root. Tell the agent when to read each reference. References over ~100 lines get a table of contents. No secrets, no time-sensitive tax rates, no interactive scripts. Scripts: `--help`, JSON on stdout, errors on stderr, pinned deps. Say whether to run or read each file.

Hebrew output templates can live in `references/` or `assets/`. State the language rule in the body ("reply in the user's language").

Side effects (send a message, book a showing, write the CRM) are enforced in app code or hooks, not by prose. In Claude Code only, `disable-model-invocation: true` is for manual workflows, and that copy is marked `CLAUDE-CODE-ONLY`.

## Testing

1. Run the task without the skill and write down the failures.
2. Add at least three evals in `evals/evals.json` (happy path, messy Hebrew input, edge case), each with and without the skill, in a fresh session.
3. Add trigger queries in `evals/triggers.json`: should-trigger and near-miss should-not-trigger. Do not paste failed queries verbatim into the description.
4. Check coexistence with the other skills in `skills/`.

`evals/` is omitted from the zip.

## Before you finish

```bash
python -m pip install -r tooling/requirements.txt
python tooling/validate_skills.py
python tooling/package_skill.py <skill-name>
```

Warnings (line count, missing "Use when", missing Hebrew under `skills/`) fail the check only with `--strict`. Errors always fail.

## Checklist

- [ ] `name` matches the folder and the character rules
- [ ] `description` ≤ 1024, third person, Hebrew triggers, `Use when…`, `Do NOT use for…`, no `<>`
- [ ] Only the six spec fields, or a `CLAUDE-CODE-ONLY` marker
- [ ] `metadata.version` bumped; API pin recorded when uploaded
- [ ] Body under 500 lines; gotchas, one default, validation loop
- [ ] No secrets; scripts non-interactive
- [ ] ≥3 evals and a trigger set, including a baseline without the skill
- [ ] `python tooling/validate_skills.py` exits 0
