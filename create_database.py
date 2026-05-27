import sqlite3
import ui
import console

# ตาราง lots: คงไว้ตามเดิม แต่เน้น lot_number เป็น UNIQUE และ NOT NULL
CREATE_LOTS_TABLE = """
CREATE TABLE IF NOT EXISTS lots (
    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    lot_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('OPEN', 'CLOSED')) DEFAULT 'OPEN',
    buy_date TEXT NOT NULL,
    buy_volume REAL NOT NULL,
    buy_price_per_unit REAL NOT NULL,
    buy_commission REAL NOT NULL DEFAULT 0,
    remaining_volume REAL NOT NULL
);
"""

# ตาราง dividends: แก้ lot_id เป็น TEXT
CREATE_DIVIDENDS_TABLE = """
CREATE TABLE IF NOT EXISTS dividends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL, -- เปลี่ยนเป็น TEXT เพื่อเก็บ lot_number
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL,
    tax REAL DEFAULT 0,
    FOREIGN KEY (lot_id) REFERENCES lots (lot_number) -- อ้างอิงไปที่ lot_number
);
"""

# ตาราง capital_returns: แก้ lot_id เป็น TEXT
CREATE_CAPITAL_RETURNS_TABLE = """
CREATE TABLE IF NOT EXISTS capital_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL, -- เปลี่ยนเป็น TEXT เพื่อเก็บ lot_number
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (lot_id) REFERENCES lots (lot_number) -- อ้างอิงไปที่ lot_number
);
"""

# ตาราง sales: แก้ lot_id เป็น TEXT (จุดที่เป็นปัญหาบน Desktop)
CREATE_SALES_TABLE = """
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL, -- เปลี่ยนเป็น TEXT เพื่อเก็บ lot_number
    sell_date TEXT NOT NULL,
    sell_volume REAL NOT NULL,
    sell_price_per_unit REAL NOT NULL,
    sell_commission REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (lot_id) REFERENCES lots (lot_number) -- อ้างอิงไปที่ lot_number
);
"""

# ตาราง waiting_lots: ปรับปรุงให้สอดคล้องกัน
CREATE_WAITING_LOTS_TABLE = """
CREATE TABLE IF NOT EXISTS waiting_lots (
    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    lot_number TEXT,
    date TEXT NOT NULL,
    volume REAL NOT NULL,
    price_per_unit REAL NOT NULL,
    amount REAL,
    remaining_volume REAL,
    commission REAL DEFAULT 0,
    status TEXT DEFAULT 'WAITING'
);
"""

def create_database(db_path):
    """Connects to the database and creates tables with TEXT lot_id."""
    conn = None
    try:
        console.hud_alert(f"กำลังสร้างฐานข้อมูล...", 'success')
        print(f"Connecting to database '{db_path}'...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # เปิดใช้งาน Foreign Key Support ใน SQLite (สำคัญ)
        cursor.execute("PRAGMA foreign_keys = ON;")

        print("Creating 'lots' table...")
        cursor.execute(CREATE_LOTS_TABLE)

        print("Creating 'dividends' table...")
        cursor.execute(CREATE_DIVIDENDS_TABLE)

        print("Creating 'capital_returns' table...")
        cursor.execute(CREATE_CAPITAL_RETURNS_TABLE)
        
        print("Creating 'sales' table...")
        cursor.execute(CREATE_SALES_TABLE)
        
        print("Creating 'waiting_lots' table...")
        cursor.execute(CREATE_WAITING_LOTS_TABLE)

        conn.commit()
        console.hud_alert(f"สร้างฐานข้อมูลสำเร็จ", 'success')
        print("Database schema updated to TEXT lot_id.")

    except sqlite3.Error as e:
        console.hud_alert(f"Database error: {e}", 'error')
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    # สำหรับทดสอบบน Pythonista
    import os
    test_db = os.path.join(os.path.expanduser('~'), 'Documents/test_stock.db')
    create_database(test_db)