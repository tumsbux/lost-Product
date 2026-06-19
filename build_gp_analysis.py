"""build_gp_analysis.py — GP (Gross Profit) Analysis
Store + Product + Monthly trend | MTD + last 3 months

Output: gp_analysis_data.json
Usage:
  py build_gp_analysis.py              # build + push
  py build_gp_analysis.py --no-push   # build only
  py build_gp_analysis.py --months 6  # custom lookback
"""

import sys, os, json, argparse, traceback, gc
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict

try:
    import mysql.connector
except ImportError:
    print('ERROR: pip install mysql-connector-python'); sys.exit(1)

# ── config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'gp_analysis_data.json')
BUILT_BY    = 'antigravity-gemini-3-flash'
EXCLUDED_ITY = {'03', '12', '15', '20', '26'}  # Supply Use, อุปกรณ์ไฟฟ้า, สินทรัพย์, ค่าใช้จ่าย, สินค้าสมนาคุณ

DB_PATHS = [
    os.path.join(SCRIPT_DIR, 'db_config.json'),
    r'F:\co work dashboard\db_config.json',
]

def load_db_config():
    for p in DB_PATHS:
        if os.path.exists(p):
            return json.load(open(p, encoding='utf-8'))
    raise FileNotFoundError('db_config.json not found')

def get_conn(cfg, database='data-lake'):
    return mysql.connector.connect(
        host=cfg['host'], port=int(cfg.get('port', 13306)),
        user=cfg['user'], password=cfg['password'],
        database=database, charset='utf8mb3',
        connection_timeout=60,
    )

# ── step 1: raw GP data from fact_sales ──────────────────────────────────────
def query_gp_data(cfg, start_date):
    """Returns list of (sotowhs, iprod, month_str, sales, cost, sku_disc, bill_disc) tuples."""
    print(f'[1/4] Querying GP data from fact_sales (since {start_date}) ...')
    conn = get_conn(cfg)
    cur = conn.cursor()
    cur.execute("""
        SELECT sotowhs, iprod,
               CONCAT(YEAR(sodate), '-', LPAD(MONTH(sodate),2,'0')) as mo,
               SUM(net_sales_amt) as sales,
               SUM(total_cost) as cost,
               SUM(soqty * sopricdisc) as sku_disc,
               SUM(solineamt - net_sales_amt) as bill_disc
        FROM `data-lake`.fact_sales
        WHERE sodate >= %s
          AND solinetype NOT IN ('C','R')
          AND soretflag = 'N'
          AND sotowhs >= '001' AND sotowhs <= '500'
        GROUP BY sotowhs, iprod, mo
    """, (start_date.isoformat(),))
    rows = []
    for sotowhs, iprod, mo, sales, cost, sku_disc, bill_disc in cur:
        mo_str = mo.decode() if isinstance(mo, (bytes, bytearray)) else str(mo)
        rows.append((
            str(sotowhs).zfill(3),
            str(iprod),
            mo_str,
            float(sales) if sales else 0.0,
            float(cost)  if cost  else 0.0,
            float(sku_disc) if sku_disc else 0.0,
            float(bill_disc) if bill_disc else 0.0,
        ))
    cur.close(); conn.close()
    print(f'  {len(rows):,} aggregated rows loaded')
    return rows

# ── step 2: dim lookups ──────────────────────────────────────────────────────
def query_stores(cfg):
    print('[2/4] Querying stores from dim_branch ...')
    conn = get_conn(cfg)
    cur = conn.cursor()
    cur.execute("SELECT code, name, dm, rm FROM `data-lake`.dim_branch")
    stores = {}
    for code, name, dm, rm in cur:
        try:
            n = int(str(code).strip())
            stores[f'{n:03d}'] = {'name': name or '', 'dm': dm or '', 'rm': rm or ''}
        except (ValueError, TypeError):
            pass
    cur.close(); conn.close()
    print(f'  {len(stores):,} stores')
    return stores

