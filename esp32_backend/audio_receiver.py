import socket
import wave
import signal
import sys
import os

UDP_IP = "0.0.0.0"
UDP_PORT = 8081

# Ses ayarları (ESP32'deki I2S ayarlarına uygun olmalı)
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPWIDTH = 2 # 16-bit (2 bytes)

# Sockets
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"UDP sunucusu {UDP_PORT} portunda başlatıldı...")
except Exception as e:
    print(f"UDP sunucusu başlatılamadı: {e}")
    sys.exit(1)

frames = []

def save_wav(signum, frame):
    print("\n[+] Ses kaydediliyor: output.wav")
    try:
        with wave.open("output.wav", "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPWIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
        print(f"[✓] Kaydedildi! Toplam {len(frames)} paket alındı.")
    except Exception as e:
        print(f"[x] Kayıt sırasında hata oluştu: {e}")
    sys.exit(0)

# Ctrl+C ile kapatıldığında kaydet
signal.signal(signal.SIGINT, save_wav)

print("Ses dinleniyor... Kaydetmek ve çıkmak için Ctrl+C'ye basın.")
print("ESP32'den veri bekleniyor...")

while True:
    try:
        data, addr = sock.recvfrom(4096)
        if len(frames) == 0:
            print(f">>> İlk veri paketi {addr} adresinden alındı! Boyut: {len(data)} byte")
        frames.append(data)
    except Exception as e:
        print(f"Hata: {e}")
        break
