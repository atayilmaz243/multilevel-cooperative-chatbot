import network
import time
from machine import Pin
from simple_ws import SimpleWebSocket

# --- AYARLAR ---
SSID = "Ata"
PASSWORD = "ata20032003"
SERVER_IP = "172.20.10.5"  # Mac M1'inin yerel IP adresi
SERVER_PORT = 8080

# Dahili Mavi LED (ESP32 DevKit modellerinde genelde Pin 2'dir)
led = Pin(2, Pin.OUT)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Wi-Fi'ya bağlanılıyor...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            led.value(not led.value())
            time.sleep(0.5)
    print("Bağlantı başarılı! IP:", wlan.ifconfig()[0])
    led.value(0)

def listen_server():
    while True:
        try:
            connect_wifi()
            
            ws = SimpleWebSocket(SERVER_IP, SERVER_PORT, path="/ws")
            ws.connect()
            print("WebSocket Receiver Moduna Geçildi...")
            
            while True:
                msg = ws.recv_frames()
                
                if msg == "PING_RECEIVED" or msg is None:
                    continue
                
                print(f"Alınan Mesaj: {msg}")
                
                # Sadece string gelirse içinde string arıyoruz
                if isinstance(msg, str) and "LED_TOGGLE" in msg:
                    print(">>> Komut Alındı: Mavi Işık Durumu Değiştiriliyor!")
                    led.value(not led.value())
                
        except Exception as e:
            print("Bağlantı x hatası:", e)
            print("5 saniye içinde yeniden bağlanılıyor...")
            try: ws.close()
            except: pass
            time.sleep(5)

# Programı başlat
listen_server()