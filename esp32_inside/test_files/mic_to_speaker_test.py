import time
import gc
from machine import Pin, I2S

# --- PINS ---
# MIC (INMP441)
MIC_SCK_PIN = 19
MIC_WS_PIN = 18
MIC_SD_PIN = 5

# SPEAKER (MAX98357A)
SPK_BCLK_PIN = 2
SPK_LRC_PIN = 4
SPK_DIN_PIN = 15

def record_and_play():
    print("=== MİKROFON -> HOPARLÖR TESTİ ===")
    
    # 1. Initialize Microphone (I2S.RX)
    print("Mikrofon başlatılıyor (I2S_0)...")
    try:
        audio_in = I2S(
            0,
            sck=Pin(MIC_SCK_PIN),
            ws=Pin(MIC_WS_PIN),
            sd=Pin(MIC_SD_PIN),
            mode=I2S.RX,
            bits=16,
            format=I2S.MONO,
            rate=16000,
            ibuf=2048 # Hafıza hatasını önlemek için düşük tuttuk
        )
    except Exception as e:
        print("Mikrofon başlatılamadı:", e)
        return
        
    print("\n>>> KAYIT BAŞLIYOR (yaklaşık 4 saniye sürecek) <<<")
    print("Lütfen mikrofona konuşun...\n")
    
    # 1 saniyelik ses = 16000 Hz * 2 byte = 32000 byte
    # 4 saniye = 128 KB. Parçalar halinde liste içinde tutarsak hafıza parçalanmasını önleriz.
    CHUNK_SIZE = 1024
    chunks = []
    buffer = bytearray(CHUNK_SIZE)
    
    # 32000 / 1024 = saniyede ~31 chunk.
    # 4 saniye için 125 chunk yeterli.
    for i in range(125):
        try:
            num_bytes = audio_in.readinto(buffer)
            if num_bytes > 0:
                # Hafızaya kaydet
                chunks.append(bytes(buffer[:num_bytes]))
        except Exception as e:
            print("Kayıt sırasında hata (Hafıza dolmuş olabilir):", e)
            break
            
    print("\nKayıt tamamlandı! Mikrofon I2S kapatılıyor...")
    audio_in.deinit()
    
    print("Hafıza temizleniyor...")
    gc.collect() # Çöp toplayıcıyı çalıştırarak hoparlör için yer açalım
    time.sleep(1)
    
    # 2. Initialize Speaker (I2S.TX)
    print("\nHoparlör başlatılıyor (I2S_1)...")
    try:
        audio_out = I2S(
            1,
            sck=Pin(SPK_BCLK_PIN),
            ws=Pin(SPK_LRC_PIN),
            sd=Pin(SPK_DIN_PIN),
            mode=I2S.TX,
            bits=16,
            format=I2S.MONO,
            rate=16000,
            ibuf=2048
        )
    except Exception as e:
        print("Hoparlör başlatılamadı:", e)
        return
        
    print("\n>>> KAYDEDİLEN SES ÇALINIYOR <<<")
    
    for chunk in chunks:
        try:
            audio_out.write(chunk)
        except Exception as e:
            print("Çalma sırasında hata:", e)
            break
            
    print("\nÇalma tamamlandı! Hoparlör kapatılıyor...")
    audio_out.deinit()
    
    print("=== TEST BAŞARIYLA BİTTİ ===")

try:
    record_and_play()
except KeyboardInterrupt:
    print("Program kullanıcı tarafından durduruldu.")
