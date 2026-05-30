import machine
import neopixel
import math
import time
import config

# --- NeoPixel nesnesi (modül yüklendiğinde oluşturulur) ---
np = neopixel.NeoPixel(machine.Pin(config.NEOPIXEL_PIN), config.NUM_LEDS)

# --- Breathing efekti dahili durumu ---
_breathe_angle = 0.0        # Sinüs dalgası açısı (radyan)
_BREATHE_SPEED = 0.12       # Her adımda açı artışı (küçük = daha yavaş nefes)

# --- Rainbow chase efekti dahili durumu ---
_chase_pos = 0              # Gökkuşağı kuyruklu ışığın mevcut pozisyonu

# --- Yardımcı ---
def _wheel(pos):
    """0-255 arası değer alıp RGB tuple döndürür (gökkuşağı paleti)."""
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)


def _scale_color(color, brightness):
    """RGB rengi verilen parlaklık (0.0 - 1.0) ile ölçeklendirir."""
    return (
        int(color[0] * brightness),
        int(color[1] * brightness),
        int(color[2] * brightness)
    )


def _level_color(level):
    """
    Seviye (0-10) için baz RGB renk döndürür (tam parlaklıkta).
    0 = Yeşil (max cooperative) → 5 = Sarı → 10 = Kırmızı (min cooperative)
    """
    level = max(0, min(level, 10))
    if level <= 5:
        r = int(255 * level / 5)
        g = 255
    else:
        r = 255
        g = int(255 * (10 - level) / 5)
    return (r, g, 0)


# =====================================================================
#  DURUM EFEKTLERİ
# =====================================================================

def off():
    """Tüm LED'leri kapatır."""
    np.fill((0, 0, 0))
    np.write()


def solid_green():
    """Tüm LED'leri sabit yeşil yakar."""
    np.fill((0, 255, 0))
    np.write()


# ---------------------------------------------------------------------
#  SEVIYE RENK GÖSTERİMİ  (Idle durumu)
# ---------------------------------------------------------------------

def solid_level_color(level):
    """
    Cooperativeness seviyesine (0-10) göre LED rengini ayarlar.
    Yeşil (0/cooperative) → Sarı (5) → Kırmızı (10/uncooperative) gradyanı.
    Tüm LED'ler yanar, renk seviyeyi gösterir.
    """
    color = _level_color(level)
    np.fill(color)
    np.write()


# ---------------------------------------------------------------------
#  BREATHING EFEKTI  (Kayıt sırasında — PTT basılıyken)
# ---------------------------------------------------------------------

def breathe_reset():
    """
    Breathing efekti dahili durumunu sıfırlar.
    Yeni bir kayıt başlamadan önce çağrılmalıdır.
    """
    global _breathe_angle
    _breathe_angle = 0.0


def breathe_step():
    """
    Sinüs dalgası tabanlı nefes efekti (NON-BLOCKING, tek adım).
    
    Lineer yerine sinüs kullanarak çok daha doğal ve yumuşak bir 
    parlaklık geçişi sağlar. Minimum parlaklık 5%, maksimum 100%.
    
    Renk: Beyaz-Kırmızı arası (nefeste beyaza yaklaşır, solduğunda koyu kırmızı).
    """
    global _breathe_angle

    _breathe_angle += _BREATHE_SPEED

    # sin(x) çıktısı -1..1 → 0..1 aralığına normalize et
    brightness = (math.sin(_breathe_angle) + 1.0) / 2.0
    
    # Minimum parlaklık %5, maksimum %100
    brightness = 0.05 + brightness * 0.95
    
    # Kırmızı-Beyaz arası: parlakken hafif beyaza kayar
    r = int(255 * brightness)
    g = int(60 * brightness * brightness)  # Daha az yeşil — kırmızımsı kalır
    b = int(40 * brightness * brightness)  # Hafif sıcak ton
    
    # LED'lere dalga deseni uygula (ortadan kenara yayılarak)
    center = config.NUM_LEDS // 2
    for i in range(config.NUM_LEDS):
        dist = abs(i - center)
        # Merkezden uzaklaştıkça hafif faz kayması (dalga efekti)
        phase_offset = dist * 0.08
        local_bright = (math.sin(_breathe_angle - phase_offset) + 1.0) / 2.0
        local_bright = 0.05 + local_bright * 0.95
        
        lr = int(255 * local_bright)
        lg = int(60 * local_bright * local_bright)
        lb = int(40 * local_bright * local_bright)
        np[i] = (lr, lg, lb)
    
    np.write()


# ---------------------------------------------------------------------
#  RAINBOW CHASE EFEKTI  (Yanıt çalarken)
# ---------------------------------------------------------------------

def rainbow_chase_reset():
    """Rainbow chase efektinin pozisyonunu sıfırlar."""
    global _chase_pos
    _chase_pos = 0


def rainbow_chase_step():
    """
    Gökkuşağı kovalama (chase) efekti — NON-BLOCKING, tek adım.
    
    Parlak bir gökkuşağı kuyruğu LED şeridin üzerinde döner.
    Kuyruk uzunluğu şeridin %40'ı kadardır. Kuyruktan uzaklaşan LED'ler
    hızla söner, önde parlak renkler parlar.
    
    Her ses chunk'ı sonrası bir kez çağrılır.
    """
    global _chase_pos
    
    tail_len = max(config.NUM_LEDS * 2 // 5, 8)  # Kuyruk uzunluğu (%40)
    
    for i in range(config.NUM_LEDS):
        # Baş pozisyonundan uzaklık (dairesel)
        dist = (_chase_pos - i) % config.NUM_LEDS
        
        if dist < tail_len:
            # Kuyruk içinde — gökkuşağı rengi + solma
            fade = 1.0 - (dist / tail_len)
            fade = fade * fade  # Kuadratik solma — daha dramatik
            rainbow_color = _wheel((i * 256 // config.NUM_LEDS) & 255)
            np[i] = _scale_color(rainbow_color, fade)
        else:
            # Kuyruk dışı — kapalı
            np[i] = (0, 0, 0)
    
    np.write()
    _chase_pos = (_chase_pos + 1) % config.NUM_LEDS


# ---------------------------------------------------------------------
#  WI-FI BLINK EFEKTI
# ---------------------------------------------------------------------

def blue_blink(count=1, interval_ms=300):
    """
    Mavi yanıp-söner (WiFi bağlanırken).
    count: kaç kez blink yapacak
    interval_ms: açık/kapalı süre (ms)
    """
    for _ in range(count):
        np.fill((0, 0, 255))
        np.write()
        time.sleep_ms(interval_ms)
        np.fill((0, 0, 0))
        np.write()
        time.sleep_ms(interval_ms)


# ---------------------------------------------------------------------
#  ESKİ FONKSİYONLAR (geriye dönük uyumluluk)
# ---------------------------------------------------------------------

def rainbow_cycle(wait_ms=10):
    """
    Tek tam gökkuşağı döngüsü çalıştırır (0-254 adım).
    Blocking çağrıdır; çalma/bekleme süresince while döngüsünde çağırın.
    """
    for j in range(255):
        for i in range(config.NUM_LEDS):
            pixel_index = (i * 256 // config.NUM_LEDS) + j
            np[i] = _wheel(pixel_index & 255)
        np.write()
        time.sleep_ms(wait_ms)


def rainbow_static():
    """
    Gökkuşağı renklerini LED şeride statik olarak yazar.
    """
    for i in range(config.NUM_LEDS):
        pixel_index = (i * 256 // config.NUM_LEDS)
        np[i] = _wheel(pixel_index & 255)
    np.write()
