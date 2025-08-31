#!/usr/bin/env python3
"""
ANÄ€MAVÄ€K v4.0 - Enhanced Secure Real-Time Messaging System
Advanced multi-layer encryption with enhanced security features
"""

import os
import re
import json
import time
import hmac
import base64
import hashlib
import secrets
import sqlite3
import socket
import webbrowser
import threading
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO
from threading import Lock

import qrcode
from flask import Flask, render_template_string, request, jsonify, session, send_file, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from werkzeug.utils import secure_filename

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max file size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60, ping_interval=25)

# Global locks and state
db_lock = Lock()
users_lock = Lock()
active_users = {}
failed_attempts = {}
rate_limits = {}

# Enhanced Morse code mapping
MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/', '.': '.-.-.-', ',': '--..--',
    '?': '..--..', "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.',
    ')': '-.--.-', '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-',
    '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-',
    '@': '.--.-.'
}
MORSE_DECODE = {v: k for k, v in MORSE_CODE.items()}

class EnhancedCryptoManager:
    """Advanced multi-layer encryption system"""
    
    @staticmethod
    def generate_key():
        return secrets.token_bytes(32)
    
    @staticmethod
    def derive_key(password, salt):
        """Derive encryption key using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    @staticmethod
    def aes_encrypt(data, key):
        """AES-256-GCM encryption"""
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        encrypted_package = iv + ciphertext + encryptor.tag
        return base64.b64encode(encrypted_package).decode()
    
    @staticmethod
    def aes_decrypt(encrypted_data, key):
        """AES-256-GCM decryption"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            iv = encrypted_bytes[:12]
            tag = encrypted_bytes[-16:]
            ciphertext = encrypted_bytes[12:-16]
            
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return decryptor.update(ciphertext) + decryptor.finalize()
        except Exception:
            return None
    
    @staticmethod
    def text_to_morse(text):
        return ' '.join(MORSE_CODE.get(char.upper(), '') for char in text)
    
    @staticmethod
    def morse_to_text(morse):
        try:
            return ''.join(MORSE_DECODE.get(code, '') for code in morse.split(' '))
        except:
            return ""
    
    @staticmethod
    def xor_encrypt(data, key):
        """XOR encryption layer"""
        key_bytes = hashlib.sha256(key.encode()).digest()
        result = bytearray()
        for i, byte in enumerate(data):
            result.append(byte ^ key_bytes[i % len(key_bytes)])
        return bytes(result)
    
    @staticmethod
    def generate_hmac(data, key):
        return hmac.new(key.encode(), data, hashlib.sha256).hexdigest()
    
    @staticmethod
    def verify_hmac(data, key, signature):
        expected = hmac.new(key.encode(), data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    @classmethod
    def quadruple_encrypt(cls, message, user_key):
        """Enhanced 4-layer encryption"""
        salt = secrets.token_bytes(16)
        
        # Layer 1: Morse code obfuscation
        morse_message = cls.text_to_morse(message)
        
        # Layer 2: XOR encryption
        xor_encrypted = cls.xor_encrypt(morse_message.encode(), user_key + "xor_salt")
        
        # Layer 3: AES-256-GCM encryption
        derived_key = cls.derive_key(user_key, salt)
        aes_encrypted = cls.aes_encrypt(xor_encrypted, derived_key)
        
        # Layer 4: HMAC integrity
        hmac_key = user_key + "hmac_salt"
        signature = cls.generate_hmac(aes_encrypted.encode(), hmac_key)
        
        package = {
            'salt': base64.b64encode(salt).decode(),
            'data': aes_encrypted,
            'signature': signature,
            'version': '4.0'
        }
        
        return base64.b64encode(json.dumps(package).encode()).decode()
    
    @classmethod
    def quadruple_decrypt(cls, encrypted_package, user_key):
        """Enhanced 4-layer decryption"""
        try:
            package_data = json.loads(base64.b64decode(encrypted_package).decode())
            salt = base64.b64decode(package_data['salt'])
            encrypted_data = package_data['data']
            signature = package_data['signature']
            
            # Verify HMAC
            hmac_key = user_key + "hmac_salt"
            if not cls.verify_hmac(encrypted_data.encode(), hmac_key, signature):
                return None
            
            # Decrypt AES-256-GCM
            derived_key = cls.derive_key(user_key, salt)
            xor_encrypted = cls.aes_decrypt(encrypted_data, derived_key)
            if xor_encrypted is None:
                return None
            
            # Decrypt XOR
            morse_message = cls.xor_encrypt(xor_encrypted, user_key + "xor_salt")
            
            # Decode Morse
            return cls.morse_to_text(morse_message.decode())
        except Exception:
            return None

class SecurityManager:
    """Enhanced security features"""
    
    @staticmethod
    def is_rate_limited(ip):
        now = time.time()
        if ip not in rate_limits:
            rate_limits[ip] = []
        
        rate_limits[ip] = [req_time for req_time in rate_limits[ip] if now - req_time < 3600]
        return len(rate_limits[ip]) >= 100
    
    @staticmethod
    def add_request(ip):
        now = time.time()
        if ip not in rate_limits:
            rate_limits[ip] = []
        rate_limits[ip].append(now)
    
    @staticmethod
    def is_brute_force_attempt(ip):
        now = time.time()
        if ip not in failed_attempts:
            failed_attempts[ip] = []
        
        failed_attempts[ip] = [attempt_time for attempt_time in failed_attempts[ip] if now - attempt_time < 900]
        return len(failed_attempts[ip]) >= 5
    
    @staticmethod
    def add_failed_attempt(ip):
        now = time.time()
        if ip not in failed_attempts:
            failed_attempts[ip] = []
        failed_attempts[ip].append(now)

class EnhancedDatabaseManager:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT NOT NULL,
                    encrypted_content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    session_id TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    encrypted_data TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_size TEXT,
                    ip_address TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action TEXT,
                    user_key TEXT,
                    success BOOLEAN DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    ip_address TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    severity INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def log_security_event(self, event_type, ip, details, severity=1):
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO security_events (event_type, ip_address, details, severity) VALUES (?, ?, ?, ?)',
                (event_type, ip, details, severity)
            )
            conn.commit()
            conn.close()
    
    def log_access(self, ip, user_agent, action, user_key=None, success=True):
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO access_logs (ip_address, user_agent, action, user_key, success) VALUES (?, ?, ?, ?, ?)',
                (ip, user_agent, action, user_key, success)
            )
            conn.commit()
            conn.close()
    
    def store_message(self, user_key, encrypted_message, ip, session_id):
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO messages (user_key, encrypted_content, ip_address, session_id) VALUES (?, ?, ?, ?)',
                (user_key, encrypted_message, ip, session_id)
            )
            conn.commit()
            conn.close()
    
    def get_messages(self, user_key):
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT encrypted_content, timestamp FROM messages WHERE user_key = ? ORDER BY timestamp DESC LIMIT 100',
                (user_key,)
            )
            messages = cursor.fetchall()
            conn.close()
            return messages
    
    def store_file(self, user_key, filename, encrypted_data, file_size, ip):
        file_hash = hashlib.sha256(encrypted_data.encode()).hexdigest()
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO files (user_key, filename, encrypted_data, file_hash, file_size, ip_address) VALUES (?, ?, ?, ?, ?, ?)',
                (user_key, filename, encrypted_data, file_hash, file_size, ip)
            )
            conn.commit()
            conn.close()
    
    def get_files(self, user_key):
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, filename, upload_time, file_size FROM files WHERE user_key = ? ORDER BY upload_time DESC',
                (user_key,)
            )
            files = cursor.fetchall()
            conn.close()
            return files
    
    def get_file_data(self, file_id, user_key):
        with db_lock:
            conn = sqlite3.connect('cybervault_v4.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT filename, encrypted_data, file_hash FROM files WHERE id = ? AND user_key = ?',
                (file_id, user_key)
            )
            result = cursor.fetchone()
            conn.close()
            return result

