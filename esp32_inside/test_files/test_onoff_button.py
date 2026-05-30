"""
On/Off Switch Testi
===================
Kilitli switch (toggle) - bir pozisyonda açık, diğerinde kapalı.
  - Bir bacak -> GND
  - Diğer bacak -> D13 (GPIO13)

Switch'i çevirin ve değerin değişip değişmediğine bakın.
"""

from machine import Pin
import time

BUTTON_PIN = 4

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

print("=== ON/OFF SWITCH TESTİ ===")
print(f"Pin: D{BUTTON_PIN}")
print("Switch'i açıp kapatın. Çıkmak için Ctrl+C")
print("-" * 30)

last = -1
try:
    while True:
        raw = button.value()
        # Pull-up: switch kapalı (GND'ye bağlı) = 0, açık = 1
        state = "ON" if raw == 0 else "OFF"
        
        if raw != last:
            print(f">>> DEĞİŞTİ! Raw={raw}  Switch={state}")
            last = raw
        else:
            print(f"Raw={raw}  Switch={state}")
        
        time.sleep_ms(300)
except KeyboardInterrupt:
    print("\nTest durduruldu.")
