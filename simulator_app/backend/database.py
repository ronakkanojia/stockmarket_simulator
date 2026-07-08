import sqlite3

DB_NAME = "simulator.db"

def init_db():
    """Initializes the database tables and seeds the initial virtual cash."""
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    cursor = conn.cursor()
    
    # Create User Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cash REAL NOT NULL
        )
    ''')
    
    # Create Positions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            strike REAL NOT NULL,
            option_type TEXT NOT NULL, -- 'CALL' or 'PUT'
            expiry TEXT NOT NULL,
            quantity INTEGER NOT NULL,  -- Positive for long, negative for short
            avg_price REAL NOT NULL,
            UNIQUE(ticker, strike, option_type, expiry)
        )
    ''')
    
    # Create Trade History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            strike REAL NOT NULL,
            option_type TEXT NOT NULL,
            expiry TEXT NOT NULL,
            action TEXT NOT NULL, -- 'BUY' or 'SELL'
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Seed ₹1,00,000 cash if database is empty
    cursor.execute("SELECT COUNT(*) FROM user")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO user (cash) VALUES (100000.00)")
        
    conn.commit()
    conn.close()

def get_cash():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    cursor = conn.cursor()
    cursor.execute("SELECT cash FROM user WHERE id = 1")
    cash = cursor.fetchone()[0]
    conn.close()
    return cash

def update_cash(new_cash):
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    cursor = conn.cursor()
    cursor.execute("UPDATE user SET cash = ? WHERE id = 1", (new_cash,))
    conn.commit()
    conn.close()

# Initialize the DB automatically when this module is imported
init_db()