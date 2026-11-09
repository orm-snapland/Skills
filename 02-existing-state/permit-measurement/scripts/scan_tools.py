#!/usr/bin/env python3
"""כלי עבודה על סריקת היתר.

  extract   <pdf> <outdir>                       → מחלץ את התמונה המקורית (pdfimages) ומפצל לאריחים לסקירה
  zoom      <png> <x1> <y1> <x2> <y2> <out> [s]  → חיתוך מוגדל + ניגודיות (קואורדינטות פיקסל)
  mask      <png> <x1> <y1> <x2> <y2> <out.npy>  → מסכת קירות אדום/כחול (צבעוני = קיר/עמוד בהיתרים ישנים)
  profile   <out.npy> [threshold]               → הטלות שורות/עמודות של המסכה → מיקומי קירות בפיקסלים
  grid      <png> <calib.json> <x1cm> <y1cm> <x2cm> <y2cm> <out> [s]
                                               → חיתוך בס"מ עם רשת ס"מ כל 50/100 – לקריאת מיקום קירות פנימיים

calib.json: {"x":[[cm,px],...], "y":[[cm,px],...]}  – נקודות עיגון (≥2 לכל ציר), מיפוי ליניארי למקוטעין.
"""
import sys, json, subprocess, pathlib
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw
Image.MAX_IMAGE_PIXELS = None


def interp(pts, v):
    pts = sorted(pts)
    if v <= pts[0][0]:
        (a, pa), (b, pb) = pts[0], pts[1]
    elif v >= pts[-1][0]:
        (a, pa), (b, pb) = pts[-2], pts[-1]
    else:
        for (a, pa), (b, pb) in zip(pts, pts[1:]):
            if a <= v <= b:
                break
    return pa + (pb - pa) * (v - a) / (b - a)


def cm2px(cal, x, y):
    return interp(cal["x"], x), interp(cal["y"], y)


def extract(pdf, outdir):
    out = pathlib.Path(outdir); out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdfimages", "-png", pdf, str(out / "scan")], check=True)
    imgs = sorted(out.glob("scan-*.png"))
    for p in imgs:
        im = Image.open(p); W, H = im.size
        n = max(1, round(W / max(H, 1)))           # גיליונות ארוכים מקופלים → אריח לכל "דף"
        w = W // n
        for i in range(n):
            im.crop((i * w, 0, (i + 1) * w, H)).save(out / f"{p.stem}-tile{i:02d}.png")
        print(p.name, im.size, f"{n} tiles")


def zoom(png, x1, y1, x2, y2, out, s=3):
    im = Image.open(png).convert("RGB").crop((x1, y1, x2, y2))
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    ImageEnhance.Contrast(im).enhance(1.8).save(out)


def mask(png, x1, y1, x2, y2, out):
    a = np.array(Image.open(png).convert("RGB").crop((x1, y1, x2, y2))).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = ((r - g > 50) & (r - b > 40)) | ((b - r > 30) & (b - g > 5))
    np.save(out, m)
    Image.fromarray((m * 255).astype(np.uint8)).save(str(out).replace(".npy", ".png"))
    ys, xs = np.where(m)
    print("extent px (in crop):", xs.min(), xs.max(), ys.min(), ys.max())


def bands(p, th):
    out, i = [], 0
    while i < len(p):
        if p[i] >= th:
            j = i
            while j < len(p) and p[j] >= th:
                j += 1
            out.append((i, j - 1, int(p[i:j].max()))); i = j
        else:
            i += 1
    return out


def profile(npy, th=25):
    m = np.load(npy)
    print("COLS (x_from,x_to,strength):", bands(m.sum(0), th))
    print("ROWS (y_from,y_to,strength):", bands(m.sum(1), th))


def grid(png, calib, x1, y1, x2, y2, out, s=4):
    cal = json.load(open(calib))
    im = Image.open(png).convert("RGB")
    (ax, ay), (bx, by) = cm2px(cal, x1, y2), cm2px(cal, x2, y1)
    box = (int(min(ax, bx)), int(min(ay, by)), int(max(ax, bx)), int(max(ay, by)))
    r = im.crop(box); r = r.resize((r.width * s, r.height * s), Image.LANCZOS)
    r = ImageEnhance.Contrast(r).enhance(1.8); d = ImageDraw.Draw(r)
    for xc in range(int(x1 // 50 * 50), int(x2) + 1, 50):
        px = (cm2px(cal, xc, y1)[0] - box[0]) * s
        d.line([(px, 0), (px, r.height)], fill=(0, 0, 255) if xc % 100 == 0 else (160, 160, 255)); d.text((px + 2, 2), str(xc), fill=(0, 0, 255))
    for yc in range(int(y1 // 50 * 50), int(y2) + 1, 50):
        py = (cm2px(cal, x1, yc)[1] - box[1]) * s
        d.line([(0, py), (r.width, py)], fill=(0, 140, 0) if yc % 100 == 0 else (160, 220, 160)); d.text((2, py + 2), str(yc), fill=(0, 120, 0))
    r.save(out)


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    if cmd == "extract": extract(*a)
    elif cmd == "zoom": zoom(a[0], *map(int, a[1:5]), a[5], *(map(float, a[6:7])))
    elif cmd == "mask": mask(a[0], *map(int, a[1:5]), a[5])
    elif cmd == "profile": profile(a[0], *(map(int, a[1:2])))
    elif cmd == "grid": grid(a[0], a[1], *map(float, a[2:6]), a[6], *(map(int, a[7:8])))
    else: sys.exit(__doc__)
