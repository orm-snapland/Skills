#!/usr/bin/env python3
"""Validate Snapland skill folders against the Agent Skills upload rules.

With no arguments, checks every skill under skills/ and the template at
templates/your-skill-name/. Pass directories to validate those instead.

Exit status is 0 when every skill has no errors. Line-count and description
style problems are warnings unless --strict is set.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import skillslib  # noqa: E402


class _UsageError(Exception):
    pass


def _expand(paths: list[Path]) -> list[Path]:
    targets: list[Path] = []
    for path in paths:
        if not path.exists():
            raise _UsageError(f"Path does not exist: {path}")
        if (path / "SKILL.md").is_file():
            targets.append(path)
            continue
        if path.is_dir():
            targets.extend(skillslib.iter_skill_dirs(path))
            continue
        raise _UsageError(
            f"Not a skill directory or a parent of skill directories: {path}"
        )
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Skill directories, or parents such as skills/. Default: skills/ plus the template.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (line count, description style, missing Hebrew) as errors.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    root = (args.repo_root or skillslib.repo_root()).resolve()
    try:
        if args.paths:
            targets = _expand(
                [path if path.is_absolute() else Path.cwd() / path for path in args.paths]
            )
        else:
            targets = skillslib.default_targets(root)
    except _UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not targets:
        print("No skill folders found. Add skills/<name>/SKILL.md, or pass a path.")
        return 0

    if not skillslib.pyyaml_available():
        print(
            "PyYAML is not installed. Run: python -m pip install -r tooling/requirements.txt",
            file=sys.stderr,
        )
        return 1

    reports = []
    for target in targets:
        reports.append(
            skillslib.validate_skill(
                target,
                expect_hebrew=skillslib.expect_hebrew_for(target, root),
            )
        )

    for report in reports:
        print(skillslib.format_report(report))
    error_count = sum(len(report.errors) for report in reports)
    warning_count = sum(len(report.warnings) for report in reports)
    print(
        f"\n{len(reports)} skill(s), {error_count} error(s), {warning_count} warning(s)."
    )
    failed = error_count + (warning_count if args.strict else 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
