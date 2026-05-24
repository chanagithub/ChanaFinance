import os
import platform
import sys

def get_icloud_path(folder_name):
    """
    สร้าง path ไปยังโฟลเดอร์ Pythonista ใน iCloud แบบ Universal
    รองรับทั้ง macOS และ Windows (กรณีใช้ iCloud for Windows)
    """
    system = platform.system()
    home = os.path.expanduser("~")
    
    if system == "Darwin":  # macOS
        # path มาตรฐานของ iCloud บน Mac
        base_path = os.path.join(home, "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents")
    elif system == "Windows":  # Windows
        # path ของ iCloud บน Windows มักจะอยู่ใน iCloudDrive
        base_path = os.path.join(home, "iCloudDrive/Pythonista 3/Documents")
    else:
        return "Unsupported OS"

    target_path = os.path.join(base_path, folder_name)
    return target_path

# --- ส่วนการใช้งาน ---
if __name__ == "__main__":
    # รับชื่อโฟลเดอร์จาก Command Line Argument หรือใส่ชื่อโครงการที่นี่
    # เช่น python find_path.py ChanaFinance
    if len(sys.argv) > 1:
        project_folder = sys.argv[1]
    else:
        # ค่าเริ่มต้นหากไม่ได้ใส่ชื่อโครงการมา
        project_folder = "ChanaFinance"

    path = get_icloud_path(project_folder)
    print(f"Path สำหรับโครงการ '{project_folder}' คือ:")
    print(path)
    
    # เพิ่มคำสั่งเปิดโฟลเดอร์เพื่อตรวจสอบความถูกต้อง (ถ้าต้องการ)
    if os.path.exists(path):
        print("สถานะ: พบโฟลเดอร์นี้ใน iCloud เรียบร้อยแล้ว")
    else:
        print("สถานะ: ไม่พบโฟลเดอร์ดังกล่าว กรุณาตรวจสอบว่าสร้างไว้ใน Pythonista แล้วหรือยัง")