def query_products(cfg):
    print('[3/4] Querying products from dim_product + item_group + item_type ...')
    conn = get_conn(cfg)
    cur = conn.cursor()
    cur.execute("SELECT iprod, idesc, igrcode FROM `data-lake`.dim_product")
    prods = {}
    for iprod, idesc, igrcode in cur:
        prods[str(iprod)] = {'name': idesc or '', 'group': str(igrcode or '')}
    cur.close(); conn.close()

    # group names
    conn2 = mysql.connector.connect(
        host=cfg['host'], port=int(cfg.get('port', 13306)),
        user=cfg['user'], password=cfg['password'],
        database='MYPOS2018_CENTER', charset='utf8mb3', connection_timeout=30,
    )
    cur2 = conn2.cursor()
    cur2.execute("SELECT igrcode, igrdesc FROM MYPOS2018_CENTER.item_group")
    groups = {str(c): (d or '') for c, d in cur2}
    cur2.execute("SELECT itycode, itydesc FROM MYPOS2018_CENTER.item_type")
    types = {str(c): (d or '') for c, d in cur2}

    # barcode -> master iprod mapping
    cur2.execute("SELECT barcode, parcode FROM MYPOS2018_CENTER.item_barcode WHERE baractive = 'Y'")
    barcodes = {str(b): str(p) for b, p in cur2}
    cur2.close(); conn2.close()

    print(f'  {len(prods):,} products, {len(groups):,} groups, {len(types):,} types, {len(barcodes):,} barcodes')
    return prods, groups, types, barcodes

