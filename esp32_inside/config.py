# --- AĞ AYARLARI ---
SSID = "Ata"
PASSWORD = "ata20032003"
# Backend API URL'si
SERVER_URL = "http://139.162.160.73/api/chat"

# --- DONANIM PİNLERİ ---
# INMP441 Mikrofon Pinleri
MIC_SCK_PIN = 21
MIC_WS_PIN = 19
MIC_SD_PIN = 18

# MAX98357A DAC Hoparlör Pinleri
SPK_BCLK_PIN = 26   # RCLK -> D35
SPK_LRC_PIN = 27    # LRC  -> D27
SPK_DIN_PIN = 25   # DIN  -> D33

# NeoPixel (Rainbow) LED
NEOPIXEL_PIN = 23
NUM_LEDS = 60

# Potansiyometre (ADC) Pini — orta bacak
POT_PIN = 35
POT_STABLE_MS = 300  # Seviye değişikliği kabul süresi (ms)

# Push-to-Talk Buton Pini (diğer bacak GND'ye bağlı, dahili pull-up kullanılır)
PTT_BUTTON_PIN = 32

# On/Off Switch Pini (kilitli toggle, diğer bacak GND'ye bağlı, dahili pull-up)
ONOFF_PIN = 4

# --- UYGULAMA AYARLARI ---
# Cooperativeness seviyeleri (0-10)
DEFAULT_LEVEL = 5
MAX_LEVEL = 10

# Push-to-Talk güvenlik limiti — maksimum kayıt süresi (saniye)
MAX_RECORD_DURATION = 30

# I2S Örnekleme Hızı (16 kHz önerilir)
SAMPLE_RATE = 16000
