#!/usr/bin/env python3
"""Zip skills into dist/ in the layout claude.ai expects.

The archive root is the skill folder:

    dist/my-skill.zip
      my-skill/SKILL.md
      my-skill/scripts/...

Root-level evals/, __pycache__, node_modules, .git, virtualenvs, .pyc,
.DS_Store, .gitkeep, and the CLAUDE-CODE-ONLY marker are left out. The skill
is validated before zipping.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import skillslib  # noqa: E402


class _UsageError(Exception):
    pass


def _skills_to_package(args: argparse.Namespace) -> list[Path]:
    if args.path:
        paths = []
        for raw in args.path:
            path = raw if raw.is_absolute() else Path.cwd() / raw
            if not (path / "SKILL.md").is_file():
                raise _UsageError(f"No SKILL.md in {path}")
            paths.append(path)
        return paths

    if args.skills_dir is not None:
        skills_dir = args.skills_dir
        if not skills_dir.is_absolute():
            skills_dir = Path.cwd() / skills_dir
        if args.skill == "all":
            return [
                path
                for path in skillslib.iter_skill_dirs(skills_dir)
                if (path / "SKILL.md").is_file()
            ]
        candidate = skills_dir / args.skill
        if not (candidate / "SKILL.md").is_file():
            raise _UsageError(f"No skill named '{args.skill}' under {skills_dir}")
        return [candidate]

    if args.skill == "all":
        return skillslib.iter_repo_skills()

    matches = skillslib.find_skill(args.skill)
    if not matches:
        areas = ", ".join(area.name for area in skillslib.skill_areas()) or "none"
        raise _UsageError(
            f"No skill named '{args.skill}'. Areas searched: {areas}."
        )
    if len(matches) > 1:
        listed = ", ".join(str(match.relative_to(skillslib.repo_root())) for match in matches)
        raise _UsageError(
            f"'{args.skill}' exists in more than one area ({listed}). Pass --path."
        )
    return matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill",
        nargs="?",
        default="all",
        help="Skill folder name, looked up across every area, or 'all' (default).",
    )
    parser.add_argument(
        "--path",
        action="append",
        type=Path,
        help="Package this skill directory instead of looking it up by name. Repeatable.",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=None,
        help="Look the name up in this directory instead of searching every area.",
    )
    parser.add_argument(
        "--dist",
        type=Path,
        default=skillslib.repo_root() / "dist",
        help="Output directory (default: dist/).",
    )
    parser.add_argument(
        "--allow-claude-code-only",
        action="store_true",
        help="Package a skill even if it has a CLAUDE-CODE-ONLY marker. The zip will not upload to claude.ai.",
    )
    args = parser.parse_args(argv)

    if not skillslib.pyyaml_available():
        print(
            "PyYAML is not installed. Run: python -m pip install -r tooling/requirements.txt",
            file=sys.stderr,
        )
        return 1

    try:
        targets = _skills_to_package(args)
    except _UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not targets:
        where = args.skills_dir or "the repo's areas"
        print(f"No skills to package under {where}.")
        return 0

    dist = args.dist if args.dist.is_absolute() else Path.cwd() / args.dist
    wrote = 0
    for target in targets:
        try:
            archive = skillslib.package_skill(
                target,
                dist,
                allow_claude_code_only=args.allow_claude_code_only,
            )
        except skillslib.SkillError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Packaged {archive}")
        wrote += 1
    print(f"\n{wrote} zip(s) in {dist}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
