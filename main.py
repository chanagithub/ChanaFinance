import ui
import console
import chanafunction
import os
import dialogs

# ฟังก์ชันสำหรับสร้างปุ่มแบบกำหนดเอง
def create_button(parent_view, y_pos, title, action_func):
    btn = ui.Button(title=title)
    btn.frame = (50, y_pos, parent_view.width - 100, 50)
    btn.background_color = '#007AFF'
    btn.tint_color = 'white'
    btn.corner_radius = 10
    btn.action = action_func
    parent_view.add_subview(btn)
    return btn

def settings_action(sender):
    try:
        button_index = console.alert('เมนูจัดการ', 'เลือกรายการที่ต้องการ', 'สร้างไฟล์ใหม่', 'จัดการข้อมูล')
        if button_index == 1:
            menu_action_create()
        elif button_index == 2:
            print('ไปที่หน้าจัดการข้อมูล')
    except Exception as e:
        # ดักกรณีผู้ใช้กด Cancel หรือปิดหน้าต่าง Alert
        print(f"ยกเลิกหรือปิดเมนู: {e}")

def menu_action_create():
    chanafunction.create_new_file()

# เรียกฟังก์ชันนี้ใน Event ของปุ่มในเมนูของคุณ


def main():

    # 1. กำหนดโฟลเดอร์เริ่มต้นเป็นโฟลเดอร์ของสคริปต์
    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    
    # 2. ใช้ file_picker เพื่อเลือกไฟล์ .db
    # ปรับแต่งให้กรองเฉพาะไฟล์ .db และเลือกได้แค่ไฟล์เดียว
    selected_file_path = dialogs.file_picker(
        title='กรุณาเลือกไฟล์ฐานข้อมูล',
        root_dir=script_dir, # เริ่มต้นที่โฟลเดอร์ของสคริปต์
        multiple=False,
        file_types=['.db'] # หรือใช้ ['.db'] ถ้า Pythonista รองรับ
    )
    
    # 3. ตรวจสอบว่าผู้ใช้เลือกไฟล์หรือไม่ (ถ้ากด Cancel จะได้ค่าเป็น None)
    if selected_file_path:
        # พิมพ์บอกใน Console
        print(f"คุณเลือกไฟล์: {selected_file_path}")
        
        # เก็บ path ไฟล์ไว้ใช้งานต่อไป (อาจจะทำเป็นตัวแปร global หรือส่งเข้า class)
        # ต่อไปนี้คือส่วนแสดงหน้า UI เมนูหลักที่คุณมีอยู่แล้ว
        show_main_menu(selected_file_path)
    else:
        print("ยังไม่ได้เลือกไฟล์ โปรแกรมจะปิดตัวลง")
        return

def show_main_menu(db_path):
    view = ui.View(name='ChanaFinance')
    # ใช้ขนาดหน้าจออุปกรณ์เป็นตัวกำหนด frame ของ view
    w, h = ui.get_screen_size()
    view.frame = (0, 0, w, h)
    view.background_color = 'white'

    buttons = [
        ('รายรับ', lambda _: print('รายรับ')),
        ('รายจ่าย', lambda _: print('รายจ่าย')),
        ('สรุปรายรับ-รายจ่าย/เดือน', lambda _: print('สรุปรายเดือน')),
        ('สรุปยอดรายปี', lambda _: print('สรุปรายปี')),
        ('ออก', lambda _: view.close())
    ]

    for i, (title, action) in enumerate(buttons):
        # ลด y ลงมาให้มั่นใจว่าอยู่ในจอ
        create_button(view, 50 + (i * 80), title, action)

    settings_btn = ui.ButtonItem(title='•••')
    settings_btn.action = settings_action
    view.right_button_items = [settings_btn]

    view.present(style='full_screen')

if __name__ == '__main__':
    main()
