---
name: valid-skill
description: Echoes a short fixture payload so the Snapland skill validator and packager can be tested. Use when running the repository test suite or checking ZIP layout, including the phrases בדיקת ולידציה and חבילת בדיקה. Do NOT use for real-estate leads, listings, pricing, documents, or any production task.
license: Proprietary. LICENSE.txt has complete terms
metadata:
  author: snapland
  version: "0.1.0"
---

# Validator fixture

This folder is a test fixture. It is not a Snapland real-estate skill.

## Quick start

Run the bundled script. Do not read it for instructions; its output is the result.

```bash
python3 scripts/echo.py --message ok
```

## Gotchas

- Prices and property facts do not belong here. This skill only echoes `--message`.
