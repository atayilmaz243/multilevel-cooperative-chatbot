import socket
import binascii
import os

class SimpleWebSocket:
    def __init__(self, host, port, path="/ws"):
        self.host = host
        self.port = port
        self.path = path
        self.sock = None

    def connect(self):
        print(f"[{self.host}:{self.port}] Baglaniliyor...")
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        self.sock = socket.socket()
        self.sock.settimeout(None)
        self.sock.connect(addr)
        
        # 16-byte random key base64
        key = binascii.b2a_base64(os.urandom(16))[:-1].decode()
        
        handshake = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            f"Connection: Upgrade\r\n"
            f"Upgrade: websocket\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Origin: http://{self.host}:{self.port}\r\n\r\n"
        )
        self.sock.send(handshake.encode())
        
        # Oku ve geç
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(1)
            if not chunk:
                raise Exception("Handshake okunamadi!")
            response += chunk
            
        if b"101 Switching Protocols" not in response:
            raise Exception("Sunucu reddetti:\n" + response.decode('utf-8','ignore'))
            
        print("El sikisma basarili.")

    def send_text(self, text):
        payload = text.encode()
        length = len(payload)
        
        # Istemciden sunucuya giderken MASK zorunludur!
        # Maskesiz giderse FastAPI/Uvicorn baglantiyi aninda kapatir.
        header = bytearray()
        header.append(0x81) # FIN + Text Frame
        
        if length <= 125:
            header.append(length | 0x80)
        elif length >= 126 and length <= 65535:
            header.append(126 | 0x80)
            header.append((length >> 8) & 255)
            header.append(length & 255)
        else:
            raise Exception("Cok buyuk veri")
            
        mask_key = os.urandom(4)
        header.extend(mask_key)
        
        masked_payload = bytearray(length)
        for i in range(length):
            masked_payload[i] = payload[i] ^ mask_key[i % 4]
            
        self.sock.send(header + masked_payload)

    def recv_frames(self):
        header = self.sock.recv(2)
        if not header or len(header) < 2:
            raise Exception("Baglanti koptu")
            
        b1, b2 = header[0], header[1]
        opcode = b1 & 0x0f
        mask = bool(b2 & 0x80)
        payload_len = b2 & 0x7f
        
        if payload_len == 126:
            ext = self.sock.recv(2)
            payload_len = (ext[0] << 8) | ext[1]
        elif payload_len == 127:
            ext = self.sock.recv(8)
            payload_len = (ext[4] << 24) | (ext[5] << 16) | (ext[6] << 8) | ext[7]
            
        mask_key = None
        if mask:
            mask_key = self.sock.recv(4)
            
        payload = bytearray()
        while len(payload) < payload_len:
            chunk = self.sock.recv(payload_len - len(payload))
            if not chunk:
                break
            payload.extend(chunk)
            
        if mask and mask_key:
            for i in range(payload_len):
                payload[i] ^= mask_key[i % 4]
                
        if opcode == 1: # Text
            return payload.decode('utf-8', 'ignore')
        elif opcode == 2: # Binary
            return payload
        elif opcode == 9: # Ping
            pong_hdr = bytearray([0x8a, payload_len])
            self.sock.send(pong_hdr + payload)
            return "PING_RECEIVED"
        elif opcode == 8: # Close
            raise Exception("Sunucu Close frame gonderdi")
            
        return None

    def close(self):
        if self.sock:
            try: self.sock.close()
            except: pass
