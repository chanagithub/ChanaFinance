import os
import platform
import sqlite3

import dialogs


def get_icloud_path(folder_name):
    """Return the Pythonista iCloud folder path for macOS or Windows."""
    system = platform.system()
    home = os.path.expanduser('~')

    if system == 'Darwin':
        base_path = os.path.join(
            home,
            'Library/Mobile Documents/iCloud~com~omz-software~Pythonista3',
        )
    elif system == 'Windows':
        base_path = os.path.join(
            home,
            'iCloudDrive/iCloud~com~omz-software~Pythonista3',
        )
    else:
        return 'Unsupported OS'

    target_path = os.path.join(base_path, folder_name)
    print("Path สำหรับโครงการ '{}':\n{}".format(folder_name, target_path))
    return target_path


def normalize_db_file_name(file_name):
    file_name = file_name.strip()
    if not file_name.endswith('.db'):
        file_name += '.db'
    return file_name


def ask_new_db_path(folder_path):
    while True:
        file_name = dialogs.input_alert(
            'สร้างฐานข้อมูลใหม่',
            'โปรดระบุชื่อไฟล์ (ไม่ต้องใส่นามสกุล .db)',
        )

        if not file_name:
            return None, False

        file_name = normalize_db_file_name(file_name)
        db_path = os.path.join(folder_path, file_name)

        if not os.path.exists(db_path):
            return db_path, False

        try:
            button_index = dialogs.alert(
                'พบไฟล์ชื่อนี้แล้ว',
                'ไฟล์ {} มีอยู่แล้ว ต้องการเขียนไฟล์เปล่าทับ หรือใส่ชื่อใหม่'.format(file_name),
                'เขียนทับ',
                'ใส่ชื่อใหม่',
                'ยกเลิก',
            )
        except Exception:
            return None, False

        if button_index == 1:
            return db_path, True
        if button_index == 2:
            continue
        return None, False


def create_tables(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript('''
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
                detail_id INTEGER,
                detail_text TEXT, category_id INTEGER, amount REAL, note TEXT
            );

            CREATE TABLE IF NOT EXISTS expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, year INTEGER, month INTEGER,
                detail_id INTEGER,
                detail_text TEXT, category_id INTEGER, payment_type_id INTEGER, amount REAL, note TEXT
            );
        ''')
        conn.commit()
    finally:
        conn.close()


def create_new_file():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    db_path, overwrite = ask_new_db_path(folder_path)

    if not db_path:
        return

    file_name = os.path.basename(db_path)

    try:
        if overwrite:
            os.remove(db_path)

        create_tables(db_path)
        dialogs.hud_alert('สร้างไฟล์ {} เรียบร้อยแล้ว'.format(file_name), icon='success')
        print('ไฟล์ฐานข้อมูลถูกสร้างที่: {}'.format(db_path))
    except Exception as e:
        dialogs.hud_alert('เกิดข้อผิดพลาดในการสร้างไฟล์', icon='error')
        print(e)
