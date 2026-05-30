"""
Potansiyometre HAM DEĞER (RAW) + LED Testi
==========================================
Bu kod seviyenin değişmesini BEKLEMEZ. 
Her 200ms'de bir potansiyometreden okunan HAM (RAW) ADC değerini 
sürekli olarak ekrana basar. Böylece temassızlık anında ne okuduğunuzu net görürsünüz.
"""

from machine import Pin, ADC
import neopixel
import time

# --- AYARLAR ---
POT_PIN = 35
NEOPIXEL_PIN = 23
NUM_LEDS = 60
MAX_LEVEL = 10

# --- LED BAŞLAT ---
np = neopixel.NeoPixel(Pin(NEOPIXEL_PIN), NUM_LEDS)

# --- ADC BAŞLAT ---
adc = ADC(Pin(POT_PIN))
adc.atten(ADC.ATTN_11DB)

def level_to_color(level):
    level = max(0, min(level, 10))
    if level <= 5:
        r = int(255 * level / 5)
        g = 255
    else:
        r = 255
        g = int(255 * (10 - level) / 5)
    return (r, g, 0)

print("=== POTANSİYOMETRE HAM (RAW) DEĞER TESTİ ===")
print("Değerler sürekli akacak. Çevirdiğinizde RAW'ın 0 ile 4095 arası değişmesi lazım.")
print("Eğer değerler rastgele atlıyorsa temassızlık / bozuk pot vardır.")
print("-" * 50)

try:
    while True:
        raw = adc.read()
        level = min(raw * (MAX_LEVEL + 1) // 4096, MAX_LEVEL)
        
        # LED rengini güncelle
        color = level_to_color(level)
        np.fill(color)
        np.write()
        
        # HER DURUMDA EKRANA BAS (Değişmesini beklemeden)
        print(f"RAW DEĞER: {raw:4d}  |  Hesaplanan Seviye: {level:2d}/10")
        
        time.sleep_ms(200)

except KeyboardInterrupt:
    np.fill((0, 0, 0))
    np.write()
    print("\nTest durduruldu. LED'ler kapatıldı.")
