# SchiedChat 🛡️

**SchiedChat** is a secure chat system built on WebSockets, using **AES-GCM 256-bit encryption** for messages and RSA authentication. The server acts as a relay between clients, ensuring confidentiality  

---

## 🔒 Features

- **Secure messaging** with AES-GCM 256-bit encryption.  
- **RSA handshake** for client-server authentication.  
- **Replay protection** using nonces and timestamps.  
- **No-log policy**: plaintext messages are never stored or printed.  
- **Secure message forwarding** between clients.  
- **Supports multiple simultaneous clients**.  

---

## 🚀 Installation
```bash
git clone https://github.com/tuo-username/SchiedChat.git
cd SchiedChat
pip install -r requirements.txt
```

---

## ⚡ Use
### Run the server
```bash
cd server 
python3 main.py
```
### Run the client
```bash
cd client 
python3 main.py
```

---

## 🛡️ Security
- AES-GCM 256-bit for confidentiality and authenticity
- Nonces + timestamps prevent replay attacks
- Forward with session AES keys
- Nothing is logged
