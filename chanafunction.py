import os
import platform

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

# --- ส่วนการใช้งาน ---
if __name__ == "__main__":
    # ใส่ชื่อโฟลเดอร์ที่คุณต้องการ เช่น 'ChanaFinance'
    get_icloud_path("ChanaFinance")