from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import sqlite3
import qrcode
import os
from io import BytesIO
import base64
import hashlib
import json
from datetime import datetime
# QR processing dependencies (OpenCV required; pyzbar optional)
QR_PROCESSING_AVAILABLE = False
PYZBAR_AVAILABLE = False
try:
    import cv2
    import numpy as np
    QR_PROCESSING_AVAILABLE = True
    try:
        from pyzbar import pyzbar
        PYZBAR_AVAILABLE = True
    except Exception:
        # Catch DLL load errors and any other issues so startup doesn't fail
        PYZBAR_AVAILABLE = False
except ImportError:
    QR_PROCESSING_AVAILABLE = False
import re
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/qrcodes'

# Initialize database
def init_db():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  email TEXT,
                  company_name TEXT,
                  phone TEXT,
                  wallet_address TEXT,
                  customer_id TEXT UNIQUE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  category TEXT,
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
        c.execute("INSERT INTO users (username, password, role, email, company_name) VALUES (?, ?, ?, ?, ?)",
                 ('admin', 'admin123', 'admin', 'admin@system.com', 'System Admin'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()
    
    # Add category column if it doesn't exist (for existing databases)
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        c.execute("ALTER TABLE products ADD COLUMN category TEXT")
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add customer_id column if it doesn't exist (for existing databases)
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        # Check if column exists
        c.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in c.fetchall()]
        if 'customer_id' not in columns:
            # SQLite doesn't support UNIQUE in ALTER TABLE, so add without it
            c.execute("ALTER TABLE users ADD COLUMN customer_id TEXT")
            # Create unique index separately
            try:
                c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_customer_id ON users(customer_id)")
            except sqlite3.OperationalError:
                # Index might already exist or unique constraint failed, ignore
                pass
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        # Column already exists or other error, ignore
        print(f"Note: customer_id column migration: {e}")
        pass
    
    # Create demo products for testing
    create_demo_products()

def create_demo_products():
    """Create demo products for testing verification"""
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        
        # Check if demo products already exist
        existing = c.execute("SELECT COUNT(*) FROM products WHERE name LIKE 'Demo Product%'").fetchone()[0]
        if existing > 0:
            conn.close()
            return
        
        # Get the first manufacturer user
        manufacturer = c.execute("SELECT id FROM users WHERE role = 'manufacturer' LIMIT 1").fetchone()
        if not manufacturer:
            conn.close()
            return
        
        manufacturer_id = manufacturer[0]
        
        # Create demo products
        demo_products = [
            {
                'name': 'Demo Product 1 - Electronics',
                'description': 'A demo electronic product for testing',
                'category': 'Electronics',
                'batch_number': 'DEMO-001',
                'manufacturing_date': '2024-01-15',
                'expiry_date': '2026-01-15',
                'qr_code_hash': 'demo_qr_hash_manufacturer_1',
                'blockchain_tx_hash': '0x' + hashlib.sha256('demo1'.encode()).hexdigest()[:40]
            },
            {
                'name': 'Demo Product 2 - Furniture',
                'description': 'A demo furniture product for testing',
                'category': 'Furniture',
                'batch_number': 'DEMO-002',
                'manufacturing_date': '2024-02-01',
                'expiry_date': '2029-02-01',
                'qr_code_hash': 'demo_qr_hash_manufacturer_2',
                'blockchain_tx_hash': '0x' + hashlib.sha256('demo2'.encode()).hexdigest()[:40]
            },
            {
                'name': 'Demo Product 3 - Food',
                'description': 'A demo food product for testing',
                'category': 'Packaged Food & Beverages',
                'batch_number': 'DEMO-003',
                'manufacturing_date': '2024-03-01',
                'expiry_date': '2025-03-01',
                'qr_code_hash': 'demo_qr_hash_manufacturer_3',
                'blockchain_tx_hash': '0x' + hashlib.sha256('demo3'.encode()).hexdigest()[:40]
            }
        ]
        
        for product in demo_products:
            c.execute('''INSERT INTO products 
                        (name, description, category, manufacturer_id, batch_number, 
                         manufacturing_date, expiry_date, qr_code_hash, blockchain_tx_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (product['name'], product['description'], product['category'], 
                     manufacturer_id, product['batch_number'], product['manufacturing_date'], 
                     product['expiry_date'], product['qr_code_hash'], product['blockchain_tx_hash']))
        
        conn.commit()
        conn.close()
        print("Demo products created successfully!")
        
    except Exception as e:
        print(f"Error creating demo products: {e}")
        if 'conn' in locals():
            conn.close()

def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn


def set_user_session(user_row):
    """Persist the minimal session payload we need everywhere."""
    session['user_id'] = user_row['id']
    session['username'] = user_row['username']
    session['role'] = user_row['role']
    session['email'] = user_row['email']
    session['company_name'] = user_row['company_name']


def resolve_next_url(default_endpoint):
    """Return a safe next URL confined to this app."""
    candidate = request.args.get('next') or request.form.get('next')
    if candidate and candidate.startswith('/') and not candidate.startswith('//'):
        return candidate
    return url_for(default_endpoint)

# Initialize database
init_db()

# Ensure settings table exists before any component tries to use it
def ensure_settings_table():
    try:
        conn = get_db_connection()
        conn.execute('''CREATE TABLE IF NOT EXISTS settings
                     (key TEXT PRIMARY KEY,
                      value TEXT)''')
        conn.commit()
        conn.close()
    except Exception:
        # Best-effort; downstream code also guards
        pass

ensure_settings_table()

# Simple key/value settings helpers
def get_setting(key, default=None):
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
        conn.close()
        return row['value'] if row else default
    except Exception:
        return default

def set_setting(key, value):
    try:
        conn = get_db_connection()
        conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# QR signing key management (Ethereum-style ECDSA using eth_account)
def get_or_create_qr_signing_keypair():
    """Create or load an app-level QR signing private key; return (private_key_hex, address)."""
    priv = get_setting('qr_signing_private_key')
    if not priv:
        # Generate a new private key (32 bytes hex) and store it
        acct = Account.create()
        priv = acct.key.hex()
        set_setting('qr_signing_private_key', priv)
        set_setting('qr_signing_address', acct.address)
        return priv, acct.address
    # Derive address from the stored private key
    account = Account.from_key(priv)
    # Ensure address stored for reference
    set_setting('qr_signing_address', account.address)
    return priv, account.address

def sign_product_hash(product_hash):
    """Sign the product hash with the app's QR signing key and return 0x-hex signature and signer address."""
    priv, address = get_or_create_qr_signing_keypair()
    # Ethereum signed message prefix (EIP-191) via encode_defunct
    message = encode_defunct(text=product_hash)
    signed = Account.sign_message(message, private_key=priv)
    return signed.signature.hex(), address

def verify_qr_signature(product_hash, signature_hex, expected_address=None):
    """Verify signature; optionally check matches expected signer address. Returns (bool, recovered_address)."""
    try:
        if signature_hex.startswith('0x'):
            sig_bytes = bytes.fromhex(signature_hex[2:])
        else:
            sig_bytes = bytes.fromhex(signature_hex)
        message = encode_defunct(text=product_hash)
        recovered = Account.recover_message(message, signature=sig_bytes)
        if expected_address:
            return recovered.lower() == expected_address.lower(), recovered
        return True, recovered
    except Exception:
        return False, None

def build_qr_payload(product_hash):
    """Build signed QR payload JSON string for a product hash."""
    signature, signer = sign_product_hash(product_hash)
    payload = {
        'v': 1,
        'ph': product_hash,
        'sig': signature,
        'addr': signer,
        'ts': int(datetime.utcnow().timestamp())
    }
    # Compact JSON to reduce QR size
    return json.dumps(payload, separators=(',', ':'))

def build_verification_url(qr_content):
    """Return a full, short URL that renders product details when opened on mobile.
    If given a signed JSON payload, extract the product hash and use /verify?ph=<hash>.
    If given a legacy hash string, use it directly.
    """
    product_hash = None
    try:
        if isinstance(qr_content, str) and qr_content.strip().startswith('{'):
            payload = json.loads(qr_content)
            product_hash = payload.get('ph')
    except Exception:
        product_hash = None
    if not product_hash:
        product_hash = qr_content
    # Prefer a configured public base URL so mobile scanners can resolve outside localhost
    public_base = os.environ.get('PUBLIC_BASE_URL', '').strip()
    if public_base:
        public_base = public_base.rstrip('/')
        return f"{public_base}{url_for('public_verify', ph=product_hash)}"
    # Fallback: build external URL from current request context
    return url_for('public_verify', ph=product_hash, _external=True)

# Ganache Blockchain Integration
class GanacheBlockchain:
    def __init__(self):
        # Connect to Ganache
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
        self.contract_address = None
        self.contract = None
        self.contract_abi = self.get_contract_abi()
        self.deploy_contract()
    
    def get_contract_abi(self):
        """Return the ABI for our product registry contract"""
        return [
            {
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "bytes32",
                        "name": "productId",
                        "type": "bytes32"
                    },
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "manufacturer",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "string",
                        "name": "productName",
                        "type": "string"
                    }
                ],
                "name": "ProductRegistered",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "bytes32",
                        "name": "productId",
                        "type": "bytes32"
                    },
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "fromAddress",
                        "type": "address"
                    },
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "toAddress",
                        "type": "address"
                    }
                ],
                "name": "ProductTransferred",
                "type": "event"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "productId",
                        "type": "bytes32"
                    }
                ],
                "name": "getProduct",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "manufacturer",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "registrationTime",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "exists",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "productId",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "string",
                        "name": "productName",
                        "type": "string"
                    }
                ],
                "name": "registerProduct",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "productId",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "address",
                        "name": "toAddress",
                        "type": "address"
                    }
                ],
                "name": "transferProduct",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "",
                        "type": "bytes32"
                    }
                ],
                "name": "products",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "manufacturer",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "registrationTime",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "exists",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def deploy_contract(self):
        """Deploy the contract to Ganache"""
        try:
            if self.w3.is_connected():
                # Check if we already have a contract address stored
                conn = get_db_connection()
                setting = conn.execute("SELECT value FROM settings WHERE key = 'contract_address'").fetchone()
                conn.close()
                
                if setting:
                    self.contract_address = setting['value']
                    self.contract = self.w3.eth.contract(
                        address=self.contract_address,
                        abi=self.contract_abi
                    )
                    print(f"Contract loaded from storage: {self.contract_address}")
                    return
                
                # Deploy new contract
                account = self.w3.eth.accounts[0]
                
                # Contract bytecode (you'd need the actual compiled bytecode)
                # For now, we'll use a mock deployment
                contract_bytecode = "0x" + "0" * 40  # Mock bytecode
                
                # Build deployment transaction
                ProductRegistry = self.w3.eth.contract(
                    abi=self.contract_abi,
                    bytecode=contract_bytecode
                )
                
                transaction = ProductRegistry.constructor().build_transaction({
                    'from': account,
                    'nonce': self.w3.eth.get_transaction_count(account),
                    'gas': 3000000,
                    'gasPrice': self.w3.to_wei('50', 'gwei')
                })
                
                # For demo purposes, we'll create a mock contract address
                # In production, you'd sign and send the actual transaction
                mock_contract_address = Web3.to_checksum_address(
                    "0x" + hashlib.sha256(b"product_registry").hexdigest()[:40]
                )
                
                self.contract_address = mock_contract_address
                self.contract = self.w3.eth.contract(
                    address=self.contract_address,
                    abi=self.contract_abi
                )
                
                # Store contract address
                conn = get_db_connection()
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                           ('contract_address', self.contract_address))
                conn.commit()
                conn.close()
                
                print(f"Contract deployed at: {self.contract_address}")
                
            else:
                print("Not connected to Ganache")
                self.contract = None
                
        except Exception as e:
            print(f"Contract deployment error: {e}")
            self.contract = None
    
    def is_connected(self):
        return self.w3.is_connected()
    
    def get_accounts(self):
        """Get available accounts from Ganache"""
        if self.is_connected():
            return self.w3.eth.accounts
        return []
    
    def generate_product_hash(self, product_data):
        """Generate unique hash for product"""
        data_string = f"{product_data['name']}{product_data['batch_number']}{product_data['manufacturing_date']}"
        return self.w3.keccak(text=data_string).hex()
    
    def register_product(self, product_data, manufacturer_address=None):
        """Register product on blockchain"""
        try:
            if not self.contract:
                raise Exception("Contract not deployed")
            
            product_hash = self.generate_product_hash(product_data)
            product_hash_bytes = self.w3.to_bytes(hexstr=product_hash)
            
            # Use first Ganache account if no manufacturer address provided
            if not manufacturer_address and self.get_accounts():
                manufacturer_address = self.get_accounts()[0]
            
            # Build transaction
            transaction = self.contract.functions.registerProduct(
                product_hash_bytes,
                product_data['name']
            ).build_transaction({
                'from': manufacturer_address,
                'nonce': self.w3.eth.get_transaction_count(manufacturer_address),
                'gas': 2000000,
                'gasPrice': self.w3.to_wei('50', 'gwei')
            })
            
            # For demo, create a mock transaction hash
            # In production, you'd sign and send the actual transaction
            tx_hash = self.w3.keccak(text=f"{product_hash}{datetime.now().timestamp()}").hex()
            
            print(f"Product registered on blockchain: {tx_hash}")
            return tx_hash, product_hash
            
        except Exception as e:
            print(f"Blockchain registration error: {e}")
            # Fallback: generate local hash
            data_string = f"{product_data['name']}{product_data['batch_number']}{product_data['manufacturing_date']}{datetime.now().timestamp()}"
            product_hash = hashlib.sha256(data_string.encode()).hexdigest()
            tx_hash = "0x" + hashlib.sha256(f"mock{product_hash}".encode()).hexdigest()[:40]
            return tx_hash, product_hash
    
    def transfer_product(self, product_hash, from_address, to_address):
        """Transfer product ownership on blockchain"""
        try:
            if not self.contract:
                raise Exception("Contract not deployed")
            
            product_hash_bytes = self.w3.to_bytes(hexstr=product_hash)
            
            transaction = self.contract.functions.transferProduct(
                product_hash_bytes,
                to_address
            ).build_transaction({
                'from': from_address,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'gas': 2000000,
                'gasPrice': self.w3.to_wei('50', 'gwei')
            })
            
            # Mock transaction hash for demo
            tx_hash = self.w3.keccak(text=f"transfer{product_hash}{datetime.now().timestamp()}").hex()
            
            print(f"Product transferred on blockchain: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            print(f"Blockchain transfer error: {e}")
            tx_hash = "0x" + hashlib.sha256(f"transfer{product_hash}{datetime.now().timestamp()}".encode()).hexdigest()[:40]
            return tx_hash
    
    def verify_product(self, product_hash):
        """Verify product on blockchain"""
        try:
            if not self.contract:
                return None
            
            product_hash_bytes = self.w3.to_bytes(hexstr=product_hash)
            
            # Mock verification for demo
            # In production, you'd call the actual contract function
            return {
                'manufacturer': self.get_accounts()[0] if self.get_accounts() else '0x0',
                'registrationTime': int(datetime.now().timestamp()),
                'exists': True,
                'blockNumber': self.w3.eth.block_number if self.is_connected() else 1
            }
            
        except Exception as e:
            print(f"Blockchain verification error: {e}")
            return None

# Initialize blockchain
try:
    blockchain = GanacheBlockchain()
    BLOCKCHAIN_ACTIVE = blockchain.is_connected()
except Exception as e:
    print(f"Blockchain initialization failed: {e}")
    blockchain = None
    BLOCKCHAIN_ACTIVE = False

def generate_qr_code(data):
    """Generate QR code and return as base64"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"QR generation error: {e}")
        return None

# Routes
@app.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'manufacturer':
            return redirect(url_for('manufacturer_dashboard'))
        elif session['role'] == 'vendor':
            return redirect(url_for('vendor_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    
    # Show landing page for non-logged-in users
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                           (username, password)).fetchone()
        conn.close()
        
        if user:
            set_user_session(user)
            flash('Login successful!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'manufacturer':
                return redirect(url_for('manufacturer_dashboard'))
            elif user['role'] == 'vendor':
                return redirect(url_for('vendor_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')


@app.route('/consumer/login', methods=['GET', 'POST'])
def consumer_login():
    """Dedicated login screen for consumers before accessing verification."""
    if session.get('role') == 'consumer':
        return redirect(resolve_next_url('customer_dashboard'))
    
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? AND password = ? AND role = ?',
            (email, password, 'consumer')
        ).fetchone()
        conn.close()
        
        if user:
            set_user_session(user)
            flash('Consumer login successful.', 'success')
            return redirect(resolve_next_url('customer_dashboard'))
        error = 'Invalid email or password. Please try again.'
    
    return render_template('consumer_login.html', error=error, next=resolve_next_url('customer_dashboard'))

def generate_customer_id():
    """Generate a unique Customer ID"""
    import random
    import string
    # Generate a 10-character alphanumeric ID with prefix CUST-
    prefix = "CUST-"
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return prefix + random_part

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        company_name = request.form.get('company_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = 'consumer'  # Public registrations are consumer-only
        
        # Validate inputs
        if not username or not password or not email:
            flash('Username, email, and password are required', 'error')
            return render_template('register.html')
        
        # Email validation
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address', 'error')
            return render_template('register.html')
        
        # Username validation (3-30 characters, alphanumeric and underscores)
        if len(username) < 3 or len(username) > 30:
            flash('Username must be between 3 and 30 characters', 'error')
            return render_template('register.html')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username can only contain letters, numbers, and underscores', 'error')
            return render_template('register.html')
        
        # Password validation
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('register.html')
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter', 'error')
            return render_template('register.html')
        if not re.search(r'[a-z]', password):
            flash('Password must contain at least one lowercase letter', 'error')
            return render_template('register.html')
        if not re.search(r'[0-9]', password):
            flash('Password must contain at least one number', 'error')
            return render_template('register.html')
        if not re.search(r'[!@#$%^&*]', password):
            flash('Password must contain at least one special character (!@#$%^&*)', 'error')
            return render_template('register.html')
        
        # Generate unique Customer ID
        conn = get_db_connection()
        
        # Ensure customer_id column exists (runtime check)
        try:
            c = conn.cursor()
            c.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in c.fetchall()]
            if 'customer_id' not in columns:
                c.execute("ALTER TABLE users ADD COLUMN customer_id TEXT")
                try:
                    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_customer_id ON users(customer_id)")
                except:
                    pass
                conn.commit()
        except Exception as e:
            print(f"Warning: Could not ensure customer_id column exists: {e}")
        
        customer_id = generate_customer_id()
        
        # Ensure Customer ID is unique
        max_attempts = 100
        for attempt in range(max_attempts):
            try:
                existing = conn.execute('SELECT id FROM users WHERE customer_id = ?', (customer_id,)).fetchone()
                if not existing:
                    break
            except sqlite3.OperationalError:
                # Column doesn't exist yet, skip uniqueness check for first attempt
                if attempt == 0:
                    break
            customer_id = generate_customer_id()
        else:
            conn.close()
            flash('Error generating unique Customer ID. Please try again.', 'error')
            return render_template('register.html')
        
        # Generate a mock wallet address for the user
        wallet_address = Web3.to_checksum_address(
            "0x" + hashlib.sha256(f"{username}{datetime.now().timestamp()}".encode()).hexdigest()[:40]
        )
        
        try:
            conn.execute('INSERT INTO users (username, password, role, email, company_name, phone, wallet_address, customer_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (username, password, role, email, company_name, phone, wallet_address, customer_id))
            conn.commit()
            
            # Store customer_id in session temporarily to display on success page
            session['registration_customer_id'] = customer_id
            session['registration_username'] = username
            
            flash(f'Registration successful! Your Customer ID is: {customer_id}', 'success')
            return redirect(url_for('registration_success'))
        except sqlite3.IntegrityError as e:
            error_msg = str(e)
            if 'username' in error_msg.lower():
                flash('Username already exists. Please choose a different username.', 'error')
            elif 'customer_id' in error_msg.lower():
                flash('Error: Customer ID conflict. Please try again.', 'error')
            else:
                flash('Registration failed. Please try again.', 'error')
        except Exception as e:
            flash(f'Registration error: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/registration/success')
def registration_success():
    """Display registration success page with Customer ID"""
    customer_id = session.pop('registration_customer_id', None)
    username = session.pop('registration_username', None)
    
    if not customer_id or not username:
        flash('Registration information not found. Redirecting to login.', 'info')
        return redirect(url_for('login'))
    
    return render_template('registration_success.html', customer_id=customer_id, username=username)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not username or not email:
            flash('Username and email are required.', 'error')
            return redirect(url_for('forgot_password'))
        
        if new_password != confirm_password:
            flash('New password and confirmation do not match.', 'error')
            return redirect(url_for('forgot_password'))
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND email = ?',
            (username, email)
        ).fetchone()
        
        if not user:
            conn.close()
            flash('No account matches the provided details.', 'error')
            return redirect(url_for('forgot_password'))
        
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, user['id']))
        conn.commit()
        conn.close()
        flash('Password updated successfully. Please login with the new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    products = conn.execute('''SELECT p.*, u.username as manufacturer_name 
                             FROM products p 
                             JOIN users u ON p.manufacturer_id = u.id''').fetchall()
    
    # Get blockchain status
    blockchain_status = {
        'connected': BLOCKCHAIN_ACTIVE,
        'accounts': blockchain.get_accounts() if blockchain else [],
        'contract_address': blockchain.contract_address if blockchain else None,
        'block_number': blockchain.w3.eth.block_number if blockchain and BLOCKCHAIN_ACTIVE else 0
    }
    
    conn.close()
    
    return render_template('admin.html', 
                         users=users, 
                         products=products,
                         blockchain=blockchain_status)


@app.route('/admin/users/create', methods=['POST'])
def admin_create_user():
    if session.get('role') != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    email = request.form.get('email', '').strip()
    company_name = request.form.get('company_name', '').strip()
    phone = request.form.get('phone', '').strip()
    role = request.form.get('role', 'manufacturer').strip()
    
    # Only allow manufacturer and vendor roles (consumers self-register)
    if role not in ('manufacturer', 'vendor'):
        flash('Invalid role. Only Manufacturer and Vendor accounts can be created by admin.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if not username or not password:
        flash('Username and password are required to create a user.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    try:
        wallet_address = Web3.to_checksum_address(
            "0x" + hashlib.sha256(f"{username}{datetime.now().timestamp()}".encode()).hexdigest()[:40]
        )
        conn.execute(
            '''INSERT INTO users (username, password, role, email, company_name, phone, wallet_address)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (username, password, role, email, company_name, phone, wallet_address)
        )
        conn.commit()
        flash(f'{role.capitalize()} account created successfully.', 'success')
    except sqlite3.IntegrityError:
        flash('Username already exists. Please choose a different one.', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/manufacturer/dashboard')
def manufacturer_dashboard():
    if session.get('role') != 'manufacturer':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE manufacturer_id = ?', 
                           (session['user_id'],)).fetchall()
    
    # Generate QR codes for each product
    products_with_qr = []
    for product in products:
        product_dict = dict(product)
        if product_dict['qr_code_hash']:
            payload = build_qr_payload(product_dict['qr_code_hash'])
            verify_url = build_verification_url(payload)
            qr_code = generate_qr_code(verify_url)
            product_dict['qr_code'] = qr_code
        products_with_qr.append(product_dict)
    
    conn.close()
    
    return render_template('manufacturer.html', products=products_with_qr)

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if session.get('role') != 'vendor':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    products = conn.execute('''SELECT p.*, u.username as manufacturer_name 
                             FROM products p 
                             JOIN users u ON p.manufacturer_id = u.id''').fetchall()
    
    inventory = conn.execute('''SELECT p.*, u.username as manufacturer_name, t.timestamp as purchase_date
                              FROM products p
                              JOIN transactions t ON p.id = t.product_id
                              JOIN users u ON p.manufacturer_id = u.id
                              WHERE t.to_user_id = ? AND t.transaction_type = 'purchase'
                              ORDER BY t.timestamp DESC''', 
                           (session['user_id'],)).fetchall()

    # Compute vendor dashboard KPIs
    # 1) Verified products among available products
    verified_products_count = 0
    manufacturers_set = set()
    for p in products:
        if p['blockchain_tx_hash'] and len(str(p['blockchain_tx_hash']).strip()) > 0:
            verified_products_count += 1
        manufacturers_set.add(p['manufacturer_id'])

    # 2) Transactions involving this vendor (purchases and sales)
    tx_row = conn.execute('''SELECT COUNT(*) as cnt FROM transactions 
                          WHERE to_user_id = ? OR from_user_id = ?''',
                        (session['user_id'], session['user_id'])).fetchone()
    transactions_count = tx_row['cnt'] if tx_row else 0
    
    manufacturers_count = len(manufacturers_set)
    
    inventory_with_qr = []
    for item in inventory:
        item_dict = dict(item)
        if item_dict['qr_code_hash']:
            payload = build_qr_payload(item_dict['qr_code_hash'])
            verify_url = build_verification_url(payload)
            qr_code = generate_qr_code(verify_url)
            item_dict['qr_code'] = qr_code
        inventory_with_qr.append(item_dict)
    
    conn.close()
    
    return render_template('vendor.html', 
                         products=products, 
                         inventory=inventory_with_qr,
                         verified_products=verified_products_count,
                         transactions=transactions_count,
                         manufacturers=manufacturers_count)

@app.route('/customer/dashboard')
def customer_dashboard():
    if session.get('role') != 'consumer':
        flash('Please login as a consumer to access product verification.', 'error')
        return redirect(url_for('consumer_login', next=url_for('customer_dashboard')))
    return render_template('customer.html')

@app.route('/manufacturer/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'manufacturer':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    batch_number = request.form['batch_number']
    manufacturing_date = request.form['manufacturing_date']
    expiry_date = request.form['expiry_date']
    
    if manufacturing_date >= expiry_date:
        flash('Expiry date must be after manufacturing date!', 'error')
        return redirect(url_for('manufacturer_dashboard'))
    
    product_data = {
        'name': name,
        'batch_number': batch_number,
        'manufacturing_date': manufacturing_date
    }
    
    try:
        # Register on blockchain
        tx_hash, qr_hash = blockchain.register_product(product_data) if blockchain else (
            "0x" + hashlib.sha256(f"mock{datetime.now().timestamp()}".encode()).hexdigest()[:40],
            hashlib.sha256(f"{name}{batch_number}{manufacturing_date}".encode()).hexdigest()
        )
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO products 
                        (name, description, category, manufacturer_id, batch_number, 
                         manufacturing_date, expiry_date, qr_code_hash, blockchain_tx_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (name, description, category, session['user_id'], batch_number,
                     manufacturing_date, expiry_date, qr_hash, tx_hash))
        conn.commit()
        conn.close()
        
        flash(f'Product added successfully! Blockchain TX: {tx_hash[:20]}...', 'success')
        
    except Exception as e:
        flash(f'Error adding product: {str(e)}', 'error')
    
    return redirect(url_for('manufacturer_dashboard'))

@app.route('/scan_qr', methods=['POST'])
def scan_qr():
    try:
        qr_data = request.json.get('qr_data')
        
        if not qr_data:
            return jsonify({'success': False, 'message': 'No QR data provided'})
        
        print(f"Scanning QR: {qr_data}")  # Debug log

        # Detect signed payload vs legacy hash
        signed_payload = None
        product_hash = None
        signature_valid = None
        signer_address = None
        try:
            if isinstance(qr_data, str) and qr_data.strip().startswith('{'):
                signed_payload = json.loads(qr_data)
                product_hash = signed_payload.get('ph')
                sig = signed_payload.get('sig')
                addr = signed_payload.get('addr')
                ok, recovered = verify_qr_signature(product_hash, sig, expected_address=addr)
                signature_valid = ok
                signer_address = recovered
        except Exception as _:
            signed_payload = None
            product_hash = None

        # Fallback to legacy behavior if not signed payload
        if not product_hash:
            product_hash = qr_data
        
        conn = get_db_connection()
        product = conn.execute('''SELECT p.*, u.username as manufacturer_name 
                                FROM products p 
                                JOIN users u ON p.manufacturer_id = u.id 
                                WHERE p.qr_code_hash = ?''', (product_hash,)).fetchone()
        conn.close()
        
        if product:
            print(f"Product found: {product['name']}")  # Debug log
            
            # Verify on blockchain (only when blockchain is active)
            blockchain_verification = (
                blockchain.verify_product(product_hash)
                if (blockchain and BLOCKCHAIN_ACTIVE)
                else None
            )
            
            product_info = {
                'name': product['name'],
                'description': product['description'],
                'category': product['category'] if 'category' in product.keys() else None,
                'manufacturer': product['manufacturer_name'],
                'batch_number': product['batch_number'],
                'manufacturing_date': product['manufacturing_date'],
                'expiry_date': product['expiry_date'],
                'blockchain_verified': bool(
                    blockchain_verification and blockchain_verification.get('exists')
                ),
                'blockchain_tx_hash': product['blockchain_tx_hash'],
                'qr_code_hash': product['qr_code_hash']
            }

            # Attach signature verification results when available
            if signed_payload is not None:
                product_info.update({
                    'signature_present': True,
                    'signature_valid': bool(signature_valid),
                    'signer_address': signer_address,
                })
            else:
                product_info.update({
                    'signature_present': False
                })
            
            if blockchain_verification:
                product_info.update({
                    'blockchain_manufacturer': blockchain_verification['manufacturer'],
                    'blockchain_timestamp': blockchain_verification['registrationTime'],
                    'blockchain_block': blockchain_verification['blockNumber']
                })
            
            return jsonify({'success': True, 'product': product_info})
        else:
            print(f"No product found for QR: {qr_data}")  # Debug log
            return jsonify({'success': False, 'message': 'Product not found'})
            
    except Exception as e:
        print(f"Error in scan_qr: {e}")  # Debug log
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/process_qr_image', methods=['POST'])
def process_qr_image():
    """Process uploaded QR code image and extract hash"""
    try:
        data = request.json
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'})
        
        if not QR_PROCESSING_AVAILABLE:
            return jsonify({'success': False, 'message': 'QR processing libraries not available. Please install opencv-python and numpy.'})
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Invalid image format'})
        
        # 1) Try OpenCV's QRCodeDetector first (no external DLLs required)
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(image)
        if data:
            qr_text = data.strip()
            # Handle URLs (e.g., https://domain.com/verify?ph=hash)
            if qr_text.startswith('http://') or qr_text.startswith('https://'):
                from urllib.parse import urlparse, parse_qs
                try:
                    parsed = urlparse(qr_text)
                    params = parse_qs(parsed.query)
                    # Extract product hash from URL params
                    if 'ph' in params and params['ph']:
                        product_hash = params['ph'][0]
                        return jsonify({'success': True, 'qr_hash': product_hash})
                    # If no ph param, try to extract from path or use full URL
                    if '/verify' in parsed.path:
                        # Fallback: try to extract hash from URL
                        path_parts = parsed.path.split('/')
                        if len(path_parts) > 2:
                            possible_hash = path_parts[-1]
                            if re.match(r'^[a-zA-Z0-9]+$', possible_hash) and len(possible_hash) > 10:
                                return jsonify({'success': True, 'qr_hash': possible_hash})
                except Exception:
                    pass  # Continue to other checks
            # Accept signed JSON payloads
            if qr_text.startswith('{'):
                return jsonify({'success': True, 'qr_hash': qr_text})
            # Accept legacy hashes (alphanumeric, length > 10)
            if re.match(r'^[a-zA-Z0-9]+$', qr_text) and len(qr_text) > 10:
                return jsonify({'success': True, 'qr_hash': qr_text})
            return jsonify({'success': False, 'message': 'Invalid QR code format'})

        # 2) Fallback to pyzbar if available
        if PYZBAR_AVAILABLE:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            qr_codes = pyzbar.decode(gray)
            if not qr_codes:
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                qr_codes = pyzbar.decode(blurred)
                if not qr_codes:
                    thresh = cv2.adaptiveThreshold(
                        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                    )
                    qr_codes = pyzbar.decode(thresh)
            if qr_codes:
                qr_data = qr_codes[0].data.decode('utf-8')
                qr_text = qr_data.strip()
                # Handle URLs (e.g., https://domain.com/verify?ph=hash)
                if qr_text.startswith('http://') or qr_text.startswith('https://'):
                    from urllib.parse import urlparse, parse_qs
                    try:
                        parsed = urlparse(qr_text)
                        params = parse_qs(parsed.query)
                        # Extract product hash from URL params
                        if 'ph' in params and params['ph']:
                            product_hash = params['ph'][0]
                            return jsonify({'success': True, 'qr_hash': product_hash})
                        # If no ph param, try to extract from path
                        if '/verify' in parsed.path:
                            path_parts = parsed.path.split('/')
                            if len(path_parts) > 2:
                                possible_hash = path_parts[-1]
                                if re.match(r'^[a-zA-Z0-9]+$', possible_hash) and len(possible_hash) > 10:
                                    return jsonify({'success': True, 'qr_hash': possible_hash})
                    except Exception:
                        pass  # Continue to other checks
                # Accept signed JSON payloads
                if qr_text.startswith('{'):
                    return jsonify({'success': True, 'qr_hash': qr_text})
                # Accept legacy hashes (alphanumeric, length > 10)
                if re.match(r'^[a-zA-Z0-9]+$', qr_text) and len(qr_text) > 10:
                    return jsonify({'success': True, 'qr_hash': qr_text})
                return jsonify({'success': False, 'message': 'Invalid QR code format'})

        return jsonify({'success': False, 'message': 'No QR code found in image'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'})

@app.route('/download_qr/<qr_hash>')
def download_qr(qr_hash):
    # Build signed payload and embed as verification URL so mobile scanners open details page
    payload = build_qr_payload(qr_hash)
    verify_url = build_verification_url(payload)
    qr_img = generate_qr_code(verify_url)
    if qr_img:
        qr_data = qr_img.split(',')[1]
        qr_bytes = base64.b64decode(qr_data)
        
        return send_file(
            BytesIO(qr_bytes),
            mimetype='image/png',
            as_attachment=True,
            download_name=f'qr_code_{qr_hash[:8]}.png'
        )
    else:
        flash('Error generating QR code', 'error')
        return redirect(url_for('manufacturer_dashboard'))

@app.route('/api/purchase_product', methods=['POST'])
def purchase_product():
    if session.get('role') != 'vendor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    product_id = data.get('product_id')
    
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({'success': False, 'message': 'Product not found'})
    
    try:
        # Get user wallet addresses
        manufacturer = conn.execute('SELECT wallet_address FROM users WHERE id = ?', 
                                  (product['manufacturer_id'],)).fetchone()
        vendor = conn.execute('SELECT wallet_address FROM users WHERE id = ?', 
                            (session['user_id'],)).fetchone()
        
        # Transfer on blockchain
        tx_hash = blockchain.transfer_product(
            product['qr_code_hash'],
            manufacturer['wallet_address'] if manufacturer else '0x0',
            vendor['wallet_address'] if vendor else '0x0'
        ) if blockchain else "0x" + hashlib.sha256(f"transfer{datetime.now().timestamp()}".encode()).hexdigest()[:40]
        
        # Record transaction
        conn.execute('''INSERT INTO transactions 
                        (product_id, from_user_id, to_user_id, transaction_type, blockchain_tx_hash) 
                        VALUES (?, ?, ?, ?, ?)''',
                    (product_id, product['manufacturer_id'], session['user_id'], 'purchase', tx_hash))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product purchased successfully', 'tx_hash': tx_hash})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/profile')
def profile():
    if not session.get('user_id'):
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Get user stats
    stats = {}
    if session['role'] == 'manufacturer':
        total_products_row = conn.execute(
            'SELECT COUNT(*) as count FROM products WHERE manufacturer_id = ?',
            (session['user_id'],)
        ).fetchone()
        blockchain_products_row = conn.execute(
            """
            SELECT COUNT(*) as count FROM products 
            WHERE manufacturer_id = ? 
              AND blockchain_tx_hash IS NOT NULL 
              AND TRIM(blockchain_tx_hash) <> ''
            """,
            (session['user_id'],)
        ).fetchone()
        qr_codes_row = conn.execute(
            """
            SELECT COUNT(*) as count FROM products 
            WHERE manufacturer_id = ? 
              AND qr_code_hash IS NOT NULL 
              AND TRIM(qr_code_hash) <> ''
            """,
            (session['user_id'],)
        ).fetchone()
        stats = {
            'total_products': total_products_row['count'] if total_products_row else 0,
            'blockchain_products': blockchain_products_row['count'] if blockchain_products_row else 0,
            'qr_codes': qr_codes_row['count'] if qr_codes_row else 0
        }
    elif session['role'] == 'vendor':
        purchased = conn.execute('SELECT COUNT(*) as count FROM transactions WHERE to_user_id = ? AND transaction_type = ?', 
                               (session['user_id'], 'purchase')).fetchone()
        stats = {'products_purchased': purchased['count'] if purchased else 0}
    elif session['role'] == 'admin' or session['role'] == 'consumer':
        # For admin/consumer, calculate verification and scan statistics
        # Note: These would ideally come from a verification log table
        # For now, we'll calculate from available transaction data
        verified = conn.execute(
            'SELECT COUNT(DISTINCT product_id) as count FROM transactions WHERE to_user_id = ? AND transaction_type = ?',
            (session['user_id'], 'verification')
        ).fetchone()
        stats = {
            'verified_count': verified['count'] if verified else 0,
            'scan_count': 0  # Would need a scan log table for accurate count
        }
    
    conn.close()
    
    return render_template('profile.html', user=dict(user), stats=stats)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    username = request.form['username']
    email = request.form.get('email', '')
    company_name = request.form.get('company_name', '')
    phone = request.form.get('phone', '')
    current_password = request.form['current_password']
    new_password = request.form.get('new_password', '')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
    if user['password'] != current_password:
        conn.close()
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    try:
        if new_password:
            conn.execute('''UPDATE users SET username = ?, email = ?, company_name = ?, phone = ?, password = ? 
                          WHERE id = ?''',
                        (username, email, company_name, phone, new_password, session['user_id']))
        else:
            conn.execute('''UPDATE users SET username = ?, email = ?, company_name = ?, phone = ? 
                          WHERE id = ?''',
                        (username, email, company_name, phone, session['user_id']))
        
        conn.commit()
        session['username'] = username
        session['email'] = email
        session['company_name'] = company_name
        
        # Recalculate and refresh user statistics
        stats = {}
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        if user_role == 'manufacturer':
            total_products_row = conn.execute(
                'SELECT COUNT(*) as count FROM products WHERE manufacturer_id = ?',
                (user_id,)
            ).fetchone()
            blockchain_products_row = conn.execute(
                """
                SELECT COUNT(*) as count FROM products 
                WHERE manufacturer_id = ? 
                  AND blockchain_tx_hash IS NOT NULL 
                  AND TRIM(blockchain_tx_hash) <> ''
                """,
                (user_id,)
            ).fetchone()
            qr_codes_row = conn.execute(
                """
                SELECT COUNT(*) as count FROM products 
                WHERE manufacturer_id = ? 
                  AND qr_code_hash IS NOT NULL 
                  AND TRIM(qr_code_hash) <> ''
                """,
                (user_id,)
            ).fetchone()
            stats = {
                'total_products': total_products_row['count'] if total_products_row else 0,
                'blockchain_products': blockchain_products_row['count'] if blockchain_products_row else 0,
                'qr_codes': qr_codes_row['count'] if qr_codes_row else 0
            }
        elif user_role == 'vendor':
            purchased = conn.execute('SELECT COUNT(*) as count FROM transactions WHERE to_user_id = ?', 
                                   (user_id,)).fetchone()
            stats = {'products_purchased': purchased['count'] if purchased else 0}
        elif user_role == 'consumer' or user_role == 'admin':
            # For consumers/admins, calculate verification and scan counts
            # Note: This would require a verification/scan log table if it exists
            # For now, we'll set to 0 or calculate from available data
            verified_count = conn.execute(
                'SELECT COUNT(DISTINCT product_id) as count FROM transactions WHERE to_user_id = ? AND transaction_type = ?',
                (user_id, 'verification')
            ).fetchone()
            stats = {
                'verified_count': verified_count['count'] if verified_count else 0,
                'scan_count': 0  # Would need scan log table
            }
        
        conn.close()
        
        # Get refreshed blockchain status
        blockchain_status = {
            'connected': BLOCKCHAIN_ACTIVE,
            'accounts': blockchain.get_accounts() if blockchain else [],
            'contract_address': blockchain.contract_address if blockchain else None,
            'block_number': blockchain.w3.eth.block_number if blockchain and BLOCKCHAIN_ACTIVE else 0,
            'active': blockchain is not None
        }
        
        flash('Profile updated successfully!', 'success')
        return jsonify({
            'success': True, 
            'message': 'Profile updated successfully',
            'stats': stats,
            'blockchain_status': blockchain_status
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/blockchain/status')
def blockchain_status():
    status = {
        'connected': BLOCKCHAIN_ACTIVE,
        'accounts': blockchain.get_accounts() if blockchain else [],
        'contract_address': blockchain.contract_address if blockchain else None,
        'block_number': blockchain.w3.eth.block_number if blockchain and BLOCKCHAIN_ACTIVE else 0,
        'active': blockchain is not None
    }
    return jsonify(status)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

# Add these routes to the existing app.py

@app.route('/api/product_details/<int:product_id>')
def api_product_details(product_id):
    """API endpoint for product details"""
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'})
    
    conn = get_db_connection()
    product = conn.execute('''SELECT p.*, u.username as manufacturer_name, u.company_name
                            FROM products p 
                            JOIN users u ON p.manufacturer_id = u.id 
                            WHERE p.id = ?''', (product_id,)).fetchone()
    conn.close()
    
    if product:
        product_dict = dict(product)
        # Generate QR code for the product
        if product_dict['qr_code_hash']:
            payload = build_qr_payload(product_dict['qr_code_hash'])
            verify_url = build_verification_url(payload)
            product_dict['qr_code'] = generate_qr_code(verify_url)
        
        # Get blockchain verification
        blockchain_info = blockchain.verify_product(product_dict['qr_code_hash']) if blockchain else {
            'manufacturer': '0x' + hashlib.sha256(b"mock_manufacturer").hexdigest()[:40],
            'registrationTime': int(datetime.now().timestamp()),
            'exists': True,
            'blockNumber': 123456
        }
        product_dict['blockchain_info'] = blockchain_info
        
        return jsonify(product_dict)
    else:
        return jsonify({'error': 'Product not found'})

@app.route('/api/vendor_inventory')
def api_vendor_inventory():
    """API endpoint for vendor inventory"""
    if session.get('role') != 'vendor':
        return jsonify([])
    
    conn = get_db_connection()
    inventory = conn.execute('''SELECT p.*, u.username as manufacturer_name, u.company_name, 
                               t.timestamp as purchase_date, t.blockchain_tx_hash
                              FROM products p
                              JOIN transactions t ON p.id = t.product_id
                              JOIN users u ON p.manufacturer_id = u.id
                              WHERE t.to_user_id = ? AND t.transaction_type = 'purchase'
                              ORDER BY t.timestamp DESC''', 
                           (session['user_id'],)).fetchall()
    conn.close()
    
    inventory_list = []
    for item in inventory:
        item_dict = dict(item)
        # Generate QR code for each inventory item
        if item_dict['qr_code_hash']:
            payload = build_qr_payload(item_dict['qr_code_hash'])
            verify_url = build_verification_url(payload)
            item_dict['qr_code'] = generate_qr_code(verify_url)
        inventory_list.append(item_dict)
    
    return jsonify(inventory_list)

@app.route('/api/sell_product', methods=['POST'])
def api_sell_product():
    """API endpoint for selling products"""
    if session.get('role') != 'vendor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    product_id = data.get('product_id')
    
    conn = get_db_connection()
    
    # Check if product exists and belongs to vendor
    product = conn.execute('''SELECT p.*, t.id as transaction_id 
                            FROM products p
                            JOIN transactions t ON p.id = t.product_id
                            WHERE p.id = ? AND t.to_user_id = ? AND t.transaction_type = 'purchase'
                            ORDER BY t.timestamp DESC LIMIT 1''', 
                         (product_id, session['user_id'])).fetchone()
    
    if not product:
        conn.close()
        return jsonify({'success': False, 'message': 'Product not found in inventory'})
    
    try:
        # Record sale transaction
        conn.execute('''INSERT INTO transactions 
                        (product_id, from_user_id, to_user_id, transaction_type, blockchain_tx_hash) 
                        VALUES (?, ?, ?, ?, ?)''',
                    (product_id, session['user_id'], None, 'sale', 
                     "0x" + hashlib.sha256(f"sale{datetime.now().timestamp()}".encode()).hexdigest()[:40]))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product marked as sold successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


# Create settings table if not exists
def create_settings_table():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT)''')
    conn.commit()
    conn.close()

create_settings_table()

# Public mobile-friendly verification route so Google Lens (or any scanner) opens details directly
@app.route('/verify', methods=['GET'])
def public_verify():
    # Prefer short hash param for robust mobile scanning
    product_hash = (request.args.get('ph') or '').strip()
    qr_data = (request.args.get('qr') or request.args.get('q') or request.args.get('d') or '').strip()
    if not product_hash and not qr_data:
        return render_template('public_verify.html', success=False, message='No QR data provided')

    # If a full payload is provided in qr_data, try to parse and verify signature
    try:
        signed_payload = None
        signature_valid = None
        signer_address = None
        if not product_hash and qr_data and qr_data.startswith('{'):
            try:
                signed_payload = json.loads(qr_data)
                product_hash = signed_payload.get('ph')
                sig = signed_payload.get('sig')
                addr = signed_payload.get('addr')
                ok, recovered = verify_qr_signature(product_hash, sig, expected_address=addr)
                signature_valid = ok
                signer_address = recovered
            except Exception:
                signed_payload = None
                signature_valid = None
                signer_address = None
        elif not product_hash:
            product_hash = qr_data

        conn = get_db_connection()
        product = conn.execute('''SELECT p.*, u.username as manufacturer_name 
                                FROM products p 
                                JOIN users u ON p.manufacturer_id = u.id 
                                WHERE p.qr_code_hash = ?''', (product_hash,)).fetchone()
        conn.close()

        if not product:
            return render_template('public_verify.html', success=False, message='Product not found')

        # Optional blockchain verification
        blockchain_verification = (
            blockchain.verify_product(product_hash)
            if (blockchain and BLOCKCHAIN_ACTIVE)
            else None
        )

        product_info = {
            'name': product['name'],
            'description': product['description'],
            'category': product['category'] if 'category' in product.keys() else None,
            'manufacturer': product['manufacturer_name'],
            'batch_number': product['batch_number'],
            'manufacturing_date': product['manufacturing_date'],
            'expiry_date': product['expiry_date'],
            'blockchain_verified': bool(blockchain_verification and blockchain_verification.get('exists')),
            'blockchain_tx_hash': product['blockchain_tx_hash'],
            'qr_code_hash': product['qr_code_hash']
        }

        if signed_payload is not None:
            product_info.update({
                'signature_present': True,
                'signature_valid': bool(signature_valid),
                'signer_address': signer_address,
            })
        else:
            product_info.update({'signature_present': False})

        if blockchain_verification:
            product_info.update({
                'blockchain_manufacturer': blockchain_verification['manufacturer'],
                'blockchain_timestamp': blockchain_verification['registrationTime'],
                'blockchain_block': blockchain_verification['blockNumber']
            })

        return render_template('public_verify.html', success=True, product=product_info)
    except Exception as e:
        return render_template('public_verify.html', success=False, message=f'Error: {str(e)}')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Optional HTTPS for camera access on mobile (set FLASK_USE_HTTPS=1)
    use_https = os.environ.get('FLASK_USE_HTTPS', '0') == '1'
    port = int(os.environ.get('PORT', '5000'))
    ssl_context = 'adhoc' if use_https else None
    app.run(debug=True, host='0.0.0.0', port=port, ssl_context=ssl_context)
    
    
    from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy consumer credentials for example
valid_consumer = {
    "email": "consumer@example.com",
    "password": "12345"
}

@app.route("/consumer/login", methods=["GET", "POST"])
def consumer_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email == valid_consumer["email"] and password == valid_consumer["password"]:
            return redirect(url_for("consumer_dashboard"))
        else:
            return render_template("consumer_login.html", error="Invalid email or password!")

    return render_template("consumer_login.html")


@app.route("/consumer/dashboard")
def consumer_dashboard():
    return render_template("customer_dashboard.html")  # Your existing customer page


from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Simple in-memory user for demo
VALID_USER = {"email": "consumer@example.com", "password": "12345"}

@app.route("/")
def index():
    return redirect(url_for("consumer_login"))

@app.route("/consumer/login", methods=["GET", "POST"])
def consumer_login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if email == VALID_USER["email"] and password == VALID_USER["password"]:
            return redirect(url_for("consumer_dashboard"))
        else:
            error = "Invalid email or password!"
    return render_template("consumer_login.html", error=error)

@app.route("/consumer/dashboard")
def consumer_dashboard():
    return render_template("customer_dashboard.html")

if __name__ == "__main__":
    # Use debug True to auto-reload on changes
    app.run(debug=True)

