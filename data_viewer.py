# data_viewer.py
# v3 — READ/WRITE: เพิ่ม / แก้ไข / ลบ ได้จากหน้า HTML โดยตรง
# ใช้งานใน Pythonista บน iPhone/iPad
#
# วิธีเรียกใช้:
#   import data_viewer
#   viewer = data_viewer.DataViewer(db_path)
#   viewer.show_income()            # รายรับ
#   viewer.show_expense()           # รายจ่าย
#   viewer.show_detail_master()     # รายละเอียด (รายรับ+รายจ่าย)
#   viewer.show_category_income()   # หมวดหมู่รายรับ
#   viewer.show_category_expense()  # หมวดหมู่รายจ่าย
#   viewer.show_payment_type()      # ประเภทการชำระเงิน
#
# ทุกหน้ามีปุ่ม + เพิ่ม / แก้ไข / ลบ ในตัว

import ui
import sqlite3
import json
import datetime
import urllib.parse
import console


# =======================================================
# Metadata  (จุดเดียวที่ต้องแก้เมื่อเพิ่มตารางใหม่ — ดู handoff [4.5])
# =======================================================

_ENTITIES = {
    'income': {
        'title': 'รายรับทั้งหมด',
        'kind': 'txn',
        'table': 'income',
        'cat_table': 'category_income',
        'detail_type': 'รายรับ',
        'has_payment': False,
    },
    'expense': {
        'title': 'รายจ่ายทั้งหมด',
        'kind': 'txn',
        'table': 'expense',
        'cat_table': 'category_expense',
        'detail_type': 'รายจ่าย',
        'has_payment': True,
    },
    'category_income': {
        'title': 'หมวดหมู่รายรับ',
        'kind': 'lookup',
        'table': 'category_income',
        'name_col': 'name',
        'label': 'ชื่อหมวดหมู่',
    },
    'category_expense': {
        'title': 'หมวดหมู่รายจ่าย',
        'kind': 'lookup',
        'table': 'category_expense',
        'name_col': 'name',
        'label': 'ชื่อหมวดหมู่',
    },
    'payment_type': {
        'title': 'ประเภทการชำระเงิน',
        'kind': 'lookup',
        'table': 'payment_type',
        'name_col': 'name',
        'label': 'ชื่อประเภท',
    },
    'detail_master': {
        'title': 'รายละเอียด',
        'kind': 'detail',
        'table': 'detail_master',
        'name_col': 'detail_name',
        'label': 'ชื่อรายละเอียด',
    },
}

_DETAIL_TYPES = ('รายรับ', 'รายจ่าย')


# =======================================================
# Helper
# =======================================================

def _escape(text):
    text = str(text) if text is not None else ''
    text = text.strip()
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _attr(text):
    text = str(text) if text is not None else ''
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text


def _fmt_amount(value):
    try:
        return "{:,.2f}".format(float(value))
    except (TypeError, ValueError):
        return ''


def _parse_amount(value):
    """คืน float หรือ None ถ้าแปลงไม่ได้ — return ครบทุก branch (handoff [5])"""
    if value is None:
        return None
    s = str(value).strip().replace(',', '')
    if s == '':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _split_year_month(date_str):
    """แยกปี/เดือนจาก 'YYYY-MM-DD' โดยไม่แปลง ค.ศ./พ.ศ. — เก็บตามที่ผู้ใช้กรอก"""
    parts = str(date_str or '').split('-')
    if len(parts) < 2:
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None


def _today_iso():
    return datetime.date.today().strftime('%Y-%m-%d')


# =======================================================
# CSS  (string ธรรมดา — ใช้ { } เดี่ยวเท่านั้น ดู handoff [5])
# =======================================================

