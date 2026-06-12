# --- SES AYARLARI ---

# Mikrofondan gelen sesin yükseltme katsayısı (ffmpeg volume filtresi)
# Örn: 4.0 = %400 / 4 kat yükseltme
MIC_INPUT_VOLUME = 4.0

# TTS çıkışının ses seviyesi (ffmpeg volume filtresi)
# Donanım kazancı (GAIN VDD'ye bağlı) yüksek olduğu için dijital patlamayı önlemek adına 1.0 yapıldı.
TTS_OUTPUT_VOLUME = 1.0
