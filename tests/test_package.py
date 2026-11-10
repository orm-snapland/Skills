"""Packager coverage: claude.ai zip layout and exclusion rules."""

from __future__ import annotations

import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

import skillslib  # noqa: E402
import package_skill  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "valid-skill"
TEMPLATE = ROOT / "templates" / "your-skill-name"


class PackageTests(unittest.TestCase):
    def test_fixture_zip_layout_and_exclusions(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            # Junk that must not ship, created beside the fixture via a copy.
            skill = Path(raw) / "valid-skill"
            _copy_fixture(skill)
            (skill / ".DS_Store").write_bytes(b"junk")
            cache = skill / "__pycache__"
            cache.mkdir()
            (cache / "echo.pyc").write_bytes(b"pyc")
            modules = skill / "node_modules" / "leftpad"
            modules.mkdir(parents=True)
            (modules / "index.js").write_text("module.exports = 1\n", encoding="utf-8")
            nested_cache = skill / "scripts" / "__pycache__"
            nested_cache.mkdir()
            (nested_cache / "echo.pyc").write_bytes(b"pyc")

            archive = skillslib.package_skill(skill, dist)
            self.assertEqual(archive.name, "valid-skill.zip")
            with zipfile.ZipFile(archive) as zipped:
                names = set(zipped.namelist())
            self.assertIn("valid-skill/SKILL.md", names)
            self.assertIn("valid-skill/scripts/echo.py", names)
            self.assertIn("valid-skill/references/notes.md", names)
            self.assertIn("valid-skill/LICENSE.txt", names)
            self.assertFalse(any(name.startswith("valid-skill/evals/") for name in names))
            self.assertFalse(any(name.endswith(".pyc") for name in names))
            self.assertFalse(any(".DS_Store" in name for name in names))
            self.assertFalse(any("node_modules" in name for name in names))
            self.assertFalse(any("__pycache__" in name for name in names))
            self.assertFalse(any(name.endswith(".gitkeep") for name in names))
            self.assertTrue(all("/" in name and not name.endswith("/") for name in names))
            # ZIP root is the skill folder, not SKILL.md itself.
            self.assertNotIn("SKILL.md", names)

    def test_symlink_escape_is_refused(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            skill = Path(raw) / "valid-skill"
            _copy_fixture(skill)
            outside = Path(raw) / "secret.txt"
            outside.write_text("nope\n", encoding="utf-8")
            (skill / "scripts" / "secret.txt").symlink_to(outside)
            with self.assertRaises(skillslib.SkillError):
                skillslib.package_skill(skill, Path(raw) / "dist")

    def test_claude_code_only_refused_unless_allowed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            skill = Path(raw) / "valid-skill"
            _copy_fixture(skill)
            (skill / "CLAUDE-CODE-ONLY").write_text("local only\n", encoding="utf-8")
            # Marker alone does not add frontmatter fields, so validation still passes.
            with self.assertRaises(skillslib.SkillError):
                skillslib.package_skill(skill, Path(raw) / "dist")
            archive = skillslib.package_skill(
                skill, Path(raw) / "dist", allow_claude_code_only=True
            )
            with zipfile.ZipFile(archive) as zipped:
                self.assertNotIn("valid-skill/CLAUDE-CODE-ONLY", zipped.namelist())

    def test_invalid_skill_is_not_written(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            skill = Path(raw) / "broken"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# nope\n", encoding="utf-8")
            dist = Path(raw) / "dist"
            with self.assertRaises(skillslib.SkillError):
                skillslib.package_skill(skill, dist)
            self.assertFalse(dist.exists())

    def test_cli_packages_template_by_path(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw) / "dist"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "package_skill.py"),
                    "--path",
                    str(TEMPLATE),
                    "--dist",
                    str(dist),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            archive = dist / "your-skill-name.zip"
            self.assertTrue(archive.is_file())
            with zipfile.ZipFile(archive) as zipped:
                names = zipped.namelist()
            self.assertIn("your-skill-name/SKILL.md", names)
            self.assertFalse(any("evals" in name for name in names))

            empty = Path(raw) / "skills"
            empty.mkdir()
            code = package_skill.main(["all", "--skills-dir", str(empty), "--dist", str(dist)])
            self.assertEqual(code, 0)

    def test_cli_packages_fixture_by_directory_name(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw) / "dist"
            code = package_skill.main(
                [
                    "valid-skill",
                    "--skills-dir",
                    str(FIXTURE.parent),
                    "--dist",
                    str(dist),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((dist / "valid-skill.zip").is_file())


def _copy_fixture(destination: Path) -> None:
    import shutil

    shutil.copytree(FIXTURE, destination)


if __name__ == "__main__":
    unittest.main()
