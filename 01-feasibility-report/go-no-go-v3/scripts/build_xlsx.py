#!/usr/bin/env python3
"""Excel model (the "דוח אפס" attachment of stage 1) with live formulas, mirroring scripts/model.py exactly.
    python3 scripts/build_xlsx.py xlsx_input.json out.xlsx
    python3 /mnt/skills/public/xlsx/scripts/recalc.py out.xlsx 90        # then verify against model.py
Schema of xlsx_input.json: see references/economics.md §Excel. deal = "קומבינציה" (renewal) or "מכר" (residual).
Colors: blue = input · green = link · black = formula · yellow fill = key assumption."""
import json, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L

F = 'Arial'
BLUE = Font(name=F, color='0000FF'); BLK = Font(name=F); GRN = Font(name=F, color='008000')
B = Font(name=F, bold=True); H1 = Font(name=F, bold=True, size=14); WH = Font(name=F, bold=True, color='FFFFFF')
HDR = PatternFill('solid', fgColor='12263A'); KEY = PatternFill('solid', fgColor='FFFF00')
BOX = Border(bottom=Side(style='thin', color='D7DEE5'))
NIS = '#,##0;(#,##0);-'; NIS_M = '#,##0.0,,"M";(#,##0.0,,"M");-'; PCT = '0.0%;(0.0%);-'; SQM = '#,##0;(#,##0);-'; DEC = '0.00'
GREY = Font(name=F, italic=True, color='3D5163')


