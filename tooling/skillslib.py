"""Rules for Snapland Agent Skills.

Mirrors the Agent Skills spec fields that claude.ai and the Skills API accept,
plus the repo's versioning and Hebrew-trigger conventions. See
docs/anthropic-skills-guide.md.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only when the dep is missing
    yaml = None

SPEC_FIELDS = frozenset(
    {
        "allowed-tools",
        "compatibility",
        "description",
        "license",
        "metadata",
        "name",
    }
)

# Claude Code accepts these in addition to the spec fields. They are rejected
# on claude.ai and Skills API uploads.
CLAUDE_CODE_ONLY_FIELDS = frozenset(
    {
        "agent",
        "argument-hint",
        "arguments",
        "background",
        "context",
        "disable-model-invocation",
        "disallowed-tools",
        "effort",
        "hooks",
        "model",
        "paths",
        "shell",
        "user-invocable",
        "when_to_use",
    }
)

MARKER_FILENAME = "CLAUDE-CODE-ONLY"
MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
MAX_COMPATIBILITY_LEN = 500
MAX_SKILL_LINES = 500
RESERVED_NAME_WORDS = ("anthropic", "claude")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
NAME_RE = re.compile(r"^[a-z0-9-]+$")
HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
FIRST_PERSON_RE = re.compile(
    r"(?i)^\s*(i['’]?m\b|i can\b|i will\b|i help\b|you can\b|you should\b|אני\b|אתה יכול|את יכולה)"
)

# Root-level names omitted from claude.ai zips. `evals/` holds test prompts and
# must not ship. The marker file is repo metadata, not skill content.
EXCLUDED_ROOT_DIRS = frozenset({"evals"})
EXCLUDED_DIR_NAMES = frozenset({"__pycache__", "node_modules", ".git", ".venv", "venv"})
EXCLUDED_FILE_NAMES = frozenset(
    {".DS_Store", "Thumbs.db", ".gitkeep", MARKER_FILENAME}
)
EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})

# Fixed timestamp so repeated packages of unchanged skills are byte-stable.
ZIP_DATE_TIME = (2026, 9, 30, 0, 0, 0)


class SkillError(Exception):
    """A skill failed validation or packaging."""


@dataclass
class Issue:
    level: str  # "error" or "warning"
    message: str


@dataclass
class SkillReport:
    path: Path
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def pyyaml_available() -> bool:
    return yaml is not None


def iter_skill_dirs(parent: Path) -> list[Path]:
    """Return child directories of `parent` that are skill candidates."""
    if not parent.is_dir():
        return []
    return sorted(
        child
        for child in parent.iterdir()
        if child.is_dir() and not child.name.startswith(".")
    )


def default_targets(root: Path | None = None) -> list[Path]:
    """Skills under skills/, plus the checked-in template folder."""
    root = root or repo_root()
    targets = iter_skill_dirs(root / "skills")
    template = root / "templates" / "your-skill-name"
    if (template / "SKILL.md").is_file():
        targets.append(template)
    return targets


def is_claude_code_only(skill_dir: Path) -> bool:
    return (skill_dir / MARKER_FILENAME).is_file()


def _add(report: SkillReport, level: str, message: str) -> None:
    report.issues.append(Issue(level, message))


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (yaml_text, body). The opening --- must be the first line."""
    if text.startswith("\ufeff"):
        raise SkillError(
            "SKILL.md starts with a UTF-8 BOM. Remove it so the opening --- is the first bytes of the file."
        )
    if not text.startswith("---"):
        raise SkillError(
            "SKILL.md must start with YAML frontmatter (an opening --- on line 1). "
            "Claude Code only recognizes frontmatter in that position."
        )
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillError(
            "The opening --- must be alone on line 1. Frontmatter was not recognized."
        )
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise SkillError("Closing --- of the frontmatter was not found.")
    yaml_text = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :])
    return yaml_text, body


