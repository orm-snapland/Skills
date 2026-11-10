#!/usr/bin/env python3
"""Cheap code checks before the expensive steps. Exit 0 = passed, 1 = failed, 2 = could not run.
    python3 scripts/gate.py pre-model  data.json [--stage 1|3] [--rules /path/israel-massing-rules/SKILL.md]
    python3 scripts/gate.py pre-render body.html [--stage 1|3]
--stage 1 (default): Go/No-Go — no massing; pre-render fails on any alternative content.
--stage 3: alternatives — pre-model checks massing.max_len against israel-massing-rules; pre-render needs the
           alternatives table and an updated decision compared with stage 1.
    python3 scripts/gate.py --self-test
data.json — the data registry (schema in stages/1-go-no-go/structure.md):
  {"archetype": "...", "headline_metric": "...", "uses": ["מגורים"], "deal_types": ["קומבינציה"],
   "massing": {"max_len": 21},          # stage 3 only
   "planning": {"מתאר": {...}, "תוכנית אב": {...}, "מדיניות": {...}, "תב\"עות 500 מ'": {...}},
   "values": [{"key": "lot_area", "value": 3647, "unit": "מ\"ר", "source": "מערכת", "certainty": 2, "ref": "lan-..."}]}"""
import json, re, sys, pathlib, os

SOURCES = {'מערכת', 'מסמך', 'חישוב', 'כלל אצבע', 'החלטה', 'הנחה', 'חסר', 'קלט משתמש', 'סותר', 'ידע כללי', 'החלטת הסקיל'}
ARCH = {'מתחם משותף': 'שווי שיורי × חלק יחסי', 'זכויות מומשו': 'בנצ\'מרק מחיר ולו"ז', 'מגרש ריק': 'שווי שיורי',
        'התחדשות': 'קומבינציה', 'בוטיק': 'שווי שיורי'}
STAGE1 = ['lot_area', 'land_use', 'ownership', 'existing_buildings', 'rights', 'plans_in_process', 'plans_500m',
          'ring_50m', 'regulatory', 'transactions', 'permits_nearby', 'environment']
PLANNING = ['מתאר', 'תוכנית אב', 'מדיניות', 'תב"עות 500 מ\'']
SALE_ONLY = {'תעסוקה', 'מלאכה ולוגיסטיקה'}
HEB = re.compile(r'[\u0590-\u05FF]')


def rules_max_len(path):
    try:
        t = pathlib.Path(path).read_text(encoding='utf-8')
    except Exception:
        return None
    for pat in (r'(\d{2})\s*מ[\'׳]?\s*(?:אורך|לאורך)', r'אורך[^\n]{0,60}?(\d{2})\s*מ', r'\d{2}\s*[×x]\s*(\d{2})'):
        m = re.search(pat, t)
        if m: return int(m.group(1))
    return None


def pre_model(data, rules=None, stage=1):
    err, warn = [], []
    vals = {v.get('key'): v for v in data.get('values', [])}
    for k in STAGE1:
        if k not in vals: err.append(f'נתון שלב 1 חסר במרשם: {k} (רשום ערך, או source="חסר")')
    a = data.get('archetype'); h = data.get('headline_metric')
    if a not in ARCH: err.append(f'ארכיטיפ לא נקבע או לא מוכר: {a}')
    elif h != ARCH[a] and not data.get('archetype_borderline'):
        err.append(f'מדד הכותרת "{h}" לא תואם לארכיטיפ "{a}" (צפוי: {ARCH[a]})')
    for v in data.get('values', []):
        s = v.get('source')
        if s not in SOURCES: err.append(f'{v.get("key")}: תג מקור לא חוקי "{s}"')
        if 'ראה הערה' in str(v.get('raw', '')) + str(v.get('value', '')) and s == 'מערכת':
            err.append(f'{v.get("key")}: ערך "ראה הערה" מתויג "מערכת" — צריך "חישוב"')
        if s == 'סותר' and not ('alt' in v and v.get('alt_source')):
            err.append(f'{v.get("key")}: נתון "סותר" בלי הערך השני ומקורו (alt, alt_source)')
    pl = data.get('planning', {})
    for k in PLANNING:
        if k not in pl or not pl[k].get('status'):
            err.append(f'בדיקה תכנונית: המקור "{k}" לא נבדק (status: נמצא / לא חל / חסר)')
    for u in data.get('uses', []):
        if u in SALE_ONLY and 'קומבינציה' in data.get('deal_types', []):
            err.append(f'שימוש "{u}": אין קומבינציה, רק מכר')
    for u, p in (data.get('prices') or {}).items():
        if p.get('source') not in ('מערכת', 'חישוב', 'קלט משתמש', 'מסמך'):
            err.append(f'מחיר לשימוש "{u}" בלי מקור תקין — אם אין עסקאות, שואלים את המשתמש ומתייגים "קלט משתמש"')
    if stage != 3: return err, warn
    ml = (data.get('massing') or {}).get('max_len')
    rl = rules_max_len(rules) if rules else None
    if rules and rl is None: warn.append('לא הצלחתי לקרוא אורך מבנה מרבי מחוקי הבינוי — בדוק ידנית')
    elif rl is not None and ml != rl: err.append(f'max_len={ml} לא תואם לחוקי הבינוי ({rl})')
    return err, warn


