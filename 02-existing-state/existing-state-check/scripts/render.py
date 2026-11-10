#!/usr/bin/env python3
"""
בדיקת מצב קיים — רינדור HTML ל-PDF בעברית (Chromium, פונט Heebo מוטמע).

מטמיע את פונט Heebo כ-base64 (אין תלות ברשת), מזריק את גיליון הסגנון,
מרנדר דרך Chromium ומוסיף כותרת תחתונה ומטא-דאטה.

    python3 render.py body.html out.pdf --footer "מצב קיים · גוש X חלקה Y · כתובת"

body.html צריך להכיל את שני הסמנים /*FONTFACE*/ ו-/*STYLE*/ בתוך תגית <style>.
"""
import argparse, base64, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

# טווחי יוניקוד לפי תת-הקבוצות של fontsource
RANGES = {
    "hebrew": "U+0590-05FF, U+200C-2010, U+20AA, U+25CC, U+FB1D-FB4F",
    "latin": ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+2000-206F, "
              "U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215"),
}


def font_css(fonts_dir: pathlib.Path) -> str:
    out = []
    for weight in (400, 500, 700):
        for subset, rng in RANGES.items():
            f = fonts_dir / f"heebo-{subset}-{weight}-normal.woff2"
            if not f.exists():
                sys.exit(f"missing font file: {f}")
            b64 = base64.b64encode(f.read_bytes()).decode()
            out.append(
                "@font-face{font-family:Heebo;font-style:normal;"
                f"font-weight:{weight};font-display:block;"
                f"src:url(data:font/woff2;base64,{b64}) format(\"woff2\");"
                f"unicode-range:{rng};}}"
            )
    return "\n".join(out)


def build(body_path, out_pdf, footer_text, title, subject):
    html = pathlib.Path(body_path).read_text(encoding="utf-8")
    if "/*FONTFACE*/" not in html or "/*STYLE*/" not in html:
        sys.exit("body html must contain /*FONTFACE*/ and /*STYLE*/ markers")
    html = html.replace("/*FONTFACE*/", font_css(ASSETS / "fonts"))
    html = html.replace("/*STYLE*/", (ASSETS / "report.css").read_text(encoding="utf-8"))

    tmp = pathlib.Path(out_pdf).with_suffix(".build.html")
    tmp.write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright
    foot = f"""
    <div style="width:100%;font-family:sans-serif;font-size:7pt;color:#3D5163;
     padding:0 15mm;display:flex;justify-content:space-between;direction:rtl;">
     <span>{footer_text}</span>
     <span>עמוד <span class="pageNumber"></span> מתוך <span class="totalPages"></span></span>
    </div>"""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(tmp.resolve().as_uri(), wait_until="networkidle")
        pg.wait_for_timeout(1200)          # לאפשר לפונט המוטמע להיטען
        pg.pdf(path=str(out_pdf), format="A4", print_background=True,
               display_header_footer=True,
               header_template="<div></div>", footer_template=foot,
               margin={"top": "14mm", "bottom": "16mm", "left": "15mm", "right": "15mm"})
        b.close()
    tmp.unlink(missing_ok=True)

    if title:
        from pypdf import PdfReader, PdfWriter
        r = PdfReader(out_pdf); w = PdfWriter()
        for page in r.pages:
            w.add_page(page)
        w.add_metadata({"/Title": title, "/Subject": subject,
                        "/Author": "Snapland", "/Creator": "Snapland – בדיקת מצב קיים"})
        w.write(out_pdf)

    print(f"wrote {out_pdf}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("body")
    ap.add_argument("out")
    ap.add_argument("--footer", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--subject",
                    default="בדיקת מצב קיים · מקור נתונים: Snapland")
    a = ap.parse_args()
    build(a.body, a.out, a.footer, a.title, a.subject)
