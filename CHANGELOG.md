# Changelog

היסטוריית הריפו. הגרסה של כל Skill היא `metadata.version` ב-`SKILL.md` שלו, לא מספר כאן.

Repo history. Each skill's package version is `metadata.version` inside that skill. Bump it whenever the skill changes, and record the API ids below after upload. Production bots must pin `version` to a `skver_…` id, never `latest`.

## API version pins

| Skill | metadata.version | skill_id | version id (pin this) | Uploaded |
| --- | --- | --- | --- | --- |
| _none yet_ | | | | |

## 0.2.0 — 2026-11-10

- Added the production skills, grouped by the kind of work they do: `01-feasibility-report/` (`go-no-go-v3`, `planning-check`), `02-existing-state/` (`permit-measurement`), `03-market-survey/` (a placeholder README), and `shared/israel-massing-rules`.
- Dropped the catch-all `skills/` folder. The type folders and `shared/` are the only homes for a skill.
- `tooling/` discovers skills in every `NN-*` folder and in `shared/`; `package_skill.py <name>` looks a name up across them. The Hebrew equivalents of `Use when…` and `Do NOT use for…` now satisfy the description check.
- Gave each skill a `metadata.version`: `go-no-go-v3` 3.0.0, the other three 1.0.0. None uploaded to the API yet.

## 0.1.0 — 2026-09-30

- Initial layout for Snapland's Claude Agent Skills: `skills/` (replaced in 0.2.0 by the type folders), `docs/`, `templates/`, and `tooling/`.
- Validator and packager, with a GitHub Actions check on pull requests and pushes to `main`.
- No production skills yet. The only `SKILL.md` files are the template and a fixture under `tests/`.
