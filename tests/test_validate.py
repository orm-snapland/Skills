"""Validator coverage for the Agent Skills rules this repo enforces."""

from __future__ import annotations

import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

import skillslib  # noqa: E402
import validate_skills  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "valid-skill"
TEMPLATE = ROOT / "templates" / "your-skill-name"


def _write_skill(directory: Path, frontmatter: str, body: str = "\n# Body\n") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    text = f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n{body}"
    (directory / "SKILL.md").write_text(text, encoding="utf-8")
    return directory


def _errors(report: skillslib.SkillReport) -> list[str]:
    return [issue.message for issue in report.errors]


class ValidateSkillTests(unittest.TestCase):
    def test_fixture_and_template_are_clean(self) -> None:
        for path in (FIXTURE, TEMPLATE):
            report = skillslib.validate_skill(path, expect_hebrew=False)
            self.assertTrue(report.ok, skillslib.format_report(report))
            self.assertEqual(report.warnings, [])

    def test_template_copies_match(self) -> None:
        canonical = (ROOT / "templates" / "SKILL.template.md").read_text(encoding="utf-8")
        packaged = (TEMPLATE / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(canonical, packaged)

    def test_hebrew_trigger_required_inside_an_area(self) -> None:
        report = skillslib.validate_skill(FIXTURE, expect_hebrew=True)
        self.assertTrue(report.ok, skillslib.format_report(report))
        self.assertEqual(report.warnings, [])

    def test_expect_hebrew_only_inside_an_area(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            typed = root / "01-feasibility-report" / "valid-skill"
            shared = root / "shared" / "valid-skill"
            outside = root / "templates" / "valid-skill"
            for path in (typed, shared, outside):
                path.mkdir(parents=True)
            self.assertTrue(skillslib.expect_hebrew_for(typed, root))
            self.assertTrue(skillslib.expect_hebrew_for(shared, root))
            self.assertFalse(skillslib.expect_hebrew_for(outside, root))
            self.assertFalse(skillslib.expect_hebrew_for(TEMPLATE, ROOT))

    def test_areas_are_the_numbered_folders_and_shared(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name in ("01-feasibility-report", "shared", "docs", "tooling"):
                (root / name).mkdir()
            _write_skill(
                root / "01-feasibility-report" / "a-skill",
                """
                name: a-skill
                description: Checks a parcel. השתמש בסקיל הזה כשמבקשים בדיקה. Do NOT use for pricing.
                """,
            )
            (root / "docs" / "not-a-skill").mkdir()
            self.assertEqual(
                [area.name for area in skillslib.skill_areas(root)],
                ["01-feasibility-report", "shared"],
            )
            self.assertEqual(
                [skill.name for skill in skillslib.iter_repo_skills(root)],
                ["a-skill"],
            )
            self.assertEqual(
                [skill.name for skill in skillslib.find_skill("a-skill", root)],
                ["a-skill"],
            )

    def test_hebrew_use_when_clause_is_accepted(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            skill = _write_skill(
                Path(raw) / "hebrew-clauses",
                """
                name: hebrew-clauses
                description: מודד דירות מתוך היתר בנייה ומחזיר פוליגונים. השתמש בסקיל הזה כשמבקשים מדידת היתר או שטחי שירות. אל תפעיל אותו על תשריט שאינו היתר.
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(skill, expect_hebrew=True)
            self.assertTrue(report.ok, skillslib.format_report(report))
            self.assertEqual(report.warnings, [])

    def test_missing_hebrew_warns_when_requested(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            skill = _write_skill(
                Path(raw) / "no-hebrew",
                """
                name: no-hebrew
                description: Summarizes fixture notes. Use when the user asks for a summary of the fixture. Do NOT use for pricing.
                metadata:
                  author: snapland
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(skill, expect_hebrew=True)
            self.assertTrue(report.ok)
            self.assertTrue(any("Hebrew" in issue.message for issue in report.warnings))

    def test_name_rules(self) -> None:
        import tempfile

        cases = {
            "bad name": (
                "has-space",
                "name: has space",
                "lowercase",
            ),
            "starts-hyphen": (
                "-leading",
                "name: -leading",
                "hyphen",
            ),
            "double-hyphen": (
                "bad--name",
                "name: bad--name",
                "'--'",
            ),
            "reserved-claude": (
                "using-claude-api",
                "name: using-claude-api",
                "claude",
            ),
            "reserved-anthropic": (
                "anthropic-helper",
                "name: anthropic-helper",
                "anthropic",
            ),
            "too-long": (
                "n" * 65,
                "name: " + ("n" * 65),
                "64",
            ),
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for folder, (dirname, name_line, needle) in cases.items():
                with self.subTest(folder):
                    skill = _write_skill(
                        root / dirname,
                        f"""
                        {name_line}
                        description: Does a thing. Use when testing. Do NOT use for production.
                        metadata:
                          version: "0.1.0"
                        """,
                    )
                    report = skillslib.validate_skill(skill)
                    self.assertFalse(report.ok)
                    self.assertTrue(
                        any(needle in message for message in _errors(report)),
                        _errors(report),
                    )

    def test_name_must_match_folder(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            skill = _write_skill(
                Path(raw) / "folder-name",
                """
                name: other-name
                description: Does a thing. Use when testing. Do NOT use for production.
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(skill)
            self.assertFalse(report.ok)
            self.assertTrue(any("must match" in message for message in _errors(report)))

    def test_name_at_length_limit_passes(self) -> None:
        import tempfile

        name = "a" * 64
        with tempfile.TemporaryDirectory() as raw:
            skill = _write_skill(
                Path(raw) / name,
                f"""
                name: {name}
                description: Does a thing. Use when testing. Do NOT use for production.
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(skill)
            self.assertTrue(report.ok, skillslib.format_report(report))

    def test_rejects_non_spec_fields_unless_marked(self) -> None:
        import tempfile

        frontmatter = """
        name: marked-skill
        description: Does a thing. Use when testing. Do NOT use for production.
        disable-model-invocation: true
        metadata:
          version: "0.1.0"
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plain = _write_skill(root / "marked-skill", frontmatter)
            # Folder name must match; the second skill needs its own folder.
            report = skillslib.validate_skill(plain)
            self.assertFalse(report.ok)
            self.assertTrue(any("disable-model-invocation" in message for message in _errors(report)))

            marked = _write_skill(root / "marked-skill-cc", frontmatter.replace("marked-skill", "marked-skill-cc"))
            (marked / "CLAUDE-CODE-ONLY").write_text(
                "Not uploaded to claude.ai or the API.\n", encoding="utf-8"
            )
            report = skillslib.validate_skill(marked)
            self.assertTrue(report.ok, skillslib.format_report(report))

            bogus = _write_skill(
                root / "marked-skill-bad",
                """
                name: marked-skill-bad
                description: Does a thing. Use when testing. Do NOT use for production.
                dependencies: python
                metadata:
                  version: "0.1.0"
                """,
            )
            (bogus / "CLAUDE-CODE-ONLY").write_text("marker\n", encoding="utf-8")
            report = skillslib.validate_skill(bogus)
            self.assertFalse(report.ok)
            self.assertTrue(any("dependencies" in message for message in _errors(report)))

    def test_description_limits(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            angled = _write_skill(
                root / "angled",
                """
                name: angled
                description: Parses <files>. Use when testing. Do NOT use for production.
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(angled)
            self.assertFalse(report.ok)
            self.assertTrue(any("angle" in message or "'<'" in message for message in _errors(report)))

            long_desc = "Does a thing. Use when testing. Do NOT use for production. " + ("x" * 1000)
            long_skill = _write_skill(
                root / "too-long",
                f"""
                name: too-long
                description: {long_desc}
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(long_skill)
            self.assertFalse(report.ok)
            self.assertTrue(any("1024" in message for message in _errors(report)))

    def test_description_style_warnings(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            skill = _write_skill(
                Path(raw) / "first-person",
                """
                name: first-person
                description: I can help with files.
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(skill)
            self.assertTrue(report.ok)
            messages = " ".join(issue.message for issue in report.warnings)
            self.assertIn("Use when", messages)
            self.assertIn("Do NOT use", messages)
            self.assertIn("third person", messages)

    def test_version_must_be_quoted_semver(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            missing = _write_skill(
                root / "no-version",
                """
                name: no-version
                description: Does a thing. Use when testing. Do NOT use for production.
                """,
            )
            report = skillslib.validate_skill(missing)
            self.assertFalse(report.ok)
            self.assertTrue(any("metadata.version" in message for message in _errors(report)))

            floated = _write_skill(
                root / "float-version",
                """
                name: float-version
                description: Does a thing. Use when testing. Do NOT use for production.
                metadata:
                  version: 1.0
                """,
            )
            report = skillslib.validate_skill(floated)
            self.assertFalse(report.ok)
            self.assertTrue(any("quoted string" in message for message in _errors(report)))

            loose = _write_skill(
                root / "loose-version",
                """
                name: loose-version
                description: Does a thing. Use when testing. Do NOT use for production.
                metadata:
                  version: "1.0"
                """,
            )
            report = skillslib.validate_skill(loose)
            self.assertFalse(report.ok)
            self.assertTrue(any("semver" in message for message in _errors(report)))

    def test_compatibility_limit_and_metadata_shape(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            long_compat = _write_skill(
                root / "long-compat",
                f"""
                name: long-compat
                description: Does a thing. Use when testing. Do NOT use for production.
                compatibility: {"y" * 501}
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(long_compat)
            self.assertFalse(report.ok)
            self.assertTrue(any("compatibility" in message for message in _errors(report)))

            bad_meta = _write_skill(
                root / "bad-meta",
                """
                name: bad-meta
                description: Does a thing. Use when testing. Do NOT use for production.
                metadata:
                  - not-a-map
                """,
            )
            report = skillslib.validate_skill(bad_meta)
            self.assertFalse(report.ok)
            self.assertTrue(any("mapping" in message for message in _errors(report)))

            bad_tools = _write_skill(
                root / "bad-tools",
                """
                name: bad-tools
                description: Does a thing. Use when testing. Do NOT use for production.
                allowed-tools:
                  - Bash
                metadata:
                  version: "0.1.0"
                """,
            )
            report = skillslib.validate_skill(bad_tools)
            self.assertFalse(report.ok)
            self.assertTrue(any("allowed-tools" in message for message in _errors(report)))

    def test_frontmatter_must_parse_and_start_the_file(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            missing = root / "missing-fm"
            missing.mkdir()
            (missing / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
            report = skillslib.validate_skill(missing)
            self.assertFalse(report.ok)
            self.assertTrue(any("line 1" in message for message in _errors(report)))

            padded = root / "padded"
            padded.mkdir()
            (padded / "SKILL.md").write_text("\n---\nname: padded\n---\n", encoding="utf-8")
            report = skillslib.validate_skill(padded)
            self.assertFalse(report.ok)

            broken = _write_skill(
                root / "broken-yaml",
                """
                name: [unterminated
                description: Does a thing.
                """,
            )
            report = skillslib.validate_skill(broken)
            self.assertFalse(report.ok)
            self.assertTrue(any("parsed" in message for message in _errors(report)))

    def test_line_count_is_a_warning_unless_strict(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            body = "\n".join(f"line {index}" for index in range(520))
            skill = _write_skill(
                Path(raw) / "long-skill",
                """
                name: long-skill
                description: Does a thing. Use when testing. Do NOT use for production.
                metadata:
                  version: "0.1.0"
                """,
                body="\n" + body + "\n",
            )
            report = skillslib.validate_skill(skill)
            self.assertTrue(report.ok, skillslib.format_report(report))
            self.assertTrue(any("500" in issue.message for issue in report.warnings))

            code = validate_skills.main(["--strict", str(skill)])
            self.assertEqual(code, 1)
            code = validate_skills.main([str(skill)])
            self.assertEqual(code, 0)

    def test_cli_on_repo_template(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tooling" / "validate_skills.py")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("OK", completed.stdout)
        self.assertIn("your-skill-name", completed.stdout)

    def test_empty_area_message(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            area = root / "01-feasibility-report"
            area.mkdir()
            code = validate_skills.main(["--repo-root", str(root), str(area)])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