# ── step 3: aggregate ────────────────────────────────────────────────────────
def build_json(rows, stores, prods, groups, types, barcodes, months, current_month, days_elapsed):
    print('[4/4] Building gp_analysis_data.json ...')

    # ── resolve barcodes -> master iprod & filter excluded types ──────────────
    resolved_rows = []
    barcode_resolved = 0
    excluded_type = 0
    for whs, iprod, mo, sales, cost, sd, bd in rows:
        # resolve barcode to master product code
        master = iprod
        if iprod not in prods and iprod in barcodes:
            master = barcodes[iprod]
            barcode_resolved += 1
        # filter excluded item types
        pi = prods.get(master, {})
        ty = pi.get('group', '')[:2]
        if ty in EXCLUDED_ITY:
            excluded_type += 1
            continue
        resolved_rows.append((whs, master, mo, sales, cost, sd, bd))
    print(f'  barcode->master resolved: {barcode_resolved:,}, excluded types: {excluded_type:,}, kept: {len(resolved_rows):,}')
    rows = resolved_rows

    # ── monthly totals ────────────────────────────────────────────────────────
    monthly = defaultdict(lambda: {'sales': 0, 'cost': 0, 'disc': 0})
    for whs, iprod, mo, sales, cost, sd, bd in rows:
        monthly[mo]['sales'] += sales
        monthly[mo]['cost']  += cost
        monthly[mo]['disc']  += sd + bd

    monthly_list = []
    for mo in sorted(monthly.keys()):
        m = monthly[mo]
        gp = m['sales'] - m['cost']
        monthly_list.append({
            'month':  mo,
            'sales':  round(m['sales'], 2),
            'cost':   round(m['cost'],  2),
            'disc':   round(m['disc'],  2),
            'gp':     round(gp, 2),
            'gp_pct': round(gp / m['sales'] * 100, 1) if m['sales'] else 0,
            'is_mtd': mo == current_month,
        })

    # ── store aggregation (current month only for MTD view) ───────────────────
    store_agg = defaultdict(lambda: {'sales': 0, 'cost': 0, 'disc': 0})
    store_all = defaultdict(lambda: defaultdict(lambda: {'sales': 0, 'cost': 0}))
    for whs, iprod, mo, sales, cost, sd, bd in rows:
        store_all[whs][mo]['sales'] += sales
        store_all[whs][mo]['cost']  += cost
        if mo == current_month:
            store_agg[whs]['sales'] += sales
            store_agg[whs]['cost']  += cost
            store_agg[whs]['disc']  += sd + bd

    store_list = []
    for whs in sorted(store_agg.keys()):
        s = store_agg[whs]
        si = stores.get(whs, {})
        gp = s['sales'] - s['cost']
        # monthly trend per store
        trend = []
        for mo in sorted(store_all[whs].keys()):
            sm = store_all[whs][mo]
            sgp = sm['sales'] - sm['cost']
            trend.append({
                'month': mo,
                'sales': round(sm['sales'], 2),
                'cost':  round(sm['cost'],  2),
                'gp':    round(sgp, 2),
                'gp_pct': round(sgp / sm['sales'] * 100, 1) if sm['sales'] else 0,
            })
        store_list.append({
            'code':     whs,
            'name':     si.get('name', ''),
            'dm':       si.get('dm', ''),
            'rm':       si.get('rm', ''),
            'sales':    round(s['sales'], 2),
            'cost':     round(s['cost'],  2),
            'disc':     round(s['disc'],  2),
            'gp':       round(gp, 2),
            'gp_pct':   round(gp / s['sales'] * 100, 1) if s['sales'] else 0,
            'trend':    trend,
        })
    store_list.sort(key=lambda x: x['gp_pct'])  # worst GP% first

    # ── product aggregation (current month MTD) ──────────────────────────────
    prod_agg = defaultdict(lambda: {'sales': 0, 'cost': 0, 'sku_disc': 0, 'bill_disc': 0})
    for whs, iprod, mo, sales, cost, sd, bd in rows:
        if mo == current_month:
            prod_agg[iprod]['sales']     += sales
            prod_agg[iprod]['cost']      += cost
            prod_agg[iprod]['sku_disc']  += sd
            prod_agg[iprod]['bill_disc'] += bd

    prod_list = []
    for iprod in sorted(prod_agg.keys(), key=lambda k: prod_agg[k]['sales'] - prod_agg[k]['cost']):
        p = prod_agg[iprod]
        pi = prods.get(iprod, {})
        gr_code = pi.get('group', '')
        ty_code = gr_code[:2]
        gp = p['sales'] - p['cost']
        disc = p['sku_disc'] + p['bill_disc']
        prod_list.append({
            'iprod':      iprod,
            'name':       pi.get('name', ''),
            'group':      gr_code,
            'group_name': groups.get(gr_code, ''),
            'type_code':  ty_code,
            'type_name':  types.get(ty_code, ''),
            'sales':      round(p['sales'], 2),
            'cost':       round(p['cost'],  2),
            'disc':       round(disc, 2),
            'sku_disc':   round(p['sku_disc'], 2),
            'bill_disc':  round(p['bill_disc'], 2),
            'gp':         round(gp, 2),
            'gp_pct':     round(gp / p['sales'] * 100, 1) if p['sales'] else 0,
        })
    # sort by GP% ascending (worst first)
    prod_list.sort(key=lambda x: x['gp_pct'])

    # ── product × store breakdown (current month MTD) ────────────────────────
    ps_agg = defaultdict(lambda: defaultdict(lambda: {'sales': 0, 'cost': 0}))
    for whs, iprod, mo, sales, cost, sd, bd in rows:
        if mo == current_month:
            ps_agg[iprod][whs]['sales'] += sales
            ps_agg[iprod][whs]['cost']  += cost

    prod_stores = {}
    for iprod, stores_data in ps_agg.items():
        # include store detail for products with GP% < 15% (low/negative margin)
        pa = prod_agg.get(iprod)
        if pa and pa['sales'] > 0:
            pgp_pct = (pa['sales'] - pa['cost']) / pa['sales'] * 100
            if pgp_pct >= 15:
                continue
        detail = []
        for whs, v in stores_data.items():
            si = stores.get(whs, {})
            gp = v['sales'] - v['cost']
            detail.append({
                'c': whs,
                'n': si.get('name', ''),
                's': round(v['sales'], 2),
                'k': round(v['cost'], 2),
                'g': round(gp, 2),
                'p': round(gp / v['sales'] * 100, 1) if v['sales'] else 0,
            })
        detail.sort(key=lambda x: x['s'], reverse=True)
        prod_stores[iprod] = detail

    print(f'  prod_stores: {len(prod_stores)} products with store detail (of {len(ps_agg)} total)')

    # ── summary ──────────────────────────────────────────────────────────────
    mtd = monthly.get(current_month, {'sales': 0, 'cost': 0, 'disc': 0})
    mtd_gp = mtd['sales'] - mtd['cost']

    payload = {
        '_meta': {
            'schema':     3,
            'built_by':   BUILT_BY,
            'built_at':   datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'current_month': current_month,
            'days_elapsed':  days_elapsed,
            'months':     months,
        },
        'summary': {
            'sales':  round(mtd['sales'], 2),
            'disc':   round(mtd['disc'],  2),
            'cost':   round(mtd['cost'],  2),
            'gp':     round(mtd_gp, 2),
            'gp_pct': round(mtd_gp / mtd['sales'] * 100, 1) if mtd['sales'] else 0,
            'store_count': len(store_list),
            'product_count': len(prod_list),
        },
        'monthly':  monthly_list,
        'stores':   store_list,
        'products': prod_list,
        'prod_stores': prod_stores,
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))

    size_mb = os.path.getsize(OUTPUT_FILE) / 1024 / 1024
    print(f'  Wrote {len(store_list):,} stores + {len(prod_list):,} products -> {OUTPUT_FILE} ({size_mb:.1f} MB)')
    return payload

