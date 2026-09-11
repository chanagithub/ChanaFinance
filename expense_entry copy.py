# expense_entry.py
# ใช้งานใน Pythonista บน iPhone / iPad
# วิธีเรียกใช้: import expense_entry; expense_entry.show(db_path)

import ui
import sqlite3
import datetime

BORDER_STYLE_ROUNDED = getattr(ui, "INPUT_ROUNDED_RECT", "rounded_rect")
KEYBOARD_DEFAULT     = getattr(ui, "KEYBOARD_DEFAULT",     "default")
KEYBOARD_DECIMAL_PAD = getattr(ui, "KEYBOARD_DECIMAL_PAD", "decimal_pad")


# ─────────────────────────────────────────────
#  Helper: ดึงข้อมูลจาก DB
# ─────────────────────────────────────────────

def _get_items(db_path, table, type_filter=None):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if table == "detail_master":
            if type_filter:
                cur.execute(
                    "SELECT id, detail_name FROM detail_master WHERE type = ? ORDER BY detail_name",
                    (type_filter,),
                )
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
        if table == "detail_master":
            cur.execute(
                "INSERT INTO detail_master (detail_name, type) VALUES (?, 'รายจ่าย')",
                (name,),
            )
            conn.commit()
            return cur.lastrowid
        else:
            cur.execute(f"INSERT OR IGNORE INTO {table} (name) VALUES (?)", (name,))
            conn.commit()
            cur.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def _save_expense(db_path, date_str, detail_id, detail_text,
                  category_id, payment_type_id, amount, note):
    detail_text = (detail_text or '').strip()
    note        = (note or '').strip()
    parts = date_str.split("-")
    year, month = int(parts[0]), int(parts[1])
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expense "
            "(date, year, month, detail_id, detail_text, category_id, payment_type_id, amount, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (date_str, year, month, detail_id, detail_text,
             category_id, payment_type_id, amount, note),
        )
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  Picker Popup
# ─────────────────────────────────────────────

