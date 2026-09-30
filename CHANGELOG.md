# Changelog

היסטוריית הריפו. הגרסה של כל Skill היא `metadata.version` ב-`SKILL.md` שלו, לא מספר כאן.

Repo history. Each skill's package version is `metadata.version` inside that skill. Bump it whenever the skill changes, and record the API ids below after upload. Production bots must pin `version` to a `skver_…` id, never `latest`.

## API version pins

| Skill | metadata.version | skill_id | version id (pin this) | Uploaded |
| --- | --- | --- | --- | --- |
| _none yet_ | | | | |

## 0.1.0 — 2026-09-30

- Initial layout for Snapland's Claude Agent Skills: `skills/`, `docs/`, `templates/`, and `tooling/`.
- Validator and packager, with a GitHub Actions check on pull requests and pushes to `main`.
- No production skills yet. The only `SKILL.md` files are the template and a fixture under `tests/`.
