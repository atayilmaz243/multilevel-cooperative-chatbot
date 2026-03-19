import socket
import wave
import sys
import time

# ESP32'nin IP Adresi (Cihaz bağlandıktan sonra ekrandaki IP'yi buraya yazın)
UDP_IP = "172.20.10.10" # ESP32'nin IP Adresi (ÖRNEK) 
UDP_PORT = 8082

FILE_NAME = "output.wav"

try:
    with wave.open(FILE_NAME, 'rb') as wf:
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        
        print(f"[{FILE_NAME}] açıldı. (Hız: {sample_rate}Hz, Kanal: {channels}, Bit: {sampwidth*8}-bit)")
        
        # Sockets
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Chunk boyutu I2S buffer'ına uygun olmalı
        chunk_size = 1024
        
        print(f"ESP32'ye Gönderiliyor... ({UDP_IP}:{UDP_PORT})")
        
        data = wf.readframes(chunk_size)
        while data:
            sock.sendto(data, (UDP_IP, UDP_PORT))
            
            # ESP32'nin buffer'ını taşırmamak için biraz bekleyelim (1024 byte 16kHz'de yaklaşık 0.03 saniye sürer)
            time.sleep(0.025) 
            
            data = wf.readframes(chunk_size)
            
        print("Ses dosyası başarıyla gönderildi!")
except FileNotFoundError:
    print(f"Hata: '{FILE_NAME}' dosyası bulunamadı. Önce mikrofon testini yapıp sesi kaydettiğinizden emin olun.")
except Exception as e:
    print(f"Hata oluştu: {e}")