# ── push ──────────────────────────────────────────────────────────────────────
def push_to_github(cfg):
    import subprocess
    push_script = os.path.join(SCRIPT_DIR, 'push_lost_product_files.py')
    if not os.path.exists(push_script):
        print('WARNING: push_lost_product_files.py not found — skipping push')
        return
    result = subprocess.run(
        [sys.executable, push_script, OUTPUT_FILE, '-m', 'data(gp): rebuild gp_analysis_data.json'],
        capture_output=True, text=True
    )
    if result.stdout: print(result.stdout)
    if result.stderr: print(result.stderr, file=sys.stderr)

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-push', action='store_true')
    parser.add_argument('--months', type=int, default=4, help='Lookback months including current (default: 4)')
    args = parser.parse_args()

    cfg = load_db_config()
    today = date.today()
    current_month = today.strftime('%Y-%m')

    # start from N months ago first day
    start_date = (today.replace(day=1) - timedelta(days=(args.months - 1) * 30)).replace(day=1)
    months_list = []
    d = start_date
    while d <= today:
        months_list.append(d.strftime('%Y-%m'))
        if d.month == 12:
            d = d.replace(year=d.year+1, month=1)
        else:
            d = d.replace(month=d.month+1)

    print(f'=== GP Analysis Builder === months={args.months} ({start_date} -> {today})')
    try:
        raw = query_gp_data(cfg, start_date)
        gc.collect()

        # auto-detect days_elapsed from data
        month_start = today.replace(day=1).isoformat()
        if today.month == 12:
            next_month_start = today.replace(year=today.year+1, month=1, day=1).isoformat()
        else:
            next_month_start = today.replace(month=today.month+1, day=1).isoformat()
            
        conn = get_conn(cfg)
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(DAY(sodate)) FROM `data-lake`.fact_sales
            WHERE sodate >= %s AND sodate < %s
              AND soretflag = 'N'
              AND sotowhs >= '001' AND sotowhs <= '500'
        """, (month_start, next_month_start))
        row = cur.fetchone()
        days_elapsed = int(row[0]) if row and row[0] else 1
        cur.close(); conn.close()
        print(f'  days_elapsed = {days_elapsed}')

        stores = query_stores(cfg)
        gc.collect()
        prods, groups, types, barcodes = query_products(cfg)
        gc.collect()
        payload = build_json(raw, stores, prods, groups, types, barcodes, months_list, current_month, days_elapsed)
        del raw
        gc.collect()

        s = payload['summary']
        print(f'\nSummary (MTD {current_month}, day 1-{days_elapsed}):')
        print(f"  Net Sales : ฿{s['sales']:,.0f}")
        print(f"  Cost      : ฿{s['cost']:,.0f}")
        print(f"  GP        : ฿{s['gp']:,.0f}  ({s['gp_pct']:.1f}%)")
        print(f"  Stores    : {s['store_count']:,}")
        print(f"  Products  : {s['product_count']:,}")

        if not args.no_push:
            push_to_github(cfg)
        else:
            print('(--no-push: skipping GitHub push)')

    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e!r}')
        traceback.print_exc()

if __name__ == '__main__':
    main()
