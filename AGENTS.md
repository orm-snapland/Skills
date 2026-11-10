# Instructions for coding agents

Read and follow [CLAUDE.md](CLAUDE.md) before editing this repository. It is the canonical authoring checklist for Snapland skills. The long-form spec notes live in [docs/anthropic-skills-guide.md](docs/anthropic-skills-guide.md).

Hard rules, even before you open those files:

- Skills are grouped by type: `01-feasibility-report/`, `02-existing-state/`, `03-market-survey/`, and `shared/` for skills other skills depend on. A portable skill goes in `<NN>-<type>/<kebab-case-name>/` or `shared/<kebab-case-name>/`. There is no catch-all `skills/` folder.
- The `name` in `SKILL.md` must equal the folder name.
- Frontmatter may contain only `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools`, unless the folder has a `CLAUDE-CODE-ONLY` marker.
- `description` is third person, at most 1024 characters, with no `<` or `>`. Include Hebrew trigger phrases, a `Use when…` clause, and a `Do NOT use for…` boundary.
- Keep `SKILL.md` under 500 lines. Set `metadata.version` to a quoted semver string and bump it when the skill changes.
- Do not put secrets, customer data, or production real-estate skills in the repo unless someone asked for that skill. Fixtures belong in `tests/`.
- Run `python tooling/validate_skills.py` before you finish; with no arguments it walks every type folder and `shared/`. Package uploadable skills with `python tooling/package_skill.py <name>`, which looks the name up across the type folders.