def _base_css():
    return """
  * { box-sizing: border-box; margin: 0; padding: 0;  }
  body {
    background: #1c1c1e;
    color: #e5e5ea;
    font-family: -apple-system, "Helvetica Neue", sans-serif;
    font-size: 14px;
    padding: 8px 8px 40px 8px;
  }
  a { text-decoration: none; }
  h2 {
    text-align: center;
    font-size: 17px;
    font-weight: bold;
    padding: 10px 0 12px 0;
    color: #ffffff;
  }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 2px 12px 2px;
  }
  .toolbar .count { flex: 1; font-size: 13px; color: #98989f; }
  .btn {
    display: inline-block;
    padding: 9px 14px;
    border-radius: 9px;
    background: #0a84ff;
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
  }
  .btn.ghost  { background: #3a3a3c; color: #e5e5ea; }
  .btn.danger { background: #ff453a; }
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
  th.act    { text-align: center; width: 92px; }
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
  td.act    { white-space: nowrap; text-align: center; }
  .icon {
    display: inline-block;
    width: 34px;
    height: 30px;
    line-height: 30px;
    text-align: center;
    border-radius: 7px;
    font-size: 15px;
    margin: 0 2px;
    background: #3a3a3c;
  }
  .icon.del { background: #4a2b2b; }
  .footer   { text-align: center; padding: 12px 0 6px 0; font-size: 12px; color: #636366; }
  details { margin-bottom: 12px; border-radius: 8px; overflow: hidden; }
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
  .form {
    background: #2c2c2e;
    border-radius: 12px;
    padding: 6px 14px 16px 14px;
  }
  .form label {
    display: block;
    font-size: 13px;
    color: #98989f;
    margin: 14px 0 6px 0;
  }
  .form input, .form select {
    width: 100%;
    padding: 11px 10px;
    border-radius: 9px;
    border: 1px solid #48484a;
    background: #1c1c1e;
    color: #e5e5ea;
    font-size: 16px;
    -webkit-appearance: none;
    appearance: none;
  }
  .form select { background-image: none; }
  .form .hint { font-size: 12px; color: #636366; margin-top: 5px; }
  .actions { display: flex; gap: 10px; margin-top: 22px; }
  .actions a { flex: 1; text-align: center; padding: 13px 0; border-radius: 10px; font-size: 15px; }
    .card {
    background: #2c2c2e;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }
  .card .top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .card .cdate { font-size: 12px; color: #98989f; }
  .card .cat {
    font-size: 12px;
    color: #64b5ff;
    background: rgba(10,132,255,0.16);
    padding: 2px 9px;
    border-radius: 6px;
  }
  .card .amt {
    margin-left: auto;
    font-size: 17px;
    font-weight: bold;
    font-variant-numeric: tabular-nums;
  }
  .card .amt.inc { color: #30d158; }
  .card .amt.exp { color: #ff453a; }
  .card .ctitle { font-size: 15px; color: #ffffff; margin-top: 9px; }
  .card .cnote  { font-size: 12px; color: #98989f; margin-top: 4px; }
  .card .acts   { display: flex; gap: 8px; margin-top: 12px; }
  .card .acts a {
    flex: 1;
    text-align: center;
    padding: 10px 0;
    border-radius: 8px;
    background: #3a3a3c;
    color: #e5e5ea;
    font-size: 13px;
    touch-action: manipulation;
  }
  .card .acts a.del { background: #4a2b2b; color: #ff8a80; }
  .card .acts a:active { opacity: 0.55; }
  .lrow {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #2c2c2e;
    border-radius: 10px;
    padding: 11px 12px;
    margin-bottom: 8px;
  }
  .lrow .lid   { font-size: 12px; color: #636366; min-width: 30px; }
  .lrow .lname { flex: 1; font-size: 15px; color: #e5e5ea; }
  .lrow a {
    width: 40px;
    height: 34px;
    line-height: 34px;
    text-align: center;
    border-radius: 8px;
    background: #3a3a3c;
    font-size: 15px;
    touch-action: manipulation;
  }
  .lrow a.del { background: #4a2b2b; }
  .lrow a:active { opacity: 0.55; }
  .empty-box { text-align: center; padding: 30px 0; color: #636366; }
"""


def _page(title, body_html, extra_js=''):
    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, '
        'maximum-scale=1.0, user-scalable=no">'
        '<style>' + _base_css() + '</style>'
        '</head><body>'
        '<h2>' + _escape(title) + '</h2>'
        + body_html +
        '<script>' + _COMMON_JS + extra_js + '</script>'
        '</body></html>'
    )


# JS กลาง — ไม่ใช่ f-string จึงใช้ { } เดี่ยวได้ตามปกติ
_COMMON_JS = """
function go(u) { window.location.href = u; }
function sendForm(entity, rid) {
  var els = document.querySelectorAll('[data-key]');
  var o = {};
  for (var i = 0; i < els.length; i++) {
    o[els[i].getAttribute('data-key')] = els[i].value;
  }
  o['id'] = rid;
  var payload = encodeURIComponent(JSON.stringify(o));
  window.location.href = 'dv://save/' + entity + '?data=' + payload;
}
function syncDetail(sel) {
  var t = document.getElementById('detail_text');
  if (!t) { return; }
  if (sel.value !== '') {
    t.value = sel.options[sel.selectedIndex].getAttribute('data-name');
  }
}
"""


