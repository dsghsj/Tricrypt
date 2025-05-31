#!/usr/bin/env python3
"""
CyberVault - Secure Messaging Application
A Flask-based encrypted messaging system with multi-layer encryption
"""

import os
import json
import time
import socket
import hashlib
import secrets
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global storage (in production, use a database)
messages = []
login_attempts = []
upload_folder = 'uploads'

# Ensure upload directory exists
os.makedirs(upload_folder, exist_ok=True)

def print_ascii_header():
    """Display professional ASCII art header"""
    header = """
   
░█████╗░██╗░░░██╗██████╗░███████╗██████╗░  ██╗░░░██╗░█████╗░██╗░░░██╗██╗░░░░░████████╗
██╔══██╗╚██╗░██╔╝██╔══██╗██╔════╝██╔══██╗  ██║░░░██║██╔══██╗██║░░░██║██║░░░░░╚══██╔══╝
██║░░╚═╝░╚████╔╝░██████╦╝█████╗░░██████╔╝  ╚██╗░██╔╝███████║██║░░░██║██║░░░░░░░░██║░░░
██║░░██╗░░╚██╔╝░░██╔══██╗██╔══╝░░██╔══██╗  ░╚████╔╝░██╔══██║██║░░░██║██║░░░░░░░░██║░░░
╚█████╔╝░░░██║░░░██████╦╝███████╗██║░░██║  ░░╚██╔╝░░██║░░██║╚██████╔╝███████╗░░░██║░░░
░╚════╝░░░░╚═╝░░░╚═════╝░╚══════╝╚═╝░░╚═╝  ░░░╚═╝░░░╚═╝░░╚═╝░╚═════╝░╚══════╝░░░╚═╝░░░
    	║                                                               ║
        ║                    SECURE MESSAGING SYSTEM                    ║
        ║                         Version 2.0                           ║
        ╚═══════════════════════════════════════════════════════════════╝
    """
    print(header)
    print("    [SYSTEM] Initializing secure communication protocol...")
    print("    [SYSTEM] Loading encryption modules...")
    print("    [SYSTEM] Establishing secure channels...")

def get_system_info():
    """Display system information"""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"    [INFO] Hostname: {hostname}")
    print(f"    [INFO] Local IP: {local_ip}")
    print(f"    [INFO] Encryption: 3-Layer Custom Algorithm")
    print(f"    [INFO] Max File Size: 16MB")
    print("    [STATUS] System ready for secure operations")

def generate_qr_code(url):
    """Generate QR code for server URL"""
    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    
    # Convert to ASCII art
    matrix = qr.get_matrix()
    qr_ascii = []
    for row in matrix:
        line = ""
        for cell in row:
            line += "██" if cell else "  "
        qr_ascii.append(line)
    
    return qr_ascii

def validate_key(key):
    """Validate 11-digit numeric key"""
    if not key or len(key) != 11 or not key.isdigit():
        return False
    return True

