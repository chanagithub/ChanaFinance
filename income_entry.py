# income_entry.py
# ใช้งานใน Pythonista บน iPhone
# วิธีเรียกใช้: import income_entry; income_entry.show(db_path)

import ui
import sqlite3
import datetime

BORDER_STYLE_ROUNDED = getattr(ui, "INPUT_ROUNDED_RECT", "rounded_rect")
KEYBOARD_DEFAULT = getattr(ui, "KEYBOARD_DEFAULT", "default")
KEYBOARD_DECIMAL_PAD = getattr(ui, "KEYBOARD_DECIMAL_PAD", "decimal_pad")


# ─────────────────────────────────────────────
#  Helper: ดึงข้อมูลจาก DB
# ─────────────────────────────────────────────

def _get_items(db_path, table, type_filter=None):
    """
    ดึง (id, name) จากตาราง
    - table = 'detail_master' : ใช้ column detail_name และกรอง type ได้
    - ตารางอื่น               : ใช้ column name ตามปกติ
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if table == 'detail_master':
            if type_filter:
                cur.execute(
                    "SELECT id, detail_name FROM detail_master WHERE type = ? ORDER BY detail_name",
                    (type_filter,)
                )
            else:
                cur.execute("SELECT id, detail_name FROM detail_master ORDER BY detail_name")
        else:
            cur.execute(f"SELECT id, name FROM {table} ORDER BY name")
        return cur.fetchall()  # [(id, name), ...]
    finally:
        conn.close()


def _insert_item(db_path, table, name):
    """
    เพิ่มรายการใหม่
    - table = 'detail_master' : insert พร้อม type = 'รายรับ'
    - ตารางอื่น               : insert ปกติ
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if table == 'detail_master':
            cur.execute(
                "INSERT INTO detail_master (detail_name, type) VALUES (?, 'รายรับ')",
                (name,)
            )
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


def _save_income(db_path, date_str, detail_id, category_id, amount, note):
    parts = date_str.split("-")
    year, month = int(parts[0]), int(parts[1])
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO income (date, year, month, detail_id, category_id, amount, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date_str, year, month, detail_id, category_id, amount, note),
        )
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  Picker Popup (TableView ลอยอยู่บน View หลัก)
# ─────────────────────────────────────────────

class PickerPopup(ui.View):
    """
    Popup สำหรับเลือกรายการหรือพิมพ์รายการใหม่
    on_select(id, name) จะถูกเรียกเมื่อผู้ใช้เลือก/สร้างรายการ
    """

    def __init__(self, db_path, table, title, on_select, **kwargs):
        type_filter = kwargs.pop("type_filter", None)
        super().__init__(**kwargs)
        self.db_path = db_path
        self.table = table
        self.on_select = on_select
        self.all_items = _get_items(db_path, table, type_filter)  # [(id, name)]

        self.background_color = (0, 0, 0, 0.45)
        self.name = title

        # กล่องกลาง
        card = ui.View(frame=(20, 80, self.width - 40, self.height - 160))
        card.background_color = "white"
        card.corner_radius = 12
        card.flex = "WH"
        self.add_subview(card)

        # หัวข้อ
        lbl = ui.Label(frame=(0, 0, card.width, 44))
        lbl.text = title
        lbl.font = ("<system-bold>", 17)
        lbl.text_color = "black"
        lbl.alignment = ui.ALIGN_CENTER
        lbl.flex = "W"
        card.add_subview(lbl)

        # ช่องค้นหา / พิมพ์ใหม่
        self.search_tf = ui.TextField(frame=(8, 50, card.width - 16, 36))
        self.search_tf.placeholder = "ค้นหาหรือพิมพ์รายการใหม่..."
        self.search_tf.border_style = BORDER_STYLE_ROUNDED
        self.search_tf.flex = "W"
        self.search_tf.delegate = self
        card.add_subview(self.search_tf)

        # TableView
        self.tv = ui.TableView(frame=(0, 94, card.width, card.height - 94 - 44))
        self.tv.flex = "WH"
        self.tv.data_source = self
        self.tv.delegate = self
        self.tv.separator_color = "#eeeeee"
        card.add_subview(self.tv)

        # ปุ่มล่าง
        btn_add = ui.Button(frame=(8, card.height - 40, (card.width - 24) / 2, 36))
        btn_add.title = "➕ เพิ่มรายการนี้"
        btn_add.background_color = "#4CAF50"
        btn_add.tint_color = "white"
        btn_add.corner_radius = 8
        btn_add.action = self._add_new
        btn_add.flex = "W"
        card.add_subview(btn_add)

        btn_cancel = ui.Button(
            frame=(btn_add.width + 16, card.height - 40, (card.width - 24) / 2, 36)
        )
        btn_cancel.title = "ยกเลิก"
        btn_cancel.background_color = "#9E9E9E"
        btn_cancel.tint_color = "white"
        btn_cancel.corner_radius = 8
        btn_cancel.action = self._cancel
        btn_cancel.flex = "W"
        card.add_subview(btn_cancel)

        self.card = card
        self._filtered = list(self.all_items)

    # --- TableView DataSource ---
    def tableview_number_of_rows(self, tv, section):
        return len(self._filtered)

    def tableview_cell_for_row(self, tv, section, row):
        cell = ui.TableViewCell()
        cell.text_label.text = self._filtered[row][1]
        return cell

    def tableview_did_select(self, tv, section, row):
        item = self._filtered[row]
        self.on_select(item[0], item[1])
        self.close()

    # --- TextField Delegate ---
    def textfield_should_change(self, tf, range_, replacement):
        return True

    def textfield_did_change(self, tf):
        q = tf.text.strip().lower()
        if q:
            self._filtered = [i for i in self.all_items if q in i[1].lower()]
        else:
            self._filtered = list(self.all_items)
        self.tv.reload()

    def _add_new(self, sender):
        name = self.search_tf.text.strip()
        if not name:
            _alert("กรุณาพิมพ์ชื่อรายการก่อน")
            return
        new_id = _insert_item(self.db_path, self.table, name)
        if new_id is None:
            _alert("ไม่สามารถเพิ่มรายการได้")
            return
        self.on_select(new_id, name)
        self.close()

    def _cancel(self, sender):
        self.close()

    def close(self):
        self.superview.remove_subview(self)


