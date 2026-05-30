"""
Push-to-Talk Buton Testi
========================
Donanım bağlantısı:
  - Butonun bir bacağı -> GND
  - Butonun diğer bacağı -> D32 (GPIO32)

Dahili pull-up direnci kullanılır.
Butona basılınca: 1
Bırakılınca: 0
"""

from machine import Pin
import time

# Buton pini - dahili pull-up ile (GND'ye bağlı diğer bacak)
BUTTON_PIN = 32

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

print("=== PUSH-TO-TALK BUTON TESTİ ===")
print(f"Pin: D{BUTTON_PIN}")
print("Butona basın ve bırakın. Çıkmak için Ctrl+C")
print("-" * 30)

try:
    while True:
        # Pull-up: basılınca 0 gelir, bırakılınca 1
        # Kullanıcıya basılı=1, bırakılmış=0 göstermek için ters çeviriyoruz
        state = 1 if button.value() == 0 else 0
        print(state)
        time.sleep_ms(100)
except KeyboardInterrupt:
    print("\nTest durduruldu.")
