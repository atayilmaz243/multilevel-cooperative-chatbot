import time
import gc
from machine import Pin
import config
from network_app import connect_wifi, stream_record_and_play

# Hoparlör ve LED Pin 2'yi paylaşıyor
led = Pin(config.LED_PIN, Pin.OUT)

def main_loop():
    print("=== ESP32 SESLİ ASİSTAN BAŞLATILDI ===")
    connect_wifi()
    gc.collect()
    
    while True:
        print("\n[Hazır] Bir sonraki döngü başlıyor...")
        
        # Hazırlık bekleme süresi
        print(f"Lütfen hazırlanın... {config.PREPARATION_DELAY} saniye sonra kayıt başlayacak.")
        for i in range(config.PREPARATION_DELAY, 0, -1):
            print(f"{i}...", end=" ")
            time.sleep(1)
        print()
        
        # Ağ üzerinden stream (hem kaydeder hem gönderir hem dinler hem de çalar)
        # LED kontrolü doğrudan bu fonksiyon içinde, "sadece tam kayıt esnasında" yapılacak
        stream_record_and_play(config.RECORD_DURATION, led)
        
        print("Döngü sonu temizliği...")
        gc.collect()
        
        # Kısa bekleme sonrası yeni döngü
        time.sleep(2)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Kullanıcı tarafından durduruldu.")