# =======================================================
# HTML builders — LIST
# =======================================================

def _toolbar(entity, count, extra_btn=''):
    return (
        '<div class="toolbar">'
        '<span class="count">ทั้งหมด ' + str(count) + ' รายการ</span>'
        + extra_btn +
        '<a class="btn" href="dv://new/' + entity + '">+ เพิ่ม</a>'
        '</div>'
    )


def _row_actions(entity, rid):
    return (
        '<td class="act">'
        '<a class="icon" href="dv://edit/' + entity + '/' + str(rid) + '">&#9998;</a>'
        '<a class="icon del" href="dv://delete/' + entity + '/' + str(rid) + '">&#128465;</a>'
        '</td>'
    )

def _card_actions(entity, rid):
    base = 'dv://%s/' + entity + '/' + str(rid)
    return (
        '<div class="acts">'
        '<a href="' + (base % 'edit')   + '">&#9998; แก้ไข</a>'
        '<a class="del" href="' + (base % 'delete') + '">&#128465; ลบ</a>'
        '</div>'
    )


def _build_list_txn(entity, title, rows, empty_msg):
    """rows: (id, date, detail_text, category, amount, note)"""
    amt_cls = 'inc' if entity == 'income' else 'exp'

    if rows:
        body = ''
        for rid, date, detail, category, amount, note in rows:
            note_html = ''
            if str(note or '').strip():
                note_html = '<div class="cnote">' + _escape(note) + '</div>'
            cat_html = ''
            if str(category or '').strip():
                cat_html = '<span class="cat">' + _escape(category) + '</span>'
            body += (
                '<div class="card">'
                '<div class="top">'
                '<span class="cdate">' + _escape(date) + '</span>'
                + cat_html +
                '<span class="amt ' + amt_cls + '">' + _fmt_amount(amount) + '</span>'
                '</div>'
                '<div class="ctitle">' + _escape(detail) + '</div>'
                + note_html
                + _card_actions(entity, rid) +
                '</div>\n'
            )
    else:
        body = '<div class="empty-box">' + _escape(empty_msg) + '</div>'

    return _page(title, _toolbar(entity, len(rows)) + body)


def _lookup_row(entity, rid, name):
    base = 'dv://%s/' + entity + '/' + str(rid)
    return (
        '<div class="lrow">'
        '<span class="lid">' + _escape(str(rid)) + '</span>'
        '<span class="lname">' + _escape(name) + '</span>'
        '<a href="' + (base % 'edit')   + '">&#9998;</a>'
        '<a class="del" href="' + (base % 'delete') + '">&#128465;</a>'
        '</div>\n'
    )


def _build_list_lookup(entity, title, rows, empty_msg):
    """rows: (id, name)"""
    if rows:
        body = ''
        for rid, name in rows:
            body += _lookup_row(entity, rid, name)
    else:
        body = '<div class="empty-box">' + _escape(empty_msg) + '</div>'
    return _page(title, _toolbar(entity, len(rows)) + body)


def _detail_section(label, rows, open_attr):
    count = len(rows)
    if rows:
        body = ''
        for rid, name in rows:
            body += _lookup_row('detail_master', rid, name)
    else:
        body = '<div class="empty-box">ยังไม่มีข้อมูล</div>'

    add_url = 'dv://new/detail_master?type=' + urllib.parse.quote(label)
    return (
        '<details ' + open_attr + '>'
        '<summary>' + _escape(label) + ' (' + str(count) + ' รายการ)</summary>'
        '<div class="toolbar" style="padding:10px 2px">'
        '<span class="count"></span>'
        '<a class="btn" href="' + add_url + '">+ เพิ่ม' + _escape(label) + '</a>'
        '</div>'
        + body +
        '</details>'
    )



def _build_list_detail(income_rows, expense_rows):
    s1 = _detail_section('รายรับ', income_rows, 'open')
    s2 = _detail_section('รายจ่าย', expense_rows, '')
    return _page('รายละเอียด', s1 + s2)


