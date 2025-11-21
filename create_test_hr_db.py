import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
db_path = ROOT / "data" / "test_hr.db"
db_path.parent.mkdir(exist_ok=True)

schema = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT,
    hire_date TEXT,
    status TEXT DEFAULT 'active'
);

INSERT OR IGNORE INTO employees (first_name, last_name, email, department, hire_date, status)
VALUES
    ('Alice', 'Johnson', 'alice@company.com', 'Engineering', '2024-01-15', 'active'),
    ('Bob', 'Smith', 'bob@company.com', 'Sales', '2024-03-20', 'active'),
    ('Carol', 'Williams', 'carol@company.com', 'Engineering', '2024-02-10', 'active');
"""

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.executescript(schema)
conn.commit()

cur.execute("SELECT COUNT(*) FROM employees")
count = cur.fetchone()[0]
conn.close()

print(f"Database created at {db_path} with {count} employees")
