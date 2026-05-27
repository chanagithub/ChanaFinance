import dialogs
import os
import platform
import sqlite3

def get_icloud_path(folder_name):
    if platform.system() == 'Darwin':  # ตรวจสอบว่าเป็น iOS หรือ macOS
        base_path = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs')
        return os.path.join(base_path, folder_name)
    else:
        raise Exception("ระบบปฏิบัติการนี้ไม่รองรับการใช้งาน iCloud")   



def create_new_file():
    # 1. ถามชื่อไฟล์จากผู้ใช้
    file_name = dialogs.input_alert("สร้างฐานข้อมูลใหม่", "โปรดระบุชื่อไฟล์ (ไม่ต้องใส่นามสกุล .db)")
    
    if not file_name:
        return # ยกเลิกหากกด cancel

    # เติมนามสกุล .db ให้โดยอัตโนมัติ
    if not file_name.endswith('.db'):
        file_name += '.db'

    # 2. หา Path โฟลเดอร์โครงการ (สมมติชื่อโฟลเดอร์โครงการคือ 'ChanaFinance')
    folder = "ChanaFinance"
    folder_path = get_icloud_path(folder)

    db_path = os.path.join(folder_path, file_name)

    # 4. สร้างไฟล์ฐานข้อมูลและตารางต่างๆ
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # สร้างตารางตามโครงสร้างที่คุณต้องการ
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS category_income (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS category_expense (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS payment_type (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS detail_master (id INTEGER PRIMARY KEY, detail_name TEXT, type TEXT);
            
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
        cursor.close()
        conn.commit()
        conn.close()
        dialogs.hud_alert(f"สร้างไฟล์ {file_name} เรียบร้อยแล้ว", icon='success')
        print(f"ไฟล์ฐานข้อมูลถูกสร้างที่: {db_path}")
        #find_my_file_path('test_connection.txt')  # เรียกฟังก์ชันค้นหาไฟล์ทดสอบ
        find_db_files("new")

    except Exception as e:
        dialogs.hud_alert("เกิดข้อผิดพลาดในการสร้างไฟล์", icon='error')
        print(e)

    