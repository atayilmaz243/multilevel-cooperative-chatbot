import time
import config
import led
import machine
from hardware import HardwareController
from network_app import connect_wifi, stream_record_and_play


def main():
    led.off() # Sistem reset yediğinde (OFF edildiğinde) LED'ler sönük başlasın
    print("=== Multilevel Cooperative Chatbot - ESP32 ===")

    # Donanım kontrolcüsünü başlat
    hw = HardwareController()

    # 1. On/Off switch kontrolü — açılana kadar bekle
    print("On/Off switch bekleniyor...")
    while not hw.is_system_on():
        time.sleep_ms(200)
    print("Sistem AÇIK!")

    # 2. Wi-Fi Bağlantısı (mavi blink efekti ile)
    ip = connect_wifi()
    
    # 2.5. DNS Önbelleğini Doldur (İlk istek gecikmesini önlemek için)
    from network_app import pre_warm_dns
    pre_warm_dns()
    
    print(f"Cihaz hazır. IP: {ip}")

    # 3. İlk seviye okuması ve LED renk gösterimi
    current_level = hw.read_level()
    led.solid_level_color(current_level)
    print(f"Başlangıç seviyesi: {current_level}/10")

    # 4. Ana Döngü — Push-to-Talk tabanlı
    while True:
        # --- On/Off Kontrolü (Tam Reset) ---
        if not hw.is_system_on():
            print("\n!!! SİSTEM KAPATILDI (OFF) !!!")
            led.off()
            # Tekrar açılana kadar burada hiçbir şey yapmadan bekle
            while not hw.is_system_on():
                time.sleep_ms(200)
            
            print("Sistem tekrar AÇIK! Cihaz resetleniyor (Hard Reset)...")
            time.sleep_ms(500) # Switch'in mekanik titremesini (bounce) geçmek için kısa bekleme
            machine.reset() # ESP32'yi tamamen fişten çekip takmış gibi yeniden başlatır


        # --- Potansiyometre Kontrolü ---
        new_level = hw.read_level_if_changed()
        if new_level is not None:
            current_level = new_level
            print(f"Seviye değişti: {current_level}/10")
            led.solid_level_color(current_level)

        # --- Push-to-Talk Kontrolü ---
        if hw.is_ptt_pressed():
            print(f"\n--- KAYIT BAŞLIYOR (Seviye: {current_level}) ---")
            stream_record_and_play(hw, current_level)
            print("--- İşlem tamamlandı ---")

            # Kayıt/çalma bitti, seviye rengine geri dön
            current_level = hw.read_level()
            led.solid_level_color(current_level)

        # Ana döngü yavaşlatma (busy-wait önleme)
        time.sleep_ms(50)


if __name__ == "__main__":
    main()
