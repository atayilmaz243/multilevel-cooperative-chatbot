import gc
from machine import I2S, Pin
import config

def init_mic():
    print("Mikrofon başlatılıyor (RX)...")
    try:
        audio_in = I2S(
            0,
            sck=Pin(config.MIC_SCK_PIN),
            ws=Pin(config.MIC_WS_PIN),
            sd=Pin(config.MIC_SD_PIN),
            mode=I2S.RX,
            bits=16,
            format=I2S.MONO,
            rate=config.SAMPLE_RATE,
            ibuf=4096
        )
        return audio_in
    except Exception as e:
        print("Mikrofon başlatılamadı:", e)
        return None

def deinit_mic(audio_in):
    if audio_in:
        audio_in.deinit()
    gc.collect()

def init_speaker():
    print("Hoparlör başlatılıyor (TX)...")
    try:
        audio_out = I2S(
            1,
            sck=Pin(config.SPK_BCLK_PIN),
            ws=Pin(config.SPK_LRC_PIN),
            sd=Pin(config.SPK_DIN_PIN),
            mode=I2S.TX,
            bits=16,
            format=I2S.MONO,
            rate=config.SAMPLE_RATE,
            ibuf=4096
        )
        return audio_out
    except Exception as e:
        print("Hoparlör başlatılamadı:", e)
        return None

def deinit_speaker(audio_out):
    if audio_out:
        audio_out.deinit()
    gc.collect()
