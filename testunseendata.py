import sqlite3
import os
from chanafunction import get_icloud_path


# 1. ใช้ฟังก์ชันที่คุณมั่นใจว่าถูกต้อง
folder_name = "ChanaFinance"
db_path = os.path.join(get_icloud_path(folder_name), "new04.db")

def test_database_operations():
    print(f"กำลังทำงานกับไฟล์ที่: {db_path}")
    
    # --- ส่วนที่ 1: สร้างตารางและใส่ข้อมูล ---
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # สร้างตารางถ้ายังไม่มี
    cursor.execute('''CREATE TABLE IF NOT EXISTS income 
                      (id INTEGER PRIMARY KEY, description TEXT, amount REAL)''')

    # ใส่ข้อมูล 2 เรคคอร์ด
    cursor.execute("INSERT INTO income (detail_id, amount) VALUES (?, ?)", (1, 50000))
    cursor.execute("INSERT INTO income (detail_id, amount) VALUES (?, ?)", (2, 5000))

    conn.commit()
    conn.close() # ปิดไฟล์
    print("ใส่ข้อมูล 2 เรคคอร์ดเรียบร้อยและปิดไฟล์แล้ว")
    
    # --- ส่วนที่ 2: เปิดไฟล์ใหม่และอ่านข้อมูล ---
    print("\nกำลังเปิดไฟล์อีกครั้งเพื่ออ่านข้อมูล...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM income")
    rows = cursor.fetchall()
    
    print("ข้อมูลในตาราง income:")
    for row in rows:
        print(f"ID: {row[0]}, Detail ID: {row[1]}, Amount: {row[2]}")
        
    conn.close()
    print("\nพิสูจน์สำเร็จ: อ่านไฟล์ได้จริง!")

# รันฟังก์ชันทดสอบ
test_database_operations()