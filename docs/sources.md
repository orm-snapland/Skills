# Sources read (2026-09-30)

## Anthropic platform docs (platform.claude.com)
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview: Skills overview: 3-level loading, frontmatter rules, surfaces, security, runtime constraints, cross-surface limits.
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices: Authoring best practices: conciseness, degrees of freedom, naming, descriptions, progressive disclosure patterns, workflows/feedback loops, evals, Claude A/B, anti-patterns, checklist.
- https://platform.claude.com/docs/en/build-with-claude/skills-guide (+ .md): Using Skills with the API: container.skills, code execution tool, Skills API CRUD/versions, limits (20/request, 30 MB), GA migration from skills-2025-10-02, workspace scoping.
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise.md: Skills for enterprise: risk tiers, review checklist, content scanning, eval dimensions, lifecycle, versioning, registry.
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart.md: API quickstart (downloaded; skimmed only).
- https://platform.claude.com/docs/en/managed-agents/skills.md: Managed Agents skills (beta): attach up to 500/session, GitHub repo `.claude/skills` discovery, `ant apply` + claude-lock.json.
- https://platform.claude.com/llms.txt: Docs index (used to find skill-related pages, incl. the beta skill-usage analytics endpoint listing).

## Claude Code docs (code.claude.com)
- https://code.claude.com/docs/en/skills: Claude Code skills: locations, precedence, full frontmatter reference, substitutions, dynamic context injection, context: fork, permissions, skillOverrides, claude.ai sync, evals with skill-creator / claude plugin eval, troubleshooting.
- https://code.claude.com/docs/en/agent-sdk/skills.md: Agent SDK skills: settingSources, `skills` option, init message, command dispatch, troubleshooting.
- https://code.claude.com/docs/en/features-overview.md: "Extend Claude Code": when to use CLAUDE.md vs skills vs subagents vs hooks vs MCP vs plugins; context costs.
- https://code.claude.com/docs/en/sub-agents.md: Subagents (searched for skills-related parts: `skills` preload field, isolation).
- https://code.claude.com/docs/llms.txt: Claude Code docs index.

## Open standard (agentskills.io)
- https://agentskills.io/specification: The Agent Skills spec: fields, constraints, directory conventions, progressive disclosure, validation (skills-ref).
- https://agentskills.io/skill-creation/best-practices.md: Best practices for skill creators: real expertise, gotchas, templates, calibrating control, plan-validate-execute.
- https://agentskills.io/skill-creation/optimizing-descriptions.md: Description optimization: trigger eval queries, near-misses, trigger rate, train/validation split.
- https://agentskills.io/skill-creation/evaluating-skills.md: Output-quality evals: evals.json, with/without skill, grading.json, benchmark.json, human review, iteration.
- https://agentskills.io/skill-creation/using-scripts.md: Scripts in skills: one-off commands, PEP 723 self-contained scripts, agent-friendly script design.
- https://agentskills.io/home.md and https://agentskills.io/llms.txt: Overview page / index (little text content extracted).

## Anthropic engineering blog
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills: Agent Skills launch post (2025-10-16; open-standard update 2025-12-18): anatomy, progressive disclosure, code execution, dev/eval guidelines, security.
- https://www.anthropic.com/engineering/building-effective-agents: Building effective agents (2024-12-19, with a newer note): workflows vs agents, prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer, ACI/tool design.

## Claude Help Center
- https://support.claude.com/en/articles/12512198-creating-custom-skills: How to create custom skills (claude.ai): zip packaging, record-a-skill, best practices. Contains values that conflict with the platform docs.
- https://support.claude.com/en/articles/12512180-using-skills-in-claude: Use skills in Claude: enabling, uploading, sharing/publishing/provisioning, M365 add-ins, Claude Code sync, troubleshooting, security.

## GitHub
- https://github.com/anthropics/skills (cloned, commit 8a1541c, 2026-09-28): README, template/SKILL.md, spec pointer, marketplace.json, all example SKILL.md frontmatters.
- https://github.com/anthropics/skills/tree/main/skills/skill-creator: skill-creator SKILL.md, scripts/quick_validate.py, scripts/package_skill.py (eval loop, description optimizer, packaging rules).

## Israeli real-estate context (for real-estate-ideas.md)
- https://www.gov.il/en/service/real_estate_information: Israel Tax Authority public real-estate transactions database (free; search by address or block/parcel).
- https://www.gov.il/en/service/land_registration_extract: Ministry of Justice: generating a Tabu (land registry) extract; contents; gush/chelka/tat-chelka.
- https://www.odata.org.il/dataset/nadlan: "מידע לעם" open real-estate transactions dataset (seen via search result only).
- https://www.themarker.com/realestate/2026-09-27/ty-article/.premium/000001a0-dccc-d259-a3b4-dcdc5e560000: TheMarker article on the 3.8M-transaction dataset release (paywalled; search snippet only).
- https://github.com/nitzpo/nadlan-mcp: Community MCP server wrapping Govmap real-estate deal APIs (search snippet only; third-party, unaudited).
