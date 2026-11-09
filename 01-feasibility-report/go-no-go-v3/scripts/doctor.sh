#!/bin/bash
# doctor.sh — go-no-go-v3: exit 0 ready, 1 missing required
need=0
python3 -c "import shapely" 2>/dev/null && echo "ok shapely" || { echo "MISSING shapely (envelope/massing/maps) → pip install shapely --break-system-packages"; need=1; }
python3 -c "import playwright, pypdf" 2>/dev/null && echo "ok playwright+pypdf" || { echo "MISSING playwright/pypdf (render)"; need=1; }
python3 -c "import openpyxl" 2>/dev/null && echo "ok openpyxl (xlsx)" || { echo "MISSING openpyxl (build_xlsx)"; need=1; }
command -v pdftoppm >/dev/null && echo "ok pdftoppm" || { echo "MISSING pdftoppm (visual check)"; need=1; }
command -v soffice >/dev/null || command -v libreoffice >/dev/null && echo "ok libreoffice (xlsx recalc)" || echo "optional libreoffice: absent → xlsx formulas not recalculated/verified"
[ -d /mnt/user-data/outputs ] && echo "out: ${GNG_OUT:-/mnt/user-data/outputs}" || echo "out: ${GNG_OUT:-./out}"
exit $need
