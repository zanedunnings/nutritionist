import sqlite3

DATABASE = 'meal_plans.db'

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create table for meal plans keyed by week
cursor.execute('''
CREATE TABLE IF NOT EXISTS meal_plans (
    week_key TEXT PRIMARY KEY,
    plan TEXT NOT NULL
)
''')

# Create table for modifications
cursor.execute('''
CREATE TABLE IF NOT EXISTS modifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_key TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    context TEXT,
    day TEXT,
    response TEXT,
    FOREIGN KEY (week_key) REFERENCES meal_plans(week_key)
)
''')

conn.commit()
conn.close()

print("Database initialized and tables created.")

