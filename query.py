import sqlite3

conn = sqlite3.connect("retail_management_system.db")

cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

# Clear tables
'''cursor.execute("DELETE FROM customers;")

cursor.execute("DELETE FROM sqlite_sequence WHERE name='customers';")'''

conn.commit()