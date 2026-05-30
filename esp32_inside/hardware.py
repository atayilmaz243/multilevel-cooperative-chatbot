"""
Hardware Controller
===================
Potansiyometre (ADC), Push-to-Talk butonu ve On/Off switch'i yönetir.

Pin Haritası:
  - Potansiyometre orta bacak -> D34 (GPIO34, sadece giriş, ADC1_CH6)
  - Push-to-Talk buton        -> D32 (GPIO32, dahili pull-up)
  - On/Off switch             -> D4  (GPIO4, dahili pull-up)
"""

import machine
import time
import config


class HardwareController:
    def __init__(self):
        # --- Potansiyometre (ADC) ---
        self._adc = machine.ADC(machine.Pin(config.POT_PIN))
        self._adc.atten(machine.ADC.ATTN_11DB)      # 0 – 3.3V tam aralık
        # 12-bit (0-4095) varsayılan, width() çağrısı yeni sürümlerde kaldırıldı

        # --- Push-to-Talk Buton ---
        self._ptt = machine.Pin(config.PTT_BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

        # --- On/Off Switch ---
        self._onoff = machine.Pin(config.ONOFF_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
        
        # Switch "OFF" konumuna geçtiğinde (0 -> 1 yani RISING) anında sistemi durdurmak için Interrupt ekliyoruz.
        self._onoff.irq(trigger=machine.Pin.IRQ_RISING, handler=self._emergency_shutdown)

        # Dahili durum
        self._confirmed_level = -1     # Onaylanmış (stabil) seviye
        self._candidate_level = -1     # Aday seviye (henüz onaylanmamış)
        self._candidate_time = 0       # Aday seviyenin ilk görüldüğü zaman (ms)
        self._STABLE_MS = config.POT_STABLE_MS  # Config'den stabilizasyon süresi
        
        self._ptt_last_raw = 1         # Debounce için son durum
        self._ptt_last_time = 0        # Debounce zamanlayıcı (ms)
        self._ptt_stable = 1           # Debounce sonrası kararlı değer
        self._debounce_ms = 50         # Debounce süresi

    def _emergency_shutdown(self, pin):
        """
        Kesme (Interrupt) fonksiyonu: Switch OFF olduğu an sistemi donanımsal resetler.
        Hard IRQ içinde olduğumuz için sadece reset atıyoruz.
        """
        import machine
        machine.reset()

    # ------------------------------------------------------------------
    # Potansiyometre  →  Seviye  (0 – 10)  — 1 saniye stabilizasyonlu
    # ------------------------------------------------------------------
    def _read_raw_level(self) -> int:
        """Ham ADC okur ve 0-10 seviyeye çevirir (stabilizasyonsuz)."""
        raw = self._adc.read()
        # ESP32 ADC 3.3V'da bile 4095'e ulaşamaz
        # Üst limiti düşürüyoruz ki pot en sona geldiğinde seviye 10 olabilsin
        ADC_MAX = 3200
        raw = min(raw, ADC_MAX)
        return min(raw * (config.MAX_LEVEL + 1) // ADC_MAX, config.MAX_LEVEL)

    def read_level(self) -> int:
        """
        Onaylanmış (stabil) seviyeyi döndürür.
        İlk çağrıda anlık değeri kabul eder (başlangıç).
        """
        raw_level = self._read_raw_level()
        now = time.ticks_ms()
        
        # İlk okuma — hemen kabul et
        if self._confirmed_level == -1:
            self._confirmed_level = raw_level
            self._candidate_level = raw_level
            self._candidate_time = now
            return self._confirmed_level
        
        # Ham seviye aday seviyeyle aynıysa zamanlayıcı devam etsin
        if raw_level == self._candidate_level:
            # Aday yeterince uzun süredir stabil mi?
            if raw_level != self._confirmed_level:
                if time.ticks_diff(now, self._candidate_time) >= self._STABLE_MS:
                    self._confirmed_level = raw_level
        else:
            # Yeni bir aday seviye — zamanlayıcıyı sıfırla
            self._candidate_level = raw_level
            self._candidate_time = now

        return self._confirmed_level

    def read_level_if_changed(self):
        """
        Seviye değiştiyse (1 saniye stabil kaldıktan sonra) yeni seviyeyi döndürür.
        Değişmediyse None döner.
        """
        old = self._confirmed_level
        current = self.read_level()

        if current != old and old != -1:
            return current

        return None

    # ------------------------------------------------------------------
    # Push-to-Talk Buton  (debounce'lu)
    # ------------------------------------------------------------------
    def is_ptt_pressed(self) -> bool:
        """
        Push-to-Talk butonunun basılı olup olmadığını döndürür.
        50ms debounce uygulanır.
        Pull-up: basılı = 0, bırakılmış = 1.
        """
        raw = self._ptt.value()
        now = time.ticks_ms()

        if raw != self._ptt_last_raw:
            self._ptt_last_raw = raw
            self._ptt_last_time = now

        if time.ticks_diff(now, self._ptt_last_time) >= self._debounce_ms:
            self._ptt_stable = raw

        # Pull-up: basılı = 0  →  True döndür
        return self._ptt_stable == 0

    # ------------------------------------------------------------------
    # On/Off Switch
    # ------------------------------------------------------------------
    def is_system_on(self) -> bool:
        """
        On/Off switch durumunu döndürür.
        Pull-up: switch ON (GND'ye bağlı) = 0  →  True.
        """
        return self._onoff.value() == 0
