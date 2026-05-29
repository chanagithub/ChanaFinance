import os

import console
import dialogs
import ui

import chanafunction
import db_manager
from file_helper import pick_db_file
import income_entry 



def create_button(parent_view, y_pos, title, action_func):
    btn = ui.Button(title=title)
    btn.frame = (50, y_pos, parent_view.width - 100, 50)
    btn.background_color = '#007AFF'
    btn.tint_color = 'white'
    btn.corner_radius = 10
    btn.action = action_func
    parent_view.add_subview(btn)
    return btn


def settings_action(sender, db_path=None):
    try:
        button_index = console.alert(
            'เมนูจัดการ',
            'เลือกรายการที่ต้องการ',
            'สร้างไฟล์ใหม่',
            'จัดการข้อมูล',
        )
    except (KeyboardInterrupt, Exception) as e:
        print('ยกเลิกหรือปิดเมนู: {}'.format(e))
        return

    if button_index == 1:
        chanafunction.create_new_file()
    elif button_index == 2:
        if db_path:
            db_manager.open_database_manager(db_path)
        else:
            dialogs.hud_alert('ยังไม่ได้เลือกไฟล์ฐานข้อมูล', icon='error')

def main():
    script_dir = chanafunction.get_chana_finance_path("ChanaFinance")
    #script_dir = os.path.dirname(os.path.abspath(__file__))
    selected_file_path = pick_db_file('Select Database File', script_dir, ['.db'])

    if selected_file_path:
        print('คุณเลือกไฟล์: {}'.format(selected_file_path))
        show_main_menu(selected_file_path)
    else:
        print('ยังไม่ได้เลือกไฟล์ฐานข้อมูล โปรแกรมจะปิดตัวลง')


def show_main_menu(db_path):
    view = ui.View(name='ChanaFinance')
    w, h = ui.get_screen_size()
    view.frame = (0, 0, w, h)
    view.background_color = 'white'

    buttons = [
        ('รายรับ', lambda sender: income_entry.show(db_path)),    
        ('รายจ่าย', lambda sender: print('รายจ่าย')),
        ('สรุปรายรับ-รายจ่าย/เดือน', lambda sender: print('สรุปรายเดือน')),
        ('สรุปยอดรายปี', lambda sender: print('สรุปรายปี')),
        ('ออก', lambda sender: view.close()),
    ]

    for index, (title, action) in enumerate(buttons):
        create_button(view, 50 + (index * 80), title, action)

    settings_btn = ui.ButtonItem(title='...')
    settings_btn.action = lambda sender: settings_action(sender, db_path)
    view.right_button_items = [settings_btn]

    view.present(style='full_screen')


if __name__ == '__main__':
    main()
