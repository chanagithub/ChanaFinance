# data_viewer.py
# ใช้งานใน Pythonista บน iPhone/iPad
# วิธีเรียกใช้:
#   import data_viewer
#   viewer = data_viewer.DataViewer(db_path)
#   viewer.show_income()      # แสดงรายรับทั้งหมด
#   viewer.show_expense()     # แสดงรายจ่ายทั้งหมด

import ui
import sqlite3
import unicodedata


# ---- ความกว้างคอลัมน์ (หน่วย: monospace column) ----
COL_DATE     = 12   # วันที่
COL_DETAIL   = 22   # รายการ
COL_CATEGORY = 16   # หมวดหมู่
COL_AMOUNT   = 14   # จำนวนเงิน (right-align)
COL_NOTE     = 20   # หมายเหตุ

SEP = " | "         # ตัวคั่นคอลัมน์


# -------------------------------------------------------
# ฟังก์ชันนับความกว้างตัวอักษร (รองรับภาษาไทย)
# -------------------------------------------------------

def _char_width(ch):
    """
    คืนความกว้างของตัวอักษร 1 ตัวในหน่วย monospace column:
      - Combining characters (สระ/วรรณยุกต์ ทั้งภาษาไทยและ Unicode อื่น) -> 0
      - ตัวอักษรทั่วไป (รวมถึงตัวอักษรไทยพื้นฐาน) -> 1
    หมายเหตุ: ใช้ 1 ต่อตัวอักษรไทย เพราะ Menlo/Courier บน iOS
    render ตัวไทยกว้างเท่า Latin ไม่ใช่ double-width
    """
    cat = unicodedata.category(ch)
    # Mn = Non-spacing mark (สระลอย, วรรณยุกต์)
    # Mc = Spacing combining mark
    # Me = Enclosing mark
    if cat.startswith('M'):
        return 0
    return 1


def _display_width(s):
    """นับความกว้างรวมของ string โดยไม่นับ combining characters"""
    return sum(_char_width(ch) for ch in s)


def _pad(text, width, align='left'):
    """
    ตัด/เติม string ให้ได้ความกว้าง `width` columns
    กรอง combining characters (สระ/วรรณยุกต์) ออกจากการนับ
    เพื่อให้คอลัมน์ตรงกันในทุกบรรทัด
    """
    text = str(text) if text is not None else ''

    dw = _display_width(text)

    # ตัดถ้ายาวเกิน (เหลือที่ไว้ 1 column สำหรับ '...')
    if dw > width:
        result = ''
        w = 0
        for ch in text:
            cw = _char_width(ch)
            if cw == 0:
                # combining character ใส่ได้เสมอ ไม่กระทบความกว้าง
                result += ch
                continue
            if w + cw > width - 1:
                break
            result += ch
            w += cw
        text = result + '…'
        dw = _display_width(text)

    pad_size = width - dw
    if align == 'right':
        return ' ' * pad_size + text
    else:
        return text + ' ' * pad_size


def _format_amount(amount):
    try:
        return f"{float(amount):>13,.2f}"
    except (TypeError, ValueError):
        return _pad('', COL_AMOUNT)


def _build_header():
    parts = [
        _pad('วันที่',     COL_DATE),
        _pad('รายการ',    COL_DETAIL),
        _pad('หมวดหมู่',  COL_CATEGORY),
        _pad('จำนวนเงิน', COL_AMOUNT, 'right'),
        _pad('หมายเหตุ',  COL_NOTE),
    ]
    header = SEP.join(parts)
    divider = '-' * _display_width(header)
    return header + '\n' + divider


def _build_row(date, detail, category, amount, note):
    parts = [
        _pad(date,     COL_DATE),
        _pad(detail,   COL_DETAIL),
        _pad(category, COL_CATEGORY),
        _format_amount(amount),
        _pad(note,     COL_NOTE),
    ]
    return SEP.join(parts)


# -------------------------------------------------------
# ResultView — หน้าต่างแสดงผล fullscreen
# -------------------------------------------------------
class _ResultView(ui.View):

    def __init__(self, title, content_text):
        super().__init__()
        self.name = title
        self.background_color = '#1c1c1e'

        # --- Title bar ---
        title_lbl = ui.Label()
        title_lbl.text = title
        title_lbl.font = ('<system-bold>', 17)
        title_lbl.text_color = 'white'
        title_lbl.alignment = ui.ALIGN_CENTER
        title_lbl.flex = 'W'
        self.add_subview(title_lbl)
        self._title_lbl = title_lbl

        # --- TextView ---
        tv = ui.TextView()
        tv.text = content_text
        tv.font = ('Menlo', 11)
        tv.text_color = '#e5e5ea'
        tv.background_color = '#2c2c2e'
        tv.editable = False
        tv.flex = 'WH'
        self.add_subview(tv)
        self._tv = tv

        # --- Record count label ---
        count_lbl = ui.Label()
        count_lbl.font = ('<system>', 12)
        count_lbl.text_color = '#8e8e93'
        count_lbl.alignment = ui.ALIGN_CENTER
        count_lbl.flex = 'W'
        self.add_subview(count_lbl)
        self._count_lbl = count_lbl

        # นับจำนวน record (บรรทัดที่ไม่ใช่ header, divider, หรือว่าง)
        lines = [l for l in content_text.splitlines()
                 if l.strip() and not l.startswith('-')]
        record_count = max(0, len(lines) - 1)   # ลบ header 1 บรรทัด
        count_lbl.text = f'ทั้งหมด {record_count} รายการ'

    def layout(self):
        W, H = self.width, self.height
        margin = 12
        title_h = 44
        count_h = 28

        self._title_lbl.frame = (0, 0, W, title_h)
        self._count_lbl.frame = (0, H - count_h, W, count_h)
        self._tv.frame = (margin, title_h + 4,
                          W - margin * 2,
                          H - title_h - count_h - 8)


# -------------------------------------------------------
# DataViewer — คลาสหลัก
# -------------------------------------------------------
class DataViewer:

    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _present(self, title, lines):
        content = '\n'.join(lines)
        v = _ResultView(title, content)
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

        lines = [_build_header()]
        if rows:
            for date, detail, category, amount, note in rows:
                lines.append(_build_row(date, detail, category, amount, note))
        else:
            lines.append('  (ยังไม่มีข้อมูลรายรับ)')

        self._present('รายรับทั้งหมด', lines)

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

        lines = [_build_header()]
        if rows:
            for date, detail, category, amount, note in rows:
                lines.append(_build_row(date, detail, category, amount, note))
        else:
            lines.append('  (ยังไม่มีข้อมูลรายจ่าย)')

        self._present('รายจ่ายทั้งหมด', lines)

    # ── 3-5. สำรองไว้สำหรับ function ถัดไป ───────────────

    def show_detail_master(self):
        pass   # จะเพิ่มในภายหลัง

    def show_category_income(self):
        pass   # จะเพิ่มในภายหลัง

    def show_category_expense(self):
        pass   # จะเพิ่มในภายหลัง