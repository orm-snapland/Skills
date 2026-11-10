#!/usr/bin/env python3
"""
Go/No-Go — economics. Stage-1 rules of thumb only; every default is an assumption to tag.

Renewal (פינוי־בינוי / התחדשות בניינית) — the metric is the owners' combination %:
    from model import renewal, breakeven, grid, tx_stats
    r = renewal(sellable=2306, owners_units=16, exist_net=59, price=67271, cost_ag=11100)
    r['comb'], r['margin'], r['surplus']

Empty lot / small lot / realised rights — use residual() (land value) instead; see references/economics.md.
tx_stats(rows) cleans transactions (partials, storage/parking, duplicates) and splits new-build clusters.
"""
import statistics as st
from collections import Counter

VAT = 1.18   # verify the rate in force


def renewal(sellable, owners_units, exist_net, price, cost_ag, *, add=25, svc=0.20, rent=7500, months=41,
            per_unit_extra=120_000, cost_base=4400, profit=0.20, fin=0.075, cont=0.07, new_unit=95,
            demolish_sqm=0, lot=0, fees=700, consultants=0.07, mgmt=0.03, marketing=0.03, balcony=12,
            parking_sqm=30):
    gross = sellable / (1 - svc)
    owners = owners_units * (exist_net + add)
    dev = sellable - owners
    units = owners_units + max(dev, 0) / new_unit
    base = units * parking_sqm
    hard = gross * cost_ag + units * balcony * cost_ag * 0.4 + base * cost_base + demolish_sqm * 300 + lot * 600
    rev = dev * price; revn = rev / VAT
    soft = hard * (consultants + mgmt) + (gross + base) * fees + revn * marketing
    evac = owners_units * (rent * months + per_unit_extra)
    total = (hard + soft + evac) * (1 + fin + cont)
    pr = total * profit
    return dict(gross=gross, owners=owners, dev=dev, units=units, comb=owners / sellable, rev=rev, revn=revn,
                total=total, evac=evac, profit=pr, surplus=revn - total - pr, margin=(revn - total) / total)


def residual(sellable, price, cost_ag, *, svc=0.20, profit=0.17, fin=0.07, cont=0.07, lot=0, fees=700,
             consultants=0.07, mgmt=0.03, marketing=0.03, units=None, new_unit=95, parking_sqm=30, cost_base=4400,
             levy=0.0):
    gross = sellable / (1 - svc); units = units or sellable / new_unit; base = units * parking_sqm
    hard = gross * cost_ag + base * cost_base + lot * 600
    rev = sellable * price; revn = rev / VAT
    soft = hard * (consultants + mgmt) + (gross + base) * fees + revn * marketing
    total = (hard + soft) * (1 + fin + cont); pr = total * profit
    res = revn - total - pr - levy
    return dict(gross=gross, rev=rev, revn=revn, total=total, profit=pr, surplus=res, share_of_rev=res / rev)


def breakeven(fn, key='surplus', lo=10_000, hi=250_000, **kw):
    for _ in range(60):
        mid = (lo + hi) / 2
        if fn(price=mid, **kw)[key] > 0: hi = mid
        else: lo = mid
    return mid


def grid(fn, price, cost_ag, steps=(0.9, 1.0, 1.1), key='surplus', **kw):
    """Rows: price +10% / base / -10%; columns: cost -10% / base / +10%. Check RTL column order visually."""
    return [[fn(price=price * pm, cost_ag=cost_ag * cm, **kw)[key] for cm in steps] for pm in reversed(steps)]


def tx_stats(rows, since='2024-01-01', min_area=15, partial_ratio=0.45, cluster_min=6):
    """rows: dicts with deal_date, deal_amount, asset_area_sqm, parcel_local_id.
    Returns cleaned groups: 'new' = parcels with a same-day cluster (likely contractor sales), 'second' = rest."""
    r = [x for x in rows if (x.get('deal_date') or '')[:10] >= since and (x.get('asset_area_sqm') or 0) >= min_area
         and x.get('deal_amount')]
    for x in r: x['ppm'] = x['deal_amount'] / x['asset_area_sqm']
    med = st.median([x['ppm'] for x in r]) if r else 0
    removed = [x for x in r if x['ppm'] < med * partial_ratio]            # partial transfers
    r = [x for x in r if x['ppm'] >= med * partial_ratio]
    seen = set(); dedup = []
    for x in r:                                                          # duplicate reports
        k = (x['deal_amount'], x['asset_area_sqm'], x.get('parcel_local_id'))
        if k in seen: continue
        seen.add(k); dedup.append(x)
    days = Counter((x.get('parcel_local_id'), x['deal_date'][:10]) for x in dedup)
    clus = {p for (p, d), n in days.items() if n >= cluster_min}
    def S(g):
        p = [x['ppm'] for x in g]
        if not p: return None
        m = st.mean(p)
        return dict(n=len(p), median=round(st.median(p)), cv=round(st.pstdev(p) / m, 3),
                    first=min(x['deal_date'][:10] for x in g), last=max(x['deal_date'][:10] for x in g))
    new = [x for x in dedup if x.get('parcel_local_id') in clus]
    sec = [x for x in dedup if x.get('parcel_local_id') not in clus]
    out = dict(new=S(new), second=S(sec), removed_partial=len(removed), new_parcels=sorted(clus))
    if out['new'] and out['second']:
        out['premium'] = round(out['new']['median'] / out['second']['median'] - 1, 3)
    return out