def fibonacci_sequence(n):
    """Generate Fibonacci sequence up to n terms"""
    if n <= 0:
        return []
    elif n == 1:
        return [1]
    elif n == 2:
        return [1, 1]
    
    fib = [1, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def is_prime(n):
    """Check if number is prime"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def get_primes(limit):
    """Get prime numbers up to limit"""
    primes = []
    for i in range(2, limit + 1):
        if is_prime(i):
            primes.append(i)
    return primes

def custom_cipher_encrypt(text, key):
    """Layer 1: Custom cipher using Fibonacci, primes, and key sum"""
    if not text:
        return ""
    
    key_sum = sum(int(digit) for digit in key)
    fib_seq = fibonacci_sequence(len(text))
    primes = get_primes(100)  # Get primes up to 100
    
    encrypted = ""
    for i, char in enumerate(text):
        # Get Fibonacci number for position (cycle if needed)
        fib_val = fib_seq[i % len(fib_seq)] if fib_seq else 1
        
        # Get prime for position (cycle if needed)
        prime_val = primes[i % len(primes)] if primes else 2
        
        # Calculate shift amount
        shift = (key_sum + fib_val + prime_val) % 256
        
        # Shift character
        new_char_code = (ord(char) + shift) % 256
        encrypted += chr(new_char_code)
    
    return encrypted

def custom_cipher_decrypt(encrypted_text, key):
    """Layer 1: Decrypt custom cipher"""
    if not encrypted_text:
        return ""
    
    key_sum = sum(int(digit) for digit in key)
    fib_seq = fibonacci_sequence(len(encrypted_text))
    primes = get_primes(100)
    
    decrypted = ""
    for i, char in enumerate(encrypted_text):
        fib_val = fib_seq[i % len(fib_seq)] if fib_seq else 1
        prime_val = primes[i % len(primes)] if primes else 2
        shift = (key_sum + fib_val + prime_val) % 256
        
        # Reverse shift
        original_char_code = (ord(char) - shift) % 256
        decrypted += chr(original_char_code)
    
    return decrypted

def text_to_morse(text):
    """Convert text to Morse code"""
    morse_dict = {
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
    
    morse = ""
    for char in text.upper():
        if char in morse_dict:
            morse += morse_dict[char] + " "
        else:
            morse += char + " "  # Keep unknown characters
    
    return morse.strip()

def morse_to_text(morse):
    """Convert Morse code back to text"""
    morse_dict = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
        '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
        '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
        '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
        '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
        '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
        '---..': '8', '----.': '9', '/': ' ', '.-.-.-': '.', '--..--': ',',
        '..--..': '?', '.----.': "'", '-.-.--': '!', '-..-.': '/', '-.--.\n': '(',
        '-.--.-': ')', '.-...': '&', '---...': ':', '-.-.-.': ';', '-...-': '=',
        '.-.-.': '+', '-....-': '-', '..--.-': '_', '.-..-.': '"', '...-..-': '$',
        '.--.-': '@'
    }
    
    text = ""
    morse_chars = morse.split(' ')
    
    for morse_char in morse_chars:
        if morse_char in morse_dict:
            text += morse_dict[morse_char]
        elif morse_char:
            text += morse_char  # Keep unknown characters
    
    return text

def swap_morse_dots_dashes(morse):
    """Layer 2: Swap dots and dashes in Morse code"""
    swapped = ""
    for char in morse:
        if char == '.':
            swapped += '-'
        elif char == '-':
            swapped += '.'
        else:
            swapped += char
    return swapped

def morse_to_binary(morse):
    """Layer 3: Convert Morse to binary (dots=1, dashes=0, spaces=2, slashes=3)"""
    binary = ""
    for char in morse:
        if char == '.':
            binary += '1'
        elif char == '-':
            binary += '0'
        elif char == ' ':
            binary += '2'
        elif char == '/':
            binary += '3'
        else:
            binary += char  # Keep other characters as-is
    return binary

def binary_to_morse(binary):
    """Convert binary back to Morse"""
    morse = ""
    for char in binary:
        if char == '1':
            morse += '.'
        elif char == '0':
            morse += '-'
        elif char == '2':
            morse += ' '
        elif char == '3':
            morse += '/'
        else:
            morse += char
    return morse

def encrypt_message(message, key):
    """Apply 3-layer encryption"""
    # Layer 1: Custom cipher
    layer1 = custom_cipher_encrypt(message, key)
    
    # Layer 2: Convert to Morse, then swap dots and dashes
    morse = text_to_morse(layer1)
    layer2 = swap_morse_dots_dashes(morse)
    
    # Layer 3: Convert to binary
    layer3 = morse_to_binary(layer2)
    
    return layer3

def decrypt_message(encrypted_message, key):
    """Reverse 3-layer encryption"""
    try:
        # Layer 3: Convert binary back to Morse
        morse = binary_to_morse(encrypted_message)
        
        # Layer 2: Swap dots and dashes back
        original_morse = swap_morse_dots_dashes(morse)
        
        # Convert Morse back to text
        layer1_text = morse_to_text(original_morse)
        
        # Layer 1: Decrypt custom cipher
        original_message = custom_cipher_decrypt(layer1_text, key)
        
        return original_message
    except Exception as e:
        return f"[DECRYPTION ERROR: {str(e)}]"

def log_login_attempt(username, success, ip_address, user_agent):
    """Log login attempts"""
    attempt = {
        'timestamp': datetime.now().isoformat(),
        'username': username,
        'success': success,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'hostname': socket.gethostname(),
        'platform': 'Web Application'
    }
    login_attempts.append(attempt)
    
    # Also save to file
    try:
        with open('login_attempts.json', 'w') as f:
            json.dump(login_attempts, f, indent=2)
    except Exception:
        pass

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberVault - Secure Messaging</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Courier New', monospace;
            background: #000;
            color: #fff;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }

        /* Matrix background effect */
        .matrix-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.1;
            background: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 20px 20px;
            animation: matrix-scroll 20s linear infinite;
        }

        @keyframes matrix-scroll {
            0% { transform: translateY(0); }
            100% { transform: translateY(20px); }
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            border: 1px solid #333;
            padding: 20px;
            background: rgba(17, 17, 17, 0.8);
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(255,255,255,0.1);
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
            text-shadow: 0 0 5px rgba(255,255,255,0.3);
        }

        .app-icon {
            width: 60px;
            height: 60px;
            background: #222;
            border: 2px solid #666;
            border-radius: 8px;
            margin: 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 24px;
            position: relative;
        }

        .app-icon:hover {
            border-color: #999;
            box-shadow: 0 0 15px rgba(255,255,255,0.2);
        }

        .app-icon.unlocking {
            animation: pulse 0.5s ease-in-out;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .login-form, .chat-container {
            background: rgba(17, 17, 17, 0.9);
            border: 1px solid #333;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 0 10px rgba(255,255,255,0.1);
        }

        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: #ccc;
        }

        input[type="text"], input[type="password"], input[type="file"], textarea {
            width: 100%;
            padding: 10px;
            background: #222;
            border: 1px solid #444;
            border-radius: 3px;
            color: #fff;
            font-family: 'Courier New', monospace;
        }

        input:focus, textarea:focus {
            outline: none;
            border-color: #666;
            box-shadow: 0 0 5px rgba(255,255,255,0.2);
        }

        button {
            background: #333;
            color: #fff;
            border: 1px solid #555;
            padding: 10px 20px;
            border-radius: 3px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            transition: all 0.3s ease;
        }

        button:hover {
            background: #444;
            border-color: #777;
            box-shadow: 0 0 5px rgba(255,255,255,0.2);
        }

        .messages {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #333;
            padding: 10px;
            margin-bottom: 15px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 3px;
        }

        .message {
            margin-bottom: 10px;
            padding: 8px;
            border-left: 2px solid #555;
            background: rgba(34, 34, 34, 0.5);
            border-radius: 3px;
        }

        .message-header {
            font-size: 0.8em;
            color: #888;
            margin-bottom: 5px;
        }

        .message-content {
            color: #fff;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .file-link {
            color: #bbb;
            text-decoration: underline;
            cursor: pointer;
        }

        .file-link:hover {
            color: #fff;
        }

        .error {
            color: #ff6b6b;
            margin-top: 10px;
        }

        .success {
            color: #51cf66;
            margin-top: 10px;
        }

        .tap-counter {
            position: absolute;
            top: -10px;
            right: -10px;
            background: #444;
            color: #fff;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            font-size: 12px;
            display: none;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .tap-counter.visible {
            opacity: 0;
        }

        .message-form {
            display: none;
        }

        .message-form.unlocked {
            display: block;
        }

        @media (max-width: 600px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 1.5em;
            }
        }

        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    
    <div class="container">
        {% if not session.get('logged_in') %}
        <div class="header">
            <h1>🔐 CyberVault</h1>
            <p>Secure Messaging System</p>
            <p><em>Multi-Layer Encryption Protocol</em></p>
        </div>

        <div class="login-form">
            <h2>Authentication Required</h2>
            <form method="POST" action="/login">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="key">11-Digit Encryption Key:</label>
                    <input type="password" id="key" name="key" pattern="[0-9]{11}" required>
                </div>
                <button type="submit">Authenticate</button>
            </form>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </div>
        {% else %}
        <div class="header">
            <h1>🔐 CyberVault</h1>
            <p>Welcome, {{ session.username }}</p>
            <p><em>Secure Channel Established</em></p>
            
            <div class="app-icon" id="app-icon">
                🔒
                <div class="tap-counter" id="tap-counter">0</div>
            </div>
            <p><small>There's Nothing here Bitch</small></p>
        </div>

        <div class="chat-container">
            <div class="messages" id="messages">
                <!-- Messages will be loaded here -->
            </div>
            
            <div class="message-form" id="message-form">
                <div class="form-group">
                    <textarea id="message-text" placeholder="Enter your message..." rows="3"></textarea>
                </div>
                <div class="form-group">
                    <input type="file" id="file-upload" accept="*/*">
                </div>
                <button onclick="sendMessage()">Send Message</button>
                <button onclick="sendFile()">Send File</button>
                <a href="/logout" style="margin-left: 20px; color: #888;">Logout</a>
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        let tapCount = 0;
        let tapTimer = null;
        let isUnlocked = false;

        // 5-tap unlock mechanism
        document.getElementById('app-icon')?.addEventListener('click', function() {
            if (isUnlocked) return;
            
            tapCount++;
            const counter = document.getElementById('tap-counter');
            counter.textContent = tapCount;
            counter.classList.add('visible');
            
            this.classList.add('unlocking');
            setTimeout(() => this.classList.remove('unlocking'), 500);
            
            if (tapCount >= 5) {
                unlock();
            } else {
                // Reset counter after 3 seconds of inactivity
                clearTimeout(tapTimer);
                tapTimer = setTimeout(() => {
                    tapCount = 0;
                    counter.textContent = '0';
                    counter.classList.remove('visible');
                }, 3000);
            }
        });

        function unlock() {
            isUnlocked = true;
            document.getElementById('app-icon').innerHTML = '🔓';
            document.getElementById('message-form').classList.add('unlocked');
            document.getElementById('tap-counter').style.display = 'none';
            
            // Start loading messages
            loadMessages();
            setInterval(loadMessages, 3000); // Auto-refresh every 3 seconds
        }

        function loadMessages() {
            if (!isUnlocked) return;
            
            fetch('/get_messages')
                .then(response => response.json())
                .then(data => {
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';
                    
                    data.messages.forEach(msg => {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = 'message';
                        
                        const headerDiv = document.createElement('div');
                        headerDiv.className = 'message-header';
                        headerDiv.textContent = `${msg.username} - ${msg.timestamp}`;
                        
                        const contentDiv = document.createElement('div');
                        contentDiv.className = 'message-content';
                        
                        if (msg.file_path) {
                            const link = document.createElement('a');
                            link.href = `/download/${msg.file_path}`;
                            link.className = 'file-link';
                            link.textContent = `📎 ${msg.content}`;
                            contentDiv.appendChild(link);
                        } else {
                            contentDiv.textContent = msg.content;
                        }
                        
                        messageDiv.appendChild(headerDiv);
                        messageDiv.appendChild(contentDiv);
                        messagesDiv.appendChild(messageDiv);
                    });
                    
                    // Auto-scroll to bottom
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                })
                .catch(error => console.error('Error loading messages:', error));
        }

        function sendMessage() {
            const messageText = document.getElementById('message-text').value.trim();
            if (!messageText) return;
            
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: messageText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('message-text').value = '';
                    loadMessages();
                } else {
                    alert('Error sending message: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error sending message');
            });
        }

        function sendFile() {
            const fileInput = document.getElementById('file-upload');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file first');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/upload_file', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fileInput.value = '';
                    loadMessages();
                } else {
                    alert('Error uploading file: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error uploading file');
            });
        }

        // Enter key support for message input
        document.getElementById('message-text')?.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    key = request.form.get('key', '').strip()
    
    # Log login attempt
    log_login_attempt(
        username, 
        False,  # Will update if successful
        request.remote_addr,
        request.headers.get('User-Agent', 'Unknown')
    )
    
    if not username:
        return render_template_string(HTML_TEMPLATE, error="Username is required")
    
    if not validate_key(key):
        return render_template_string(HTML_TEMPLATE, error="Invalid key format. Must be 11 digits.")
    
    # Successful login
    session['logged_in'] = True
    session['username'] = username
    session['key'] = key
    session['session_id'] = secrets.token_hex(16)
    
    # Update login attempt to successful
    if login_attempts:
        login_attempts[-1]['success'] = True
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/send_message', methods=['POST'])
def send_message():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Message cannot be empty'})
    
    # Encrypt the message
    encrypted_message = encrypt_message(message, session['key'])
    
    # Store message
    message_data = {
        'username': session['username'],
        'content': message,  # Store original for display
        'encrypted_content': encrypted_message,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'key': session['key'],
        'file_path': None
    }
    
    messages.append(message_data)
    
    return jsonify({'success': True})

@app.route('/get_messages')
def get_messages():
    if not session.get('logged_in'):
        return jsonify({'messages': []})
    
    user_key = session['key']
    user_messages = []
    
    for msg in messages:
        if msg['key'] == user_key:  # Only show messages from same key group
            try:
                # Decrypt message for display
                if 'encrypted_content' in msg:
                    decrypted = decrypt_message(msg['encrypted_content'], user_key)
                    display_content = decrypted
                else:
                    display_content = msg['content']
                
                user_messages.append({
                    'username': msg['username'],
                    'content': display_content,
                    'timestamp': msg['timestamp'],
                    'file_path': msg['file_path']
                })
            except Exception as e:
                # If decryption fails, show error
                user_messages.append({
                    'username': msg['username'],
                    'content': f'[DECRYPTION ERROR]',
                    'timestamp': msg['timestamp'],
                    'file_path': msg['file_path']
                })
    
    return jsonify({'messages': user_messages})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file selected'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Secure filename
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({'success': False, 'error': 'Invalid filename'})
    
    # Add timestamp to prevent conflicts
    timestamp = str(int(time.time()))
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(upload_folder, filename)
    
    try:
        file.save(filepath)
        
        # Store file message
        message_data = {
            'username': session['username'],
            'content': file.filename,  # Original filename for display
            'encrypted_content': None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'key': session['key'],
            'file_path': filename
        }
        
        messages.append(message_data)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return "Access denied", 403
    
    # Security check - ensure user has access to this file
    file_accessible = False
    for msg in messages:
        if msg['file_path'] == filename and msg['key'] == session['key']:
            file_accessible = True
            break
    
    if not file_accessible:
        return "File not found or access denied", 404
    
    filepath = os.path.join(upload_folder, filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    
    return send_file(filepath)

@app.route('/admin/logs')
def admin_logs():
    """Admin endpoint to view login attempts"""
    # Simple admin access (in production, implement proper admin authentication)
    admin_key = request.args.get('admin_key')
    if admin_key != 'demigod``':  # Change this in production
        return "Access denied", 403
    
    return jsonify({
        'login_attempts': login_attempts,
        'total_attempts': len(login_attempts),
        'successful_logins': len([a for a in login_attempts if a['success']]),
        'failed_attempts': len([a for a in login_attempts if not a['success']])
    })

def get_local_ip():
    """Get local IP address"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def main():
    """Main function to start the application"""
    print_ascii_header()
    get_system_info()
    
    # Get port from user input
    try:
        port = input("\n    [INPUT] Enter port number (default 5000): ").strip()
        port = int(port) if port else 5000
    except ValueError:
        port = 5000
    
    local_ip = get_local_ip()
    hostname = socket.gethostname()
    
    print(f"\n    [SERVER] Starting CyberVault on port {port}")
    print(f"    [ACCESS] Local: http://127.0.0.1:{port}")
    print(f"    [ACCESS] Network: http://{local_ip}:{port}")
    print(f"    [ACCESS] Hostname: http://{hostname}.local:{port}")
    
    # Generate and display QR code
    server_url = f"http://{local_ip}:{port}"
    print(f"\n    [QR CODE] Scan to access: {server_url}")
    qr_lines = generate_qr_code(server_url)
    for line in qr_lines:
        print(f"    {line}")
    
    print(f"\n    [ADMIN] Login logs: http://{local_ip}:{port}/admin/logs?admin_key=")
    print("    [STATUS] Server ready - Press Ctrl+C to stop")
    print("    " + "="*60)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n    [SYSTEM] Server shutdown initiated")
        print("    [SYSTEM] Goodbye!")

if __name__ == '__main__':
    main()