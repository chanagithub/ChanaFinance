import ui
import console

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
            print('ไปที่หน้าสร้างไฟล์')
        elif button_index == 2:
            print('ไปที่หน้าจัดการข้อมูล')
    except Exception as e:
        # ดักกรณีผู้ใช้กด Cancel หรือปิดหน้าต่าง Alert
        print(f"ยกเลิกหรือปิดเมนู: {e}")

        
def main():
    view = ui.View(name='ChanaFinance')
    view.background_color = 'white'

    # สร้างปุ่มเมนูหลัก
    buttons = [
        ('รายรับ', lambda s: print('เปิดหน้ารายรับ')),
        ('รายจ่าย', lambda s: print('เปิดหน้ารายจ่าย')),
        ('สรุปรายรับ-รายจ่าย/เดือน', lambda s: print('เปิดหน้าสรุปรายเดือน')),
        ('สรุปยอดรายปี', lambda s: print('เปิดหน้าสรุปรายปี')),
        ('ออก', lambda s: view.close())
    ]

    for i, (title, action) in enumerate(buttons):
        create_button(view, 100 + (i * 70), title, action)

    # สร้างเมนู 3 จุด
    settings_btn = ui.ButtonItem(title='•••')
    settings_btn.action = settings_action
    view.right_button_items = [settings_btn]

    view.present(style='full_screen')

if __name__ == '__main__':
    main()