# ---------------------------------------------------------------- v2 additions
# Deal types. The skill knows there are several deal types; v2 implements two of them.
DEAL_TYPES = {
    'מכר': 'כמה לשלם על הקרקע כמו שהיא היום → טווח מחיר לקרקע (שווי שיורי)',
    'קומבינציה': 'באיזה יחס העסקה רווחית → יחס הקומבינציה שבו העסקה כדאית',
}
NOT_IMPLEMENTED_DEALS = ['קומבינציה כספית / תמורות מעורבות', 'שותפות / עסקת חלוקה', 'חכירה']
USES = ['מגורים', 'עירוב שימושים', 'מסחר', 'תעסוקה', 'מלאכה ולוגיסטיקה', 'דאטה סנטר', 'אנרגיה מתחדשת']


def allowed_deals(use):
    """Residential & mixed-use → sale or combination. Employment (offices) and light industry & logistics → sale only
    (logistics is part of employment). Retail, data center, renewable energy → sale; combination not stated → skill decision."""
    if use in ('מגורים', 'עירוב שימושים'):
        return ['מכר', 'קומבינציה'], None
    if use in ('תעסוקה', 'מלאכה ולוגיסטיקה'):
        return ['מכר'], None
    return ['מכר'], 'החלטת הסקיל: ההנחיות לא מגדירות קומבינציה לשימוש זה'


def blended_price(mix):
    """mix: [{'use':..., 'sqm':..., 'price':...}] → weighted price per sellable m²."""
    s = sum(m['sqm'] for m in mix)
    return sum(m['sqm'] * m['price'] for m in mix) / s if s else 0


def land_value_range(fn_residual, price, steps=(0.9, 1.0, 1.1)):
    """Sale deal: residual land value at price -10% / base / +10%.
    Recommended range = [−10%, base], floored at 0 (conservative side of the market)."""
    v = [fn_residual(price=price * s)['surplus'] for s in steps]
    return dict(low=max(v[0], 0), base=max(v[1], 0), high=max(v[2], 0), recommended=(max(v[0], 0), max(v[1], 0)))


def combination_breakeven(sellable, price, cost_ag, **kw):
    """Combination on land without existing owners (empty / small lot): the share of sellable area the landowner
    can receive in kind while the developer still earns the target profit. Returns the share (0–1)."""
    lo, hi = 0.0, 0.95
    for _ in range(60):
        r = (lo + hi) / 2
        res = residual(sellable, price, cost_ag, owner_share=r, **kw)['surplus']
        if res > 0: lo = r
        else: hi = r
    return lo


_residual_v1 = residual


def residual(sellable, price, cost_ag, *, owner_share=0.0, **kw):  # noqa: F811  (extends v1 with owner_share)
    if not owner_share:
        return _residual_v1(sellable, price, cost_ag, **kw)
    r = _residual_v1(sellable, price, cost_ag, **kw)
    rev = sellable * (1 - owner_share) * price; revn = rev / VAT
    mk = kw.get('marketing', 0.03); fin = kw.get('fin', 0.07); cont = kw.get('cont', 0.07)
    total = r['total'] - (r['revn'] - revn) * mk * (1 + fin + cont)
    pr = total * kw.get('profit', 0.17)
    res = revn - total - pr - kw.get('levy', 0.0)
    return dict(r, rev=rev, revn=revn, total=total, profit=pr, surplus=res, share_of_rev=res / rev if rev else 0)


def decide(surplus, total, comb=None, buildable_surplus=None, buildable_total=None):
    """Three-way decision (v2 keeps 'גבולי').
    NO-GO: combination ≥ 60%, or a deficit larger than 10% of total cost on the rights envelope.
    GO: surplus above 5% of total cost, and (when a buildable envelope exists) the buildable envelope is positive too.
    Otherwise גבולי; 'נוטה ל-NO-GO' when the buildable envelope loses more than 10% of its cost."""
    if (comb is not None and comb >= 0.60) or surplus < -0.10 * total:
        return 'NO-GO'
    if surplus > 0.05 * total and (buildable_surplus is None or buildable_surplus > 0):
        return 'GO'
    if buildable_surplus is not None and buildable_total and buildable_surplus < -0.10 * buildable_total:
        return 'גבולי — נוטה ל-NO-GO'
    return 'גבולי'