def _parse_frontmatter(yaml_text: str) -> dict:
    if yaml is None:
        raise SkillError(
            "PyYAML is not installed. Run: python -m pip install -r tooling/requirements.txt"
        )
    if not yaml_text.strip():
        raise SkillError("Frontmatter is empty.")
    try:
        loaded = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise SkillError(f"Frontmatter YAML could not be parsed: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SkillError(
            f"Frontmatter must be a YAML mapping, got {type(loaded).__name__}."
        )
    return loaded


def _check_name(report: SkillReport, frontmatter: dict, skill_dir: Path) -> None:
    if "name" not in frontmatter:
        _add(report, "error", "Missing required frontmatter field 'name'.")
        return
    name = frontmatter["name"]
    if not isinstance(name, str):
        _add(report, "error", f"'name' must be a string, got {type(name).__name__}.")
        return
    if name != name.strip():
        _add(report, "error", "'name' must not have leading or trailing whitespace.")
    if not name or len(name) > MAX_NAME_LEN:
        _add(
            report,
            "error",
            f"'name' must be 1-{MAX_NAME_LEN} characters, got {len(name)}.",
        )
    if not NAME_RE.fullmatch(name):
        _add(
            report,
            "error",
            "'name' may contain only lowercase letters, digits, and hyphens (a-z, 0-9, -).",
        )
    if name.startswith("-") or name.endswith("-") or "--" in name:
        _add(
            report,
            "error",
            "'name' must not start or end with a hyphen or contain '--'.",
        )
    for reserved in RESERVED_NAME_WORDS:
        if reserved in name:
            _add(
                report,
                "error",
                f"'name' must not contain the reserved word '{reserved}'.",
            )
    if "<" in name or ">" in name:
        _add(report, "error", "'name' must not contain angle brackets or XML tags.")
    if skill_dir.name != name:
        _add(
            report,
            "error",
            f"'name' must match the skill folder. Frontmatter has '{name}', folder is '{skill_dir.name}'.",
        )


def _check_description(
    report: SkillReport, frontmatter: dict, *, expect_hebrew: bool
) -> None:
    if "description" not in frontmatter:
        _add(report, "error", "Missing required frontmatter field 'description'.")
        return
    description = frontmatter["description"]
    if not isinstance(description, str):
        _add(
            report,
            "error",
            f"'description' must be a string, got {type(description).__name__}.",
        )
        return
    stripped = description.strip()
    if not stripped:
        _add(report, "error", "'description' must be non-empty.")
        return
    if len(description) > MAX_DESCRIPTION_LEN:
        _add(
            report,
            "error",
            f"'description' must be at most {MAX_DESCRIPTION_LEN} characters, got {len(description)}.",
        )
    if "<" in description or ">" in description:
        _add(
            report,
            "error",
            "'description' must not contain '<' or '>' (XML tags are rejected on upload).",
        )
    lowered = description.lower()
    if "use when" not in lowered:
        _add(
            report,
            "warning",
            "Description should include a 'Use when…' clause with the phrasings that should trigger the skill.",
        )
    if "do not use" not in lowered:
        _add(
            report,
            "warning",
            "Description should include a 'Do NOT use for…' boundary so this skill does not steal sibling triggers.",
        )
    if FIRST_PERSON_RE.search(description):
        _add(
            report,
            "warning",
            "Description should be third person (\"Extracts…\", not \"I can…\" or \"You can…\"). It is injected into the system prompt.",
        )
    if expect_hebrew and not HEBREW_RE.search(description):
        _add(
            report,
            "warning",
            "Description has no Hebrew characters. Add Hebrew trigger phrases the team actually types.",
        )