def build(I, out):
    wb = Workbook(); wb.remove(wb.active)
    def sheet(name, title, widths):
        ws = wb.create_sheet(name); ws.sheet_view.rightToLeft = True
        ws['A1'] = title; ws['A1'].font = H1
        for i, w in enumerate(widths, 1): ws.column_dimensions[L(i)].width = w
        return ws
    def hdr(ws, row, vals):
        for i, v in enumerate(vals, 1):
            c = ws.cell(row, i, v); c.font = WH; c.fill = HDR; c.alignment = Alignment(horizontal='right', vertical='center', wrap_text=True)
    renewal = I.get('deal', 'קומבינציה') == 'קומבינציה'
    ex = I.get('existing'); env = I.get('envelope'); tx = I.get('transactions')

    # ---- הנחות
    A = sheet('הנחות', 'הנחות ותשומות — עריכה בתאים הכחולים בלבד', [36, 16, 12, 16, 60])
    A['A2'] = 'כחול = קלט לעריכה · ירוק = קישור · שחור = נוסחה · צהוב = הנחה מרכזית.'; A['A2'].font = GREY
    hdr(A, 4, ['פרמטר', 'ערך', 'יחידה', 'מקור', 'הערה'])
    N = {}
    links = {'@units': "='יחידות קיימות'!C9", '@net': "=ROUND('יחידות קיימות'!C12,0)", '@price': '=ROUND(עסקאות!J4,-2)'}
    for i, a in enumerate(I['assumptions']):
        r = 5 + i; N[a['key']] = f'הנחות!$B${r}'
        v = links.get(a['value'], a['value']) if isinstance(a['value'], str) else a['value']
        A.cell(r, 1, a['label']); c = A.cell(r, 2, v); A.cell(r, 3, a.get('unit', '')); A.cell(r, 4, a.get('source', '')); A.cell(r, 5, a.get('note', ''))
        c.font = GRN if isinstance(v, str) and v.startswith('=') else BLUE
        if a.get('unit') == '%': c.number_format = PCT
        elif isinstance(v, (int, float)) and abs(v) >= 1000: c.number_format = NIS
        if a.get('key_flag'): c.fill = KEY
        for j in range(1, 6): A.cell(r, j).border = BOX
    A.freeze_panes = 'A5'

    # ---- יחידות קיימות
    if ex:
        U = sheet('יחידות קיימות', 'יחידות קיימות וגודלן — כלל אצבע', [34] + [16] * len(ex['buildings']) + [40])
        nb = len(ex['buildings']); lastc = L(1 + nb); notec = 2 + nb
        hdr(U, 3, ['נתון'] + [b['name'] for b in ex['buildings']] + ['מקור / הערה'])
        rows = [('טביעת רגל (מ"ר)', 'footprint', 'מערכת — פוליגון המבנה'), ('קומות מעל הקרקע', 'floors', 'מערכת'),
                ('מתוכן קומת עמודים', 'pillar', 'מערכת'), (None, None, None), ('כניסות', 'entrances', 'הנחה — לאמת')]
        for k, (lab, key, src) in enumerate(rows):
            r = 4 + k
            if lab is None:
                U.cell(r, 1, 'קומות מגורים')
                for j in range(nb): U.cell(r, 2 + j, f'={L(2 + j)}5-{L(2 + j)}6')
                U.cell(r, notec, 'חישוב'); continue
            U.cell(r, 1, lab); U.cell(r, notec, src)
            for j, b in enumerate(ex['buildings']): c = U.cell(r, 2 + j, b.get(key, 0)); c.font = BLUE
        sp = '+'.join(f'{L(2 + j)}4*{L(2 + j)}7' for j in range(nb)); ss = '+'.join(f'{L(2 + j)}7*{L(2 + j)}8' for j in range(nb))
        U['A9'] = 'יח"ד קיימות (סה"כ)'; U['C9'] = ex['units']; U['C9'].font = BLUE; U['C9'].fill = KEY; U.cell(9, notec, ex.get('units_source', 'הנחה'))
        U['A10'] = 'ברוטו מגורים (מ"ר)'; U['C10'] = f'={sp}'
        U['A11'] = 'חדר מדרגות (מ"ר)'; U['C11'] = f'=15*({ss})'; U.cell(11, notec, 'כלל אצבע — 15 מ"ר לקומה לכניסה')
        U['A12'] = 'גודל דירה ממוצע נטו (מ"ר)'; U['C12'] = '=(C10-C11)/C9'; U['C12'].font = B
        U['A13'] = 'חציון שטח בעסקאות על החלקה (טאבו)'; U['C13'] = ex.get('tabu_median') or 0; U['C13'].font = BLUE
        U['A14'] = 'טווח צפוי לפי טאבו +15–20%'; U['C14'] = '=IF(C13=0,"—",TEXT(C13*1.15,"0")&"–"&TEXT(C13*1.2,"0"))'
        U['A15'] = 'בדיקת סבירות'; U['C15'] = '=IF(C13=0,"אין נתון",IF(C12<C13*1.15,"נמוך מהטווח — לבדוק מספר יח""ד",IF(C12>C13*1.2,"גבוה מהטווח","מתיישב")))'
        U['A16'] = 'שטח קיים כולל נטו (מ"ר)'; U['C16'] = '=C10-C11'
        for r in range(9, 17):
            if r not in (14, 15): U.cell(r, 3).number_format = '#,##0.0' if r == 12 else SQM

    # ---- מעטפת
    E = sheet('מעטפת', 'מעטפת וזכויות — קיים מול מותר', [42, 16, 12, 44])
    hdr(E, 3, ['רכיב', 'ערך', 'יחידה', 'מקור'])
    rows = [('שטח מגרש', f'={N["lot"]}', 'מ"ר', 'מערכת'), ('רח"ק', f'={N["far"]}', '', I.get('far_source', 'מערכת')),
            ('ברוטו מעל הקרקע לפי זכויות', '=B4*B5', 'מ"ר', 'חישוב'), ('סחיר (פלדלת)', f'=B6*(1-{N["svc"]})', 'מ"ר', 'חישוב')]
    if env:
        rows += [('חלופה בסיסית — טביעת רגל כוללת', env['footprint'], 'מ"ר', env.get('footprint_note', 'חישוב — כללי הסטודיו')),
                 (env.get('cap_label', 'תקרת קומות'), env['floor_cap'], 'קומות', 'מערכת'),
                 ('קומות בחלופה', '=MIN(B9,INT(B6/B8))', 'קומות', 'חישוב — עיגול כלפי מטה'), ('ברוטו בחלופה', '=B10*B8', 'מ"ר', 'חישוב'),
                 ('ניצול הזכויות', '=B11/B6', '%', 'חישוב'),
                 (env.get('cap_alt_label', 'תקרת קומות חלופית'), env.get('floor_cap_alt', env['floor_cap']), 'קומות', 'מערכת'),
                 ('ברוטו בתקרה החלופית', '=MIN(B13,INT(B6/B8))*B8', 'מ"ר', 'חישוב'), ('ניצול בתקרה החלופית', '=B14/B6', '%', 'חישוב'),
                 ('יח"ד בחלופה', f'=B10*{env.get("units_per_floor", 0)}', 'יח"ד', 'חישוב'),
                 ('קיים — בנוי מעל הקרקע', env.get('existing_gross', 0), 'מ"ר', 'מערכת'), ('מקדם קיים', '=B17/B4', '', 'חישוב'),
                 (env.get('approved_label', 'מאושר'), env.get('approved_gross', 0), 'מ"ר', 'מערכת'),
                 ('קומות לאיזון בטביעת הרגל של החלופה', None, 'קומות', 'חישוב'), ('טביעת רגל לקומה לאיזון בתקרה', None, 'מ"ר', 'חישוב')]
    for i, (lab, v, u, s) in enumerate(rows):
        r = 4 + i; E.cell(r, 1, lab); E.cell(r, 3, u); E.cell(r, 4, s)
        if v is None: continue
        c = E.cell(r, 2, v); c.font = GRN if isinstance(v, str) and 'הנחות' in v else (BLK if isinstance(v, str) else BLUE)
        c.number_format = PCT if u == '%' else (DEC if u == '' else SQM)

    # ---- מודל
    cols = [('בסיס', 1, 1, 0, 0, 'exprop'), ('הפקעה חלופית', 1, 1, 0, 0, 'exprop_alt'), ('מחיר +1,000', 1, 1, 1000, 0, 'exprop'),
            ('רח"ק +0.1', 1, 1, 0, 0.1, 'exprop')]
    for pm, pl in ((1.1, '+10%'), (1.0, 'בסיס'), (0.9, '−10%')):
        for cm, cl in ((0.9, '−10%'), (1.0, 'בסיס'), (1.1, '+10%')):
            cols.append((f'מ{pl} ע{cl}', pm, cm, 0, 0, 'exprop'))
    if I.get('compare'): cols.append((I['compare']['label'], 1, 1, 0, f'={I["compare"]["far"]}-{N["far"]}', 'exprop'))
    if env: cols.append(('בינוי בתקרת הקומות', 1, 1, 0, f'=מעטפת!$B$11/מעטפת!$B$4-{N["far"]}', 'exprop'))
    M = sheet('מודל', 'מודל ' + ('קומבינציה — התחדשות (renewal)' if renewal else 'מכר — שווי שיורי (residual)') + ', עמודה לכל תרחיש',
              [34] + [13] * len(cols))
    hdr(M, 3, ['שורה'] + [c[0] for c in cols])
    if renewal:
        lab = {10: 'מחיר ₪/מ"ר', 11: 'עלות מעל הקרקע ₪/מ"ר', 12: 'רח"ק', 13: 'מגרש לזכויות', 14: 'ברוטו', 15: 'סחיר (פלדלת)', 16: 'לבעלים',
               17: 'ליזם', 18: 'יח"ד סה"כ', 19: 'מרתף', 20: 'עלויות ישירות', 21: 'הכנסות (כולל מע"מ)', 22: 'הכנסות נטו', 23: 'עלויות רכות',
               24: 'פינוי', 25: 'סך עלויות', 26: 'רווח יזמי נדרש', 27: 'עודף / גירעון', 28: 'רווח על עלות', 29: 'אחוז קומבינציה'}
    else:
        lab = {10: 'מחיר ₪/מ"ר', 11: 'עלות מעל הקרקע ₪/מ"ר', 12: 'רח"ק', 13: 'מגרש לזכויות', 14: 'ברוטו', 15: 'סחיר', 16: '—', 17: '—',
               18: 'יח"ד', 19: 'מרתף', 20: 'עלויות ישירות', 21: 'הכנסות (כולל מע"מ)', 22: 'הכנסות נטו', 23: 'עלויות רכות', 24: '—',
               25: 'סך עלויות', 26: 'רווח יזמי נדרש', 27: 'שווי קרקע שיורי', 28: 'שווי שיורי למ"ר מגרש', 29: 'שיורי מההכנסות'}
    for r, t in {4: 'מכפיל מחיר', 5: 'מכפיל עלות', 6: 'תוספת מחיר ₪', 7: 'הפקעה', 8: 'תוספת רח"ק', **lab}.items():
        M.cell(r, 1, t).font = B if r in (27, 29) else BLK
    for j, (name, pm, cm, padd, fadd, exk) in enumerate(cols):
        c = L(j + 2)
        M[f'{c}4'] = pm; M[f'{c}5'] = cm; M[f'{c}6'] = padd; M[f'{c}8'] = fadd
        for rr in (4, 5, 6, 8): M[f'{c}{rr}'].font = BLK if isinstance(M[f'{c}{rr}'].value, str) else BLUE
        M[f'{c}8'].number_format = DEC
        M[f'{c}7'] = f'={N[exk]}'; M[f'{c}7'].font = GRN; M[f'{c}7'].number_format = PCT
        f = {10: f'={N["price"]}*{c}4+{c}6', 11: f'={N["cost"]}*{c}5', 12: f'={N["far"]}+{c}8', 13: f'={N["lot"]}*(1-{c}7)',
             14: f'={c}13*{c}12', 15: f'={c}14*(1-{N["svc"]})'}
        if renewal:
            f.update({16: f'={N["units"]}*({N["net"]}+{N["add"]})', 17: f'={c}15-{c}16', 18: f'={N["units"]}+MAX({c}17,0)/{N["new_unit"]}',
                      19: f'={c}18*{N["parking"]}',
                      20: f'={c}14*{c}11+{c}18*{N["balcony"]}*{c}11*{N["bal_f"]}+{c}19*{N["cost_base"]}+{N["demo"]}*{N["demo_c"]}+{N["lot"]}*{N["dev_c"]}',
                      21: f'={c}17*{c}10', 24: f'={N["units"]}*({N["rent"]}*{N["months"]}+{N["extra"]})',
                      25: f'=({c}20+{c}23+{c}24)*(1+{N["fin"]}+{N["cont"]})', 28: f'=IF({c}25=0,0,({c}22-{c}25)/{c}25)',
                      29: f'=IF({c}15=0,0,{c}16/{c}15)'})
        else:
            f.update({18: f'={c}15/{N["new_unit"]}', 19: f'={c}18*{N["parking"]}',
                      20: f'={c}14*{c}11+{c}19*{N["cost_base"]}+{N["lot"]}*{N["dev_c"]}', 21: f'={c}15*{c}10',
                      25: f'=({c}20+{c}23)*(1+{N["fin"]}+{N["cont"]})', 28: f'={c}27/{N["lot"]}', 29: f'=IF({c}21=0,0,{c}27/{c}21)'})
        f.update({22: f'={c}21/(1+{N["vat"]})', 23: f'={c}20*({N["cons"]}+{N["mgmt"]})+({c}14+{c}19)*{N["fees"]}+{c}22*{N["mkt"]}',
                  26: f'={c}25*{N["profit"]}', 27: f'={c}22-{c}25-{c}26-{N["levy"]}'})
        for r, fx in f.items():
            x = M[f'{c}{r}']; x.value = fx; x.font = B if r in (27, 29) else BLK
            x.number_format = PCT if r in (28, 29) and (renewal or r == 29) else (DEC if r == 12 else (NIS_M if r >= 20 and r != 28 else
                              NIS if r in (10, 11, 28) else '#,##0.0' if r == 18 else SQM))
    lastcol = {name: L(j + 2) for j, (name, *_) in enumerate(cols)}
    M['A31'] = 'נקודות איזון (המודל לינארי — נגזרות מעמודות "מחיר +1,000" ו"רח"ק +0.1")'; M['A31'].font = B
    M['A32'] = 'מחיר איזון ₪/מ"ר'; M['B32'] = '=B10-B27*(D10-B10)/(D27-B27)'
    M['A33'] = 'רח"ק איזון'; M['B33'] = '=B12-B27*(E12-B12)/(E27-B27)'
    M['A34'] = 'סחיר באיזון (מ"ר)'; M['B34'] = f'=B13*B33*(1-{N["svc"]})'
    M['A35'] = 'קומבינציה באיזון' if renewal else '—'; M['B35'] = '=B16/B34' if renewal else ''
    M['A36'] = 'רח"ק איזון — תרחיש הפקעה'; M['B36'] = f'=B34/(1-{N["svc"]})/C13'
    for r, fm in ((32, NIS), (33, DEC), (34, SQM), (35, PCT), (36, DEC)): M[f'B{r}'].number_format = fm; M[f'B{r}'].font = B
    M.freeze_panes = 'B4'
    if env:
        E['B20'] = f'=מודל!B34/(1-{N["svc"]})/B8'; E['B20'].number_format = '0.0'
        E['B21'] = f'=מודל!B34/(1-{N["svc"]})/B9'; E['B21'].number_format = SQM

    # ---- רגישויות
    R = sheet('רגישויות', 'רגישויות — ' + ('עודף/גירעון' if renewal else 'שווי קרקע שיורי') + ' (₪) · תרחיש בסיס', [22, 18, 18, 18])
    hdr(R, 3, ['', 'עלות בנייה −10%', 'עלות בסיס', 'עלות בנייה +10%'])
    for i, lb in enumerate(['מחיר מכירה +10%', 'מחיר בסיס', 'מחיר מכירה −10%']):
        R.cell(4 + i, 1, lb).font = B
        for j in range(3):
            c = R.cell(4 + i, 2 + j, f'=מודל!{L(6 + 3 * i + j)}27'); c.font = GRN; c.number_format = NIS_M
    R['A8'] = 'תרחישים חיוביים מתוך 9'; R['B8'] = '=COUNTIF(B4:D6,">0")'; R['B8'].font = B
    if not renewal:
        R['A10'] = 'טווח מומלץ לקרקע (מחיר −10% עד בסיס)'; R['B10'] = '=MAX(0,C6)'; R['C10'] = '=MAX(0,C5)'
        for c in ('B10', 'C10'): R[c].number_format = NIS_M; R[c].font = B

    # ---- עסקאות
    if tx:
        T = sheet('עסקאות', I.get('tx_title', 'עסקאות — אחרי ניקוי'), [14, 13, 14, 10, 13, 4, 26, 14, 14, 14])
        hdr(T, 3, ['חלקה', 'תאריך', 'סכום ₪', 'מ"ר', '₪/מ"ר', '', 'סיכום', 'בנייה חדשה', 'יד שנייה', 'התאמה לגודל'])
        r = 4; T.cell(r, 1, tx.get('new_label', 'בנייה חדשה')).font = B; r += 1; n0 = r
        for x in tx['new']:
            for k, v in enumerate((x['parcel'], x['date'], x['amount'], x['area']), 1): T.cell(r, k, v).font = BLUE
            T.cell(r, 3).number_format = NIS; T.cell(r, 5, f'=C{r}/D{r}').number_format = NIS; r += 1
        n1 = r - 1; r += 1; T.cell(r, 1, 'יד שנייה').font = B; r += 1; s0 = r
        for x in tx['second']:
            for k, v in enumerate((x['parcel'], x['date'], x['amount'], x['area']), 1): T.cell(r, k, v).font = BLUE
            T.cell(r, 3).number_format = NIS; T.cell(r, 5, f'=C{r}/D{r}').number_format = NIS; r += 1
        s1 = r - 1
        for i, (lb, a, b) in enumerate([('n', f'=COUNT(E{n0}:E{n1})', f'=COUNT(E{s0}:E{s1})'), ('חציון ₪/מ"ר', f'=MEDIAN(E{n0}:E{n1})', f'=MEDIAN(E{s0}:E{s1})'),
                                         ('מינימום', f'=MIN(E{n0}:E{n1})', f'=MIN(E{s0}:E{s1})'), ('מקסימום', f'=MAX(E{n0}:E{n1})', f'=MAX(E{s0}:E{s1})'),
                                         ('CV', f'=STDEVP(E{n0}:E{n1})/AVERAGE(E{n0}:E{n1})', f'=STDEVP(E{s0}:E{s1})/AVERAGE(E{s0}:E{s1})'),
                                         ('פרמיה (חדש ÷ יד שנייה − 1)', '=H5/I5-1', '')]):
            T.cell(4 + i, 7, lb).font = B; x = T.cell(4 + i, 8, a); y = T.cell(4 + i, 9, b)
            for c in (x, y): c.number_format = PCT if lb.startswith(('CV', 'פרמיה')) else NIS
        T['J3'] = f'התאמה ל-{tx.get("target_sqm", 80)} מ"ר'
        T['J4'] = f'=INTERCEPT(E{n0}:E{n1},D{n0}:D{n1})+SLOPE(E{n0}:E{n1},D{n0}:D{n1})*{tx.get("target_sqm", 80)}'; T['J4'].number_format = NIS; T['J4'].font = B
        T['J5'] = f'=SLOPE(E{n0}:E{n1},D{n0}:D{n1})'; T['J5'].number_format = '#,##0.0'
        for i, t in enumerate(tx.get('notes', [])): T.cell(11 + i, 7, t)

    # ---- תקציר
    S = wb.create_sheet('תקציר', 0); S.sheet_view.rightToLeft = True
    for i, w in enumerate([42, 18, 16, 18, 46], 1): S.column_dimensions[L(i)].width = w
    S['A1'] = I['title']; S['A1'].font = H1; S['A2'] = I.get('subtitle', ''); S['A2'].font = GREY
    bcol = lastcol.get('בינוי בתקרת הקומות')
    hdr(S, 4, ['מדד', 'זכויות מלאות', 'הפקעה חלופית', 'בינוי בתקרת הקומות' if bcol else '', 'הערה'])
    g = lambda r: (f'=מודל!B{r}', f'=מודל!C{r}', f'=מודל!{bcol}{r}' if bcol else '')
    if renewal:
        summ = [('סחיר (פלדלת) מ"ר', *g(15), SQM, ''), ('לבעלים מ"ר', *g(16), SQM, 'יח"ד × (נטו קיים + תמורה)'),
                ('אחוז קומבינציה', *g(29), PCT, '~50% עובד במרכז ת"א; 60%+ → NO-GO'), ('הכנסות נטו', *g(22), NIS_M, ''),
                ('סך עלויות', *g(25), NIS_M, 'כולל פינוי'), ('רווח על עלות', *g(28), PCT, 'יעד 20%'),
                ('עודף / גירעון אחרי רווח', *g(27), NIS_M, '')]
    else:
        summ = [('סחיר מ"ר', *g(15), SQM, ''), ('הכנסות נטו', *g(22), NIS_M, ''), ('סך עלויות', *g(25), NIS_M, 'בלי קרקע'),
                ('רווח יזמי נדרש', *g(26), NIS_M, ''), ('שווי קרקע שיורי', *g(27), NIS_M, 'מה שאפשר לשלם על הקרקע'),
                ('שיורי מההכנסות', *g(29), PCT, 'מעל 40% — לבדוק סבירות'), ('טווח מומלץ לקרקע (מ−10% עד בסיס)', '=רגישויות!B10', '=רגישויות!C10', '', NIS_M, '')]
    summ += [('מחיר איזון ₪/מ"ר', '=מודל!B32', '', '', NIS, ''), ('רח"ק איזון', '=מודל!B33', '=מודל!B36', '', DEC, ''),
             ('תרחישים חיוביים ברשת 3×3', '=רגישויות!B8', '', '', '0', '')]
    if I.get('compare'): summ.append((f'השוואה: {I["compare"]["label"]}', f'=מודל!{lastcol[I["compare"]["label"]]}27', '', '', NIS_M, 'אותן הנחות'))
    if renewal: summ.append(('הפקעה מרבית שמשאירה עודף ≥ 0', '=MAX(0,1-מודל!B33/מודל!B12)', '', '', PCT, ''))
    if env: summ += [('קומות לאיזון בטביעת הרגל של החלופה', '=מעטפת!B20', '', '', '0.0', ''), ('טביעת רגל לקומה לאיזון בתקרה', '=מעטפת!B21', '', '', SQM, '')]
    for i, (lb, a, b, d, fm, nt) in enumerate(summ):
        r = 5 + i; S.cell(r, 1, lb); S.cell(r, 5, nt)
        for col, v in ((2, a), (3, b), (4, d)):
            if v: c = S.cell(r, col, v); c.font = GRN; c.number_format = fm
    dr = 6 + len(summ)
    S.cell(dr, 1, 'החלטה').font = B
    if renewal:
        bs = f'D{5 + 6}' if bcol else '0'; bt = f'D{5 + 4}' if bcol else '1'
        S.cell(dr, 2, f'=IF(OR(B7>=0.6,B11<-0.1*B9),"NO-GO",IF(AND(B11>0.05*B9,{bs}>=0),"GO",IF({bs}<-0.1*{bt},"גבולי — נוטה ל-NO-GO","גבולי")))')
        S.cell(dr + 2, 1, 'הכלל: קומבינציה 60%+ או גירעון מעל 10% מהעלויות → NO-GO; עודף מעל 5% (וחיובי גם בבינוי) → GO; ביניהם → גבולי.')
    else:
        S.cell(dr, 2, '=IF(B9<=0,"NO-GO",IF(רגישויות!B10>0,"GO","גבולי"))')
        S.cell(dr + 2, 1, 'הכלל: שווי שיורי ≤ 0 → NO-GO; חיובי גם במחיר −10% → GO; אחרת גבולי. מול מחיר מבוקש — השווה לטווח המומלץ.')
    S.cell(dr, 2).font = Font(name=F, bold=True, size=13, color='9E3B32'); S.cell(dr + 2, 1).font = GREY

    # ---- מקורות
    Q = sheet('מקורות', 'מקורות', [30, 30, 50]); hdr(Q, 3, ['נושא', 'מקור', 'מזהה / תאריך'])
    for i, row in enumerate(I.get('sources', [])):
        for j, v in enumerate(row): Q.cell(4 + i, 1 + j, v)
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                f = c.font
                if f is None or f.name != F: c.font = Font(name=F, bold=f.bold, italic=f.italic, size=f.size, color=f.color)
                c.alignment = Alignment(horizontal='right', vertical='center', wrap_text=bool(c.alignment and c.alignment.wrap_text))
    wb.save(out)


if __name__ == '__main__':
    build(json.load(open(sys.argv[1], encoding='utf-8')), sys.argv[2]); print('saved', sys.argv[2])
