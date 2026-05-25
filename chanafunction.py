import os
import platform
import sqlite3
import dialogs

def get_icloud_path(folder_name):
    """
    สร้าง path ไปยังโฟลเดอร์ Pythonista ใน iCloud แบบ Universal
    รองรับทั้ง macOS และ Windows
    """
    system = platform.system()
    home = os.path.expanduser("~")
    
    if system == "Darwin":  # macOS
        base_path = os.path.join(home, "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3")
    elif system == "Windows":  # Windows
        base_path = os.path.join(home, "iCloudDrive/iCloud~com~omz-software~Pythonista3")
    else:
        return "Unsupported OS"

    target_path = os.path.join(base_path, folder_name)
    print(f"Path สำหรับโครงการ '{folder_name}' คือ:\n{target_path}")
    return target_path

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
    
    # 3. สร้างโฟลเดอร์ถ้ายังไม่มี
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
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
        test_file_creation()  # เรียกฟังก์ชันทดสอบการสร้างไฟล์
        
    except Exception as e:
        dialogs.hud_alert("เกิดข้อผิดพลาดในการสร้างไฟล์", icon='error')
        print(e)


def test_file_creation():
    # 1. กำหนดโฟลเดอร์โครงการ (ชื่อเดียวกับที่คุณใช้สร้าง .db)
    folder_name = "ChanaFinance"
    base_path = os.path.expanduser('~/Documents')
    folder_path = os.path.join(base_path, folder_name)
    
    # 2. สร้างโฟลเดอร์ถ้ายังไม่มี
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # 3. กำหนด path ของไฟล์ทดสอบ
    test_file_path = os.path.join(folder_path, 'test_connection.txt')
    
    # 4. เขียนไฟล์ทดสอบ
    try:
        with open(test_file_path, 'w') as f:
            f.write("Test successful! I can write here.")
        
        print(f"เขียนไฟล์สำเร็จที่: {test_file_path}")
        print(f"ไฟล์ถูกสร้างขึ้นแล้ว: {os.path.exists(test_file_path)}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเขียนไฟล์: {e}")





# --- ส่วนการใช้งาน ---
if __name__ == "__main__":
    # ใส่ชื่อโฟลเดอร์ที่คุณต้องการ เช่น 'ChanaFinance'
    get_icloud_path("ChanaFinance")