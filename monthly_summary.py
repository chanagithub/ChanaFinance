# monthly_summary.py
# ใช้งานใน Pythonista บน iPhone/iPad
# วิธีเรียกใช้:
#   import monthly_summary
#   monthly_summary.show(db_path)

import ui
import sqlite3
import datetime

# ── ค่าคงที่ที่อาจไม่มีใน Pythonista บางเวอร์ชัน ──────────────
BORDER_ROUNDED  = getattr(ui, 'INPUT_ROUNDED_RECT', 3)
KB_NUMBER_PAD   = getattr(ui, 'KEYBOARD_NUMBER_PAD', 'number-pad')

CLINIC_INCOME_NAME  = 'รายรับของคลินิก'
CLINIC_EXPENSE_NAME = 'รายจ่ายของคลินิก'


# ─────────────────────────────────────────────────────────────
# SQL helpers
# ─────────────────────────────────────────────────────────────

def _fetch_income_summary(db_path, year, month):
    """คืนค่า list of (category_name, total) เรียงตาม total DESC"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT COALESCE(ci.name, '(ไม่ระบุหมวดหมู่)') AS cat,
                   SUM(i.amount) AS total
            FROM income i
            LEFT JOIN category_income ci ON i.category_id = ci.id
            WHERE i.year = ? AND i.month = ?
            GROUP BY cat
            ORDER BY total DESC
        ''', (year, month))
        return cur.fetchall()
    finally:
        conn.close()


def _fetch_expense_summary(db_path, year, month):
    """คืนค่า list of (category_name, total) เรียงตาม total DESC"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT COALESCE(ce.name, '(ไม่ระบุหมวดหมู่)') AS cat,
                   SUM(e.amount) AS total
            FROM expense e
            LEFT JOIN category_expense ce ON e.category_id = ce.id
            WHERE e.year = ? AND e.month = ?
            GROUP BY cat
            ORDER BY total DESC
        ''', (year, month))
        return cur.fetchall()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# HTML builder
# ─────────────────────────────────────────────────────────────

THAI_MONTHS = [
    '', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน',
    'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม',
    'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
]


def _fmt(n):
    try:
        return '{:,.2f}'.format(float(n))
    except (TypeError, ValueError):
        return '0.00'


def _esc(s):
    s = str(s) if s is not None else ''
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _build_html(year, month, income_rows, expense_rows):
    month_name = THAI_MONTHS[month] if 1 <= month <= 12 else str(month)
    thai_year  = year + 543
    period_str = f'{month_name} {thai_year}'

    # ── คำนวณรายรับ ──────────────────────────────────────────
    clinic_inc   = sum(t for n, t in income_rows if n == CLINIC_INCOME_NAME)
    total_inc    = sum(t for _, t in income_rows)
    non_clinic_inc = total_inc - clinic_inc

    # ── คำนวณรายจ่าย ─────────────────────────────────────────
    clinic_exp   = sum(t for n, t in expense_rows if n == CLINIC_EXPENSE_NAME)
    total_exp    = sum(t for _, t in expense_rows)
    non_clinic_exp = total_exp - clinic_exp

    # ── สร้าง row HTML ───────────────────────────────────────
    def make_rows(rows, clinic_name):
        html = ''
        for i, (cat, total) in enumerate(rows):
            is_clinic = (cat == clinic_name)
            stripe    = ' stripe' if i % 2 == 1 else ''
            bold      = ' clinic-row' if is_clinic else ''
            html += (
                f'<tr class="data-row{stripe}{bold}">'
                f'<td class="cat-cell">{_esc(cat)}</td>'
                f'<td class="amt-cell">{_fmt(total)}</td>'
                f'</tr>\n'
            )
        return html if html else '<tr><td colspan="2" class="empty-cell">ไม่มีข้อมูล</td></tr>\n'

    income_rows_html  = make_rows(income_rows,  CLINIC_INCOME_NAME)
    expense_rows_html = make_rows(expense_rows, CLINIC_EXPENSE_NAME)

    net = total_inc - total_exp
    net_class = 'net-positive' if net >= 0 else 'net-negative'
    net_sign  = '+' if net >= 0 else ''

    html = f'''<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');

  :root {{
    --bg:          #0f0f13;
    --surface:     #18181f;
    --surface2:    #22222c;
    --border:      #2e2e3a;
    --accent-inc:  #34d399;
    --accent-exp:  #f87171;
    --accent-net:  #60a5fa;
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
    font-family: 'Sarabun', 'Helvetica Neue', sans-serif;
    font-size: 15px;
    padding: 16px 12px 32px;
    min-height: 100vh;
  }}

  /* ── Header ── */
  .header {{
    text-align: center;
    margin-bottom: 24px;
  }}
  .header-label {{
    font-size: 12px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 4px;
  }}
  .header-period {{
    font-size: 26px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
  }}
  .header-divider {{
    width: 40px;
    height: 3px;
    border-radius: 2px;
    background: linear-gradient(90deg, var(--accent-inc), var(--accent-net));
    margin: 10px auto 0;
  }}

  /* ── Net bar ── */
  .net-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 20px;
  }}
  .net-label {{
    font-size: 13px;
    color: var(--text-secondary);
    font-weight: 600;
    letter-spacing: 0.5px;
  }}
  .net-value {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }}
  .net-positive {{ color: var(--accent-inc); }}
  .net-negative {{ color: var(--accent-exp); }}

  /* ── Cards ── */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 20px;
    overflow: hidden;
  }}
  .card-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 13px 16px;
    border-bottom: 1px solid var(--border);
  }}
  .card-dot {{
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .dot-inc {{ background: var(--accent-inc); box-shadow: 0 0 8px var(--accent-inc); }}
  .dot-exp {{ background: var(--accent-exp); box-shadow: 0 0 8px var(--accent-exp); }}
  .card-title {{
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.3px;
    color: var(--text-primary);
  }}

  /* ── Table ── */
  table {{ width: 100%; border-collapse: collapse; }}
  .data-row td {{ padding: 9px 16px; }}
  .data-row.stripe td {{ background: var(--surface2); }}
  .cat-cell {{ color: var(--text-primary); }}
  .amt-cell {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    color: var(--text-primary);
  }}
  .empty-cell {{
    text-align: center;
    padding: 20px;
    color: var(--text-muted);
    font-size: 13px;
  }}

  /* clinic highlight row */
  .clinic-row td {{
    color: var(--clinic-gold) !important;
    font-weight: 600;
  }}
  .clinic-row .cat-cell::before {{
    content: '★ ';
    font-size: 11px;
  }}

  /* ── Summary section ── */
  .summary-block {{
    border-top: 1px solid var(--border);
  }}
  .summary-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
  }}
  .summary-row:last-child {{ border-bottom: none; }}
  .summary-row.clinic-summary {{
    background: rgba(251,191,36,0.06);
  }}
  .summary-row.clinic-summary .s-label,
  .summary-row.clinic-summary .s-value {{
    color: var(--clinic-gold);
    font-weight: 600;
  }}
  .summary-row.total-row {{
    background: var(--surface2);
    padding: 13px 16px;
  }}
  .s-label {{ color: var(--text-secondary); }}
  .s-value {{
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    font-weight: 600;
  }}
  .s-value.inc {{ color: var(--accent-inc); font-size: 16px; }}
  .s-value.exp {{ color: var(--accent-exp); font-size: 16px; }}
  .s-label.total-label {{ color: var(--text-primary); font-weight: 700; font-size: 14px; }}

  /* ── Footer ── */
  .footer {{
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 8px;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-label">สรุปรายเดือน</div>
  <div class="header-period">{_esc(period_str)}</div>
  <div class="header-divider"></div>
</div>

<!-- Net bar -->
<div class="net-bar">
  <span class="net-label">คงเหลือสุทธิ</span>
  <span class="net-value {net_class}">{net_sign}{_fmt(net)}</span>
</div>

<!-- รายรับ -->
<div class="card">
  <div class="card-header">
    <div class="card-dot dot-inc"></div>
    <div class="card-title">รายรับ</div>
  </div>
  <table>
    <tbody>
      {income_rows_html}
    </tbody>
  </table>
  <div class="summary-block">
    <div class="summary-row clinic-summary">
      <span class="s-label">รายรับของคลินิก</span>
      <span class="s-value">{_fmt(clinic_inc)}</span>
    </div>
    <div class="summary-row">
      <span class="s-label">รายรับ (ไม่รวมคลินิก)</span>
      <span class="s-value">{_fmt(non_clinic_inc)}</span>
    </div>
    <div class="summary-row total-row">
      <span class="s-label total-label">รายรับทั้งหมด</span>
      <span class="s-value inc">{_fmt(total_inc)}</span>
    </div>
  </div>
</div>

<!-- รายจ่าย -->
<div class="card">
  <div class="card-header">
    <div class="card-dot dot-exp"></div>
    <div class="card-title">รายจ่าย</div>
  </div>
  <table>
    <tbody>
      {expense_rows_html}
    </tbody>
  </table>
  <div class="summary-block">
    <div class="summary-row clinic-summary">
      <span class="s-label">รายจ่ายของคลินิก</span>
      <span class="s-value">{_fmt(clinic_exp)}</span>
    </div>
    <div class="summary-row">
      <span class="s-label">รายจ่าย (ไม่รวมคลินิก)</span>
      <span class="s-value">{_fmt(non_clinic_exp)}</span>
    </div>
    <div class="summary-row total-row">
      <span class="s-label total-label">รายจ่ายทั้งหมด</span>
      <span class="s-value exp">{_fmt(total_exp)}</span>
    </div>
  </div>
</div>

<div class="footer">MONTHLY SUMMARY · {_esc(period_str)}</div>

</body>
</html>'''
    return html


# ─────────────────────────────────────────────────────────────
# Input form (ui.View)
# ─────────────────────────────────────────────────────────────

class _SummaryView(ui.View):

    def __init__(self, db_path):
        super().__init__()
        self.db_path   = db_path
        self.name      = 'สรุปรายเดือน'
        self.background_color = '#0f0f13'
        self._built    = False  # guard ไม่ให้ build ซ้ำ

    def layout(self):
        if not self._built:
            self._built = True
            self._build_ui()

    def _build_ui(self):
        W  = self.width
        sw = min(W, 500)
        ox = (W - sw) / 2

        now = datetime.date.today()

        # ── Title ──────────────────────────────────────────────
        lbl_title = ui.Label()
        lbl_title.text  = 'สรุปรายเดือน'
        lbl_title.font  = ('<system-bold>', 20)
        lbl_title.text_color = '#f0f0f5'
        lbl_title.alignment  = ui.ALIGN_CENTER
        lbl_title.frame = (ox, 40, sw, 30)
        self.add_subview(lbl_title)

        # ── Card background ────────────────────────────────────
        card = ui.View()
        card.background_color = '#18181f'
        card.corner_radius    = 14
        card.frame = (ox + 12, 86, sw - 24, 190)
        self.add_subview(card)

        # ── เดือน label + field ────────────────────────────────
        lbl_m = ui.Label()
        lbl_m.text       = 'เดือน (1–12)'
        lbl_m.font       = ('<system>', 13)
        lbl_m.text_color = '#8888a0'
        lbl_m.frame      = (ox + 28, 100, sw - 56, 20)
        self.add_subview(lbl_m)

        self.tf_month = ui.TextField()
        self.tf_month.text             = str(now.month)
        self.tf_month.keyboard_type    = KB_NUMBER_PAD
        self.tf_month.border_style     = BORDER_ROUNDED
        self.tf_month.background_color = '#22222c'
        self.tf_month.text_color       = '#000000'
        self.tf_month.font             = ('<system>', 16)
        self.tf_month.frame            = (ox + 28, 124, sw - 56, 40)
        self.add_subview(self.tf_month)

        # ── ปี label + field ───────────────────────────────────
        lbl_y = ui.Label()
        lbl_y.text       = 'ปี (ค.ศ.)'
        lbl_y.font       = ('<system>', 13)
        lbl_y.text_color = '#8888a0'
        lbl_y.frame      = (ox + 28, 174, sw - 56, 20)
        self.add_subview(lbl_y)

        self.tf_year = ui.TextField()
        self.tf_year.text             = str(now.year)
        self.tf_year.keyboard_type    = KB_NUMBER_PAD
        self.tf_year.border_style     = BORDER_ROUNDED
        self.tf_year.background_color = '#22222c'
        self.tf_year.text_color       = '#000000'
        self.tf_year.font             = ('<system>', 16)
        self.tf_year.frame            = (ox + 28, 198, sw - 56, 40)
        self.add_subview(self.tf_year)

        # ── ปุ่ม แสดงสรุป ──────────────────────────────────────
        btn = ui.Button()
        btn.title              = 'แสดงสรุป'
        btn.font               = ('<system-bold>', 16)
        btn.background_color   = '#34d399'
        btn.tint_color         = '#0f0f13'
        btn.corner_radius      = 12
        btn.frame              = (ox + 12, 296, sw - 24, 50)
        btn.action             = self._on_show
        self.add_subview(btn)

        self._btn = btn
        self._ox  = ox
        self._sw  = sw

    def _on_show(self, sender):
        # validate
        try:
            month = int(self.tf_month.text.strip())
            year  = int(self.tf_year.text.strip())
            assert 1 <= month <= 12
            assert 2000 <= year <= 2100
        except Exception:
            self._shake(sender)
            return

        income_rows  = _fetch_income_summary(self.db_path,  year, month)
        expense_rows = _fetch_expense_summary(self.db_path, year, month)
        html = _build_html(year, month, income_rows, expense_rows)

        result = _ResultView('สรุป ' + THAI_MONTHS[month] + ' ' + str(year + 543), html)
        result.present('fullscreen', animated=True)

    def _shake(self, btn):
        """สั่น button เบาๆ เมื่อ input ผิด"""
        import math
        orig_x = btn.x
        for i in range(6):
            dx = 6 * math.cos(i * math.pi / 1.5)
            btn.x = orig_x + dx
        btn.x = orig_x


# ─────────────────────────────────────────────────────────────
# Result WebView
# ─────────────────────────────────────────────────────────────

class _ResultView(ui.View):

    def __init__(self, title, html):
        super().__init__()
        self.name = title
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
    W, H = ui.get_screen_size()
    v = _SummaryView(db_path)
    v.frame = (0, 0, W, H)
    v.present('fullscreen', animated=True)