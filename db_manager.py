import os
import sqlite3

import console
import dialogs
import ui


DETAIL_TYPES = ('รายรับ', 'รายจ่าย')


TABLES = [
    {
        'name': 'category_income',
        'title': 'หมวดหมู่รายรับ',
        'columns': [('name', 'ชื่อหมวดหมู่', 'text')],
    },
    {
        'name': 'category_expense',
        'title': 'หมวดหมู่รายจ่าย',
        'columns': [('name', 'ชื่อหมวดหมู่', 'text')],
    },
    {
        'name': 'payment_type',
        'title': 'ประเภทการชำระเงิน',
        'columns': [('name', 'ชื่อประเภท', 'text')],
    },
    {
        'name': 'detail_master',
        'title': 'รายละเอียดหลัก',
        'columns': [
            ('detail_name', 'ชื่อรายละเอียด', 'text'),
            ('type', 'ประเภท', 'detail_type'),
        ],
    },
    {
        'name': 'income',
        'title': 'รายรับ',
        'columns': [
            ('date', 'วันที่', 'text'),
            ('year', 'ปี', 'integer'),
            ('month', 'เดือน', 'integer'),
            ('detail_id', 'รหัสรายละเอียด', 'integer'),
            ('category_id', 'รหัสหมวดหมู่', 'integer'),
            ('amount', 'จำนวนเงิน', 'real'),
            ('note', 'หมายเหตุ', 'text'),
        ],
    },
    {
        'name': 'expense',
        'title': 'รายจ่าย',
        'columns': [
            ('date', 'วันที่', 'text'),
            ('year', 'ปี', 'integer'),
            ('month', 'เดือน', 'integer'),
            ('detail_id', 'รหัสรายละเอียด', 'integer'),
            ('category_id', 'รหัสหมวดหมู่', 'integer'),
            ('payment_type_id', 'รหัสประเภทชำระเงิน', 'integer'),
            ('amount', 'จำนวนเงิน', 'real'),
            ('note', 'หมายเหตุ', 'text'),
        ],
    },
]


TABLE_BY_NAME = {table['name']: table for table in TABLES}


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(db_path):
    conn = connect(db_path)
    try:
        conn.executescript('''
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
        ''')
        conn.commit()
    finally:
        conn.close()


def table_names():
    return [table['name'] for table in TABLES]


def get_table(table_name):
    if table_name not in TABLE_BY_NAME:
        raise ValueError('Unknown table: {}'.format(table_name))
    return TABLE_BY_NAME[table_name]


def fetch_rows(db_path, table_name):
    get_table(table_name)
    conn = connect(db_path)
    try:
        cursor = conn.execute('SELECT * FROM {} ORDER BY id DESC'.format(table_name))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def insert_row(db_path, table_name, values):
    table = get_table(table_name)
    validate_values(table, values)
    columns = [column[0] for column in table['columns']]
    placeholders = ', '.join(['?'] * len(columns))
    sql = 'INSERT INTO {} ({}) VALUES ({})'.format(
        table_name, ', '.join(columns), placeholders
    )
    conn = connect(db_path)
    try:
        conn.execute(sql, [values.get(column) for column in columns])
        conn.commit()
    finally:
        conn.close()


def update_row(db_path, table_name, row_id, values):
    table = get_table(table_name)
    validate_values(table, values)
    columns = [column[0] for column in table['columns']]
    assignments = ', '.join(['{} = ?'.format(column) for column in columns])
    sql = 'UPDATE {} SET {} WHERE id = ?'.format(table_name, assignments)
    conn = connect(db_path)
    try:
        conn.execute(sql, [values.get(column) for column in columns] + [row_id])
        conn.commit()
    finally:
        conn.close()


def delete_row(db_path, table_name, row_id):
    get_table(table_name)
    conn = connect(db_path)
    try:
        conn.execute('DELETE FROM {} WHERE id = ?'.format(table_name), (row_id,))
        conn.commit()
    finally:
        conn.close()


def validate_values(table, values):
    if table['name'] == 'detail_master':
        row_type = values.get('type')
        if row_type not in DETAIL_TYPES:
            raise ValueError('ประเภทต้องเป็น "รายรับ" หรือ "รายจ่าย" เท่านั้น')


def coerce_value(value, value_type):
    if value in (None, ''):
        return None
    if value_type == 'integer':
        return int(value)
    if value_type == 'real':
        return float(value)
    return value


def row_title(row, table):
    parts = ['ID {}'.format(row.get('id'))]
    for column, label, value_type in table['columns']:
        value = row.get(column)
        if value not in (None, ''):
            parts.append('{}: {}'.format(label, value))
        if len(parts) >= 3:
            break
    return ' | '.join(parts)


class RecordListDataSource(object):
    def __init__(self, manager_view):
        self.manager_view = manager_view

    def tableview_number_of_rows(self, tableview, section):
        return len(self.manager_view.rows)

    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell('subtitle')
        data = self.manager_view.rows[row]
        cell.text_label.text = row_title(data, self.manager_view.table)
        cell.detail_text_label.text = self.manager_view.detail_text(data)
        return cell

    def tableview_did_select(self, tableview, section, row):
        self.manager_view.selected_index = row