# ─────────────────────────────────────────────
#  Calendar Popup
# ─────────────────────────────────────────────

class CalendarPopup(ui.View):
    """
    ปฏิทินแบบง่าย: เลือกปี/เดือน แล้วแตะวัน
    on_date(date_str "YYYY-MM-DD") จะถูกเรียก
    """

    def __init__(self, current_date_str, on_date, **kwargs):
        super().__init__(**kwargs)
        self.on_date = on_date
        self.background_color = (0, 0, 0, 0.45)

        year, month, day = [int(part) for part in current_date_str.split("-")]
        d = datetime.date(year, month, day)
        self._year = d.year
        self._month = d.month

        card_w = min(self.width - 32, 320)
        card_h = 340
        card_x = (self.width - card_w) / 2
        card_y = (self.height - card_h) / 2

        self.card = ui.View(frame=(card_x, card_y, card_w, card_h))
        self.card.background_color = "white"
        self.card.corner_radius = 12
        self.add_subview(self.card)

        self._build_header()
        self._build_grid()

    def _build_header(self):
        card = self.card
        # ปุ่ม <
        btn_prev = ui.Button(frame=(0, 0, 44, 44))
        btn_prev.title = "‹"
        btn_prev.font = ("<system-bold>", 24)
        btn_prev.action = self._prev_month
        card.add_subview(btn_prev)

        # ป้ายเดือน/ปี
        self.lbl_month = ui.Label(frame=(44, 0, card.width - 88, 44))
        self.lbl_month.alignment = ui.ALIGN_CENTER
        self.lbl_month.font = ("<system-bold>", 16)
        card.add_subview(self.lbl_month)

        # ปุ่ม >
        btn_next = ui.Button(frame=(card.width - 44, 0, 44, 44))
        btn_next.title = "›"
        btn_next.font = ("<system-bold>", 24)
        btn_next.action = self._next_month
        card.add_subview(btn_next)

        # วันในสัปดาห์
        days = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]
        cell_w = self.card.width / 7
        for i, d in enumerate(days):
            lbl = ui.Label(frame=(i * cell_w, 44, cell_w, 28))
            lbl.text = d
            lbl.alignment = ui.ALIGN_CENTER
            lbl.font = ("<system>", 12)
            lbl.text_color = "#888888"
            self.card.add_subview(lbl)

        # ปุ่มยกเลิก
        btn_cancel = ui.Button(frame=(0, self.card.height - 36, self.card.width, 36))
        btn_cancel.title = "ยกเลิก"
        btn_cancel.tint_color = "#9E9E9E"
        btn_cancel.action = self._cancel
        self.card.add_subview(btn_cancel)

        self._day_btns = []
        self._update_header()

    def _build_grid(self):
        self._render_days()

    def _update_header(self):
        TH_MONTHS = [
            "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
        ]
        self.lbl_month.text = f"{TH_MONTHS[self._month]} {self._year + 543}"

    def _render_days(self):
        for b in self._day_btns:
            self.card.remove_subview(b)
        self._day_btns = []

        first = datetime.date(self._year, self._month, 1)
        start_wd = first.weekday()  # Monday=0; we want Sunday=0
        start_wd = (start_wd + 1) % 7

        import calendar
        _, days_in_month = calendar.monthrange(self._year, self._month)

        cell_w = self.card.width / 7
        cell_h = 36
        row_y_start = 72  # after header row + weekday row
        today = datetime.date.today()

        for day in range(1, days_in_month + 1):
            slot = start_wd + day - 1
            col = slot % 7
            row = slot // 7
            x = col * cell_w
            y = row_y_start + row * cell_h

            btn = ui.Button(frame=(x + 2, y + 2, cell_w - 4, cell_h - 4))
            btn.title = str(day)
            btn.font = ("<system>", 15)
            btn.corner_radius = (cell_w - 4) / 2

            d = datetime.date(self._year, self._month, day)
            if d == today:
                btn.background_color = "#1976D2"
                btn.tint_color = "white"
            else:
                btn.background_color = "clear"
                btn.tint_color = "black"

            btn.action = self._day_tapped
            self.card.add_subview(btn)
            self._day_btns.append(btn)

    def _day_tapped(self, sender):
        day = int(sender.title)
        date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
        self.on_date(date_str)
        self._close()

    def _prev_month(self, sender):
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._update_header()
        self._render_days()

    def _next_month(self, sender):
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._update_header()
        self._render_days()

    def _cancel(self, sender):
        self._close()

    def _close(self):
        self.superview.remove_subview(self)


