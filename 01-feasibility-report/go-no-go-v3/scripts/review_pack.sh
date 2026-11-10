#!/bin/bash
# review_pack.sh report.pdf data.json [outdir] — pack pages as images + data registry + rubric for a fresh reviewer.
set -e
pdf="$1"; data="$2"; out="${3:-${GNG_OUT:-./out}/review_pack}"
here="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$out/pages"
pdftoppm -r 80 -png "$pdf" "$out/pages/p"
cp "$data" "$out/data.json"
cp "$here/references/review.md" "$out/brief.md"
( cd "$out/.." && zip -qr "$(basename "$out").zip" "$(basename "$out")" )
echo "$out.zip"
