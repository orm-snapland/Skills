#!/usr/bin/env python3
"""Section 06 — housing supply in the area from permits, licensing time vs. sales, approved floors/height.

    python3 scripts/permit_supply.py permits.json transactions.json [buildings.json] [--radius 250] [--asof 2026-10-22] > supply.json

permits.json       rows (or {"items":[...]}) of nearby-construction-permits, fields:
                   permit_number,application_number,status,permit_type,work_type,application_date,issue_date,start_date,
                   completion_date,distance_m,authorized_units,authorized_floors,authorized_area_sqm,land_parcel_snap_ids
transactions.json  rows of transactions-in-area with land_parcel_snap_id (required for matching), deal_date, deal_amount,
                   asset_area_sqm. Rows without land_parcel_snap_id are ignored for sales.
buildings.json     optional rows: land_parcel_snap_id, floors_above_ground, height_m, year_built — used only when the permit
                   has no authorized_floors and the building was built after the permit (source "בנוי", not "מאושר").

Rules (why): demolition + new-construction permits of one project appear as two rows with the same units and issue date —
counted once. Sales are deduplicated by (parcel, area, amount ±0.2%, date ±7 days) — Snapland lists one deal as "דירה" and "אחר".
Sales count from the application date and are split between application and permit / after the permit. Deals between
application and permit can be presales OR apartments of the old building still standing — the data cannot tell them
apart, so the report says so (איתמר בן אב"י 2: 3 deals 05–08.2024, permit 12.2024). Sold share uses deals after the permit only. A "deal" above 400 m² is a plot or combination deed — counted
apart, never in the price. Sold share is apartment deals ÷ authorized units; in a combination part of the units go to the
owners and never sell — say so in the text.
"""
import json, sys
from datetime import date
from statistics import median

NEW = {'new_construction', 'בניה חדשה', 'בנייה חדשה'}
LAND_SQM = 400   # a 'deal' above this is a plot / building transfer, not an apartment
STAGE = {'under_review': 'בבדיקה', 'issued': 'היתר', 'active': 'בבנייה', 'completed': 'הושלם'}


def _d(s):
    return date.fromisoformat(s[:10]) if s else None


def _months(a, b):
    return None if not (a and b) else round((b.year - a.year) * 12 + (b.month - a.month) + (b.day - a.day) / 30, 1)


def _rows(x):
    return x.get('items', x) if isinstance(x, dict) else x


def _data(r):
    return r.get('data', r)


def projects(permits, radius=250):
    ps = [_data(p) for p in _rows(permits)]
    ps = [p for p in ps if (p.get('distance_m') or 0) <= radius and (p.get('authorized_units') or 0) > 0
          and (p.get('work_type') in NEW or p.get('work_type') == 'demolition')]
    ps.sort(key=lambda p: (p.get('work_type') not in NEW, p.get('distance_m') or 0))   # new construction first
    out = []
    for p in ps:
        parcels = set(p.get('land_parcel_snap_ids') or [])
        twin = next((q for q in out if (parcels & q['parcels']) or (
            q['units'] == p['authorized_units'] and (q['issue_date'] or q['application_date']) ==
            (p.get('issue_date') or p.get('application_date')))), None)
        if twin:
            twin['parcels'] |= parcels; twin['permits'].append(p.get('permit_number') or p.get('application_number'))
            continue
        out.append(dict(permits=[p.get('permit_number') or p.get('application_number')], parcels=parcels,
                        distance_m=round(p.get('distance_m') or 0), status=p.get('status'),
                        stage=STAGE.get(p.get('status'), p.get('status')), units=p['authorized_units'],
                        application_date=p.get('application_date'), issue_date=p.get('issue_date'),
                        start_date=p.get('start_date'), completion_date=p.get('completion_date'),
                        floors=p.get('authorized_floors'), floors_source='מאושר' if p.get('authorized_floors') else None,
                        height_m=None, permit_type=p.get('permit_type'), work_type=p.get('work_type')))
    return out


