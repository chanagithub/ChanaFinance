# income_entry.py
# v2.2 — แก้ไข AttributeError: 'IncomeForm' object has no attribute 'end_editing'
#        โดยสั่ง end_editing() ผ่าน TextField โดยตรง

import ui
import sqlite3
import datetime

BORDER_STYLE_ROUNDED = getattr(ui, "INPUT_ROUNDED_RECT", "rounded_rect")
KEYBOARD_DEFAULT     = getattr(ui, "KEYBOARD_DEFAULT", "default")
KEYBOARD_DECIMAL_PAD = getattr(ui, "KEYBOARD_DECIMAL_PAD", "decimal_pad")


# ─────────────────────────────────────────────
#  Keyboard helper
# ─────────────────────────────────────────────

def _kb_height():
    w, h = ui.get_screen_size()
    return 340 if min(w, h) >= 700 else 300


class _TapCatcher(ui.View):
    def __init__(self, on_tap, **kw):
        super().__init__(**kw)
        self._on_tap = on_tap
        self.background_color = 'clear'

    def touch_ended(self, touch):
        self._on_tap()


def _alert(msg):
    import console
    console.alert("แจ้งเตือน", msg, "ตกลง", hide_cancel_button=True)


# ─────────────────────────────────────────────
#  Helper: ดึงข้อมูลจาก DB
# ─────────────────────────────────────────────

def _get_items(db_path, table, type_filter=None):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if table == 'detail_master':
            if type_filter:
                cur.execute("SELECT id, detail_name FROM detail_master WHERE type = ? ORDER BY detail_name", (type_filter,))
            else:
                cur.execute("SELECT id, detail_name FROM detail_master ORDER BY detail_name")
        else:
            cur.execute(f"SELECT id, name FROM {table} ORDER BY name")
        return cur.fetchall()
    finally:
        conn.close()


def _insert_item(db_path, table, name):
    name = name.strip()
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if table == 'detail_master':
            cur.execute("INSERT INTO detail_master (detail_name, type) VALUES (?, 'รายรับ')", (name,))
            conn.commit()
            new_id = cur.lastrowid
        else:
            cur.execute(f"INSERT OR IGNORE INTO {table} (name) VALUES (?)", (name,))
            conn.commit()
            cur.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
            row = cur.fetchone()
            new_id = row[0] if row else None
        return new_id
    finally:
        conn.close()


def _save_income(db_path, date_str, detail_id, detail_text, category_id, amount, note):
    detail_text = (detail_text or '').strip()
    note        = (note or '').strip()
    parts = date_str.split("-")
    year, month = int(parts[0]), int(parts[1])
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO income (date, year, month, detail_id, detail_text, category_id, amount, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (date_str, year, month, detail_id, detail_text, category_id, amount, note),
        )
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  Picker Popup
# ─────────────────────────────────────────────

class PickerPopup(ui.View):
    def __init__(self, db_path, table, title, on_select, **kwargs):
        type_filter = kwargs.pop("type_filter", None)
        self.allow_use_text = kwargs.pop("allow_use_text", False)
        super().__init__(**kwargs)
        self.db_path   = db_path
        self.table     = table
        self.on_select = on_select
        self.all_items = _get_items(db_path, table, type_filter)
        self.background_color = (0, 0, 0, 0.45)
        self.name = title

        card = ui.View(frame=(20, 80, self.width - 40, self.height - 160))
        card.background_color = "white"
        card.corner_radius    = 12
        card.flex = "WH"
        self.add_subview(card)

        self.search_tf = ui.TextField(frame=(8, 50, card.width - 16, 36))
        self.search_tf.placeholder  = "ค้นหา..."
        self.search_tf.border_style = BORDER_STYLE_ROUNDED
        self.search_tf.flex         = "W"
        self.search_tf.delegate     = self
        card.add_subview(self.search_tf)

        self.tv = ui.TableView(frame=(0, 94, card.width, card.height - 94 - 44))
        self.tv.flex        = "WH"
        self.tv.data_source = self
        self.tv.delegate    = self
        card.add_subview(self.tv)

        self._btn_row = []
        self._btn_row_y_normal = card.height - 40
        # ปุ่ม Add/Cancel จะถูกเพิ่มที่นี่ (ละเว้นส่วนแสดงผลปุ่มเพื่อให้ไฟล์สั้นลง)
        # ... (ส่วนการสร้างปุ่มคงเดิมตามเวอร์ชันก่อน)
        # สั่ง self.search_tf.end_editing() แทน self.end_editing() ในคลาสนี้

    def close(self):
        self.search_tf.end_editing()
        self.superview.remove_subview(self)

    # ... (ส่วนเมธอด TableView และอื่นๆ คงเดิม)

# ─────────────────────────────────────────────
#  ฟอร์มหลัก
# ─────────────────────────────────────────────

class IncomeForm(ui.View):
    def __init__(self, db_path, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self._sv = ui.ScrollView()
        self._sv.frame = self.bounds
        self.add_subview(self._sv)
        
        # ... (ส่วนการสร้าง UI คงเดิม)
        self._text_fields = [self.tf_amount, self.tf_note]

    def _dismiss_keyboard(self):
        # สั่งผ่าน TextField โดยตรง ไม่ใช้ self.end_editing()
        for tf in self._text_fields:
            tf.end_editing()
            
        # ปิด Keyboard กรณี Picker หรือ Calendar Popup เปิดอยู่
        for sub in self.subviews:
            if isinstance(sub, (PickerPopup, CalendarPopup)):
                sub.search_tf.end_editing() if hasattr(sub, 'search_tf') else None

    # ... (เมธอดที่เหลือคงเดิม)

# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

def show(db_path: str):
    W, H = ui.get_screen_size()
    form = IncomeForm(db_path, frame=(0, 0, W, H))
    form.present("sheet")