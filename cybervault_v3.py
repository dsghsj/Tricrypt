#!/usr/bin/env python3
"""
ANĀMAVĀK v3.0 - Secure Real-Time Messaging System
Triple-layer encryption with real-time WebSocket communication
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
from datetime import datetime
from functools import wraps
from io import BytesIO
from threading import Lock

import qrcode
from flask import Flask, render_template_string, request, jsonify, session, send_file, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from werkzeug.utils import secure_filename

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global locks and state
db_lock = Lock()
users_lock = Lock()
active_users = {}

# Morse code mapping for obfuscation layer
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

class CryptoManager:
    """Triple-layer encryption system"""
    
    @staticmethod
    def generate_key():
        return secrets.token_bytes(32)
    
    @staticmethod
    def aes_encrypt(data, key):
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad data to 16-byte boundary
        pad_len = 16 - len(data) % 16
        padded_data = data + bytes([pad_len]) * pad_len
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + encrypted).decode()
    
    @staticmethod
    def aes_decrypt(encrypted_data, key):
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            pad_len = decrypted[-1]
            return decrypted[:-pad_len]
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
    def generate_hmac(data, key):
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    @staticmethod
    def verify_hmac(data, key, signature):
        expected = hmac.new(key, data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    @classmethod
    def triple_encrypt(cls, message, user_key):
        # Layer 1: Morse code obfuscation
        morse_message = cls.text_to_morse(message)
        
        # Layer 2: AES-256 encryption
        aes_key = hashlib.sha256(user_key.encode()).digest()
        encrypted_message = cls.aes_encrypt(morse_message.encode(), aes_key)
        
        # Layer 3: HMAC integrity
        hmac_key = hashlib.sha256(user_key.encode() + b'hmac_salt').digest()
        signature = cls.generate_hmac(encrypted_message.encode(), hmac_key)
        
        return f"{encrypted_message}:{signature}"
    
    @classmethod
    def triple_decrypt(cls, encrypted_data, user_key):
        try:
            encrypted_message, signature = encrypted_data.split(':', 1)
            
            # Verify HMAC
            hmac_key = hashlib.sha256(user_key.encode() + b'hmac_salt').digest()
            if not cls.verify_hmac(encrypted_message.encode(), hmac_key, signature):
                return None
            
            # Decrypt AES-256
            aes_key = hashlib.sha256(user_key.encode()).digest()
            morse_message = cls.aes_decrypt(encrypted_message, aes_key)
            if morse_message is None:
                return None
            
            # Decode Morse
            return cls.morse_to_text(morse_message.decode())
        except Exception:
            return None

class DatabaseManager:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        with db_lock:
            conn = sqlite3.connect('cybervault.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT NOT NULL,
                    encrypted_content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_type TEXT DEFAULT 'text'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    encrypted_data TEXT NOT NULL,
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def log_access(self, ip, user_agent, action):
        with db_lock:
            conn = sqlite3.connect('cybervault.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO access_logs (ip_address, user_agent, action) VALUES (?, ?, ?)',
                (ip, user_agent, action)
            )
            conn.commit()
            conn.close()
    
    def store_message(self, user_key, encrypted_message):
        with db_lock:
            conn = sqlite3.connect('cybervault.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO messages (user_key, encrypted_content) VALUES (?, ?)',
                (user_key, encrypted_message)
            )
            conn.commit()
            conn.close()
    
    def get_messages(self, user_key):
        with db_lock:
            conn = sqlite3.connect('cybervault.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT encrypted_content, timestamp FROM messages WHERE user_key = ? ORDER BY timestamp',
                (user_key,)
            )
            messages = cursor.fetchall()
            conn.close()
            return messages
    
    def store_file(self, user_key, filename, encrypted_data):
        with db_lock:
            conn = sqlite3.connect('cybervault.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO files (user_key, filename, encrypted_data) VALUES (?, ?, ?)',
                (user_key, filename, encrypted_data)
            )
            conn.commit()
            conn.close()
    
    def get_files(self, user_key):
        with db_lock:
            conn = sqlite3.connect('cybervault.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, filename, upload_time FROM files WHERE user_key = ? ORDER BY upload_time DESC',
                (user_key,)
            )
            files = cursor.fetchall()
            conn.close()
            return files
    
    def get_file_data(self, file_id, user_key):
        with db_lock:
            conn = sqlite3.connect('cybervault.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT filename, encrypted_data FROM files WHERE id = ? AND user_key = ?',
                (file_id, user_key)
            )
            result = cursor.fetchone()
            conn.close()
            return result

# Global instances
db = DatabaseManager()
crypto = CryptoManager()

def validate_key(key):
    """Validate 11-digit numeric key"""
    return re.match(r'^\d{11}$', key) is not None

def require_auth(f):
    """Decorator for authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('welcome'))
        return f(*args, **kwargs)
    return decorated

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