# ─────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────

def _alert(msg):
    import console
    console.alert("แจ้งเตือน", msg, "ตกลง", hide_cancel_button=True)


# ─────────────────────────────────────────────
#  ฟอร์มหลัก
# ─────────────────────────────────────────────

class IncomeForm(ui.View):

    def __init__(self, db_path, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.background_color = "#F5F7FA"
        self.name = "บันทึกรายรับ"

        self._selected_detail_id = None
        self._selected_category_id = None
        self._date_str = datetime.date.today().isoformat()

        self._build_ui()

    def _build_ui(self):
        W = self.width
        pad = 16
        field_h = 44
        y = 60

        def section_label(text, y_pos):
            lbl = ui.Label(frame=(pad, y_pos, W - pad * 2, 22))
            lbl.text = text
            lbl.font = ("<system>", 13)
            lbl.text_color = "#888888"
            self.add_subview(lbl)

        def make_field(placeholder, y_pos, keyboard=KEYBOARD_DEFAULT):
            tf = ui.TextField(frame=(pad, y_pos, W - pad * 2, field_h))
            tf.placeholder = placeholder
            tf.border_style = BORDER_STYLE_ROUNDED
            tf.background_color = "white"
            tf.keyboard_type = keyboard
            tf.flex = "W"
            self.add_subview(tf)
            return tf

        def make_btn(title, y_pos, color="#ECEFF1"):
            btn = ui.Button(frame=(pad, y_pos, W - pad * 2, field_h))
            btn.title = title
            btn.background_color = color
            btn.tint_color = "#333333"
            btn.corner_radius = 8
            # ใช้ title_insets เพื่อเว้นซ้าย
            btn.flex = "W"
            self.add_subview(btn)
            return btn

        # ── วันที่ ──
        section_label("วันที่", y)
        y += 24
        self.btn_date = make_btn(f"📅  {self._date_str}", y, "#FFFFFF")
        self.btn_date.border_width = 1
        self.btn_date.border_color = "#CCCCCC"
        self.btn_date.action = self._open_calendar
        y += field_h + 16

        # ── รายละเอียด ──
        section_label("รายละเอียด", y)
        y += 24
        self.btn_detail = make_btn("แตะเพื่อเลือกรายละเอียด...", y)
        self.btn_detail.action = self._open_detail_picker
        y += field_h + 16

        # ── หมวดหมู่ ──
        section_label("หมวดหมู่", y)
        y += 24
        self.btn_category = make_btn("แตะเพื่อเลือกหมวดหมู่...", y)
        self.btn_category.action = self._open_category_picker
        y += field_h + 16

        # ── จำนวนเงิน ──
        section_label("จำนวนเงิน (บาท)", y)
        y += 24
        self.tf_amount = make_btn("", y, "#FFFFFF")
        # ใช้ TextField แทน
        self.remove_subview(self.tf_amount)
        self.tf_amount = ui.TextField(frame=(pad, y, W - pad * 2, field_h))
        self.tf_amount.placeholder = "0.00"
        self.tf_amount.border_style = BORDER_STYLE_ROUNDED
        self.tf_amount.background_color = "white"
        self.tf_amount.keyboard_type = KEYBOARD_DECIMAL_PAD
        self.tf_amount.flex = "W"
        self.add_subview(self.tf_amount)
        y += field_h + 16

        # ── หมายเหตุ ──
        section_label("หมายเหตุ (ถ้ามี)", y)
        y += 24
        self.tf_note = make_field("หมายเหตุ...", y)
        y += field_h + 24

        # ── ปุ่ม Save ──
        btn_save = ui.Button(frame=(pad, y, W - pad * 2, 50))
        btn_save.title = "💾  บันทึกรายรับ"
        btn_save.background_color = "#43A047"
        btn_save.tint_color = "white"
        btn_save.font = ("<system-bold>", 17)
        btn_save.corner_radius = 10
        btn_save.flex = "W"
        btn_save.action = self._save
        self.add_subview(btn_save)

    # ── Calendar ──
    def _open_calendar(self, sender):
        popup = CalendarPopup(
            self._date_str,
            on_date=self._on_date_selected,
            frame=self.bounds,
        )
        self.add_subview(popup)

    def _on_date_selected(self, date_str):
        self._date_str = date_str
        self.btn_date.title = f"📅  {date_str}"

    # ── Detail Picker ──
    def _open_detail_picker(self, sender):
        popup = PickerPopup(
            self.db_path,
            "detail_master",
            "เลือกรายละเอียด",
            on_select=self._on_detail_selected,
            frame=self.bounds,
            type_filter="รายรับ",
        )
        self.add_subview(popup)

    def _on_detail_selected(self, item_id, name):
        self._selected_detail_id = item_id
        self.btn_detail.title = f"✔  {name}"
        self.btn_detail.tint_color = "#1B5E20"

    # ── Category Picker ──
    def _open_category_picker(self, sender):
        popup = PickerPopup(
            self.db_path,
            "category_income",
            "เลือกหมวดหมู่",
            on_select=self._on_category_selected,
            frame=self.bounds,
        )
        self.add_subview(popup)

    def _on_category_selected(self, item_id, name):
        self._selected_category_id = item_id
        self.btn_category.title = f"✔  {name}"
        self.btn_category.tint_color = "#1B5E20"

    # ── Save ──
    def _save(self, sender):
        if self._selected_detail_id is None:
            _alert("กรุณาเลือกรายละเอียด")
            return
        if self._selected_category_id is None:
            _alert("กรุณาเลือกหมวดหมู่")
            return
        amount_str = self.tf_amount.text.strip()
        if not amount_str:
            _alert("กรุณากรอกจำนวนเงิน")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            _alert("จำนวนเงินไม่ถูกต้อง")
            return

        note = self.tf_note.text.strip()
        _save_income(
            self.db_path,
            self._date_str,
            self._selected_detail_id,
            self._selected_category_id,
            amount,
            note,
        )
        self._reset()

    def _reset(self):
        import console
        console.hud_alert("บันทึกสำเร็จ ✓", "success", 1.2)

        self._selected_detail_id = None
        self._selected_category_id = None
        self._date_str = datetime.date.today().isoformat()

        self.btn_date.title = f"📅  {self._date_str}"
        self.btn_detail.title = "แตะเพื่อเลือกรายละเอียด..."
        self.btn_detail.tint_color = "#333333"
        self.btn_category.title = "แตะเพื่อเลือกหมวดหมู่..."
        self.btn_category.tint_color = "#333333"
        self.tf_amount.text = ""
        self.tf_note.text = ""


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

def show(db_path: str):
    """
    เรียกฟังก์ชันนี้พร้อมส่ง path ของไฟล์ฐานข้อมูล
    ตัวอย่าง:
        import income_entry
        income_entry.show('/path/to/mydb.sqlite')
    """
    form = IncomeForm(db_path, frame=(0, 0, 375, 700))
    form.present("sheet")


# ── ทดสอบ standalone ──
if __name__ == "__main__":
    import os
    TEST_DB = os.path.expanduser("~/Documents/test_finance.sqlite")

    # สร้างตารางทดสอบถ้ายังไม่มี
    conn = sqlite3.connect(TEST_DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS category_income (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS category_expense (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS payment_type (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS detail_master (
            id INTEGER PRIMARY KEY,
            detail_name TEXT,
            type TEXT CHECK(type IN ('รายรับ', 'รายจ่าย'))
        );
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, year INTEGER, month INTEGER,
            detail_id INTEGER, category_id INTEGER, amount REAL, note TEXT
        );
        CREATE TABLE IF NOT EXISTS expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, year INTEGER, month INTEGER,
            detail_id INTEGER, category_id INTEGER, payment_type_id INTEGER, amount REAL, note TEXT
        );
        INSERT OR IGNORE INTO category_income (name) VALUES ('เงินเดือน'),('โบนัส'),('รายได้พิเศษ');
        INSERT OR IGNORE INTO detail_master (detail_name, type) VALUES
            ('เงินเดือนประจำ','รายรับ'),('ค่าล่วงเวลา','รายรับ'),('ดอกเบี้ย','รายรับ');
    """)
    conn.commit()
    conn.close()

    show(TEST_DB)
