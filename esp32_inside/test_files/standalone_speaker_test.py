import network
import time
import socket
from machine import Pin, I2S

# --- AYARLAR ---
SSID = "Ata"
PASSWORD = "ata20032003"
UDP_PORT = 8082 # Ses dinleme portu (ESP32)

# Dahili Mavi LED
led = Pin(2, Pin.OUT)

# --- MAX98357A I2S AMFİ AYARLARI ---
LRC_PIN = 4   # (WS - Word Select)
DIN_PIN = 15  # (SD - Serial Data)
BCLK_PIN = 2  # (SCK - Serial Clock)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)  # Reset state
    time.sleep(0.5)
    wlan.active(True)
    
    if not wlan.isconnected():
        print("Wi-Fi'ya bağlanılıyor...")
        try:
            wlan.connect(SSID, PASSWORD)
        except OSError as e:
            pass
            
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            led.value(not led.value())
            time.sleep(0.5)
            timeout -= 0.5
            
        if not wlan.isconnected():
            print("Bağlantı zaman aşımına uğradı. Cihazı yeniden başlatmayı deneyin.")
            return False
            
    print("Bağlantı başarılı! IP:", wlan.ifconfig()[0])
    led.value(0)
    return True

def stream_speaker_udp():
    if not connect_wifi():
        return

    print("I2S Hoparlör (Amfi) başlatılıyor...")
    try:
        audio_out = I2S(
            1, 
            sck=Pin(BCLK_PIN),
            ws=Pin(LRC_PIN),
            sd=Pin(DIN_PIN),
            mode=I2S.TX,
            bits=16,
            format=I2S.MONO,
            rate=16000,
            ibuf=2048 # Sıkışmaması için düşük tutuyoruz!
        )
    except Exception as e:
        print("I2S Başlatma Hatası (Donanımsal Reset Atın):", e)
        return
        
    print("I2S başarıyla başlatıldı.")
    
    # UDP Server on ESP32
    print("UDP Soketi açılıyor...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', UDP_PORT))
    
    print(f">>> HOPARLÖR DİNLENİYOR (UDP Port: {UDP_PORT})")
    print("Bilgisayardan ses (output.wav) gönderilmesini bekliyor...")
    
    while True:
        try:
            # 1024'er bytelık paketleri al ve amfiye yaz
            data, addr = udp_socket.recvfrom(2048)
            audio_out.write(data)
        except Exception as e:
            print("Ses çalarken hata:", e)
            break
            
    # Hata veya çıkışta I2S'i temizle
    print("Test durduruldu, I2S kapatılıyor.")
    audio_out.deinit()

# Programı başlat
try:
    stream_speaker_udp()
except KeyboardInterrupt:
    print("Program durduruldu.")