# =======================================================
# HTML builders — FORM
# =======================================================

def _input(key, value, placeholder='', itype='text'):
    return (
        '<input data-key="' + key + '" id="' + key + '" type="' + itype + '" '
        'value="' + _attr(value) + '" placeholder="' + _attr(placeholder) + '">'
    )


def _select(key, options, selected, blank_label=None, onchange=''):
    """options: list of (value, label)"""
    extra = ' onchange="' + onchange + '"' if onchange else ''
    html = '<select data-key="' + key + '" id="' + key + '"' + extra + '>'
    if blank_label is not None:
        mark = ' selected' if selected in (None, '', 0, '0') else ''
        html += '<option value=""' + mark + '>' + _escape(blank_label) + '</option>'
    for value, label in options:
        mark = ' selected' if str(value) == str(selected) else ''
        html += (
            '<option value="' + _attr(value) + '"' + mark +
            ' data-name="' + _attr(label) + '">' + _escape(label) + '</option>'
        )
    html += '</select>'
    return html


def _form_actions(entity, rid):
    rid_js = 'null' if rid is None else str(rid)
    return (
        '<div class="actions">'
        '<a class="btn ghost" href="dv://cancel/' + entity + '">ยกเลิก</a>'
        '<a class="btn" href="javascript:void(0)" '
        'onclick="sendForm(\'' + entity + '\',' + rid_js + ')">บันทึก</a>'
        '</div>'
    )


def _build_form_txn(entity, spec, rid, row, categories, details, payments):
    """row: dict หรือ None (กรณีเพิ่มใหม่)"""
    is_new = row is None
    title = ('เพิ่ม' if is_new else 'แก้ไข') + spec['detail_type']

    date_v = _today_iso() if is_new else row.get('date', '')
    detail_id_v = '' if is_new else (row.get('detail_id') or '')
    detail_tx_v = '' if is_new else row.get('detail_text', '')
    cat_v = '' if is_new else (row.get('category_id') or '')
    amt_v = '' if is_new else _fmt_amount(row.get('amount'))
    note_v = '' if is_new else (row.get('note') or '')

    body = '<div class="form">'
    body += '<label>วันที่</label>' + _input('date', date_v, 'YYYY-MM-DD')
    body += '<div class="hint">รูปแบบ YYYY-MM-DD (ปี/เดือนจะถูกคำนวณจากช่องนี้)</div>'

    body += '<label>เลือกจากรายการที่บันทึกไว้ (ไม่บังคับ)</label>'
    body += _select('detail_id', details, detail_id_v,
                    blank_label='— พิมพ์เอง —', onchange='syncDetail(this)')

    body += '<label>' + _escape(spec['detail_type']) + '</label>'
    body += _input('detail_text', detail_tx_v, 'พิมพ์รายการ')

    body += '<label>หมวดหมู่</label>'
    body += _select('category_id', categories, cat_v, blank_label='— เลือกหมวดหมู่ —')

    if spec['has_payment']:
        pay_v = '' if is_new else (row.get('payment_type_id') or '')
        body += '<label>ประเภทการชำระเงิน</label>'
        body += _select('payment_type_id', payments, pay_v, blank_label='— เลือก —')

    body += '<label>จำนวนเงิน</label>' + _input('amount', amt_v, '0.00')
    body += '<label>หมายเหตุ</label>' + _input('note', note_v, '')
    body += '</div>'
    body += _form_actions(entity, rid)
    return _page(title, body)


def _build_form_lookup(entity, spec, rid, row, preset_type=None):
    is_new = row is None
    title = ('เพิ่ม' if is_new else 'แก้ไข') + spec['title']

    name_v = '' if is_new else row.get('name', '')
    body = '<div class="form">'
    body += '<label>' + _escape(spec['label']) + '</label>' + _input('name', name_v, '')

    if spec['kind'] == 'detail':
        type_v = preset_type if is_new else row.get('type', '')
        body += '<label>ประเภท</label>'
        body += _select('type', [(t, t) for t in _DETAIL_TYPES], type_v)

    body += '</div>'
    body += _form_actions(entity, rid)
    return _page(title, body)


