# data_viewer.py
# ใช้งานใน Pythonista บน iPhone/iPad
# วิธีเรียกใช้:
#   import data_viewer
#   viewer = data_viewer.DataViewer(db_path)
#   viewer.show_income()         # แสดงรายรับทั้งหมด
#   viewer.show_expense()        # แสดงรายจ่ายทั้งหมด
#   viewer.show_detail_master()  # แสดงรายละเอียด (รายรับ+รายจ่าย)
#   viewer.show_category_income()   # หมวดหมู่รายรับ
#   viewer.show_category_expense()  # หมวดหมู่รายจ่าย

import ui
import sqlite3


# -------------------------------------------------------
# Helper
# -------------------------------------------------------

def _escape(text):
    text = str(text) if text is not None else ''
    text = text.strip()
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _base_css():
    return """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #1c1c1e;
    color: #e5e5ea;
    font-family: -apple-system, "Helvetica Neue", sans-serif;
    font-size: 14px;
    padding: 8px;
  }
  h2 {
    text-align: center;
    font-size: 17px;
    font-weight: bold;
    padding: 10px 0 12px 0;
    color: #ffffff;
  }
  .table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 8px;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    min-width: 300px;
    background: #2c2c2e;
  }
  thead tr { background: #3a3a3c; border-bottom: 2px solid #555; }
  th {
    padding: 10px 10px;
    text-align: left;
    font-size: 13px;
    color: rgba(235,235,245,0.8);
    white-space: nowrap;
  }
  th.amount { text-align: right; }
  td {
    padding: 8px 10px;
    vertical-align: top;
    border-bottom: 1px solid #3a3a3c;
    font-size: 14px;
    color: #e5e5ea;
  }
  tr.stripe td { background: #323234; }
  td.date   { white-space: nowrap; color: #98989f; font-size: 13px; }
  td.amount { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
  td.note   { color: #98989f; font-size: 13px; }
  td.rid    { width: 50px; text-align: center; color: #636366; font-size: 12px; }
  td.empty  { text-align: center; padding: 24px; color: #636366; }
  .footer   { text-align: center; padding: 12px 0 6px 0; font-size: 12px; color: #636366; }
  details {
    margin-bottom: 12px;
    border-radius: 8px;
    overflow: hidden;
  }
  summary {
    background: #3a3a3c;
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    padding: 12px 14px;
    cursor: pointer;
    list-style: none;
    border-radius: 8px;
  }
  details[open] summary { border-radius: 8px 8px 0 0; }
  summary::-webkit-details-marker { display: none; }
  summary::before { content: "\\25B6  "; font-size: 12px; color: #98989f; }
  details[open] summary::before { content: "\\25BC  "; }
"""


# -------------------------------------------------------
# HTML builders
# -------------------------------------------------------

def _build_html_transactions(title, rows, empty_msg):
    """HTML สำหรับรายรับ/รายจ่าย — 5 คอลัมน์"""
    css = _base_css()

    if rows:
        body = ''
        for i, (date, detail, category, amount, note) in enumerate(rows):
            try:
                amt = "{:,.2f}".format(float(amount))
            except (TypeError, ValueError):
                amt = ''
            stripe = ' class="stripe"' if i % 2 == 1 else ''
            body += (
                '<tr' + stripe + '>'
                '<td class="date">'   + _escape(date)     + '</td>'
                '<td>'                + _escape(detail)   + '</td>'
                '<td>'                + _escape(category) + '</td>'
                '<td class="amount">' + amt               + '</td>'
                '<td class="note">'   + _escape(note)     + '</td>'
                '</tr>\n'
            )
        count = len(rows)
    else:
        body = '<tr><td colspan="5" class="empty">' + empty_msg + '</td></tr>\n'
        count = 0

    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<style>' + css + '</style></head><body>'
        '<h2>' + _escape(title) + '</h2>'
        '<div class="table-wrap"><table>'
        '<thead><tr>'
        '<th>วันที่</th><th>รายการ</th><th>หมวดหมู่</th>'
        '<th class="amount">จำนวนเงิน</th><th>หมายเหตุ</th>'
        '</tr></thead>'
        '<tbody>' + body + '</tbody>'
        '</table></div>'
        '<div class="footer">ทั้งหมด ' + str(count) + ' รายการ</div>'
        '</body></html>'
    )


def _build_html_lookup(title, rows, empty_msg):
    """HTML สำหรับตาราง lookup (category) — 2 คอลัมน์"""
    css = _base_css()

    if rows:
        body = ''
        for i, (rid, name) in enumerate(rows):
            stripe = ' class="stripe"' if i % 2 == 1 else ''
            body += (
                '<tr' + stripe + '>'
                '<td class="rid">' + _escape(str(rid)) + '</td>'
                '<td>'             + _escape(name)     + '</td>'
                '</tr>\n'
            )
        count = len(rows)
    else:
        body = '<tr><td colspan="2" class="empty">' + empty_msg + '</td></tr>\n'
        count = 0

    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<style>' + css + '</style></head><body>'
        '<h2>' + _escape(title) + '</h2>'
        '<div class="table-wrap"><table>'
        '<thead><tr>'
        '<th style="width:50px;text-align:center">ID</th><th>ชื่อ</th>'
        '</tr></thead>'
        '<tbody>' + body + '</tbody>'
        '</table></div>'
        '<div class="footer">ทั้งหมด ' + str(count) + ' รายการ</div>'
        '</body></html>'
    )