# Global instances
db = EnhancedDatabaseManager()
crypto = EnhancedCryptoManager()
security = SecurityManager()

def validate_key(key):
    """Validate 11-digit numeric key"""
    return re.match(r'^\d{11}$', key) is not None

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('welcome'))
        return f(*args, **kwargs)
    return decorated

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def format_file_size(size_bytes):
    """Format file size"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

# HTML Templates - Original theme style
WELCOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ANÄ€MAVÄ€K v4.0</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier Prime', monospace;
            background: #000;
            color: #fff;
            min-height: 100vh;
            background-image: 
                linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
            background-size: 20px 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            text-align: center;
            border: 2px solid #fff;
            padding: 3rem;
            background: rgba(0,0,0,0.8);
            max-width: 600px;
            width: 90%;
        }
        
        .logo {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            cursor: pointer;
            user-select: none;
            transition: opacity 0.2s;
        }
        
        .logo:hover {
            opacity: 0.8;
        }
        
        .version {
            color: #00ff00;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
        
        .description {
            margin-bottom: 2rem;
            line-height: 1.6;
            color: #ccc;
        }
        
        .security-info {
            text-align: left;
            margin-bottom: 2rem;
            padding: 1rem;
            border: 1px solid #333;
            background: rgba(0,0,0,0.5);
        }
        
        .security-info h4 {
            color: #00ff00;
            margin-bottom: 0.5rem;
        }
        
        .security-info ul {
            list-style: none;
            color: #ccc;
            font-size: 0.9rem;
        }
        
        .security-info li {
            margin-bottom: 0.3rem;
            padding-left: 1rem;
        }
        
        .security-info li::before {
            content: '• ';
            color: #00ff00;
            margin-right: 0.5rem;
        }
        
        .status {
            height: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .access-form {
            display: none;
            margin-top: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #fff;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 0.8rem;
            background: #000;
            border: 1px solid #fff;
            color: #fff;
            font-family: 'Courier Prime', monospace;
            font-size: 1rem;
            text-align: center;
            letter-spacing: 1px;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #00ff00;
        }
        
        .btn {
            background: #000;
            color: #fff;
            border: 2px solid #fff;
            padding: 0.8rem 2rem;
            font-family: 'Courier Prime', monospace;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn:hover {
            background: #fff;
            color: #000;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .error {
            color: #ff0000;
            margin-top: 1rem;
        }
        
        .hint {
            color: #666;
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo" id="logo">ANÄ€MAVÄ€K</div>
        <div class="version">v4.0 ENHANCED</div>
        <div class="description">
            Advanced secure real-time messaging system with quadruple-layer encryption.<br>
            Enter your 11-digit access key to continue.
        </div>
        
        <div class="security-info">
            <h4>Enhanced Security Features:</h4>
            <ul>
                <li>Quadruple-layer encryption (Morse + XOR + AES-256-GCM + HMAC)</li>
                <li>PBKDF2 key derivation with 100,000 iterations</li>
                <li>Real-time encrypted WebSocket communication</li>
                <li>Advanced brute force protection</li>
                <li>Secure file transfer with integrity verification</li>
                <li>Rate limiting and session management</li>
            </ul>
        </div>
        
        <form class="access-form" id="accessForm">
            <div class="form-group">
                <label for="user_key">Access Key:</label>
                <input type="text" id="user_key" name="user_key" maxlength="11" pattern="\\d{11}" required autocomplete="off">
                <div class="hint">Click logo 7 times to reveal access form</div>
            </div>
            <button type="submit" class="btn" id="authBtn">ACCESS VAULT</button>
            <div class="error" id="error"></div>
        </form>
        
        <div class="status" id="status"></div>
    </div>
    
    <script>
        let clickCount = 0;
        const logo = document.getElementById('logo');
        const accessForm = document.getElementById('accessForm');
        const status = document.getElementById('status');
        
        logo.addEventListener('click', function() {
            clickCount++;
            if (clickCount === 7) {
                accessForm.style.display = 'block';
                document.getElementById('user_key').focus();
                clickCount = 0;
            }
        });
        
        // Auto-format key input
        document.getElementById('user_key').addEventListener('input', function(e) {
            this.value = this.value.replace(/\\D/g, '');
        });
        
        document.getElementById('accessForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const key = document.getElementById('user_key').value;
            const error = document.getElementById('error');
            const authBtn = document.getElementById('authBtn');
            
            if (!/^\\d{11}$/.test(key)) {
                error.textContent = 'Invalid key format. Must be exactly 11 digits.';
                return;
            }
            
            error.textContent = '';
            authBtn.disabled = true;
            authBtn.textContent = 'AUTHENTICATING...';
            
            fetch('/auth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_key: key})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    authBtn.textContent = 'ACCESS GRANTED';
                    window.location.href = '/vault';
                } else {
                    error.textContent = data.error || 'Authentication failed';
                    authBtn.disabled = false;
                    authBtn.textContent = 'ACCESS VAULT';
                }
            })
            .catch(() => {
                error.textContent = 'Connection error';
                authBtn.disabled = false;
                authBtn.textContent = 'ACCESS VAULT';
            });
        });
        
        // Enter key support
        document.getElementById('user_key').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('accessForm').dispatchEvent(new Event('submit'));
            }
        });
    </script>
</body>
</html>
'''

VAULT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ANÄ€MAVÄ€K v4.0 - Secure Messaging</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier Prime', monospace;
            background: #000;
            color: #fff;
            height: 100vh;
            background-image: 
                linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
            background-size: 20px 20px;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            padding: 1rem;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0,0,0,0.9);
        }
        
        .title {
            font-weight: 700;
            font-size: 1.5rem;
        }
        
        .user-info {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .status {
            color: #00ff00;
            font-size: 0.9rem;
        }
        
        .user-id {
            color: #ccc;
            font-size: 0.8rem;
        }
        
        .logout-btn {
            background: #000;
            color: #fff;
            border: 1px solid #fff;
            padding: 0.5rem 1rem;
            font-family: 'Courier Prime', monospace;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .logout-btn:hover {
            background: #fff;
            color: #000;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            overflow: hidden;
        }
        
        .messages-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #333;
        }
        
        .messages-header {
            padding: 1rem;
            border-bottom: 1px solid #333;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .messages-title {
            font-weight: 700;
        }
        
        .message-count {
            color: #666;
            font-size: 0.8rem;
        }
        
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: rgba(0,0,0,0.5);
        }
        
        .message {
            margin-bottom: 1rem;
            padding: 0.8rem;
            border: 1px solid #333;
            background: rgba(0,0,0,0.7);
        }
        
        .message:hover {
            border-color: #00ff00;
        }
        
        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            color: #00ff00;
        }
        
        .message-content {
            word-wrap: break-word;
            line-height: 1.4;
        }
        
        .message-input-area {
            padding: 1rem;
            border-top: 1px solid #333;
            background: rgba(0,0,0,0.9);
        }
        
        .input-group {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .message-input {
            flex: 1;
            padding: 0.8rem;
            background: #000;
            border: 1px solid #fff;
            color: #fff;
            font-family: 'Courier Prime', monospace;
            resize: vertical;
            min-height: 60px;
        }
        
        .message-input:focus {
            outline: none;
            border-color: #00ff00;
        }
        
        .send-btn {
            background: #000;
            color: #fff;
            border: 2px solid #fff;
            padding: 0.8rem 1.5rem;
            font-family: 'Courier Prime', monospace;
            cursor: pointer;
            white-space: nowrap;
        }
        
        .send-btn:hover {
            background: #fff;
            color: #000;
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .char-counter {
            text-align: right;
            color: #666;
            font-size: 0.8rem;
        }
        
        .files-panel {
            width: 300px;
            border-left: 1px solid #333;
            display: flex;
            flex-direction: column;
            background: rgba(0,0,0,0.8);
        }
        
        .files-header {
            padding: 1rem;
            border-bottom: 1px solid #333;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .file-count {
            color: #666;
            font-size: 0.8rem;
        }
        
        .file-upload {
            padding: 1rem;
            border-bottom: 1px solid #333;
        }
        
        .file-input {
            display: none;
        }
        
        .file-upload-btn {
            background: #000;
            color: #fff;
            border: 1px solid #fff;
            padding: 0.5rem 1rem;
            font-family: 'Courier Prime', monospace;
            cursor: pointer;
            display: block;
            width: 100%;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        .file-upload-btn:hover {
            background: #fff;
            color: #000;
        }
        
        .upload-status {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.5rem;
        }
        
        .files-list {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
        }
        
        .file-item {
            padding: 0.5rem;
            border: 1px solid #333;
            margin-bottom: 0.5rem;
            cursor: pointer;
            background: rgba(0,0,0,0.5);
        }
        
        .file-item:hover {
            border-color: #00ff00;
        }
        
        .file-name {
            font-size: 0.9rem;
            margin-bottom: 0.2rem;
        }
        
        .file-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.7rem;
            color: #666;
        }
        
        .no-messages {
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 2rem;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #000;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #333;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }
            
            .files-panel {
                width: 100%;
                height: 200px;
            }
            
            .messages-panel {
                border-right: none;
                border-bottom: 1px solid #333;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">ANÄ€MAVÄ€K v4.0</div>
        <div class="user-info">
            <div class="user-id">USER: ****</div>
            <div class="status" id="connectionStatus">CONNECTING</div>
            <button class="logout-btn" onclick="logout()">EXIT</button>
        </div>
    </div>
    
    <div class="main-content">
        <div class="messages-panel">
            <div class="messages-header">
                <div class="messages-title">SECURE MESSAGES</div>
                <div class="message-count" id="messageCount">0 messages</div>
            </div>
            
            <div class="messages-container" id="messagesContainer">
                <div class="no-messages" id="noMessages">No messages yet. Start a secure conversation.</div>
            </div>
            
            <div class="message-input-area">
                <div class="input-group">
                    <textarea class="message-input" id="messageInput" placeholder="Enter message..." rows="2" maxlength="2000"></textarea>
                    <button class="send-btn" onclick="sendMessage()" id="sendBtn">SEND MSG</button>
                </div>
                <div class="char-counter">
                    <span id="charCount">0</span>/2000 characters
                </div>
            </div>
        </div>
        
        <div class="files-panel">
            <div class="files-header">
                <span>SECURE FILES</span>
                <span class="file-count" id="fileCount">0 files</span>
            </div>
            
            <div class="file-upload">
                <input type="file" id="fileInput" class="file-input" multiple>
                <button class="file-upload-btn" onclick="document.getElementById('fileInput').click()">UPLOAD FILE</button>
                <div class="upload-status" id="uploadStatus"></div>
            </div>
            
            <div class="files-list" id="filesList">
                <!-- Files will be loaded here -->
            </div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        const messagesContainer = document.getElementById('messagesContainer');
        const messageInput = document.getElementById('messageInput');
        const fileInput = document.getElementById('fileInput');
        const connectionStatus = document.getElementById('connectionStatus');
        const messageCount = document.getElementById('messageCount');
        const fileCount = document.getElementById('fileCount');
        const charCount = document.getElementById('charCount');
        const noMessages = document.getElementById('noMessages');
        
        let messageCounter = 0;
        let fileCounter = 0;
        
        // Character counter
        messageInput.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = count;
            
            if (count > 1800) {
                charCount.style.color = '#ff0000';
            } else if (count > 1500) {
                charCount.style.color = '#ffaa00';
            } else {
                charCount.style.color = '#666';
            }
        });
        
        // Socket event handlers
        socket.on('connect', function() {
            connectionStatus.textContent = 'CONNECTED';
            connectionStatus.style.color = '#00ff00';
            loadMessages();
        });
        
        socket.on('disconnect', function() {
            connectionStatus.textContent = 'DISCONNECTED';
            connectionStatus.style.color = '#ff0000';
        });
        
        socket.on('new_message', function(data) {
            addMessageToUI(data.content, data.timestamp, false);
        });
        
        // Message handling
        function addMessageToUI(content, timestamp, isOld = false) {
            if (noMessages.style.display !== 'none') {
                noMessages.style.display = 'none';
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            
            const timeDiv = document.createElement('div');
            timeDiv.textContent = new Date(timestamp).toLocaleString();
            
            const statusDiv = document.createElement('div');
            statusDiv.textContent = 'ENCRYPTED';
            
            headerDiv.appendChild(timeDiv);
            headerDiv.appendChild(statusDiv);
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(contentDiv);
            
            if (isOld) {
                messagesContainer.appendChild(messageDiv);
            } else {
                messagesContainer.insertBefore(messageDiv, messagesContainer.firstChild);
                messageCounter++;
                updateMessageCount();
            }
            
            if (!isOld) {
                messagesContainer.scrollTop = 0;
            }
        }
        
        function updateMessageCount() {
            messageCount.textContent = `${messageCounter} messages`;
        }
        
        function updateFileCount() {
            fileCount.textContent = `${fileCounter} files`;
        }
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            sendBtn.textContent = 'ENCRYPTING...';
            
            fetch('/send_message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                sendBtn.disabled = false;
                sendBtn.textContent = 'SEND MSG';
                
                if (data.success) {
                    messageInput.value = '';
                    charCount.textContent = '0';
                    charCount.style.color = '#666';
                    socket.emit('message_sent', {content: message});
                } else {
                    alert('Failed to send message: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                sendBtn.disabled = false;
                sendBtn.textContent = 'SEND MSG';
                alert('Error sending message: ' + error);
            });
        }
        
        function loadMessages() {
            fetch('/get_messages')
            .then(response => response.json())
            .then(data => {
                messagesContainer.innerHTML = '';
                messageCounter = data.messages.length;
                
                if (messageCounter === 0) {
                    noMessages.style.display = 'block';
                } else {
                    noMessages.style.display = 'none';
                    data.messages.reverse().forEach(msg => {
                        addMessageToUI(msg.content, msg.timestamp, true);
                    });
                }
                
                updateMessageCount();
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                messageCount.textContent = 'Error loading';
            });
            
            loadFiles();
        }
        
        // File handling
        fileInput.addEventListener('change', function() {
            const files = Array.from(this.files);
            if (files.length === 0) return;
            
            files.forEach(file => uploadFile(file));
        });
        
        function uploadFile(file) {
            if (file.size > 32 * 1024 * 1024) {
                alert(`File "${file.name}" is too large. Maximum size is 32MB.`);
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            const uploadStatus = document.getElementById('uploadStatus');
            uploadStatus.textContent = `Uploading ${file.name}...`;
            uploadStatus.style.color = '#00ff00';
            
            fetch('/upload_file', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.textContent = 'Upload complete';
                    uploadStatus.style.color = '#00ff00';
                    setTimeout(() => {
                        uploadStatus.textContent = '';
                    }, 3000);
                    loadFiles();
                } else {
                    uploadStatus.textContent = 'Upload failed: ' + (data.error || 'Unknown error');
                    uploadStatus.style.color = '#ff0000';
                }
                fileInput.value = '';
            })
            .catch(error => {
                uploadStatus.textContent = 'Upload error';
                uploadStatus.style.color = '#ff0000';
                fileInput.value = '';
            });
        }
        
        function loadFiles() {
            fetch('/get_files')
            .then(response => response.json())
            .then(data => {
                const filesList = document.getElementById('filesList');
                filesList.innerHTML = '';
                fileCounter = data.files.length;
                updateFileCount();
                
                data.files.forEach(file => {
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'file-item';
                    fileDiv.onclick = () => downloadFile(file.id, file.filename);
                    
                    const nameDiv = document.createElement('div');
                    nameDiv.className = 'file-name';
                    nameDiv.textContent = file.filename;
                    
                    const metaDiv = document.createElement('div');
                    metaDiv.className = 'file-meta';
                    
                    const timeDiv = document.createElement('div');
                    timeDiv.textContent = new Date(file.upload_time).toLocaleDateString();
                    
                    const sizeDiv = document.createElement('div');
                    sizeDiv.textContent = file.file_size || 'Unknown';
                    
                    metaDiv.appendChild(timeDiv);
                    metaDiv.appendChild(sizeDiv);
                    
                    fileDiv.appendChild(nameDiv);
                    fileDiv.appendChild(metaDiv);
                    filesList.appendChild(fileDiv);
                });
            })
            .catch(error => {
                console.error('Error loading files:', error);
                fileCount.textContent = 'Error';
            });
        }
        
        function downloadFile(fileId, filename) {
            const link = document.createElement('a');
            link.href = `/download_file/${fileId}`;
            link.download = filename;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        function logout() {
            if (confirm('Exit ANÄ€MAVÄ€K?')) {
                socket.disconnect();
                window.location.href = '/logout';
            }
        }
        
        // Keyboard shortcuts
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Auto-focus message input
        messageInput.focus();
        
        // Initial load
        loadMessages();
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def welcome():
    ip = get_client_ip()
    db.log_access(ip, request.headers.get('User-Agent', ''), 'welcome_page_access')
    
    if security.is_brute_force_attempt(ip):
        db.log_security_event('blocked_access_attempt', ip, 'Blocked due to previous failures', 3)
        return "Access temporarily restricted", 429
    
    return render_template_string(WELCOME_TEMPLATE)

@app.route('/auth', methods=['POST'])
def authenticate():
    data = request.get_json()
    user_key = data.get('user_key', '').strip()
    ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    
    # Check rate limiting
    if security.is_rate_limited(ip):
        return jsonify({'success': False, 'error': 'Too many requests'}), 429
    
    security.add_request(ip)
    
    # Enhanced validation
    if not validate_key(user_key):
        security.add_failed_attempt(ip)
        db.log_access(ip, user_agent, f'failed_auth_invalid_format', user_key, False)
        db.log_security_event('invalid_key_format', ip, f'Invalid key format: {user_key}', 2)
        return jsonify({'success': False, 'error': 'Invalid key format'})
    
    # Create session
    session['user_key'] = user_key
    session['authenticated'] = True
    session['login_time'] = datetime.now().isoformat()
    session.permanent = True
    
    db.log_access(ip, user_agent, 'successful_auth', user_key, True)
    
    return jsonify({'success': True})

@app.route('/vault')
@require_auth
def vault():
    return render_template_string(VAULT_TEMPLATE)

@app.route('/send_message', methods=['POST'])
@require_auth
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Empty message'})
        
        if len(message) > 2000:
            return jsonify({'success': False, 'error': 'Message too long'})
        
        user_key = session['user_key']
        ip = get_client_ip()
        
        # Use enhanced encryption
        encrypted_message = crypto.quadruple_encrypt(message, user_key)
        
        db.store_message(user_key, encrypted_message, ip, session.get('session_id', ''))
        
        # Broadcast to other users with same key
        socketio.emit('new_message', {
            'content': message,
            'timestamp': datetime.now().isoformat()
        }, room=user_key)
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.log_security_event('message_send_error', get_client_ip(), str(e), 2)
        return jsonify({'success': False, 'error': 'Encryption failed'})

@app.route('/get_messages')
@require_auth
def get_messages():
    try:
        user_key = session['user_key']
        encrypted_messages = db.get_messages(user_key)
        
        messages = []
        for encrypted_content, timestamp in encrypted_messages:
            decrypted = crypto.quadruple_decrypt(encrypted_content, user_key)
            if decrypted:
                messages.append({
                    'content': decrypted,
                    'timestamp': timestamp
                })
        
        return jsonify({'messages': messages})
        
    except Exception as e:
        return jsonify({'messages': []})

@app.route('/upload_file', methods=['POST'])
@require_auth
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        filename = secure_filename(file.filename)
        file_data = file.read()
        file_size = len(file_data)
        
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'error': 'File too large (max 32MB)'})
        
        user_key = session['user_key']
        ip = get_client_ip()
        
        # Encrypt file data
        file_text = base64.b64encode(file_data).decode()
        encrypted_data = crypto.quadruple_encrypt(file_text, user_key + "file_salt")
        
        formatted_size = format_file_size(file_size)
        db.store_file(user_key, filename, encrypted_data, formatted_size, ip)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'File encryption failed'})

@app.route('/get_files')
@require_auth
def get_files():
    try:
        user_key = session['user_key']
        files = db.get_files(user_key)
        
        file_list = []
        for file_id, filename, upload_time, file_size in files:
            file_list.append({
                'id': file_id,
                'filename': filename,
                'upload_time': upload_time,
                'file_size': file_size or 'Unknown'
            })
        
        return jsonify({'files': file_list})
        
    except Exception as e:
        return jsonify({'files': []})

@app.route('/download_file/<int:file_id>')
@require_auth
def download_file(file_id):
    try:
        user_key = session['user_key']
        file_data = db.get_file_data(file_id, user_key)
        
        if not file_data:
            return "File not found", 404
        
        filename, encrypted_data, file_hash = file_data
        
        # Decrypt file data
        decrypted_text = crypto.quadruple_decrypt(encrypted_data, user_key + "file_salt")
        
        if decrypted_text is None:
            return "Decryption failed", 500
        
        decrypted_data = base64.b64decode(decrypted_text)
        
        return send_file(
            BytesIO(decrypted_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return f"Error: Decryption failed", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

# WebSocket events
@socketio.on('connect')
def handle_connect():
    if 'authenticated' in session and session['authenticated']:
        user_key = session['user_key']
        join_room(user_key)
        
        with users_lock:
            active_users[request.sid] = user_key

@socketio.on('disconnect')
def handle_disconnect():
    with users_lock:
        if request.sid in active_users:
            user_key = active_users[request.sid]
            leave_room(user_key)
            del active_users[request.sid]

@socketio.on('message_sent')
def handle_message_sent(data):
    if 'authenticated' in session and session['authenticated']:
        pass

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "127.0.0.1"

def generate_ascii_qr(data):
    """Generate ASCII QR code"""
    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_string = ""
        matrix = qr.get_matrix()
        for row in matrix:
            line = ""
            for cell in row:
                line += "██" if cell else "  "
            qr_string += line + "\n"
        return qr_string
    except ImportError:
        return "QR code generation requires 'qrcode' package\nInstall with: pip install qrcode[pil]"

def validate_port(port_str):
    """Validate port number"""
    try:
        port = int(port_str)
        return 1024 <= port <= 65535
    except ValueError:
        return False

def open_browser(url, delay=2):
    """Open browser after server starts"""
    def delayed_open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"\n🌐 Browser opened automatically: {url}")
        except Exception as e:
            print(f"\n⚠️  Could not open browser: {e}")
            print(f"   Please navigate to: {url}")
    
    thread = threading.Thread(target=delayed_open, daemon=True)
    thread.start()

def main():
    """Enhanced main application startup"""
    print("\n" + "="*60)
    print(" ANÄ€MAVÄ€K v4.0 - Enhanced Secure Messaging System")
    print("="*60)
    
    # Default port configuration
    default_port = 65222
    
    port_input = input(f"\nEnter port number (default {default_port}): ").strip()
    if not port_input:
        port = default_port
    elif validate_port(port_input):
        port = int(port_input)
    else:
        print("Invalid port. Using default 65222.")
        port = default_port
    
    local_ip = get_local_ip()
    
    print(f"\nServer Configuration:")
    print(f"Port: {port}")
    print(f"Local Access: http://127.0.0.1:{port}")
    print(f"Network Access: http://{local_ip}:{port}")
    
    # Generate QR code for mobile access
    network_url = f"http://{local_ip}:{port}"
    print(f"\nMobile Access QR Code:")
    print(generate_ascii_qr(network_url))
    
    print(f"\nEnhanced Security Features Active:")
    print("✓ Quadruple-layer encryption (Morse + XOR + AES-256-GCM + HMAC)")
    print("✓ PBKDF2 key derivation (100,000 iterations)")
    print("✓ Real-time WebSocket messaging")
    print("✓ Advanced brute force protection")
    print("✓ Secure file transfer with integrity verification")
    print("✓ Rate limiting and session management")
    print("✓ Auto-browser launch")
    
    print(f"\n  ANÄ€MAVÄ€K v4.0 is starting...")
    print("Press Ctrl+C to stop the server")
    print("Browser will open automatically")
    print("="*60)
    
    # Open browser automatically
    local_url = f"http://127.0.0.1:{port}"
    open_browser(local_url)
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n\n  ANÄ€MAVÄ€K v4.0 shutdown complete.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Port {port} is already in use.")
            print("   Try a different port or stop the service using this port.")
        else:
            print(f"\n❌ Error starting server: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == '__main__':
    try:
        import qrcode
    except ImportError:
        print("\n⚠️  Warning: 'qrcode' package not found.")
        print("   Install with: pip install qrcode[pil]")
    
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        print("\n❌ Error: 'cryptography' package required.")
        print("   Install with: pip install cryptography")
        exit(1)
    
    main()