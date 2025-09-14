# SchiedChat 🛡️

**SchiedChat** is a secure chat system built on WebSockets, using **AES-GCM 256-bit encryption** for messages and RSA authentication. The server acts as a relay between clients, ensuring confidentiality  

---

## 🔒 Features

- **Secure messaging** with AES-GCM 256-bit (confidentiality + authenticity).  
- **RSA + ephemeral X25519 handshake** between client and server.  
- **Persistent public key registry**: each client has a `client_id` UUID and a public key stored on the server.  
- **Challenge-response** prevents impersonation of offline clients.  
- **No message logging**: messages are never stored on the server.  
- **Secure message forwarding** between clients.  
- **Supports multiple simultaneous clients**.  
- **No phone required**: each client uses a randomly generated UUID.

---


## 🛡️ Security
- **AES-GCM 256-bit encryption** for message confidentiality and authenticity.  
- **RSA + ephemeral X25519 handshake** ensures that each client-server connection is securely established.  
- **Persistent public key registry**: the server stores each client’s public key, preventing impersonation of offline clients.  
- **Challenge-response mechanism**: clients must prove ownership of their private key before the server accepts the connection.  
- **Nonces + session AES keys** prevent replay attacks.  
- **No logging**: messages are never stored on the server.  
- **Multi-client safe**: multiple clients can communicate simultaneously without risk of message leakage.


## 🚀 Installation
```bash
git clone https://github.com/tuo-username/SchiedChat.git
cd SchiedChat
pip install -r requirements.txt
```



## ⚡ Use
### 🖥️ Server
1. **Configure the server**  
- Edit the **host** and **port** in the configuration file if needed.

2. **Start the server**  
```bash
cd server
python3 main.py
```
3. **✅ The server is now listening and ready to accept client connections.**

### 💻 Client
1. **Configure the client**  
- Make sure the **host** and **port** match the server settings.
2. **Start the client**  
```bash
cd client
python3 main.py
```
3. **Connect to another client**  
 Enter the **ID of the client** you want to chat with.
4. **Chat securely!**  
