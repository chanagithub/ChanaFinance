import os
import platform
import sys
import shutil

def get_icloud_path(folder_name):
    """
    สร้าง path ไปยังโฟลเดอร์ Pythonista ใน iCloud แบบ Universal
    รองรับทั้ง macOS และ Windows (กรณีใช้ iCloud for Windows)
    """
    system = platform.system()
    home = os.path.expanduser("~")
    
    if system == "Darwin":  # macOS
        # path มาตรฐานของ iCloud บน Mac
        base_path = os.path.join(home, "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3")
    elif system == "Windows":  # Windows
        # path ของ iCloud บน Windows มักจะอยู่ใน iCloudDrive
        base_path = os.path.join(home, "C:\\Users\\aaa\\iCloudDrive\\iCloud~com~omz-software~Pythonista3")
    else:
        return "Unsupported OS"

    target_path = os.path.join(base_path, folder_name)
    print(f"Path สำหรับโครงการ '{folder_name}' คือ:")
    print(target_path)
    return target_path

# ฟังก์ชันใหม่ที่คุณต้องการ (ไม่ต้องใส่ Parameter)
def syncfile_from_codefolder_to_pythonistaicloud():
    # 1. ดึงชื่อโฟลเดอร์ปัจจุบัน (Current Directory Name)
    current_path = os.getcwd()
    folder_name = os.path.basename(current_path)
    
    # 2. หา path ปลายทางใน iCloud
    target_dir = get_icloud_path(folder_name)
    
    # 3. เริ่มทำการ Sync
    script_name = "chanafunction.py" 
    
    print(f"กำลัง Sync ไฟล์จาก: {current_path}")
    print(f"ไปยัง: {target_dir}")

    files = os.listdir(current_path)
    print(f"พบไฟล์ทั้งหมดในโฟลเดอร์นี้: {files}") # <--- เพิ่มบรรทัดนี้
    
    if not os.path.exists(target_dir):
        print(f"ไม่พบโฟลเดอร์ปลายทาง {target_dir} กรุณาสร้างโฟลเดอร์ชื่อ {folder_name} ใน Pythonista ก่อน")
        return

    for filename in files:
        # Debug: เช็คว่าทำไมเงื่อนไขถึงไม่ผ่าน
        is_py = filename.endswith(".py")
        not_self = (filename != script_name)
        not_hidden = (not filename.startswith('.'))
        
        print(f"Checking {filename}: .py={is_py}, not_self={not_self}, not_hidden={not_hidden}")
        
        if is_py and not_self and not_hidden:
            src = os.path.join(current_path, filename)
            dst = os.path.join(target_dir, filename)
            shutil.copy2(src, dst)
            print(f"Successfully synced: {filename}")
# --- ส่วนการใช้งาน ---
if __name__ == "__main__":
    syncfile_from_codefolder_to_pythonistaicloud()