def _make_detail_section(label, rows, open_attr):
    """สร้าง <details> section สำหรับ detail_master"""
    count = len(rows)
    if rows:
        body = ''
        for i, (rid, name) in enumerate(rows):
            stripe = ' class="stripe"' if i % 2 == 1 else ''
            body += (
                '<tr' + stripe + '>'
                '<td class="rid">' + _escape(str(rid)) + '</td>'
                '<td>'             + _escape(name)     + '</td>'
                '</tr>\n'
            )
    else:
        body = '<tr><td colspan="2" class="empty">ยังไม่มีข้อมูล</td></tr>\n'

    return (
        '<details ' + open_attr + '>'
        '<summary>' + label + ' (' + str(count) + ' รายการ)</summary>'
        '<div class="table-wrap" style="margin-top:6px">'
        '<table>'
        '<thead><tr>'
        '<th style="width:50px;text-align:center">ID</th>'
        '<th>ชื่อรายละเอียด</th>'
        '</tr></thead>'
        '<tbody>' + body + '</tbody>'
        '</table></div>'
        '</details>'
    )


def _build_html_detail(income_rows, expense_rows):
    """HTML สำหรับ detail_master — 2 sections พร้อม collapse/expand"""
    css = _base_css()
    s1 = _make_detail_section('รายรับ',  income_rows,  'open')
    s2 = _make_detail_section('รายจ่าย', expense_rows, '')

    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<style>' + css + '</style></head><body>'
        '<h2>รายละเอียด</h2>'
        + s1 + s2 +
        '</body></html>'
    )


# -------------------------------------------------------
# ResultView — หน้าต่างแสดงผล fullscreen ใช้ WebView
# -------------------------------------------------------
class _ResultView(ui.View):

    def __init__(self, title, html):
        super().__init__()
        self.name = title
        self.background_color = '#1c1c1e'

        wv = ui.WebView()
        wv.flex = 'WH'
        wv.scales_page_to_fit = False
        self.add_subview(wv)
        self._wv = wv
        wv.load_html(html)

    def layout(self):
        self._wv.frame = self.bounds


# -------------------------------------------------------
# DataViewer — คลาสหลัก
# -------------------------------------------------------
class DataViewer:

    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _present(self, title, html):
        v = _ResultView(title, html)
        v.present('fullscreen', animated=True)

    # ── 1. รายรับทั้งหมด ─────────────────────────────────

    def show_income(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute('''
                SELECT i.date, i.detail_text,
                       COALESCE(ci.name, '') AS category,
                       i.amount, COALESCE(i.note, '')
                FROM income i
                LEFT JOIN category_income ci ON i.category_id = ci.id
                ORDER BY i.date DESC, i.id DESC
            ''')
            rows = cur.fetchall()
        finally:
            conn.close()
        html = _build_html_transactions('รายรับทั้งหมด', rows, 'ยังไม่มีข้อมูลรายรับ')
        self._present('รายรับทั้งหมด', html)

    # ── 2. รายจ่ายทั้งหมด ────────────────────────────────

    def show_expense(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute('''
                SELECT e.date, e.detail_text,
                       COALESCE(ce.name, '') AS category,
                       e.amount, COALESCE(e.note, '')
                FROM expense e
                LEFT JOIN category_expense ce ON e.category_id = ce.id
                ORDER BY e.date DESC, e.id DESC
            ''')
            rows = cur.fetchall()
        finally:
            conn.close()
        html = _build_html_transactions('รายจ่ายทั้งหมด', rows, 'ยังไม่มีข้อมูลรายจ่าย')
        self._present('รายจ่ายทั้งหมด', html)

    # ── 3. detail_master (รายรับ + รายจ่าย แยก section) ──

    def show_detail_master(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, detail_name FROM detail_master WHERE type = ? ORDER BY detail_name",
                ('รายรับ',)
            )
            income_rows = cur.fetchall()
            cur.execute(
                "SELECT id, detail_name FROM detail_master WHERE type = ? ORDER BY detail_name",
                ('รายจ่าย',)
            )
            expense_rows = cur.fetchall()
        finally:
            conn.close()
        html = _build_html_detail(income_rows, expense_rows)
        self._present('รายละเอียด', html)

    # ── 4. หมวดหมู่รายรับ ────────────────────────────────

    def show_category_income(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM category_income ORDER BY name")
            rows = cur.fetchall()
        finally:
            conn.close()
        html = _build_html_lookup('หมวดหมู่รายรับ', rows, 'ยังไม่มีหมวดหมู่รายรับ')
        self._present('หมวดหมู่รายรับ', html)

    # ── 5. หมวดหมู่รายจ่าย ───────────────────────────────

    def show_category_expense(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM category_expense ORDER BY name")
            rows = cur.fetchall()
        finally:
            conn.close()
        html = _build_html_lookup('หมวดหมู่รายจ่าย', rows, 'ยังไม่มีหมวดหมู่รายจ่าย')
        self._present('หมวดหมู่รายจ่าย', html)