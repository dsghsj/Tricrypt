# 🔐 TriCrypt
**Secure Real-Time Messaging & File Vault with Triple-Layer Encryption**

![Version](https://img.shields.io/badge/version-3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)

---

## 📖 Overview

**TriCrypt** is a cyber-secure, real-time communication system with encrypted file transfer. It uses a **triple-layer encryption model**:
- Morse Code 🕵️ (Obfuscation)
- AES-256 🧊 (Encryption)
- HMAC 🧷 (Integrity Check)

No user accounts. Just an **11-digit key**. Fast, secure, and simple.

---

## ✨ Features

- 🔐 End-to-end encrypted real-time messaging
- 📂 Secure file upload/download (up to 16MB)
- 🔄 WebSocket-based instant sync
- 🔑 11-digit numeric key access
- 🧬 Session management & access logging
- 📱 QR code for mobile access
- 🎨 Terminal-style retro UI

---

## 🧩 Tech Stack

- **Python 3.7+**
- **Flask**, **Flask-SocketIO**
- **Cryptography**, **SQLite**
- **qrcode** (for terminal QR codes)
- HTML + CSS + JS (UI)

---

## 🧰 Installation

### 🪟 Windows
```bash
git clone https://github.com/yourusername/tricrypt.git
cd tricrypt

py -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python cybervault_v3.py

Installation:

🐧 Linux / macOS

git clone https://github.com/yourusername/tricrypt.git
cd tricrypt

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python3 cybervault_v3.py

🤖 Android (via Termux)

pkg install git python
git clone https://github.com/yourusername/tricrypt.git
cd tricrypt

pip install -r requirements.txt
python cybervault_v3.py

🚀 Getting Started

After running the app, you’ll see this in your terminal:

    ✅ App is running on http://127.0.0.1:5000

    🌐 Local network IP to access on other devices

    📱 QR code to scan from your phone

🧭 How to Use TriCrypt (Visual Guide)

🧷 Step 1: Start the Server

Run the app and choose a port (default: 5000, or enter your own like 8899).
You’ll see local and network URLs, plus a QR code for mobile access.

"python cybervault_v3.py"

![start](/docs/Start.png)



🏠 2. Home Screen

You’ll see the welcome screen titled ANĀMAVĀK v3.0.
Click the logo 7 times to unlock the secret access panel.

![Home](/docs/Homescreen.png)

🔑 3. Enter Secret Key

You’ll be prompted to enter an 11-digit key (e.g., 12345678901).
This key is your personal encryption token and determines which vault you access.

![Secret Key](/docs/Secret%20key.png.png)

💬 4. Secure Messaging Interface

Once authenticated, you’ll enter the real-time messaging interface.
You can send text messages instantly — they’re encrypted using your key.

    All messages are encrypted and only accessible by people with the same key.

    ![Interface](/docs/Interface.png)

📁 5. File Upload

You can securely upload files (up to 16MB) which are encrypted using AES-256.
Files are listed on the side and can be downloaded or deleted securely.

![start](/docs/File%20upload.png)

🔓 6. Logout

To exit your vault, click EXIT in the top-right corner.

    This ends your session and clears any stored access.

    ![start](/docs/Logout.png)

🔐 Encryption Model

Plain Text
   ↓
Morse Code (Obfuscation)
   ↓
AES-256 Encryption
   ↓
HMAC-SHA256 (Integrity Signature)

Only the correct 11-digit key can decrypt your data.

🧪 File Upload Details

Maximum file size: 16 MB

Files are encrypted client-side before storage

Only accessible by the keyholder

📱 Mobile Access

After launch, scan the QR code displayed in terminal using your phone.

    Use your phone’s browser to access your vault securely

    Input the same 11-digit key to access your data

🤝 Contributing

Pull requests are welcome! Before submitting:

# Format code
black cybervault_v3.py

# Run the server
python cybervault_v3.py

📜 License

This project is licensed under the MIT License.
Feel free to use, modify, and share responsibly.