def flips(fn, price, sellable, **kw):
    """What turns the decision: break-even price and break-even sellable area at the market price."""
    be_p = breakeven(lambda price: fn(price=price, sellable=sellable, **kw))
    lo, hi = sellable * 0.3, sellable * 4
    for _ in range(60):
        m = (lo + hi) / 2
        if fn(price=price, sellable=m, **kw)['surplus'] > 0: hi = m
        else: lo = m
    return dict(be_price=be_p, be_sellable=m, price_gap=be_p / price - 1, area_gap=m / sellable - 1)


def size_adjusted(rows, target_sqm):
    """Linear fit of ₪/m² on unit size over new-build deals → price for the target unit size.
    New-build ₪/m² falls with size (Bruria 15: 53,900 for ≤75 m² vs 44,100 above)."""
    xs = [x['asset_area_sqm'] for x in rows]; ys = [x['deal_amount'] / x['asset_area_sqm'] for x in rows]
    if len(xs) < 4: return None
    mx, my = st.mean(xs), st.mean(ys)
    b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / (sum((a - mx) ** 2 for a in xs) or 1)
    return dict(price=my + b * (target_sqm - mx), slope=b, n=len(xs))


def tx_stats_v2(rows, since='2024-01-01', min_area=15, partial_ratio=0.45, cluster_min=6, serial_min=6,
                serial_days=183, extra_new=(), use_key=None, min_n=6):
    """v1 tx_stats + (a) serial contractor sales: ≥serial_min deals in one parcel within serial_days, also on
    different days; (b) extra_new: parcels the analyst identified as projects (e.g. a same-day cluster before
    `since`); (c) per-use split when use_key is given → groups with n < min_n are flagged ask_user=True."""
    import datetime as dt
    by_parcel = {}
    for x in rows:
        if (x.get('asset_area_sqm') or 0) >= min_area and x.get('deal_date') and x.get('deal_amount'):
            by_parcel.setdefault(x.get('parcel_local_id'), []).append(x['deal_date'][:10])
    serial = set()
    for p, ds in by_parcel.items():
        ds = sorted(dt.date.fromisoformat(d) for d in ds)
        for i in range(len(ds)):
            j = i
            while j < len(ds) and (ds[j] - ds[i]).days <= serial_days: j += 1
            if j - i >= serial_min: serial.add(p); break
    base = tx_stats([dict(x) for x in rows], since, min_area, partial_ratio, cluster_min)
    newp = set(base['new_parcels']) | serial | set(extra_new)
    r = [dict(x) for x in rows if (x.get('deal_date') or '')[:10] >= since and (x.get('asset_area_sqm') or 0) >= min_area
         and x.get('deal_amount')]
    for x in r: x['ppm'] = x['deal_amount'] / x['asset_area_sqm']
    med = st.median([x['ppm'] for x in r]) if r else 0
    r = [x for x in r if x['ppm'] >= med * partial_ratio]
    seen = set(); d = []
    for x in r:
        k = (round(x['deal_amount'], -3), x['asset_area_sqm'], x.get('parcel_local_id'))
        if k in seen: continue
        seen.add(k); d.append(x)
    def S(g):
        p = [x['ppm'] for x in g]
        if not p: return None
        m = st.mean(p)
        return dict(n=len(p), median=round(st.median(p)), cv=round(st.pstdev(p) / m, 3), lo=round(min(p)), hi=round(max(p)),
                    first=min(x['deal_date'][:10] for x in g), last=max(x['deal_date'][:10] for x in g))
    groups = {}
    for x in d:
        u = x.get(use_key, 'מגורים') if use_key else 'מגורים'
        kind = 'new' if x.get('parcel_local_id') in newp else 'second'
        groups.setdefault(u, {}).setdefault(kind, []).append(x)
    out = {}
    for u, g in groups.items():
        o = {k: S(v) for k, v in g.items()}
        o['ask_user'] = sum(len(v) for v in g.values()) < min_n
        if o.get('new') and o.get('second'):
            o['premium'] = round(o['new']['median'] / o['second']['median'] - 1, 3)
        o['rows_new'] = g.get('new', []); o['rows_second'] = g.get('second', [])
        out[u] = o
    return dict(by_use=out, new_parcels=sorted(newp), serial_parcels=sorted(serial))
