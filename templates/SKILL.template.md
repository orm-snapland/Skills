---
name: your-skill-name
description: Does X and Y for Z (third person, concrete key terms, file types, domain nouns). Use when the user asks to A, B, or C, or mentions D or E, even if they don't explicitly say "X". Do NOT use for F or G (adjacent tasks handled elsewhere).
license: Proprietary. LICENSE.txt has complete terms
compatibility: Requires Python 3.11+ and uv. No network access needed.
metadata:
  author: snapland
  version: "0.1.0"
---
<!--
TEMPLATE NOTES (delete this comment block before shipping):
- Folder name MUST equal `name` (kebab-case, a-z 0-9 -, max 64 chars, no leading/trailing/double hyphen, must not contain "claude" or "anthropic").
- `description`: required, 1-1024 chars, no XML/angle brackets. Put the key use case first (Claude Code truncates description+when_to_use at 1,536 chars). Quote the value if it contains a colon followed by a space, or YAML will mis-parse it.
- Include Hebrew trigger phrases in `description` (the spec allows Unicode). Third person for the capability sentence, then "Use when…" and "Do NOT use for…".
- Frontmatter above uses ONLY the six Agent Skills spec fields (name, description, license, compatibility, metadata, allowed-tools),
  so it uploads cleanly to claude.ai and the Skills API. `license`, `compatibility`, `metadata`, and `allowed-tools` are optional: delete any you do not use.
- `allowed-tools` is upload-safe but experimental; support varies by client. Quote every `metadata` value. `metadata.version` must be semver (for example "0.1.0") and must be bumped when you upload a new API version.
- Claude Code-only fields (add ONLY in a copy that is not uploaded, and add a CLAUDE-CODE-ONLY marker file in that folder so the validator allows them and the packager refuses a claude.ai zip): when_to_use, argument-hint, arguments, disable-model-invocation, user-invocable, disallowed-tools, model, effort, context, agent, background, hooks, paths, shell.
- Keep this body under ~500 lines / ~5k tokens. Only write what Claude would get wrong without being told.
- Use forward-slash relative paths from the skill root. Keep references one level deep.
-->

# Your Skill Title

One or two sentences: the goal of this skill and what a good result looks like.

## Quick start
The most common path in a few lines, with one concrete example.

```bash
python3 scripts/main_task.py --input input.json --output out.json
```

## Workflow
Copy this checklist into your response and tick items off as you go:

```
Progress:
- [ ] Step 1: Gather inputs (see "Inputs")
- [ ] Step 2: Do the core work
- [ ] Step 3: Validate: `python3 scripts/validate.py out.json`
- [ ] Step 4: Fix any reported issues and re-run validation until it passes
- [ ] Step 5: Produce the final output using the template below
```

**Step 1: Gather inputs.** List the required fields. If any are missing, ask the user for them rather than guessing, because guessing fills gaps with facts the user never provided.

**Step 2: Core work.** Give one clear default approach. Mention an alternative only as an escape hatch:
"Use A. If B happens (e.g. scanned document), use C instead."

**Step 3–4: Validate.** Only continue once validation passes.

## Decision points
- **Case A** (e.g. rental listing) → follow the steps in [references/case-a.md](references/case-a.md)
- **Case B** (e.g. sale listing) → follow the steps in [references/case-b.md](references/case-b.md)

## Output format
Use this template, adapting sections only when the user asked for a shorter variant:

```markdown
# [Title]
## Summary
[2–3 sentences]
## Details
- ...
## Next steps
1. ...
```

## Examples
**Input:** "A realistic user message, including a Hebrew phrasing you expect in production."
**Output:** A short example of the expected result.

## Gotchas
- An environment- or domain-specific fact that defies reasonable assumptions, for example "field X is called Y in system Z".
- A correction you had to make during testing. Add a new one every time Claude gets something wrong.

## Bundled resources
- `scripts/main_task.py`: **run** it (don't read it). `--help` shows usage. Prints JSON to stdout and errors to stderr.
- `scripts/validate.py`: **run** after producing output. Exit code 0 means valid. Otherwise it lists specific problems.
- `references/case-a.md`: read **only** when handling Case A.
- `assets/template.docx`: output template. Copy it, don't modify the original.