# HTML Templates
WELCOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ANĀMAVĀK v3.0</title>
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
        
        .error {
            color: #ff0000;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo" id="logo">ANĀMAVĀK</div>
        <div class="version">v3.0</div>
        <div class="description">
            Secure real-time messaging system with triple-layer encryption.<br>
            Enter your 11-digit access key to continue.
        </div>
        
        <form class="access-form" id="accessForm" method="POST">
            <div class="form-group">
                <label for="user_key">Access Key:</label>
                <input type="text" id="user_key" name="user_key" maxlength="11" pattern="\\d{11}" required>
            </div>
            <button type="submit" class="btn">ACCESS VAULT</button>
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
                clickCount = 0;
            }
        });
        
        document.getElementById('accessForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const key = document.getElementById('user_key').value;
            const error = document.getElementById('error');
            
            if (!/^\\d{11}$/.test(key)) {
                error.textContent = 'Invalid key format. Must be 11 digits.';
                return;
            }
            
            fetch('/auth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_key: key})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/vault';
                } else {
                    error.textContent = data.error || 'Authentication failed';
                }
            })
            .catch(() => {
                error.textContent = 'Connection error';
            });
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
    <title>ANĀMAVĀK v3.0 - Secure Messaging</title>
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
        
        .message-header {
            display: flex;
            justify-content: between;
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
            resize: none;
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
        
        .file-time {
            font-size: 0.7rem;
            color: #666;
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
        <div class="title">ANĀMAVĀK v3.0</div>
        <div class="user-info">
            <div class="status" id="connectionStatus">CONNECTED</div>
            <button class="logout-btn" onclick="logout()">EXIT</button>
        </div>
    </div>
    
    <div class="main-content">
        <div class="messages-panel">
            <div class="messages-container" id="messagesContainer">
                <!-- Messages will be loaded here -->
            </div>
            
            <div class="message-input-area">
                <div class="input-group">
                    <textarea class="message-input" id="messageInput" placeholder="Enter message..." rows="2"></textarea>
                    <button class="send-btn" onclick="sendMessage()">SEND MSG</button>
                </div>
            </div>
        </div>
        
        <div class="files-panel">
            <div class="files-header">SECURE FILES</div>
            
            <div class="file-upload">
                <input type="file" id="fileInput" class="file-input">
                <button class="file-upload-btn" onclick="document.getElementById('fileInput').click()">UPLOAD FILE</button>
                <div id="uploadStatus"></div>
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
            addMessageToUI(data.content, data.timestamp);
        });
        
        // Message handling
        function addMessageToUI(content, timestamp) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            headerDiv.textContent = new Date(timestamp).toLocaleString();
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(contentDiv);
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            fetch('/send_message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    messageInput.value = '';
                    socket.emit('message_sent', {content: message});
                } else {
                    alert('Failed to send message: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                alert('Error sending message: ' + error);
            });
        }
        
        function loadMessages() {
            fetch('/get_messages')
            .then(response => response.json())
            .then(data => {
                messagesContainer.innerHTML = '';
                data.messages.forEach(msg => {
                    addMessageToUI(msg.content, msg.timestamp);
                });
            })
            .catch(error => {
                console.error('Error loading messages:', error);
            });
            
            loadFiles();
        }
        
        // File handling
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;
            
            if (file.size > 16 * 1024 * 1024) {
                alert('File too large. Maximum size is 16MB.');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('uploadStatus').textContent = 'Uploading...';
            
            fetch('/upload_file', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('uploadStatus').textContent = 'Upload complete';
                    setTimeout(() => {
                        document.getElementById('uploadStatus').textContent = '';
                    }, 3000);
                    loadFiles();
                } else {
                    document.getElementById('uploadStatus').textContent = 'Upload failed';
                }
                fileInput.value = '';
            })
            .catch(error => {
                document.getElementById('uploadStatus').textContent = 'Upload error';
                fileInput.value = '';
            });
        });
        
        function loadFiles() {
            fetch('/get_files')
            .then(response => response.json())
            .then(data => {
                const filesList = document.getElementById('filesList');
                filesList.innerHTML = '';
                
                data.files.forEach(file => {
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'file-item';
                    fileDiv.onclick = () => downloadFile(file.id, file.filename);
                    
                    const nameDiv = document.createElement('div');
                    nameDiv.className = 'file-name';
                    nameDiv.textContent = file.filename;
                    
                    const timeDiv = document.createElement('div');
                    timeDiv.className = 'file-time';
                    timeDiv.textContent = new Date(file.upload_time).toLocaleString();
                    
                    fileDiv.appendChild(nameDiv);
                    fileDiv.appendChild(timeDiv);
                    filesList.appendChild(fileDiv);
                });
            })
            .catch(error => {
                console.error('Error loading files:', error);
            });
        }
        
        function downloadFile(fileId, filename) {
            window.open(`/download_file/${fileId}`, '_blank');
        }
        
        function logout() {
            if (confirm('Exit   ANĀMAVĀK?')) {
                window.location.href = '/logout';
            }
        }
        
        // Enter key handling
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Initial load
        loadMessages();
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def welcome():
    db.log_access(get_client_ip(), request.headers.get('User-Agent', ''), 'welcome_page_access')
    return render_template_string(WELCOME_TEMPLATE)