# =======================================================
# EditorView — WebView + URL bridge
# =======================================================
class _EditorView(ui.View):

    def __init__(self, viewer, entity):
        super().__init__()
        self.viewer = viewer
        self.entity = entity
        self.name = _ENTITIES[entity]['title']
        self.background_color = '#1c1c1e'

        wv = ui.WebView()
        wv.flex = 'WH'
        wv.scales_page_to_fit = False
        wv.delegate = self
        self.add_subview(wv)
        self._wv = wv
        self.render_list()

    def layout(self):
        self._wv.frame = self.bounds

    # ── render ──────────────────────────────────────────
    def render_list(self):
        self._wv.load_html(self.viewer.build_list_html(self.entity))

    def render_form(self, rid=None, preset_type=None):
        self._wv.load_html(
            self.viewer.build_form_html(self.entity, rid, preset_type)
        )

    # ── URL bridge ──────────────────────────────────────
    def webview_should_start_load(self, webview, url, nav_type):
        if not url.startswith('dv://'):
            return True
        try:
            parsed = urllib.parse.urlparse(url)
            action = parsed.netloc
            parts = [p for p in parsed.path.split('/') if p]
            entity = parts[0] if parts else self.entity
            rid = parts[1] if len(parts) > 1 else None
            query = urllib.parse.parse_qs(parsed.query)
        except Exception as err:
            console.hud_alert('URL ผิดรูปแบบ: ' + str(err), 'error', 1.4)
            return False

        # เลื่อนออกจาก callback ก่อน แล้วค่อยทำงานหนัก/เปิด dialog
        ui.delay(lambda: self._dispatch(action, entity, rid, query), 0.01)
        return False

    def _dispatch(self, action, entity, rid, query):
        try:
            if action == 'new':
                preset = query.get('type', [None])[0]
                if preset is not None:
                    preset = urllib.parse.unquote(preset)
                self.render_form(None, preset)

            elif action == 'edit':
                self.render_form(rid)

            elif action == 'cancel':
                self.render_list()

            elif action == 'delete':
                self._do_delete(entity, rid)

            elif action == 'save':
                self._do_save(entity, query)

        except Exception as err:
            console.hud_alert('ผิดพลาด: ' + str(err), 'error', 2.0)

    @ui.in_background
    def _do_delete(self, entity, rid):
        try:
            console.alert('ยืนยันการลบ',
                          'ต้องการลบรายการ ID ' + str(rid) + ' ใช่หรือไม่?',
                          'ลบ')
        except KeyboardInterrupt:
            return
        ok, msg = self.viewer.delete_row(entity, rid)
        console.hud_alert(msg, 'success' if ok else 'error', 1.2)
        ui.delay(self.render_list, 0.01)

    def _do_save(self, entity, query):
        raw = query.get('data', [''])[0]
        if not raw:
            console.hud_alert('ไม่พบข้อมูลที่ส่งมา', 'error', 1.4)
            return
        try:
            data = json.loads(urllib.parse.unquote(raw))
        except ValueError:
            try:
                data = json.loads(raw)
            except ValueError:
                console.hud_alert('ข้อมูลที่ส่งมาเสียหาย', 'error', 1.4)
                return

        ok, msg = self.viewer.save_row(entity, data)
        if ok:
            console.hud_alert(msg, 'success', 1.0)
            self.render_list()
        else:
            console.hud_alert(msg, 'error', 1.8)


