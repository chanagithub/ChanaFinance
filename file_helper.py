import ui
import os

class DBFilePicker(ui.View):
    def __init__(self, title, root_dir, file_types):
        self.root_dir = root_dir
        self.file_types = file_types # เช่น ['.db', '.sqlite']
        self.selected_file = None
        
        # ตั้งค่า UI
        self.name = title  # นำ title มาใช้เป็นชื่อหัวหน้าต่าง
        self.background_color = 'white'
        
        # กรองไฟล์
        self.files = [f for f in os.listdir(root_dir) 
                      if any(f.endswith(ext) for ext in self.file_types)]
        
        self.table_view = ui.TableView()
        self.table_view.flex = 'WH'
        self.table_view.data_source = self
        self.table_view.delegate = self
        self.add_subview(self.table_view)
        
    def tableview_number_of_rows(self, tv, section):
        return len(self.files)
    
    def tableview_cell_for_row(self, tv, section, row):
        cell = ui.TableViewCell()
        cell.text_label.text = self.files[row]
        return cell
    
    def tableview_did_select(self, tv, section, row):
        self.selected_file = os.path.join(self.root_dir, self.files[row])
        self.close()

def pick_db_file(title, root_dir, file_types):
    picker = DBFilePicker(title, root_dir, file_types)
    picker.present('sheet')
    picker.wait_modal()
    return picker.selected_file

# วิธีใช้งาน:
# script_dir = os.path.expanduser('~/Documents') 
# result = pick_db_file('Select Database File', script_dir, ['.db'] )
# if result:
#     print(f"คุณเลือกไฟล์: {result}")