@app.route('/auth', methods=['POST'])
def authenticate():
    data = request.get_json()
    user_key = data.get('user_key', '')
    
    db.log_access(get_client_ip(), request.headers.get('User-Agent', ''), f'auth_attempt_{user_key}')
    
    if not validate_key(user_key):
        return jsonify({'success': False, 'error': 'Invalid key format'})
    
    session['user_key'] = user_key
    session['authenticated'] = True
    
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
        
        user_key = session['user_key']
        encrypted_message = crypto.triple_encrypt(message, user_key)
        
        db.store_message(user_key, encrypted_message)
        
        # Broadcast to other users with same key
        socketio.emit('new_message', {
            'content': message,
            'timestamp': datetime.now().isoformat()
        }, room=user_key)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_messages')
@require_auth
def get_messages():
    try:
        user_key = session['user_key']
        encrypted_messages = db.get_messages(user_key)
        
        messages = []
        for encrypted_content, timestamp in encrypted_messages:
            decrypted = crypto.triple_decrypt(encrypted_content, user_key)
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
        
        if file.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'error': 'File too large'})
        
        filename = secure_filename(file.filename)
        file_data = file.read()
        
        user_key = session['user_key']
        
        # Encrypt file data
        aes_key = hashlib.sha256(user_key.encode()).digest()
        encrypted_data = crypto.aes_encrypt(file_data, aes_key)
        
        db.store_file(user_key, filename, encrypted_data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_files')
@require_auth
def get_files():
    try:
        user_key = session['user_key']
        files = db.get_files(user_key)
        
        file_list = []
        for file_id, filename, upload_time in files:
            file_list.append({
                'id': file_id,
                'filename': filename,
                'upload_time': upload_time
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
        
        filename, encrypted_data = file_data
        
        # Decrypt file data
        aes_key = hashlib.sha256(user_key.encode()).digest()
        decrypted_data = crypto.aes_decrypt(encrypted_data, aes_key)
        
        if decrypted_data is None:
            return "Decryption failed", 500
        
        return send_file(
            BytesIO(decrypted_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return f"Error: {str(e)}", 500

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
        # Message already stored and broadcast in send_message route
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

def main():
    """Main application startup"""
    print("\n" + "="*60)
    print(" ANĀMAVĀK v3.0 - Secure Real-Time Messaging System")
    print("="*60)
    
    # Port selection
    while True:
        port_input = input("\nEnter port number (default 5000): ").strip()
        if not port_input:
            port = 5000
            break
        elif validate_port(port_input):
            port = int(port_input)
            break
        else:
            print("Invalid port. Must be between 1024-65535.")
    
    local_ip = get_local_ip()
    
    print(f"\nServer Configuration:")
    print(f"Port: {port}")
    print(f"Local Access: http://127.0.0.1:{port}")
    print(f"Network Access: http://{local_ip}:{port}")
    
    # Generate QR code for mobile access
    network_url = f"http://{local_ip}:{port}"
    print(f"\nMobile Access QR Code:")
    print(generate_ascii_qr(network_url))
    
    print(f"\nSecurity Features Active:")
    print("✓ Triple-layer encryption (AES-256 + HMAC + Morse)")
    print("✓ Real-time WebSocket messaging")
    print("✓ Secure file transfer")
    print("✓ Session management")
    print("✓ Access logging")
    
    print(f"\n  ANĀMAVĀK is starting...")
    print("Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n\n  ANĀMAVĀK shutdown complete.")
    except Exception as e:
        print(f"\nError starting server: {e}")

if __name__ == '__main__':
    try:
        import qrcode
    except ImportError:
        print("Warning: qrcode package not found. QR code generation will be limited.")
        print("Install with: pip install qrcode[pil]")
    
    main()