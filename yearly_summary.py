# yearly_summary.py
# ใช้งานใน Pythonista บน iPhone/iPad
# วิธีเรียกใช้:
#   import yearly_summary
#   yearly_summary.show(db_path)

import ui
import sqlite3

CLINIC_INCOME_NAME  = 'รายรับของคลินิก'
CLINIC_EXPENSE_NAME = 'รายจ่ายของคลินิก'

THAI_MONTHS_SHORT = [
    '', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.',
    'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.',
    'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
]


# ─────────────────────────────────────────────────────────────
# SQL helpers
# ─────────────────────────────────────────────────────────────

def _fetch_data(db_path):
    """
    คืนค่า dict: { (year, month): {'inc': x, 'exp': y, 'clinic_inc': z, 'clinic_exp': w} }
    ครอบคลุมทุก year/month ที่มีข้อมูลใน DB
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        # รายรับ — แยกคลินิก vs ไม่ใช่คลินิก
        cur.execute('''
            SELECT i.year, i.month,
                   COALESCE(ci.name, '') AS cat,
                   SUM(i.amount)
            FROM income i
            LEFT JOIN category_income ci ON i.category_id = ci.id
            GROUP BY i.year, i.month, cat
            ORDER BY i.year, i.month
        ''')
        income_rows = cur.fetchall()

        # รายจ่าย — แยกคลินิก vs ไม่ใช่คลินิก
        cur.execute('''
            SELECT e.year, e.month,
                   COALESCE(ce.name, '') AS cat,
                   SUM(e.amount)
            FROM expense e
            LEFT JOIN category_expense ce ON e.category_id = ce.id
            GROUP BY e.year, e.month, cat
            ORDER BY e.year, e.month
        ''')
        expense_rows = cur.fetchall()

    finally:
        conn.close()

    data = {}

    def _key(y, m):
        if (y, m) not in data:
            data[(y, m)] = {'inc': 0.0, 'exp': 0.0,
                            'clinic_inc': 0.0, 'clinic_exp': 0.0}
        return data[(y, m)]

    for y, m, cat, total in income_rows:
        d = _key(y, m)
        if cat == CLINIC_INCOME_NAME:
            d['clinic_inc'] += total
        else:
            d['inc'] += total

    for y, m, cat, total in expense_rows:
        d = _key(y, m)
        if cat == CLINIC_EXPENSE_NAME:
            d['clinic_exp'] += total
        else:
            d['exp'] += total

    return data


# ─────────────────────────────────────────────────────────────
# HTML builder
# ─────────────────────────────────────────────────────────────

def _fmt(n):
    try:
        return '{:,.2f}'.format(float(n))
    except (TypeError, ValueError):
        return '0.00'


def _signed_fmt(n):
    try:
        f = float(n)
        return ('+' if f >= 0 else '') + '{:,.2f}'.format(f)
    except (TypeError, ValueError):
        return '0.00'


def _val_class(n):
    try:
        return 'pos' if float(n) >= 0 else 'neg'
    except (TypeError, ValueError):
        return 'pos'


def _build_table_rows(months_keys, data, mode):
    """
    mode = 'normal'  → ใช้ inc / exp
    mode = 'clinic'  → ใช้ clinic_inc / clinic_exp
    """
    rows_html = ''
    cumulative = 0.0

    for i, (y, m) in enumerate(months_keys):
        d = data.get((y, m), {'inc': 0.0, 'exp': 0.0,
                               'clinic_inc': 0.0, 'clinic_exp': 0.0})
        if mode == 'clinic':
            inc = d['clinic_inc']
            exp = d['clinic_exp']
        else:
            inc = d['inc']
            exp = d['exp']

        balance    = inc - exp
        cumulative += balance
        stripe     = ' stripe' if i % 2 == 1 else ''
        bal_cls    = _val_class(balance)
        cum_cls    = _val_class(cumulative)
        month_str  = THAI_MONTHS_SHORT[m] + ' ' + str(y + 543)

        rows_html += (
            f'<tr class="data-row{stripe}">'
            f'<td class="month-cell">{month_str}</td>'
            f'<td class="amt-cell inc-col">{_fmt(inc)}</td>'
            f'<td class="amt-cell exp-col">{_fmt(exp)}</td>'
            f'<td class="amt-cell {bal_cls}">{_signed_fmt(balance)}</td>'
            f'<td class="amt-cell cum-col {cum_cls}">{_signed_fmt(cumulative)}</td>'
            f'</tr>\n'
        )

    # แถวสรุปรวม
    if mode == 'clinic':
        total_inc = sum(data.get(k, {}).get('clinic_inc', 0) for k in months_keys)
        total_exp = sum(data.get(k, {}).get('clinic_exp', 0) for k in months_keys)
    else:
        total_inc = sum(data.get(k, {}).get('inc', 0) for k in months_keys)
        total_exp = sum(data.get(k, {}).get('exp', 0) for k in months_keys)

    total_bal = total_inc - total_exp
    bal_cls   = _val_class(total_bal)

    rows_html += (
        f'<tr class="total-row">'
        f'<td class="month-cell total-label">รวมทั้งปี</td>'
        f'<td class="amt-cell inc-col total-val">{_fmt(total_inc)}</td>'
        f'<td class="amt-cell exp-col total-val">{_fmt(total_exp)}</td>'
        f'<td class="amt-cell {bal_cls} total-val">{_signed_fmt(total_bal)}</td>'
        f'<td class="amt-cell"></td>'
        f'</tr>\n'
    )
    return rows_html


def _build_html(data):
    if not data:
        return _build_empty_html()

    months_keys = sorted(data.keys())
    # หา ปี จาก key แรก (ควรเป็นปีเดียวกันทั้งไฟล์)
    year     = months_keys[0][0]
    thai_year = year + 543

    normal_rows = _build_table_rows(months_keys, data, 'normal')
    clinic_rows = _build_table_rows(months_keys, data, 'clinic')

    return f'''<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<style>
  :root {{
    --bg:          #0f0f13;
    --surface:     #18181f;
    --surface2:    #22222c;
    --border:      #2e2e3a;
    --accent-inc:  #34d399;
    --accent-exp:  #f87171;
    --clinic-gold: #fbbf24;
    --text-primary:   #f0f0f5;
    --text-secondary: #8888a0;
    --text-muted:     #55556a;
    --radius: 12px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text-primary);
    font-family: -apple-system, "Helvetica Neue", sans-serif;
    font-size: 14px;
    padding: 16px 10px 40px;
  }}

  /* ── Header ── */
  .header {{
    text-align: center;
    margin-bottom: 22px;
  }}
  .header-label {{
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 4px;
  }}
  .header-year {{
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
  }}
  .header-divider {{
    width: 40px; height: 3px;
    border-radius: 2px;
    background: linear-gradient(90deg, var(--accent-inc), var(--clinic-gold));
    margin: 10px auto 0;
  }}

  /* ── Section card ── */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 24px;
    overflow: hidden;
  }}
  .card-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
  }}
  .card-dot {{
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .dot-normal {{ background: var(--accent-inc); box-shadow: 0 0 8px var(--accent-inc); }}
  .dot-clinic {{ background: var(--clinic-gold); box-shadow: 0 0 8px var(--clinic-gold); }}
  .card-title {{
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary);
  }}
  .card-sub {{
    font-size: 11px;
    color: var(--text-muted);
    margin-left: 2px;
  }}

  /* ── Table ── */
  .table-wrap {{
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }}
  table {{ width: 100%; border-collapse: collapse; min-width: 340px; }}

  thead tr {{ background: #1e1e28; }}
  th {{
    padding: 8px 10px;
    text-align: right;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    white-space: nowrap;
    letter-spacing: 0.3px;
  }}
  th:first-child {{ text-align: left; }}

  .data-row td {{ padding: 8px 10px; border-bottom: 1px solid #1e1e28; }}
  .data-row.stripe td {{ background: var(--surface2); }}

  .month-cell {{
    white-space: nowrap;
    color: var(--text-secondary);
    font-size: 13px;
  }}
  .amt-cell {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    font-size: 13px;
  }}
  .inc-col {{ color: var(--accent-inc); }}
  .exp-col {{ color: var(--accent-exp); }}
  .pos     {{ color: #a3e635; }}
  .neg     {{ color: #fb923c; }}
  .cum-col {{ font-weight: 600; }}

  /* total row */
  .total-row td {{
    padding: 11px 10px;
    background: #1e1e28;
    border-top: 2px solid var(--border);
  }}
  .total-label {{
    font-size: 13px;
    font-weight: 700;
    color: var(--text-primary);
  }}
  .total-val {{
    font-size: 14px;
    font-weight: 700;
  }}

  /* empty */
  .empty-cell {{
    text-align: center;
    padding: 24px;
    color: var(--text-muted);
    font-size: 13px;
  }}

  .footer {{
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-label">สรุปรายปี</div>
  <div class="header-year">{thai_year}</div>
  <div class="header-divider"></div>
</div>

<!-- ตารางที่ 1 — ไม่รวมคลินิก -->
<div class="card">
  <div class="card-header">
    <div class="card-dot dot-normal"></div>
    <div>
      <div class="card-title">ภาพรวมทั่วไป</div>
      <div class="card-sub" style="color: var(--clinic-gold);">ไม่รวมรายรับ-รายจ่ายของคลินิก</div>
    </div>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>เดือน</th>
          <th>รายรับ</th>
          <th>รายจ่าย</th>
          <th>คงเหลือ</th>
          <th>สะสม</th>
        </tr>
      </thead>
      <tbody>
        {normal_rows}
      </tbody>
    </table>
  </div>
</div>

<!-- ตารางที่ 2 — เฉพาะคลินิก -->
<div class="card">
  <div class="card-header">
    <div class="card-dot dot-clinic"></div>
    <div>
      <div class="card-title" style="color: var(--clinic-gold);">คลินิก</div>
      <div class="card-sub" style="color: var(--clinic-gold);">เฉพาะรายรับ-รายจ่ายของคลินิก</div>
    </div>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>เดือน</th>
          <th>รายรับ</th>
          <th>รายจ่าย</th>
          <th>คงเหลือ</th>
          <th>สะสม</th>
        </tr>
      </thead>
      <tbody>
        {clinic_rows}
      </tbody>
    </table>
  </div>
</div>

<div class="footer">YEARLY SUMMARY · {thai_year}</div>

</body>
</html>'''


def _build_empty_html():
    return '''<!DOCTYPE html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ background:#0f0f13; color:#8888a0;
         font-family:-apple-system,sans-serif;
         display:flex; align-items:center; justify-content:center;
         height:100vh; margin:0; font-size:16px; }}
</style></head>
<body><div>ยังไม่มีข้อมูลในไฟล์นี้</div></body></html>'''


# ─────────────────────────────────────────────────────────────
# Result WebView
# ─────────────────────────────────────────────────────────────

class _ResultView(ui.View):
    def __init__(self, html):
        super().__init__()
        self.name = 'สรุปรายปี'
        self.background_color = '#0f0f13'
        wv = ui.WebView()
        wv.flex = 'WH'
        wv.scales_page_to_fit = False
        self.add_subview(wv)
        self._wv = wv
        wv.load_html(html)

    def layout(self):
        self._wv.frame = self.bounds


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def show(db_path):
    data = _fetch_data(db_path)
    html = _build_html(data)
    W, H = ui.get_screen_size()
    v = _ResultView(html)
    v.frame = (0, 0, W, H)
    v.present('fullscreen', animated=True)