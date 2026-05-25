import os
import time

def force_refresh(folder_path):
    # สั่งอัปเดตเวลาแก้ไขไฟล์ (Timestamp) เพื่อให้ระบบ iOS มองว่าไฟล์มีการเปลี่ยนแปลง
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            # แก้ไขเวลาเข้าถึง/แก้ไขไฟล์ให้เป็นปัจจุบัน
            os.utime(file_path, (time.time(), time.time()))
    print("Refresh สำเร็จ: ระบบจะตรวจพบว่าไฟล์เปลี่ยนไปแล้ว")

# ระบุ path ของโฟลเดอร์ที่อยู่นอก Sandbox ที่คุณเปิดใน Pythonista
# ใช้ตัวนี้แทนได้เลย มันจะเอา Path ของโฟลเดอร์ที่คุณเปิดค้างอยู่มาใช้ทันที
force_refresh(os.getcwd())