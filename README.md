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
### 🖥️ Server
1. **Configure the server**  
   🔹 Edit the **host** and **port** in the configuration file if needed.

2. **Start the server**  
```bash
cd server
python3 main.py
```
3. **✅ The server is now listening and ready to accept client connections.**

### 💻 Client
1. **Configure the client**  
   🔹 Make sure the **host** and **port** match the server settings.

2. **Start the client**  
```bash
cd client
python3 main.py
```
3. **Connect to another client**  
   🔹 Enter the **ID of the client** you want to chat with.

4. **Chat securely!**  
   🔒 All messages are end-to-end encrypted.



## 🛡️ Security
- AES-GCM 256-bit for confidentiality and authenticity
- Nonces + timestamps prevent replay attacks
- Forward with session AES keys
- Nothing is logged
