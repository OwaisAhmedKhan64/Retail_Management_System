import sqlite3

conn = sqlite3.connect("retail_management_system.db")
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS restocks (
    restock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    quantity_added INTEGER NOT NULL,
    cost_price_at_restock REAL NOT NULL,
    restock_date TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
""")

cursor.execute("")

conn.commit()