#!/usr/bin/env python3
"""Light tests. python3 tests/run_tests.py [--xlsx] [--massing]
stage 1 = xlsx without envelope (no alternative); stage 3 = xlsx with the alternative column + massing packing.
golden: Sanhedrin 7 (validated against the client's Excel) and Bruria 15 economics; decide(); gate self-test.
--massing: Bruria 15 multi-building packing (slow, ~1–2 min). --xlsx: build + LibreOffice recalc + compare to model.py."""
import json, sys, os, subprocess, pathlib
H = pathlib.Path(__file__).resolve().parent; S = H.parent / 'scripts'; sys.path.insert(0, str(S))
sys.path.insert(0, str(H.parent / 'stages/3-alternatives/scripts'))
from model import renewal, breakeven, grid, decide, residual, land_value_range, combination_breakeven, allowed_deals
ok = True
def check(name, cond, info=''):
    global ok; ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + name + (f'  [{info}]' if info else ''))
close = lambda a, b, tol: abs(a - b) <= tol

s = json.load(open(H / 'fixtures/sanhedrin7.json')); i = s['inputs']; e = s['expected']
fn = lambda **kw: renewal(**{**i, **kw})
r = fn()
check('sanhedrin total', close(r['total'], e['total'], 0.05e6), round(r['total']))
check('sanhedrin margin', close(r['margin'], e['margin'], 0.0005), round(r['margin'], 4))
check('sanhedrin surplus', close(r['surplus'], e['surplus'], 0.05e6), round(r['surplus']))
check('sanhedrin breakeven', close(breakeven(fn), e['be_price'], 100))
g = [[round(v / 1e6, 1) for v in row] for row in grid(fn, i['price'], i['cost_ag'])]
check('sanhedrin grid 3x3', g == e['grid'], g)
rm = fn(sellable=s['mix_sellable']); check('sanhedrin client-mix column', close(rm['surplus'], e['mix']['surplus'], 0.05e6) and close(rm['margin'], e['mix']['margin'], 0.001))
check('sanhedrin decision', decide(r['surplus'], r['total'], r['comb']) == e['decision'], decide(r['surplus'], r['total'], r['comb']))

P = dict(owners_units=56, exist_net=93, price=49200, cost_ag=9000, svc=0.22, rent=8000, months=44, cost_base=4100, new_unit=80, demolish_sqm=6192, lot=3647)
a = renewal(sellable=3647 * 6 * 0.78, **P); b = renewal(sellable=17640 * 0.78, **P); c4 = renewal(sellable=3647 * 4 * 0.78, **P)
check('bruria FAR6 surplus', close(a['surplus'], 4.72e6, 0.05e6), round(a['surplus']))
check('bruria buildable 20 floors', close(b['surplus'], -54.19e6, 0.05e6), round(b['surplus']))
check('bruria decision', decide(a['surplus'], a['total'], a['comb'], b['surplus'], b['total']) == 'גבולי — נוטה ל-NO-GO')
check('bruria FAR4 decision', decide(c4['surplus'], c4['total'], c4['comb']) == 'NO-GO')

check('deal types: employment sale only', allowed_deals('תעסוקה')[0] == ['מכר'])
check('deal types: logistics sale only', allowed_deals('מלאכה ולוגיסטיקה')[0] == ['מכר'] and allowed_deals('מלאכה ולוגיסטיקה')[1] is None)
check('deal types: residential both', allowed_deals('מגורים')[0] == ['מכר', 'קומבינציה'])
rr = lambda price, **kw: residual(sellable=4000, price=price, cost_ag=8500, lot=1000, **kw)
lv = land_value_range(rr, 45000); check('sale: land value range ordered', lv['low'] <= lv['base'] <= lv['high'], {k: round(v) for k, v in lv.items() if k != 'recommended'})
cb = combination_breakeven(4000, 45000, 8500, lot=1000)
check('empty-lot combination: owner share zeroes surplus', abs(residual(4000, 45000, 8500, lot=1000, owner_share=cb)['surplus']) < 5e4, round(cb, 3))
check('gate self-test', subprocess.run([sys.executable, str(S / 'gate.py'), '--self-test'], capture_output=True).returncode == 0)

