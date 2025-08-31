# ANÄ€MAVÄ€K v4.0 🔐

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/Security-Military%20Grade-red.svg)](https://github.com/yourusername/anamavak)
[![WebSocket](https://img.shields.io/badge/Real--Time-WebSocket-green.svg)](https://socket.io/)

> **Advanced Secure Real-Time Messaging System for Local Networks**

ANÄ€MAVÄ€K (pronounced "Anamavak") is a cutting-edge secure messaging application designed for privacy-conscious users who need military-grade encryption for local network communications. Built with Python Flask and featuring a sleek cyberpunk-inspired interface.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/anamavak.git
cd anamavak

# Install dependencies
pip install flask flask-socketio cryptography qrcode[pil]

# Run the application
python cybervault_v4.py
```

**That's it!** The application will automatically:
- 🌐 Open in your default browser
- 🔌 Start on port 65222
- 📱 Display a QR code for mobile access
- 🔒 Initialize the secure messaging environment

---

## ✨ Features

### 🛡️ **Military-Grade Security**
- **Quadruple-Layer Encryption Pipeline**:
  1. 📡 Morse code obfuscation
  2. 🔀 XOR encryption with salted keys  
  3. 🔐 AES-256-GCM authenticated encryption
  4. ✅ HMAC-SHA256 integrity verification

- **Advanced Key Derivation**: PBKDF2 with 100,000 iterations
- **Anti-Brute Force**: 5 attempts per 15 minutes lockout
- **Rate Limiting**: 100 requests per hour per IP
- **File Integrity**: SHA-256 hash verification for all uploads

### ⚡ **Real-Time Communication**
- 🔄 **WebSocket-based** instant messaging
- 🌐 **Cross-platform** web interface
- 📱 **Mobile responsive** design
- 🔌 **Auto-reconnection** with connection monitoring
- 👥 **Multi-user** support with shared access keys

### 📁 **Secure File Sharing**
- 📤 **32MB maximum** file size
- 🔒 **Encrypted file storage** with separate salt
- 📊 **File metadata** tracking (size, type, upload time)
- 🗂️ **Multiple file uploads** simultaneously
- 💾 **Secure download** with integrity verification

### 🎨 **User Experience**
- 🖥️ **Auto-browser launch** - no manual navigation
- 🎯 **Default port 65222** - instant setup
- 📱 **QR code generation** for mobile access
- ⌨️ **Keyboard shortcuts** (Ctrl+Enter, Escape)
- 🔢 **Character counter** with visual feedback
- 🎭 **Clean cyberpunk aesthetic**

---

## 🔧 Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Dependencies
```bash
pip install flask flask-socketio cryptography qrcode[pil]
```

### Optional (for enhanced QR codes)
```bash
pip install pillow
```

---

## 📖 Usage Guide

### 🔑 **Authentication**
1. Launch the application: `python cybervault_v4.py`
2. Browser opens automatically to the welcome screen
3. Click the logo **7 times** to reveal the access form
4. Enter your **11-digit numeric key** (e.g., `12345678901`)
5. Click "ACCESS VAULT" to enter the secure environment

### 💬 **Messaging**
- Type messages in the input area
- Press **Enter** or click "SEND MSG" to encrypt and send
- Messages are encrypted with quadruple-layer protection
- Real-time delivery to all users with the same access key
- **Ctrl+Enter** for quick send, **Escape** to clear

### 📁 **File Sharing**
- Click "UPLOAD FILE" in the right panel
- Select one or multiple files (max 32MB each)
- Files are automatically encrypted and stored securely
- Click any file in the list to download and decrypt
- File integrity is verified on every download

### 🌐 **Network Access**
- **Local**: `http://127.0.0.1:65222`
- **Network**: `http://[YOUR_LOCAL_IP]:65222`
- **Mobile**: Scan the QR code displayed at startup

---

## 🔐 Security Architecture

### Encryption Pipeline
```
Original Message
       ↓
1. Morse Code Obfuscation
       ↓
2. XOR Encryption (Salted Key)
       ↓
3. AES-256-GCM (PBKDF2 Derived Key)
       ↓
4. HMAC-SHA256 Integrity Check
       ↓
   Encrypted Package
```

### Key Features
- **Zero Knowledge**: Server cannot decrypt messages without user keys
- **Perfect Forward Secrecy**: Each message uses unique encryption parameters
- **Authenticated Encryption**: Built-in tamper detection
- **Brute Force Resistant**: Advanced rate limiting and attempt tracking

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │◄──►│  Flask Server    │◄──►│   SQLite DB     │
│  (Browser/Mobile)│    │  + SocketIO      │    │  (Encrypted)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │              ┌──────────────────┐
         └──────────────►│  Crypto Engine   │
                        │ (4-Layer Encrypt) │
                        └──────────────────┘
```

### Components
- **Flask**: Web framework and REST API
- **SocketIO**: Real-time WebSocket communication  
- **SQLite**: Encrypted local database storage
- **Cryptography**: AES-256-GCM and PBKDF2 implementation
- **QR Code**: Mobile access convenience

---

## ⚙️ Configuration

### Environment Variables
```bash
export ANAMAVAK_PORT=65222          # Default port
export ANAMAVAK_MAX_FILE_SIZE=32    # Max file size in MB
export ANAMAVAK_SESSION_TIMEOUT=24  # Session timeout in hours
```

### Security Settings
- **Rate Limit**: 100 requests/hour per IP
- **Brute Force**: 5 failed attempts = 15min lockout
- **Session Timeout**: 24 hours of inactivity
- **File Size Limit**: 32MB per file
- **Message Limit**: 2000 characters per message

---

## 🔒 Security Considerations

### ✅ **Best Practices**
- Use **strong 11-digit keys** (avoid sequential numbers)
- Run on **isolated local networks** only
- **Regular key rotation** for long-term use
- **Monitor access logs** for suspicious activity
- **Secure physical access** to the server machine

### ⚠️ **Important Notes**
- This is designed for **local network use only**
- **Do not expose** to the public internet without additional security layers
- **Access keys are shared** - anyone with the key can read messages
- **Messages are stored locally** in encrypted SQLite database
- **No cloud backup** - data is only on the local machine

### 🛡️ **Security Features**
- **End-to-end encryption** with zero server knowledge
- **Memory-safe** key handling
- **Secure session management**
- **Comprehensive audit logging**
- **Tamper-evident** file storage

---

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
netstat -tulpn | grep 65222

# Kill the process or use a different port
python cybervault_v4.py  # Then enter a different port
```

**Browser Doesn't Open**
- Manually navigate to `http://127.0.0.1:65222`
- Check firewall settings
- Try a different browser

**Can't Connect from Mobile**
- Ensure devices are on the same network
- Check firewall allows incoming connections
- Verify the IP address in the QR code

**Authentication Fails**
- Ensure key is exactly 11 digits
- Check for rate limiting (wait 15 minutes)
- Verify no typos in the access key

---

## 🔄 Changelog

### v4.0 (Current)
- ✨ **NEW**: Quadruple-layer encryption system
- ✨ **NEW**: Auto-browser launch functionality
- ✨ **NEW**: Advanced brute force protection
- ✨ **NEW**: Rate limiting system
- ✨ **NEW**: Enhanced file integrity verification
- ✨ **NEW**: PBKDF2 key derivation
- ✨ **NEW**: Default port 65222
- 🔧 **IMPROVED**: File size limit increased to 32MB
- 🔧 **IMPROVED**: Better WebSocket connection handling
- 🔧 **IMPROVED**: Enhanced session management
- 🐛 **FIXED**: Authentication flow issues
- 🐛 **FIXED**: Mobile responsiveness

### v3.0 (Previous)
- Triple-layer encryption (Morse + AES-256-CBC + HMAC)
- Basic real-time messaging
- File upload/download
- Simple session management
- Manual browser navigation

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. Create a **feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. Open a **Pull Request**

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/anamavak.git
cd anamavak

# Install development dependencies
pip install -r requirements.txt

# Run tests (if available)
python -m pytest tests/

# Start development server
python cybervault_v4.py
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This software is provided for **educational and legitimate use only**. Users are responsible for compliance with local laws and regulations. The authors are not responsible for any misuse of this software.

**Use responsibly and ethically.**

---

## 🙏 Acknowledgments

- **Cryptography Library**: For robust encryption primitives
- **Flask & SocketIO**: For the web framework and real-time communication
- **QR Code Library**: For mobile access convenience
- **Courier Prime Font**: For the authentic terminal aesthetic

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/anamavak/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/anamavak/discussions)
- 📧 **Security**: For security-related issues, please email security@yourdomain.com

---

## 🌟 Star This Project

If you find ANÄ€MAVÄ€K useful, please consider giving it a star ⭐ on GitHub!

---

<div align="center">

**ANÄ€MAVÄ€K v4.0** - *Secure communications for the modern age*

Made with ❤️ for privacy and security

[⬆️ Back to Top](#anÄ€mavÄ€k-v40-)

</div>