def attach_sales(projs, txs, asof):
    rows = []
    for t in sorted((_data(t) for t in _rows(txs)), key=lambda t: t.get('deal_date') or ''):
        if not t.get('land_parcel_snap_id') or not t.get('deal_date'): continue
        if any(r['land_parcel_snap_id'] == t['land_parcel_snap_id'] and r.get('asset_area_sqm') == t.get('asset_area_sqm')
               and abs((r.get('deal_amount') or 0) - (t.get('deal_amount') or 0)) <= 0.002 * (t.get('deal_amount') or 1)
               and abs((_d(r['deal_date']) - _d(t['deal_date'])).days) <= 7 for r in rows):
            continue                                                     # same deal reported twice, days apart, ±0.2%
        rows.append(t)
    for p in projs:
        iss, app = _d(p['issue_date']), _d(p['application_date'])
        p['licensing_months'] = _months(app, iss) if iss else None
        p['waiting_months'] = None if iss else _months(app, asof)
        mine = [t for t in rows if t['land_parcel_snap_id'] in p['parcels'] and app and _d(t['deal_date']) >= app]
        land = [t for t in mine if (t.get('asset_area_sqm') or 0) > LAND_SQM]          # whole-plot / combination deed
        units = [t for t in mine if t not in land and (t.get('asset_area_sqm') or 0) >= 15]
        before = [t for t in units if iss and _d(t['deal_date']) < iss] if iss else units
        p['land_deals'] = len(land)
        p['deals_before_issue'], p['deals_since_issue'] = len(before), len(units) - len(before)
        p['deals_total'] = len(units)
        p['months_since_issue'] = _months(iss, asof) if iss else None
        p['sold_share'] = round(p['deals_since_issue'] / p['units'], 2) if iss else None
        ppm = [t['deal_amount'] / t['asset_area_sqm'] for t in units]
        p['median_ppm'] = round(median(ppm)) if ppm else None
        p['first_deal'] = min((t['deal_date'][:10] for t in units), default=None)
        p['last_deal'] = max((t['deal_date'][:10] for t in units), default=None)
    return projs


def attach_height(projs, buildings):
    for p in projs:
        if p['floors'] or not buildings: continue
        iss = _d(p['issue_date'])
        cand = [_data(b) for b in _rows(buildings) if _data(b).get('land_parcel_snap_id') in p['parcels']
                and iss and (_data(b).get('year_built') or 0) >= iss.year]
        if cand:
            b = max(cand, key=lambda b: b.get('floors_above_ground') or 0)
            p['floors'], p['height_m'], p['floors_source'] = b.get('floors_above_ground'), b.get('height_m'), 'בנוי'
    return projs


def summary(projs):
    by = {}
    for p in projs: by[p['stage']] = by.get(p['stage'], 0) + p['units']
    lic = [p['licensing_months'] for p in projs if p['licensing_months']]
    return dict(projects=len(projs), units_total=sum(p['units'] for p in projs), units_by_stage=by,
                licensing_median_months=round(median(lic), 1) if lic else None,
                with_sales=sum(1 for p in projs if p['deals_total']),
                deals_total=sum(p['deals_total'] for p in projs),
                no_floors=sum(1 for p in projs if not p['floors']))


def main(a):
    radius = int(a[a.index('--radius') + 1]) if '--radius' in a else 250
    asof = _d(a[a.index('--asof') + 1]) if '--asof' in a else date.today()
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or not a[i - 1].startswith('--'))]
    permits, txs = json.load(open(pos[0])), json.load(open(pos[1]))
    bld = json.load(open(pos[2])) if len(pos) > 2 else None
    projs = attach_height(attach_sales(projects(permits, radius), txs, asof), bld)
    for p in projs: p['parcels'] = sorted(p['parcels'])
    projs.sort(key=lambda p: p['distance_m'])
    return dict(radius_m=radius, asof=str(asof), summary=summary(projs), projects=projs)


if __name__ == '__main__':
    print(json.dumps(main(sys.argv[1:]), ensure_ascii=False, indent=1))
