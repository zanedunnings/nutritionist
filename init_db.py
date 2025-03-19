import sqlite3

# DATABASE = 'meal_plans.db'

# conn = sqlite3.connect(DATABASE)
# cursor = conn.cursor()

# # Create table for meal plans keyed by week
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS meal_plans (
#     week_key TEXT PRIMARY KEY,
#     plan TEXT NOT NULL
# )
# ''')

# # Create table for modifications
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS modifications (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     week_key TEXT NOT NULL,
#     timestamp TEXT NOT NULL,
#     context TEXT,
#     day TEXT,
#     response TEXT,
#     FOREIGN KEY (week_key) REFERENCES meal_plans(week_key)
# )
# ''')

# ---------- Configuration for Auth -----------
AUTH_SECRET_KEY = "your_auth_secret_key_here"  # Change for production!
ALGORITHM = "HS256"
OTP_EXPIRATION_MINUTES = 5

# ---------- SQLite Database Configuration ----------
DATABASE = "meal_plans.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Initialize Tables (Meal Plans & Auth) ----------
def init_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Table for meal plans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_plans (
            week_key TEXT PRIMARY KEY,
            plan TEXT NOT NULL
        )
    ''')
    # Table for modifications (if used)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS modifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_key TEXT NOT NULL,
            timestamp DATETIME,
            context TEXT,
            day TEXT,
            response TEXT
        )
    ''')
    # Table for users (for phone authentication)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Table for OTPs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            otp TEXT,
            expires_at DATETIME,
            used BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_tables()



# conn.commit()
# conn.close()

print("Database initialized and tables created.")