def _check_optional_fields(report: SkillReport, frontmatter: dict, skill_dir: Path) -> None:
    unexpected = sorted(set(frontmatter) - SPEC_FIELDS)
    if unexpected:
        claude_code_only = is_claude_code_only(skill_dir)
        allowed_extra = CLAUDE_CODE_ONLY_FIELDS if claude_code_only else frozenset()
        rejected = [key for key in unexpected if key not in allowed_extra]
        if rejected:
            allowed = ", ".join(sorted(SPEC_FIELDS))
            extra = ""
            if not claude_code_only and any(
                key in CLAUDE_CODE_ONLY_FIELDS for key in rejected
            ):
                extra = (
                    f" '{rejected[0]}' is Claude Code-only. Uploads accept only: {allowed}. "
                    f"Add a {MARKER_FILENAME} file in the skill folder if this skill will never be uploaded, "
                    "or remove the field."
                )
            else:
                extra = (
                    f" Allowed properties are: {allowed}."
                    + (
                        " Unknown fields are rejected even on Claude Code-only skills."
                        if claude_code_only
                        else ""
                    )
                )
            _add(
                report,
                "error",
                "Unexpected key(s) in SKILL.md frontmatter: "
                + ", ".join(rejected)
                + "."
                + extra,
            )

    if "compatibility" in frontmatter:
        compatibility = frontmatter["compatibility"]
        if not isinstance(compatibility, str) or not compatibility.strip():
            _add(report, "error", "'compatibility' must be a non-empty string.")
        elif len(compatibility) > MAX_COMPATIBILITY_LEN:
            _add(
                report,
                "error",
                f"'compatibility' must be at most {MAX_COMPATIBILITY_LEN} characters, got {len(compatibility)}.",
            )

    if "license" in frontmatter and (
        not isinstance(frontmatter["license"], str) or not frontmatter["license"].strip()
    ):
        _add(report, "error", "'license' must be a non-empty string.")

    if "allowed-tools" in frontmatter and not isinstance(
        frontmatter["allowed-tools"], str
    ):
        _add(
            report,
            "error",
            "'allowed-tools' must be a space-separated string, for example 'Bash(git:*) Read'.",
        )

    if "metadata" in frontmatter:
        metadata = frontmatter["metadata"]
        if not isinstance(metadata, dict):
            _add(
                report,
                "error",
                f"'metadata' must be a mapping of strings, got {type(metadata).__name__}.",
            )
        else:
            for key, value in metadata.items():
                if not isinstance(key, str):
                    _add(report, "error", "Every metadata key must be a string.")
                    continue
                if not isinstance(value, str):
                    _add(
                        report,
                        "error",
                        f"metadata.{key} must be a quoted string, got {type(value).__name__}. "
                        "Quote it in YAML (version: \"0.1.0\").",
                    )
            version = metadata.get("version")
            if "version" not in metadata:
                _add(
                    report,
                    "error",
                    "Missing metadata.version. Set it to a semver string such as \"0.1.0\" so API version pins stay traceable.",
                )
            elif isinstance(version, str) and not SEMVER_RE.fullmatch(version):
                _add(
                    report,
                    "error",
                    f"metadata.version '{version}' is not semver. Use MAJOR.MINOR.PATCH, for example \"0.1.0\".",
                )
    else:
        _add(
            report,
            "error",
            "Missing metadata.version. Add metadata.version as a quoted semver string so API version pins stay traceable.",
        )


def validate_skill(skill_dir: Path, *, expect_hebrew: bool = False) -> SkillReport:
    """Validate one skill directory. Warnings never fail `.ok` on their own."""
    skill_dir = skill_dir.resolve()
    report = SkillReport(path=skill_dir)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        _add(report, "error", f"Missing SKILL.md in {skill_dir}.")
        return report

    text = skill_md.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    try:
        yaml_text, _body = split_frontmatter(text)
        frontmatter = _parse_frontmatter(yaml_text)
    except SkillError as exc:
        _add(report, "error", str(exc))
        if line_count > MAX_SKILL_LINES:
            _add(
                report,
                "warning",
                f"SKILL.md has {line_count} lines. Keep it under {MAX_SKILL_LINES}; move detail into references/.",
            )
        return report

    _check_name(report, frontmatter, skill_dir)
    _check_description(report, frontmatter, expect_hebrew=expect_hebrew)
    _check_optional_fields(report, frontmatter, skill_dir)

    if line_count > MAX_SKILL_LINES:
        _add(
            report,
            "warning",
            f"SKILL.md has {line_count} lines. Keep it under {MAX_SKILL_LINES}; move detail into references/.",
        )
    return report


