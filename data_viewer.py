# data_viewer.py
# ใช้งานใน Pythonista บน iPhone/iPad
# วิธีเรียกใช้:
#   import data_viewer
#   viewer = data_viewer.DataViewer(db_path)
#   viewer.show_income()      # แสดงรายรับทั้งหมด
#   viewer.show_expense()     # แสดงรายจ่ายทั้งหมด

import ui
import sqlite3


# -------------------------------------------------------
# สร้าง HTML table สำหรับแสดงผล
# -------------------------------------------------------

def _escape(text):
    """escape HTML special characters"""
    text = str(text) if text is not None else ''
    text = text.strip()
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _build_html(title, rows, empty_msg):
    """
    สร้าง HTML page แสดงข้อมูลเป็นตาราง
    rows = list of (date, detail, category, amount, note)
    """
    # สร้างแถวข้อมูล
    if rows:
        row_html = ''
        for i, (date, detail, category, amount, note) in enumerate(rows):
            try:
                amount_str = f"{float(amount):,.2f}"
            except (TypeError, ValueError):
                amount_str = ''

            stripe = 'class="stripe"' if i % 2 == 1 else ''
            row_html += f'''
            <tr {stripe}>
                <td class="date">{_escape(date)}</td>
                <td class="detail">{_escape(detail)}</td>
                <td class="category">{_escape(category)}</td>
                <td class="amount">{amount_str}</td>
                <td class="note">{_escape(note)}</td>
            </tr>'''
        record_count = len(rows)
    else:
        row_html = f'<tr><td colspan="5" class="empty">{empty_msg}</td></tr>'
        record_count = 0

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #1c1c1e;
    color: #e5e5ea;
    font-family: -apple-system, "Helvetica Neue", sans-serif;
    font-size: 14px;
    padding: 8px;
  }}

  h2 {{
    text-align: center;
    font-size: 17px;
    font-weight: bold;
    padding: 10px 0 12px 0;
    color: #ffffff;
  }}

  .table-wrap {{
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 8px;
  }}

  table {{
    border-collapse: collapse;
    width: 100%;
    min-width: 560px;
    background: #2c2c2e;
  }}

  thead tr {{
    background: #3a3a3c;
    border-bottom: 2px solid #555;
  }}

  th {{
    padding: 10px 10px;
    text-align: left;
    font-size: 13px;
    color: #ebebf5cc;
    white-space: nowrap;
  }}

  th.amount {{ text-align: right; }}

  td {{
    padding: 8px 10px;
    vertical-align: top;
    border-bottom: 1px solid #3a3a3c;
    font-size: 14px;
    color: #e5e5ea;
  }}

  tr.stripe td {{ background: #323234; }}

  td.date     {{ white-space: nowrap; color: #98989f; font-size: 13px; }}
  td.amount   {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
  td.note     {{ color: #98989f; font-size: 13px; }}
  td.empty    {{ text-align: center; padding: 24px; color: #636366; }}

  .footer {{
    text-align: center;
    padding: 12px 0 6px 0;
    font-size: 12px;
    color: #636366;
  }}
</style>
</head>
<body>
  <h2>{_escape(title)}</h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>วันที่</th>
          <th>รายการ</th>
          <th>หมวดหมู่</th>
          <th class="amount">จำนวนเงิน</th>
          <th>หมายเหตุ</th>
        </tr>
      </thead>
      <tbody>
        {row_html}
      </tbody>
    </table>
  </div>
  <div class="footer">ทั้งหมด {record_count} รายการ</div>
</body>
</html>'''
    return html


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

    # ── 1. แสดงรายรับทั้งหมด ─────────────────────────────

    def show_income(self):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    i.date,
                    i.detail_text,
                    COALESCE(ci.name, '') AS category,
                    i.amount,
                    COALESCE(i.note, '')
                FROM income i
                LEFT JOIN category_income ci ON i.category_id = ci.id
                ORDER BY i.date DESC, i.id DESC
            ''')
            rows = cursor.fetchall()
        finally:
            conn.close()

        html = _build_html('รายรับทั้งหมด', rows, 'ยังไม่มีข้อมูลรายรับ')
        self._present('รายรับทั้งหมด', html)

    # ── 2. แสดงรายจ่ายทั้งหมด ────────────────────────────

    def show_expense(self):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    e.date,
                    e.detail_text,
                    COALESCE(ce.name, '') AS category,
                    e.amount,
                    COALESCE(e.note, '')
                FROM expense e
                LEFT JOIN category_expense ce ON e.category_id = ce.id
                ORDER BY e.date DESC, e.id DESC
            ''')
            rows = cursor.fetchall()
        finally:
            conn.close()

        html = _build_html('รายจ่ายทั้งหมด', rows, 'ยังไม่มีข้อมูลรายจ่าย')
        self._present('รายจ่ายทั้งหมด', html)

    # ── 3-5. สำรองไว้สำหรับ function ถัดไป ───────────────

    def show_detail_master(self):
        pass   # จะเพิ่มในภายหลัง

    def show_category_income(self):
        pass   # จะเพิ่มในภายหลัง

    def show_category_expense(self):
        pass   # จะเพิ่มในภายหลัง