class PickerPopup(ui.View):

    def __init__(self, db_path, table, title, on_select, **kwargs):
        type_filter         = kwargs.pop("type_filter", None)
        self.allow_use_text = kwargs.pop("allow_use_text", False)
        super().__init__(**kwargs)

        self.db_path   = db_path
        self.table     = table
        self.on_select = on_select
        self.all_items = _get_items(db_path, table, type_filter)

        self.background_color = (0, 0, 0, 0.45)
        self.name = title

        card_w = min(self.width - 40, 480)
        card_h = min(self.height - 160, 520)
        card_x = (self.width  - card_w) / 2
        card_y = (self.height - card_h) / 2

        card = ui.View(frame=(card_x, card_y, card_w, card_h))
        card.background_color = "white"
        card.corner_radius    = 14
        self.add_subview(card)

        lbl = ui.Label(frame=(0, 0, card_w, 48))
        lbl.text       = title
        lbl.font       = ("<system-bold>", 17)
        lbl.text_color = "black"
        lbl.alignment  = ui.ALIGN_CENTER
        lbl.flex       = "W"
        card.add_subview(lbl)

        self.search_tf = ui.TextField(frame=(8, 54, card_w - 16, 38))
        self.search_tf.placeholder  = "ค้นหาหรือพิมพ์รายการใหม่..."
        self.search_tf.border_style = BORDER_STYLE_ROUNDED
        self.search_tf.flex         = "W"
        self.search_tf.delegate     = self
        card.add_subview(self.search_tf)

        btn_area_h = 48
        self.tv = ui.TableView(frame=(0, 100, card_w, card_h - 100 - btn_area_h))
        self.tv.flex            = "WH"
        self.tv.data_source     = self
        self.tv.delegate        = self
        self.tv.separator_color = "#eeeeee"
        card.add_subview(self.tv)

        btn_y  = card_h - btn_area_h + 6
        margin = 8

        if self.allow_use_text:
            n_btn = 3
            btn_w = (card_w - margin * (n_btn + 1)) / n_btn

            btn_use = ui.Button(frame=(margin, btn_y, btn_w, 36))
            btn_use.title            = "ใช้ครั้งนี้"
            btn_use.background_color = "#1976D2"
            btn_use.tint_color       = "white"
            btn_use.corner_radius    = 8
            btn_use.action           = self._use_text
            btn_use.flex             = "W"
            card.add_subview(btn_use)

            x_add    = margin * 2 + btn_w
            x_cancel = margin * 3 + btn_w * 2
        else:
            n_btn    = 2
            btn_w    = (card_w - margin * (n_btn + 1)) / n_btn
            x_add    = margin
            x_cancel = margin * 2 + btn_w

        btn_add = ui.Button(frame=(x_add, btn_y, btn_w, 36))
        btn_add.title            = "เพิ่มรายการนี้"
        btn_add.background_color = "#4CAF50"
        btn_add.tint_color       = "white"
        btn_add.corner_radius    = 8
        btn_add.action           = self._add_new
        btn_add.flex             = "W"
        card.add_subview(btn_add)

        btn_cancel = ui.Button(frame=(x_cancel, btn_y, btn_w, 36))
        btn_cancel.title            = "ยกเลิก"
        btn_cancel.background_color = "#9E9E9E"
        btn_cancel.tint_color       = "white"
        btn_cancel.corner_radius    = 8
        btn_cancel.action           = self._cancel
        btn_cancel.flex             = "W"
        card.add_subview(btn_cancel)

        self.card      = card
        self._filtered = list(self.all_items)

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

    def textfield_should_change(self, tf, range_, replacement):
        return True

    def textfield_did_change(self, tf):
        q = tf.text.strip().lower()
        if q:
            self._filtered = [i for i in self.all_items if q in i[1].lower()]
        else:
            self._filtered = list(self.all_items)
        self.tv.reload()

    def _use_text(self, sender):
        name = self.search_tf.text.strip()
        if not name:
            _alert("กรุณาพิมพ์ชื่อรายการก่อน")
            return
        self.on_select(None, name)
        self.close()

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

    def __init__(self, current_date_str, on_date, **kwargs):
        super().__init__(**kwargs)
        self.on_date = on_date
        self.background_color = (0, 0, 0, 0.45)

        year, month, day = [int(p) for p in current_date_str.split("-")]
        self._year  = year
        self._month = month

        card_w = min(self.width - 32, 340)
        card_h = 360
        card_x = (self.width  - card_w) / 2
        card_y = (self.height - card_h) / 2

        self.card = ui.View(frame=(card_x, card_y, card_w, card_h))
        self.card.background_color = "white"
        self.card.corner_radius    = 14
        self.add_subview(self.card)

        self._day_btns = []
        self._build_header()
        self._render_days()

    def _build_header(self):
        card   = self.card
        card_w = card.width

        btn_prev = ui.Button(frame=(0, 0, 44, 44))
        btn_prev.title  = "‹"
        btn_prev.font   = ("<system-bold>", 24)
        btn_prev.action = self._prev_month
        card.add_subview(btn_prev)

        self.lbl_month = ui.Label(frame=(44, 0, card_w - 88, 44))
        self.lbl_month.alignment = ui.ALIGN_CENTER
        self.lbl_month.font      = ("<system-bold>", 16)
        card.add_subview(self.lbl_month)

        btn_next = ui.Button(frame=(card_w - 44, 0, 44, 44))
        btn_next.title  = "›"
        btn_next.font   = ("<system-bold>", 24)
        btn_next.action = self._next_month
        card.add_subview(btn_next)

        days   = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]
        cell_w = card_w / 7
        for i, d in enumerate(days):
            lbl = ui.Label(frame=(i * cell_w, 44, cell_w, 28))
            lbl.text       = d
            lbl.alignment  = ui.ALIGN_CENTER
            lbl.font       = ("<system>", 12)
            lbl.text_color = "#888888"
            card.add_subview(lbl)

        btn_cancel = ui.Button(frame=(0, card.height - 38, card_w, 38))
        btn_cancel.title      = "ยกเลิก"
        btn_cancel.tint_color = "#9E9E9E"
        btn_cancel.action     = self._cancel
        card.add_subview(btn_cancel)

        self._update_header()

    def _update_header(self):
        TH_MONTHS = [
            "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
            "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
            "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
        ]
        self.lbl_month.text = f"{TH_MONTHS[self._month]} {self._year + 543}"

    def _render_days(self):
        for b in self._day_btns:
            self.card.remove_subview(b)
        self._day_btns = []

        import calendar
        first     = datetime.date(self._year, self._month, 1)
        start_wd  = (first.weekday() + 1) % 7
        _, n_days = calendar.monthrange(self._year, self._month)

        card_w      = self.card.width
        cell_w      = card_w / 7
        cell_h      = 36
        row_y_start = 72
        today       = datetime.date.today()

        for day in range(1, n_days + 1):
            slot = start_wd + day - 1
            col  = slot % 7
            row  = slot // 7
            x    = col * cell_w
            y    = row_y_start + row * cell_h

            btn = ui.Button(frame=(x + 2, y + 2, cell_w - 4, cell_h - 4))
            btn.title         = str(day)
            btn.font          = ("<system>", 15)
            btn.corner_radius = (cell_w - 4) / 2

            if datetime.date(self._year, self._month, day) == today:
                btn.background_color = "#E53935"
                btn.tint_color       = "white"
            else:
                btn.background_color = "clear"
                btn.tint_color       = "black"

            btn.action = self._day_tapped
            self.card.add_subview(btn)
            self._day_btns.append(btn)

    def _day_tapped(self, sender):
        day      = int(sender.title)
        date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
        self.on_date(date_str)
        self._close()

    def _prev_month(self, sender):
        if self._month == 1:
            self._month = 12; self._year -= 1
        else:
            self._month -= 1
        self._update_header(); self._render_days()

    def _next_month(self, sender):
        if self._month == 12:
            self._month = 1; self._year += 1
        else:
            self._month += 1
        self._update_header(); self._render_days()

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
#  ฟอร์มหลัก  (ใช้ ScrollView เพื่อหนี keyboard)
# ─────────────────────────────────────────────

