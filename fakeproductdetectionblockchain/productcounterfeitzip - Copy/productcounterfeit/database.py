import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  manufacturer_id INTEGER,
                  batch_number TEXT,
                  manufacturing_date TEXT,
                  expiry_date TEXT,
                  qr_code_hash TEXT UNIQUE,
                  blockchain_tx_hash TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (manufacturer_id) REFERENCES users (id))''')
    
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER,
                  from_user_id INTEGER,
                  to_user_id INTEGER,
                  transaction_type TEXT,
                  blockchain_tx_hash TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (product_id) REFERENCES products (id),
                  FOREIGN KEY (from_user_id) REFERENCES users (id),
                  FOREIGN KEY (to_user_id) REFERENCES users (id))''')
    
    # Insert default admin user
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                 ('admin', 'admin123', 'admin'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn
