import network
import time
import socket
import machine
from machine import Pin, I2S

# --- AYARLAR ---
SSID = "Ata"
PASSWORD = "ata20032003"
SERVER_IP = "172.20.10.5"  # Mac M1'inin yerel IP adresi
UDP_PORT = 8081

# Dahili Mavi LED
led = Pin(2, Pin.OUT)

# --- I2S MİKROFON AYARLARI (INMP441) ---
SCK_PIN = 19
WS_PIN = 18
SD_PIN = 5

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)  # Reset state
    time.sleep(0.5)
    wlan.active(True)
    
    wlan.disconnect()
    time.sleep(0.5)
    
    if not wlan.isconnected():
        print("Wi-Fi'ya bağlanılıyor...")
        try:
            wlan.connect(SSID, PASSWORD)
        except OSError as e:
            print("Wifi bağlanma hatası (İç Durum Hatası), donanımsal reset atılıyor...", e)
            time.sleep(1)
            machine.reset()
            
        timeout = 30 # 30 saniye bekle
        while not wlan.isconnected() and timeout > 0:
            led.value(not led.value())
            time.sleep(0.5)
            timeout -= 0.5
            
        if not wlan.isconnected():
            print("Bağlantı zaman aşımına uğradı (30sn). Cihazı yeniden başlatılıyor...")
            time.sleep(1)
            machine.reset()
            return False
            
    print("Bağlantı başarılı! IP:", wlan.ifconfig()[0])
    led.value(0)
    return True

def test_microphone():
    if not connect_wifi():
        return
    print("I2S Mikrofon başlatılıyor...")
    audio_in = I2S(
        0,
        sck=Pin(SCK_PIN),
        ws=Pin(WS_PIN),
        sd=Pin(SD_PIN),
        mode=I2S.RX,
        bits=16,
        format=I2S.MONO,
        rate=16000,
        ibuf=4096
    )
    
    print("UDP Soketi açılıyor...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    buffer = bytearray(1024)
    
    print(f">>> SES AKIŞI BAŞLADI (Hedef: {SERVER_IP}:{UDP_PORT})")
    print("Mikrofona konuşabilirsiniz!")
    
    while True:
        try:
            num_bytes = audio_in.readinto(buffer)
            if num_bytes > 0:
                # Sesi bilgisayara UDP ile gönder
                udp_socket.sendto(buffer[:num_bytes], (SERVER_IP, UDP_PORT))
        except Exception as e:
            print("Ses okuma/gönderme hatası:", e)
            time.sleep(1)

# Programı başlat
try:
    test_microphone()
except KeyboardInterrupt:
    print("Program durduruldu.")
