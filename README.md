# SchiedChat 🛡️

**SchiedChat** is a secure chat system built on WebSockets, using **AES-GCM 256-bit encryption** for messages and RSA authentication. The server acts as a relay between clients, ensuring confidentiality  

---

## 🔒 Features

- **Secure messaging** with AES-GCM 256-bit encryption.  
- **RSA handshake** for client-server authentication.  
- **No phone needed**: each client will have a random uuid, u can change it anytime
- **No-log policy**: messages are never stored or printed.  
- **Secure message forwarding** between clients.  
- **Supports multiple simultaneous clients**.  

---

## 🚀 Installation
```bash
git clone https://github.com/tuo-username/SchiedChat.git
cd SchiedChat
pip install -r requirements.txt
```

## ⚡ Use
Server
- Change host id and port
### Run the server
```bash
cd server 
python3 main.py
```

Client
- Change host id and port
### Run the client
```bash
cd client 
python3 main.py
```
- Enter the other client id
- Chat safely!

## 🛡️ Security
- AES-GCM 256-bit for confidentiality and authenticity
- Nonces + timestamps prevent replay attacks
- Forward with session AES keys
- Nothing is logged