class ExpenseForm(ui.View):

    def __init__(self, db_path, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.background_color = "#FFF8F8"
        self.name = "บันทึกรายจ่าย"

        self._selected_detail_id       = None
        self._selected_detail_name     = None
        self._selected_category_id     = None
        self._selected_payment_type_id = None
        self._date_str = datetime.date.today().isoformat()

        # ── ScrollView ────────────────────────────────────────
        self._sv = ui.ScrollView()
        self._sv.frame                  = self.bounds
        self._sv.flex                   = 'WH'
        self._sv.background_color       = "#FFF8F8"
        self._sv.always_bounce_vertical = True
        self.add_subview(self._sv)

        self._build_ui()

    def _build_ui(self):
        W   = self.width or 375
        pad = 16
        f_h = 44
        gap = 14
        y   = 0

        sv = self._sv

        # Title bar
        title_lbl = ui.Label(frame=(0, y, W, 52))
        title_lbl.text             = "💸  บันทึกรายจ่าย"
        title_lbl.font             = ("<system-bold>", 20)
        title_lbl.text_color       = "#B71C1C"
        title_lbl.alignment        = ui.ALIGN_CENTER
        title_lbl.background_color = "#FFEBEE"
        title_lbl.flex             = "W"
        sv.add_subview(title_lbl)
        y += 52 + 12

        def section_label(text, y_pos):
            lbl = ui.Label(frame=(pad, y_pos, W - pad * 2, 20))
            lbl.text       = text
            lbl.font       = ("<system>", 13)
            lbl.text_color = "#888888"
            lbl.flex       = "W"
            sv.add_subview(lbl)

        def make_picker_btn(placeholder, y_pos):
            btn = ui.Button(frame=(pad, y_pos, W - pad * 2, f_h))
            btn.title            = placeholder
            btn.background_color = "#ECEFF1"
            btn.tint_color       = "#555555"
            btn.corner_radius    = 8
            btn.flex             = "W"
            sv.add_subview(btn)
            return btn

        # วันที่
        section_label("วันที่", y); y += 22
        self.btn_date = make_picker_btn(f"📅  {self._date_str}", y)
        self.btn_date.background_color = "#FFFFFF"
        self.btn_date.border_width     = 1
        self.btn_date.border_color     = "#CCCCCC"
        self.btn_date.action           = self._open_calendar
        y += f_h + gap

        # รายละเอียด
        section_label("รายละเอียด", y); y += 22
        self.btn_detail = make_picker_btn("แตะเพื่อเลือกรายละเอียด...", y)
        self.btn_detail.action = self._open_detail_picker
        y += f_h + gap

        # หมวดหมู่
        section_label("หมวดหมู่", y); y += 22
        self.btn_category = make_picker_btn("แตะเพื่อเลือกหมวดหมู่...", y)
        self.btn_category.action = self._open_category_picker
        y += f_h + gap

        # ประเภทการชำระ
        section_label("ประเภทการชำระ", y); y += 22
        self.btn_payment = make_picker_btn("แตะเพื่อเลือกวิธีชำระเงิน...", y)
        self.btn_payment.action = self._open_payment_picker
        y += f_h + gap

        # จำนวนเงิน + ปุ่ม "หมายเหตุ"
        section_label("จำนวนเงิน (บาท)", y); y += 22
        note_btn_w = 80
        self.tf_amount = ui.TextField(
            frame=(pad, y, W - pad * 2 - note_btn_w - 8, f_h)
        )
        self.tf_amount.placeholder      = "0.00"
        self.tf_amount.border_style     = BORDER_STYLE_ROUNDED
        self.tf_amount.background_color = "white"
        self.tf_amount.keyboard_type    = KEYBOARD_DECIMAL_PAD
        self.tf_amount.flex             = "W"
        sv.add_subview(self.tf_amount)

        btn_go_note = ui.Button(
            frame=(pad + self.tf_amount.width + 8, y, note_btn_w, f_h)
        )
        btn_go_note.title            = "หมายเหตุ"
        btn_go_note.background_color = "#ECEFF1"
        btn_go_note.tint_color       = "#333333"
        btn_go_note.corner_radius    = 8
        btn_go_note.flex             = "L"
        btn_go_note.action           = self._focus_note
        sv.add_subview(btn_go_note)
        y += f_h + gap

        # หมายเหตุ
        section_label("หมายเหตุ (ถ้ามี)", y); y += 22
        self.tf_note = ui.TextField(frame=(pad, y, W - pad * 2, f_h))
        self.tf_note.placeholder      = "หมายเหตุ..."
        self.tf_note.border_style     = BORDER_STYLE_ROUNDED
        self.tf_note.background_color = "white"
        self.tf_note.flex             = "W"
        self.tf_note.delegate         = self   # ดัก begin/end editing
        sv.add_subview(self.tf_note)
        self._note_y = y   # เก็บ y ไว้คำนวณ scroll
        y += f_h + 28

        # ปุ่ม Save
        btn_save = ui.Button(frame=(pad, y, W - pad * 2, 52))
        btn_save.title            = "💾  บันทึกรายจ่าย"
        btn_save.background_color = "#E53935"
        btn_save.tint_color       = "white"
        btn_save.font             = ("<system-bold>", 17)
        btn_save.corner_radius    = 12
        btn_save.flex             = "W"
        btn_save.action           = self._save
        sv.add_subview(btn_save)
        y += 52 + 32   # padding ล่าง

        sv.content_size = (W, y)

    # ── TextField delegate (สำหรับ tf_note) ─────────────────

    def textfield_did_begin_editing(self, tf):
        """เมื่อเริ่มพิมพ์หมายเหตุ ให้เลื่อน scroll ขึ้นเพื่อหนี keyboard"""
        self._scroll_to_note()

    def textfield_did_end_editing(self, tf):
        """เมื่อปิด keyboard คืน scroll กลับตำแหน่งปกติ"""
        self._sv.content_offset = (0, 0)

    # ── Scroll helper ────────────────────────────────────────

    def _scroll_to_note(self):
        keyboard_h    = 260
        visible_h     = self.height - keyboard_h
        target_offset = self._note_y - visible_h / 2
        target_offset = max(0, target_offset)
        self._sv.content_offset = (0, target_offset)

    # ── Actions ─────────────────────────────────────────────

    def _focus_note(self, sender):
        self.tf_amount.end_editing()
        self.tf_note.begin_editing()

    def _open_calendar(self, sender):
        popup = CalendarPopup(
            self._date_str,
            on_date=self._on_date_selected,
            frame=self.bounds,
        )
        self.add_subview(popup)

    def _on_date_selected(self, date_str):
        self._date_str      = date_str
        self.btn_date.title = f"📅  {date_str}"

    def _open_detail_picker(self, sender):
        popup = PickerPopup(
            self.db_path,
            "detail_master",
            "เลือกรายละเอียด",
            on_select=self._on_detail_selected,
            frame=self.bounds,
            type_filter="รายจ่าย",
            allow_use_text=True,
        )
        self.add_subview(popup)

    def _on_detail_selected(self, item_id, name):
        self._selected_detail_id   = item_id
        self._selected_detail_name = name.strip()
        if item_id is None:
            self.btn_detail.title = f"ใช้ครั้งนี้: {name}"
        else:
            self.btn_detail.title = f"✔  {name}"
        self.btn_detail.tint_color = "#B71C1C"

    def _open_category_picker(self, sender):
        popup = PickerPopup(
            self.db_path,
            "category_expense",
            "เลือกหมวดหมู่",
            on_select=self._on_category_selected,
            frame=self.bounds,
        )
        self.add_subview(popup)

    def _on_category_selected(self, item_id, name):
        self._selected_category_id   = item_id
        self.btn_category.title      = f"✔  {name}"
        self.btn_category.tint_color = "#B71C1C"

    def _open_payment_picker(self, sender):
        popup = PickerPopup(
            self.db_path,
            "payment_type",
            "เลือกประเภทการชำระ",
            on_select=self._on_payment_selected,
            frame=self.bounds,
        )
        self.add_subview(popup)

    def _on_payment_selected(self, item_id, name):
        self._selected_payment_type_id = item_id
        self.btn_payment.title         = f"✔  {name}"
        self.btn_payment.tint_color    = "#B71C1C"

    def _save(self, sender):
        if self._selected_detail_id is None and not self._selected_detail_name:
            _alert("กรุณาเลือกรายละเอียด")
            return
        if self._selected_category_id is None:
            _alert("กรุณาเลือกหมวดหมู่")
            return
        if self._selected_payment_type_id is None:
            _alert("กรุณาเลือกประเภทการชำระ")
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

        detail_id   = self._selected_detail_id if self._selected_detail_id is not None else 0
        detail_text = (self._selected_detail_name or '').strip()
        note        = self.tf_note.text.strip()

        _save_expense(
            self.db_path,
            self._date_str,
            detail_id,
            detail_text,
            self._selected_category_id,
            self._selected_payment_type_id,
            amount,
            note,
        )
        self._reset()

    def _reset(self):
        import console
        console.hud_alert("บันทึกสำเร็จ ✓", "success", 1.2)

        self._selected_detail_id       = None
        self._selected_detail_name     = None
        self._selected_category_id     = None
        self._selected_payment_type_id = None
        self._date_str = datetime.date.today().isoformat()

        self.btn_date.title          = f"📅  {self._date_str}"
        self.btn_detail.title        = "แตะเพื่อเลือกรายละเอียด..."
        self.btn_detail.tint_color   = "#555555"
        self.btn_category.title      = "แตะเพื่อเลือกหมวดหมู่..."
        self.btn_category.tint_color = "#555555"
        self.btn_payment.title       = "แตะเพื่อเลือกวิธีชำระเงิน..."
        self.btn_payment.tint_color  = "#555555"
        self.tf_amount.text = ""
        self.tf_note.text   = ""
        # คืน scroll กลับบนสุด
        self._sv.content_offset = (0, 0)


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

def show(db_path: str):
    W, H = ui.get_screen_size()
    form = ExpenseForm(db_path, frame=(0, 0, W, H))
    form.present("sheet")