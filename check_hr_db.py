from pathlib import Path
import sqlite3

db_path = Path("data") / "test_hr.db"
print("DB path:", db_path)
print("Exists:", db_path.exists())

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM employees")
count = cur.fetchone()[0]
conn.close()

print("Employees in DB:", count)
