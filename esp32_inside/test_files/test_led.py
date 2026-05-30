import machine
import neopixel
import time

# --- AYARLAR ---
LED_PIN = 23    # LED'in bağlı olduğu pin (D23)
NUM_LEDS = 60   # Şeritteki tüm LED'lerin yanması için sayıyı artırdık (tam LED sayınızı buraya yazabilirsiniz)

# NeoPixel nesnesini oluştur
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)

def wheel(pos):
    """
    0'dan 255'e kadar girdi alarak RGB renkleri üretir.
    Renkler kırmızıdan yeşile, sonra maviye ve tekrar kırmızıya döner.
    """
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

def rainbow_cycle(wait):
    """Gökkuşağı efekti oluşturur."""
    for j in range(255):
        for i in range(NUM_LEDS):
            pixel_index = (i * 256 // NUM_LEDS) + j
            np[i] = wheel(pixel_index & 255)
        np.write()
        time.sleep_ms(wait)

def test_basic_colors():
    """Temel renkleri (Kırmızı, Yeşil, Mavi) test eder."""
    print("Kırmızı yanıyor...")
    np.fill((255, 0, 0))  # Tüm LED'leri Kırmızı yap
    np.write()
    time.sleep(1)

    print("Yeşil yanıyor...")
    np.fill((0, 255, 0))  # Tüm LED'leri Yeşil yap
    np.write()
    time.sleep(1)

    print("Mavi yanıyor...")
    np.fill((0, 0, 255))  # Tüm LED'leri Mavi yap
    np.write()
    time.sleep(1)

    print("LED kapatılıyor...")
    np.fill((0, 0, 0))    # LED'i kapat
    np.write()
    time.sleep(0.5)

if __name__ == "__main__":
    print("--- D23 Rainbow LED Testi Başlıyor ---")
    
    # 1. Aşama: Temel Renklerin Testi
    test_basic_colors()
    
    # 2. Aşama: Gökkuşağı Efekti Testi
    print("\nGökkuşağı efekti başlatılıyor...")
    print("(Durdurmak için klavyeden 'Ctrl + C' veya Thonny'den 'Stop/Restart' butonunu kullanabilirsiniz.)")
    
    try:
        while True:
            rainbow_cycle(10)
    except KeyboardInterrupt:
        print("\nTest kullanıcı tarafından durduruldu.")
        np.fill((0, 0, 0)) # Kapat
        np.write()
        print("LED söndürüldü.")