# =======================================================
# DataViewer — คลาสหลัก
# =======================================================
class DataViewer:

    def __init__(self, db_path):
        self.db_path = db_path

    # ── DB helper ───────────────────────────────────────
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _open(self, entity):
        view = _EditorView(self, entity)
        view.present('fullscreen', animated=True)

    # ── public entry points ─────────────────────────────
    def show_income(self):
        self._open('income')

    def show_expense(self):
        self._open('expense')

    def show_detail_master(self):
        self._open('detail_master')

    def show_category_income(self):
        self._open('category_income')

    def show_category_expense(self):
        self._open('category_expense')

    def show_payment_type(self):
        self._open('payment_type')

    # ── LIST ────────────────────────────────────────────
    def build_list_html(self, entity):
        spec = _ENTITIES[entity]
        conn = self._connect()
        try:
            cur = conn.cursor()

            if spec['kind'] == 'txn':
                cur.execute(
                    'SELECT t.id, t.date, t.detail_text, '
                    "COALESCE(c.name, '') AS category, t.amount, "
                    "COALESCE(t.note, '') AS note "
                    'FROM ' + spec['table'] + ' t '
                    'LEFT JOIN ' + spec['cat_table'] + ' c ON t.category_id = c.id '
                    'ORDER BY t.date DESC, t.id DESC'
                )
                rows = [tuple(r) for r in cur.fetchall()]
                return _build_list_txn(
                    entity, spec['title'], rows,
                    'ยังไม่มีข้อมูล' + spec['detail_type']
                )

            if spec['kind'] == 'detail':
                cur.execute(
                    'SELECT id, ' + spec['name_col'] + ' FROM ' + spec['table'] +
                    ' WHERE type = ? ORDER BY ' + spec['name_col'], ('รายรับ',)
                )
                income_rows = [tuple(r) for r in cur.fetchall()]
                cur.execute(
                    'SELECT id, ' + spec['name_col'] + ' FROM ' + spec['table'] +
                    ' WHERE type = ? ORDER BY ' + spec['name_col'], ('รายจ่าย',)
                )
                expense_rows = [tuple(r) for r in cur.fetchall()]
                return _build_list_detail(income_rows, expense_rows)

            # lookup
            cur.execute(
                'SELECT id, ' + spec['name_col'] + ' FROM ' + spec['table'] +
                ' ORDER BY ' + spec['name_col']
            )
            rows = [tuple(r) for r in cur.fetchall()]
            return _build_list_lookup(
                entity, spec['title'], rows, 'ยังไม่มี' + spec['title']
            )
        finally:
            conn.close()

    # ── FORM ────────────────────────────────────────────
    def build_form_html(self, entity, rid=None, preset_type=None):
        spec = _ENTITIES[entity]
        conn = self._connect()
        try:
            cur = conn.cursor()
            row = None
            if rid is not None:
                cur.execute(
                    'SELECT * FROM ' + spec['table'] + ' WHERE id = ?', (rid,)
                )
                found = cur.fetchone()
                if found is None:
                    return _page('ไม่พบข้อมูล',
                                 '<div class="form">ไม่พบรายการ ID ' +
                                 _escape(str(rid)) + '</div>' +
                                 _form_actions(entity, None))
                row = dict(found)

            if spec['kind'] == 'txn':
                cur.execute(
                    'SELECT id, name FROM ' + spec['cat_table'] + ' ORDER BY name'
                )
                categories = [(r['id'], r['name']) for r in cur.fetchall()]

                cur.execute(
                    'SELECT id, detail_name FROM detail_master '
                    'WHERE type = ? ORDER BY detail_name',
                    (spec['detail_type'],)
                )
                details = [(r['id'], r['detail_name']) for r in cur.fetchall()]

                payments = []
                if spec['has_payment']:
                    cur.execute('SELECT id, name FROM payment_type ORDER BY name')
                    payments = [(r['id'], r['name']) for r in cur.fetchall()]

                return _build_form_txn(entity, spec, rid, row,
                                       categories, details, payments)

            # lookup / detail — normalize ชื่อคอลัมน์ให้เป็น 'name'
            if row is not None and spec['name_col'] != 'name':
                row['name'] = row.get(spec['name_col'], '')
            return _build_form_lookup(entity, spec, rid, row, preset_type)
        finally:
            conn.close()

    # ── SAVE ────────────────────────────────────────────
    def save_row(self, entity, data):
        """คืน (ok: bool, message: str) — return ครบทุก branch"""
        spec = _ENTITIES[entity]
        rid = data.get('id')
        rid = None if rid in (None, '', 'null') else int(rid)

        if spec['kind'] == 'txn':
            return self._save_txn(entity, spec, rid, data)
        return self._save_lookup(entity, spec, rid, data)

    def _save_txn(self, entity, spec, rid, data):
        date_v = str(data.get('date', '')).strip()
        year, month = _split_year_month(date_v)
        if year is None:
            return False, 'วันที่ต้องอยู่ในรูปแบบ YYYY-MM-DD'

        detail_text = str(data.get('detail_text', '')).strip()
        if detail_text == '':
            return False, 'กรุณากรอก' + spec['detail_type']

        cat_raw = data.get('category_id', '')
        if cat_raw in (None, '', '0'):
            return False, 'กรุณาเลือกหมวดหมู่'
        category_id = int(cat_raw)

        amount = _parse_amount(data.get('amount'))
        if amount is None:
            return False, 'จำนวนเงินไม่ถูกต้อง'

        det_raw = data.get('detail_id', '')
        detail_id = None if det_raw in (None, '', '0') else int(det_raw)
        note = str(data.get('note', '')).strip()

        cols = ['date', 'year', 'month', 'detail_id', 'detail_text',
                'category_id', 'amount', 'note']
        vals = [date_v, year, month, detail_id, detail_text,
                category_id, amount, note]

        if spec['has_payment']:
            pay_raw = data.get('payment_type_id', '')
            if pay_raw in (None, '', '0'):
                return False, 'กรุณาเลือกประเภทการชำระเงิน'
            cols.append('payment_type_id')
            vals.append(int(pay_raw))

        conn = self._connect()
        try:
            cur = conn.cursor()
            if rid is None:
                placeholders = ','.join(['?'] * len(cols))
                cur.execute(
                    'INSERT INTO ' + spec['table'] +
                    ' (' + ','.join(cols) + ') VALUES (' + placeholders + ')',
                    vals
                )
                msg = 'เพิ่มรายการแล้ว'
            else:
                assigns = ','.join([c + ' = ?' for c in cols])
                cur.execute(
                    'UPDATE ' + spec['table'] + ' SET ' + assigns + ' WHERE id = ?',
                    vals + [rid]
                )
                msg = 'บันทึกการแก้ไขแล้ว'
            conn.commit()
            return True, msg
        except sqlite3.Error as err:
            return False, 'DB error: ' + str(err)
        finally:
            conn.close()

    def _save_lookup(self, entity, spec, rid, data):
        name = str(data.get('name', '')).strip()
        if name == '':
            return False, 'กรุณากรอก' + spec['label']

        cols = [spec['name_col']]
        vals = [name]

        if spec['kind'] == 'detail':
            dtype = str(data.get('type', '')).strip()
            if dtype not in _DETAIL_TYPES:
                return False, 'กรุณาเลือกประเภท'
            cols.append('type')
            vals.append(dtype)

        conn = self._connect()
        try:
            cur = conn.cursor()
            if rid is None:
                placeholders = ','.join(['?'] * len(cols))
                cur.execute(
                    'INSERT INTO ' + spec['table'] +
                    ' (' + ','.join(cols) + ') VALUES (' + placeholders + ')',
                    vals
                )
                msg = 'เพิ่มแล้ว'
            else:
                assigns = ','.join([c + ' = ?' for c in cols])
                cur.execute(
                    'UPDATE ' + spec['table'] + ' SET ' + assigns + ' WHERE id = ?',
                    vals + [rid]
                )
                msg = 'บันทึกแล้ว'
            conn.commit()
            return True, msg
        except sqlite3.IntegrityError:
            return False, 'ชื่อนี้มีอยู่แล้ว'
        except sqlite3.Error as err:
            return False, 'DB error: ' + str(err)
        finally:
            conn.close()

    # ── DELETE ──────────────────────────────────────────
    def delete_row(self, entity, rid):
        """คืน (ok: bool, message: str)"""
        spec = _ENTITIES[entity]
        guard = self._delete_guard(entity, rid)
        if guard is not None:
            return False, guard

        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM ' + spec['table'] + ' WHERE id = ?', (rid,))
            conn.commit()
            return True, 'ลบแล้ว'
        except sqlite3.Error as err:
            return False, 'DB error: ' + str(err)
        finally:
            conn.close()

    def _delete_guard(self, entity, rid):
        """คืนข้อความเตือนถ้าลบไม่ได้ / คืน None ถ้าลบได้"""
        checks = {
            'category_income':  [('income', 'category_id')],
            'category_expense': [('expense', 'category_id')],
            'payment_type':     [('expense', 'payment_type_id')],
            'detail_master':    [('income', 'detail_id'), ('expense', 'detail_id')],
        }
        if entity not in checks:
            return None

        conn = self._connect()
        try:
            cur = conn.cursor()
            total = 0
            for table, col in checks[entity]:
                cur.execute(
                    'SELECT COUNT(*) FROM ' + table + ' WHERE ' + col + ' = ?',
                    (rid,)
                )
                total += cur.fetchone()[0]
            if total > 0:
                return 'ลบไม่ได้ — ถูกใช้อยู่ ' + str(total) + ' รายการ'
            return None
        except sqlite3.Error:
            return None
        finally:
            conn.close()