class TableManagerView(ui.View):
    def __init__(self, db_path, table_name):
        ui.View.__init__(self)
        self.db_path = db_path
        self.table = get_table(table_name)
        self.rows = []
        self.selected_index = None
        self.name = self.table['title']
        self.background_color = 'white'

        self.table_view = ui.TableView(frame=self.bounds, flex='WH')
        self.data_source = RecordListDataSource(self)
        self.table_view.data_source = self.data_source
        self.table_view.delegate = self.data_source
        self.add_subview(self.table_view)

        self.left_button_items = [
            ui.ButtonItem(title='ปิด', action=lambda sender: self.close())
        ]
        self.right_button_items = [
            ui.ButtonItem(title='ลบ', action=self.delete_selected),
            ui.ButtonItem(title='แก้ไข', action=self.edit_selected),
            ui.ButtonItem(title='เพิ่ม', action=self.add_record),
        ]
        self.reload()

    def reload(self):
        self.rows = fetch_rows(self.db_path, self.table['name'])
        self.selected_index = None
        self.table_view.reload_data()

    def detail_text(self, row):
        values = []
        for column, label, value_type in self.table['columns']:
            value = row.get(column)
            if value not in (None, ''):
                values.append('{}={}'.format(column, value))
        return ', '.join(values)

    def selected_row(self):
        if self.selected_index is None:
            dialogs.hud_alert('กรุณาเลือกรายการก่อน', icon='error')
            return None
        if self.selected_index >= len(self.rows):
            return None
        return self.rows[self.selected_index]

    def add_record(self, sender):
        values = show_record_form(self.table)
        if values is None:
            return
        try:
            insert_row(self.db_path, self.table['name'], values)
            dialogs.hud_alert('เพิ่มข้อมูลแล้ว', icon='success')
            self.reload()
        except Exception as e:
            console.alert('เพิ่มข้อมูลไม่สำเร็จ', str(e), 'ตกลง', hide_cancel_button=True)

    def edit_selected(self, sender):
        row = self.selected_row()
        if row is None:
            return
        values = show_record_form(self.table, row)
        if values is None:
            return
        try:
            update_row(self.db_path, self.table['name'], row['id'], values)
            dialogs.hud_alert('แก้ไขข้อมูลแล้ว', icon='success')
            self.reload()
        except Exception as e:
            console.alert('แก้ไขข้อมูลไม่สำเร็จ', str(e), 'ตกลง', hide_cancel_button=True)

    def delete_selected(self, sender):
        row = self.selected_row()
        if row is None:
            return
        try:
            button_index = console.alert(
                'ยืนยันการลบ',
                'ต้องการลบ ID {} ใช่ไหม'.format(row['id']),
                'ลบ',
                hide_cancel_button=False,
            )
        except (KeyboardInterrupt, Exception):
            return
        if button_index != 1:
            return
        try:
            delete_row(self.db_path, self.table['name'], row['id'])
            dialogs.hud_alert('ลบข้อมูลแล้ว', icon='success')
            self.reload()
        except Exception as e:
            console.alert('ลบข้อมูลไม่สำเร็จ', str(e), 'ตกลง', hide_cancel_button=True)


def show_record_form(table, row=None):
    fields = []
    detail_type = row.get('type') if row else DETAIL_TYPES[0]

    for column, label, value_type in table['columns']:
        if value_type == 'detail_type':
            continue
        fields.append({
            'type': 'text',
            'key': column,
            'title': label,
            'value': '' if row is None or row.get(column) is None else str(row.get(column)),
        })

    title = 'เพิ่ม{}'.format(table['title']) if row is None else 'แก้ไข{}'.format(table['title'])
    result = dialogs.form_dialog(title=title, fields=fields)
    if result is None:
        return None

    values = {}
    try:
        for column, label, value_type in table['columns']:
            if value_type == 'detail_type':
                continue
            values[column] = coerce_value(result.get(column), value_type)
    except Exception as e:
        console.alert('ข้อมูลไม่ถูกต้อง', str(e), 'ตกลง', hide_cancel_button=True)
        return None

    if table['name'] == 'detail_master':
        selected = dialogs.list_dialog('เลือกประเภท', DETAIL_TYPES)
        if selected is None:
            return None
        values['type'] = selected

    return values


def open_table_manager(db_path, table_name):
    ensure_schema(db_path)
    view = TableManagerView(db_path, table_name)
    view.present('sheet')
    view.wait_modal()


def open_database_manager(db_path):
    ensure_schema(db_path)
    choices = ['{} ({})'.format(table['title'], table['name']) for table in TABLES]
    selected = dialogs.list_dialog(
        'จัดการข้อมูล: {}'.format(os.path.basename(db_path)),
        choices,
    )
    if selected is None:
        return
    table_index = choices.index(selected)
    open_table_manager(db_path, TABLES[table_index]['name'])