if '--massing' in sys.argv:
    from massing_multi import run
    m = run(json.load(open(H / 'fixtures/bruria15_massing_cfg.json')))
    check('bruria massing footprint ≥ 860', m['footprint_total'] >= 860, m['footprint_total'])
    check('bruria massing floors capped at 20', m['floors'] == 20)
    check('bruria massing blocking = floor cap', 'תקרת קומות' in m['blocking'], m['blocking'])
    check('bruria massing spacing ≥ 12', (m['min_gap'] or 99) >= 12, m['min_gap'])

from permit_supply import projects, attach_sales, attach_height, summary
from datetime import date as _date
_fx = json.load(open(H / 'fixtures/iba1_permits.json'))
_pr = attach_height(attach_sales(projects(_fx['permits']), _fx['transactions'], _date(2026, 10, 22)), _fx['buildings'])
_by = {p['permits'][0]: p for p in _pr}; _s = summary(_pr)
check('supply: demolition + new of one project counted once', '20231124' in _by['20231125']['permits'] and _s['projects'] == 10)
check('supply: units by stage', _s['units_total'] == 208 and _s['units_by_stage'].get('בבדיקה') == 92, _s['units_by_stage'])
check('supply: plot deal not an apartment', _by['20210763']['land_deals'] == 1 and _by['20210763']['deals_since_issue'] == 3)
check('supply: deals before permit, duplicates merged, no sold share from them', _by['20240700']['deals_before_issue'] == 3 and _by['20240700']['sold_share'] == 0, _by['20240700']['deals_before_issue'])
check('supply: floors from built building', _by['20210763']['floors'] == 7 and _by['20210763']['floors_source'] == 'בנוי')
check('supply: licensing months', round(_by['20240700']['licensing_months']) == 31)

if '--xlsx' in sys.argv:
    from build_xlsx import build
    from openpyxl import load_workbook
    def recalc(path):
        rc = subprocess.run([sys.executable, '/mnt/skills/public/xlsx/scripts/recalc.py', path, '90'], capture_output=True, text=True)
        return json.loads(rc.stdout[rc.stdout.index('{'):]) if '{' in rc.stdout else {}
    for stg in ('stage1', 'stage3'):
        out = f'/tmp/_bruria_{stg}.xlsx'; fx = json.load(open(H / f'fixtures/bruria15_xlsx_{stg}.json')); build(fx, out)
        res = recalc(out); check(f'{stg} xlsx recalc: 0 errors', res.get('total_errors') == 0, res.get('error_summary'))
        wb = load_workbook(out, data_only=True); S_ = wb['תקציר']; ex_ = fx['expected']
        check(f'{stg} xlsx surplus = model', close(S_['B11'].value, ex_['surplus'], 2000), round(S_['B11'].value))
        if stg == 'stage3':
            check('stage3 xlsx buildable surplus = model', close(S_['D11'].value, ex_['surplus_buildable'], 2000), round(S_['D11'].value))
        else:
            check('stage1 xlsx has no alternative rows', not any('חלופה' in str(c.value or '') for row in wb['מעטפת'].iter_rows() for c in row))
        check(f'{stg} xlsx comb', close(S_['B7'].value, ex_['comb'], 0.0005))
        dec = [S_.cell(r, 2).value for r in range(5, 30) if S_.cell(r, 1).value == 'החלטה'][0]
        check(f'{stg} xlsx decision', dec == ex_['decision'], dec)
    sale = dict(fx, deal='מכר', existing=None, envelope=None, compare=None)
    sale['assumptions'] = [dict(a, value=93) if a['key'] == 'net' else dict(a, value=56) if a['key'] == 'units' else a for a in fx['assumptions']]
    out2 = '/tmp/_sale_test.xlsx'; build(sale, out2); res2 = recalc(out2)
    check('xlsx sale recalc: 0 errors', res2.get('total_errors') == 0, res2.get('error_summary'))
    w2 = load_workbook(out2, data_only=True); price = w2['הנחות']['B13'].value
    ref = residual(3647 * 6 * 0.78, price, 9000, svc=0.22, profit=0.20, fin=0.075, cont=0.07, lot=3647, new_unit=80, cost_base=4100)
    check('xlsx sale residual = model.residual', close(w2['תקציר']['B9'].value, ref['surplus'], 2000), (round(w2['תקציר']['B9'].value), round(ref['surplus'])))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