def pre_render(html, stage=1):
    err, warn = [], []
    if '{{' in html: err.append('נשארו placeholders: ' + ', '.join(sorted(set(re.findall(r'\{\{[^}]*\}\}', html)))[:5]))
    for cell in re.findall(r'<td class="num[^"]*">(.*?)</td>', html, re.S):
        if HEB.search(re.sub(r'<[^>]+>', '', cell)): err.append(f'עברית בתוך td.num: {re.sub(r"<[^>]+>", "", cell)[:40]}')
    body = re.sub(r'<style>.*?</style>|<svg.*?</svg>|<td class="num[^"]*">.*?</td>|<bdi[^>]*>.*?</bdi>', ' ', html, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', body)
    for m in re.finditer(r'\d[\d,\.]*\s?[–−×÷]\s?\(?\d', text):
        err.append(f'ביטוי מספרי לא עטוף ב-bdi: "{text[max(0, m.start() - 12):m.end() + 8].strip()}"')
        if len(err) > 25: break
    if '→' in text: err.append('חץ → בטקסט — לא שורד RTL; נסח מחדש')
    for t in re.findall(r'<table class="sens[^"]*">.*?</table>', html, re.S):
        hd = re.findall(r'<th(?: class="[^"]*")?>(.*?)</th>', t, re.S)
        if len(hd) >= 2 and '−10%' not in hd[1] and '-10%' not in hd[1]:
            err.append(f'גריד 3×3: העמודה הראשונה אחרי כותרת השורה צריכה להיות "עלות −10%" (נמצא: {re.sub("<[^>]+>", "", hd[1])[:20]})')
    for m in re.finditer(r'<(\w+)[^>]*class="(?:g|r|y)"', html):
        err.append(f'מחלקה .{m.group(0)[-2]} בשימוש מחוץ לרמזור (<{m.group(1)}>)')
    m10 = re.search(r'<span class="snum">10</span>(.*?)(<span class="snum">11</span>|$)', html, re.S)
    if m10 and 't-con' in m10.group(1): err.append('תג "סותר" בסעיף 10 — סתירות מוצגות בשורת הנתון ובנספח א\', לא בסיכונים')
    dec = re.search(r'<div class="alert"><b>החלטה:\s*([^<]*)</b>(.*?)</div>', html, re.S)
    if not dec: err.append('אין שורת הכרעה (<div class="alert"><b>החלטה: …</b>) בסעיף 09')
    else:
        d, rest = dec.group(1), dec.group(2)
        if not re.search(r'GO|NO-GO|גבולי', d): err.append('ההכרעה אינה GO / גבולי / NO-GO')
        if ('NO-GO' in d or 'גבולי' in d) and not re.search(r'מתהפך|הופך|מותנה|רק אם|GO אם', rest + d):
            err.append('NO-GO / גבולי בלי "מה הופך את ההחלטה" — חובה, בכמות')
        if d.strip().startswith('GO') and 'סיכ' not in rest: warn.append('GO בלי סיכונים בשורת ההחלטה — ודא שסעיף 10 מפרט אותם')
    if stage == 3:
        if 'חלופה' not in text: err.append('דוח החלופות בלי טבלת חלופות')
        if 'שלב 1' not in text: err.append('דוח החלופות לא משווה להכרעה של שלב 1')
        return err, warn
    m06 = re.search(r'<span class="snum">06</span>(.*?)(<span class="snum">07</span>|$)', html, re.S)
    if m06:
        t06 = re.sub(r'<[^>]+>', ' ', m06.group(1))
        if 'מלאי' not in t06: err.append('סעיף 06: חסרה שורת מלאי (יח"ד בהיתרים לפי שלב)')
        if 'עסקאות' not in t06: err.append('סעיף 06: חסרות עסקאות בהיתרים הסמוכים (לפני / אחרי ההיתר)')
    m08 = re.search(r'<span class="snum">08</span>(.*?)(<span class="snum">09</span>|$)', html, re.S)
    if m08 and re.search(r'סעיף\s*\d', re.sub(r'<[^>]+>', ' ', m08.group(1))):
        err.append('סעיף 08: עמודת ההשפעה מפנה לסעיף אחר — כותבים את ההשפעה עצמה במילה או שתיים ומספר')
    if re.search(r'חלופה בסיסית|סטודיו הנפחים|יח"ד בחלופה', text):
        err.append('חלופת בינוי בדוח שלב 1 — החלופות שייכות לדוח ההמשך (stages/3-alternatives)')
    for k in ('מתאר', 'תוכנית אב', 'מדיניות'):
        if k not in text: err.append(f'סעיף 04: המקור "{k}" לא מוזכר (גם כשחסר — כותבים "חסר")')
    return err, warn


def self_test():
    bad_data = {'archetype': 'התחדשות', 'headline_metric': 'שווי שיורי', 'uses': ['תעסוקה'], 'deal_types': ['קומבינציה'],
                'massing': {'max_len': 28}, 'planning': {'מתאר': {'status': 'נמצא'}},
                'values': [{'key': 'rights', 'value': 'ראה הערה', 'source': 'מערכת'}, {'key': 'x', 'value': 1, 'source': 'בערך'},
                           {'key': 'floors', 'value': 4, 'source': 'סותר'}]}
    tmp = pathlib.Path('/tmp/_rules.md'); tmp.write_text('טביעת רגל עד 15×21 מ\'', encoding='utf-8')
    e, _ = pre_model(bad_data, str(tmp), stage=3)
    need = ['ארכיטיפ', 'מדד הכותרת', 'תג מקור', 'ראה הערה', 'סותר', 'תוכנית אב', 'אין קומבינציה', 'max_len', 'lot_area']
    miss = [n for n in need if not any(n in x for x in e)]
    bad_html = ('<style>.x{}</style><span class="snum">04</span>מתאר<td class="num">12 מ"ר</td><p>טווח 15–20 קומות → כאן {{MAP}}</p>'
                '<table class="sens"><tr><th class="rh">x</th><th>עלות +10%</th></tr></table><div class="g">x</div>'
                '<span class="snum">10</span><span class="tag t-con">סותר</span><span class="snum">11</span>'
                '<div class="alert"><b>החלטה: NO-GO.</b> לא נסגר.</div><div class="sub">חלופה בסיסית</div>')
    e2, _ = pre_render(bad_html)
    need2 = ['חלופת בינוי', 'placeholders', 'td.num', 'bdi', 'חץ', 'גריד', 'מחלקה', 'סעיף 10', 'מה הופך', 'תוכנית אב']
    miss2 = [n for n in need2 if not any(n in x for x in e2)]
    ok_html = ('<span class="snum">04</span>מתאר · תוכנית אב (חסר) · מדיניות<p>טווח <bdi dir="ltr">15–20</bdi></p>'
               '<table class="sens"><tr><th class="rh">x</th><th>עלות −10%</th></tr></table><span class="light g"></span>'
               '<div class="alert"><b>החלטה: גבולי.</b> GO אם המחיר עולה ב-5%.</div>')
    e3, _ = pre_render(ok_html)
    e8, _ = pre_render('<span class="snum">06</span><td>היתר</td><span class="snum">07</span><span class="snum">08</span><td>סעיף 09</td><span class="snum">09</span>')
    miss8 = [] if any('סעיף 08' in x for x in e8) else ['section 08 reference']
    if not any('שורת מלאי' in x for x in e8): miss8.append('section 06 supply')
    e4, _ = pre_render('<div class="alert"><b>החלטה: GO.</b> סיכון.</div>', stage=3)
    miss4 = [n for n in ('טבלת חלופות', 'שלב 1') if not any(n in x for x in e4)]
    e5, _ = pre_model({k: v for k, v in bad_data.items() if k != 'massing'} | {'massing': {'max_len': 28}}, str(tmp), stage=1)
    miss5 = ['stage 1 ignores max_len'] if any('max_len' in x for x in e5) else []
    print('pre-model misses:', miss or 'none'); print('pre-render misses:', miss2 or 'none'); print('clean html errors:', e3 or 'none')
    print('stage 3 misses:', (miss4 + miss5) or 'none'); print('section 08 misses:', miss8 or 'none')
    return 0 if not (miss or miss2 or e3 or miss4 or miss5 or miss8) else 1


def main(a):
    try:
        if a[:1] == ['--self-test']: return self_test()
        stage = int(a[a.index('--stage') + 1]) if '--stage' in a else 1
        if a[0] == 'pre-model':
            rules = a[a.index('--rules') + 1] if '--rules' in a else os.environ.get('MASSING_RULES', '/mnt/skills/plugins/israel-massing-rules/SKILL.md')
            e, w = pre_model(json.load(open(a[1], encoding='utf-8')), rules, stage)
        elif a[0] == 'pre-render':
            e, w = pre_render(pathlib.Path(a[1]).read_text(encoding='utf-8'), stage)
        else:
            print(__doc__); return 2
    except Exception as ex:
        print(f'gate could not run: {ex}'); return 2
    for x in w: print('WARN', x)
    for x in e: print('FAIL', x)
    print('PASS' if not e else f'{len(e)} failures')
    return 0 if not e else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
