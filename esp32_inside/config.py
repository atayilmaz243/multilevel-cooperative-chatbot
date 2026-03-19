# --- AĞ AYARLARI ---
SSID = "Ata"
PASSWORD = "ata20032003"
# Backend API URL'si
SERVER_URL = "http://192.168.1.42:8080/api/chat"

# --- DONANIM PİNLERİ ---
# Wi-Fi Durum LED'i (Ağa bağlanırken yanıp söner, bağlanınca sabitlenir)
WIFI_LED_PIN = 32

# Mavi LED
LED_PIN = 2

# INMP441 Mikrofon Pinleri
MIC_SCK_PIN = 19
MIC_WS_PIN = 18
MIC_SD_PIN = 5

# MAX98357A Hoparlör Pinleri
SPK_BCLK_PIN = 2  # LED Pin ile aynı. I2S çalışırken LED otomatik yanıp sönebilir.
SPK_LRC_PIN = 4
SPK_DIN_PIN = 15

# --- UYGULAMA AYARLARI ---
# Ses kaydına başlamadan önceki bekleme süresi (saniye)
PREPARATION_DELAY = 3

# Mavi ışığın yanma ve ses kaydetme süresi (saniye)
RECORD_DURATION = 15

# I2S Örnekleme Hızı (16 kHz önerilir)
SAMPLE_RATE = 16000