def expect_hebrew_for(skill_dir: Path, root: Path | None = None) -> bool:
    """Hebrew trigger phrases are required for skills shipped from skills/."""
    root = (root or repo_root()).resolve()
    try:
        skill_dir.resolve().relative_to(root / "skills")
    except ValueError:
        return False
    return True


def format_report(report: SkillReport) -> str:
    if report.ok and not report.warnings:
        status = "OK"
    elif report.ok:
        status = "WARN"
    else:
        status = "ERR"
    lines = [f"{status}  {report.path}"]
    for issue in report.issues:
        label = "error" if issue.level == "error" else "warning"
        lines.append(f"  - {label}: {issue.message}")
    return "\n".join(lines)


def should_exclude(relative: Path) -> bool:
    parts = relative.parts
    if not parts:
        return False
    if parts[0] in EXCLUDED_ROOT_DIRS:
        return True
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    if relative.name in EXCLUDED_FILE_NAMES:
        return True
    if relative.suffix in EXCLUDED_SUFFIXES:
        return True
    return False


def iter_package_files(skill_dir: Path) -> list[tuple[Path, Path]]:
    """Files to put in the zip, as (absolute path, path relative to the skill)."""
    skill_root = skill_dir.resolve()
    selected: list[tuple[Path, Path]] = []
    for path in sorted(skill_dir.rglob("*")):
        relative = path.relative_to(skill_dir)
        if should_exclude(relative):
            continue
        if path.is_symlink():
            resolved = path.resolve()
            if not resolved.is_file():
                continue
            if not _is_inside(resolved, skill_root):
                raise SkillError(
                    f"Refusing to package symlink that points outside the skill folder: {relative}"
                )
            selected.append((resolved, relative))
            continue
        if path.is_file():
            selected.append((path, relative))
    return selected


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def package_skill(skill_dir: Path, dist_dir: Path, *, allow_claude_code_only: bool = False) -> Path:
    """Validate `skill_dir` and write dist/<name>.zip. ZIP root is the skill folder."""
    skill_dir = skill_dir.resolve()
    report = validate_skill(
        skill_dir, expect_hebrew=expect_hebrew_for(skill_dir)
    )
    if not report.ok:
        rendered = format_report(report)
        raise SkillError(f"Refusing to package an invalid skill.\n{rendered}")
    if is_claude_code_only(skill_dir) and not allow_claude_code_only:
        raise SkillError(
            f"{skill_dir.name} is marked {MARKER_FILENAME}. "
            "claude.ai and the Skills API would reject its frontmatter. "
            "Pass --allow-claude-code-only to zip it anyway."
        )

    skill_md = skill_dir / "SKILL.md"
    # Name was validated; read it back for the archive folder.
    yaml_text, _body = split_frontmatter(skill_md.read_text(encoding="utf-8"))
    name = _parse_frontmatter(yaml_text)["name"]

    dist_dir.mkdir(parents=True, exist_ok=True)
    archive_path = dist_dir / f"{name}.zip"
    files = iter_package_files(skill_dir)

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, relative in files:
            arcname = Path(name, *relative.parts).as_posix()
            info = zipfile.ZipInfo(filename=arcname, date_time=ZIP_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Unix regular file, mode 0644. create_system 3 = Unix.
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800  # UTF-8 filenames
            data = source.read_bytes()
            archive.writestr(info, data)
    return archive_path
