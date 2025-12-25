import sqlite3

conn = sqlite3.connect("retail_management_system.db")

cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = OFF;")

# Clear tables
cursor.execute("DELETE FROM restocks;")

cursor.execute("DELETE FROM sqlite_sequence WHERE name='restocks';")

conn.commit()