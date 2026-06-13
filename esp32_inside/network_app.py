import network
import time
import socket
import config
import led
from audio import init_mic, deinit_mic, init_speaker, deinit_speaker

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while not wlan.isconnected():
        print("Wi-Fi'ya bağlanılıyor...")
        try:
            wlan.connect(config.SSID, config.PASSWORD)

            # Bağlanmayı beklerken mavi blink efekti
            timeout = 10
            while not wlan.isconnected() and timeout > 0:
                led.blue_blink(count=1, interval_ms=300)
                print(".", end="")
                timeout -= 1

        except Exception as e:
            print("\nWiFi Hatası:", e)

        if not wlan.isconnected():
            print("\nBağlantı başarısız oldu, 3 saniye sonra tekrar denenecek...")
            led.off()
            time.sleep(3)
            wlan.active(False)
            time.sleep(1)
            wlan.active(True)

    print("\nBağlantı başarılı! IP:", wlan.ifconfig()[0])
    led.off()
    return wlan.ifconfig()[0]

def parse_url(url):
    # Basit URL ayırıcı (http://172.20.10.5:8080/api/chat)
    url = url.replace("http://", "")
    parts = url.split("/", 1)
    host_port = parts[0].split(":")
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 80
    path = "/" + parts[1] if len(parts) > 1 else "/"
    return host, port, path

_cached_addr = None

def pre_warm_dns():
    """
    Wi-Fi bağlandıktan hemen sonra DNS çözümlemesini yapıp önbelleğe alır.
    Böylece kullanıcının ilk butona basışındaki 2-3 saniyelik DNS gecikmesi tamamen yok olur.
    """
    global _cached_addr
    host, port, _ = parse_url(config.SERVER_URL)
    print("\nSunucu adresi çözümleniyor (DNS Pre-warm)...")
    try:
        _cached_addr = socket.getaddrinfo(host, port)[0][-1]
        print("DNS Ön belleğe alındı:", _cached_addr)
    except Exception as e:
        print("DNS çözümlenemedi:", e)
def stream_record_and_play(hw_controller, level):
    """
    Push-to-Talk tabanlı ses kaydı ve çalma.
    
    Buton basılı olduğu sürece mikrofon sesi HTTP POST ile sunucuya akıtılır.
    Buton bırakıldığında kayıt durur, sunucudan yanıt beklenir ve çalınır.
    
    LED Efektleri:
      - Kayıt: Kırmızı nefes (breathing) efekti
      - Yanıt bekleme / çalma: Gökkuşağı
    
    Cooperativeness seviyesi X-Cooperativeness-Level header'ı ile gönderilir.
    
    Args:
        hw_controller: HardwareController nesnesi (PTT durumu kontrolü için)
        level: Cooperativeness seviyesi (1-10)
    """
    global _cached_addr
    
    # Anında tepki hissi vermek için LED'i geçici olarak turuncu/sarı yap
    led.np.fill((50, 20, 0))
    led.np.write()
    
    host, port, path = parse_url(config.SERVER_URL)

    # 1. Soket Aç
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    try:
        # DNS sorgusunu (veya IP çözümlemeyi) önbelleğe alıyoruz.
        # Bu, her butona basıldığında yaşanan 2-3 saniyelik gecikmeyi (DNS Timeout) önler!
        if _cached_addr is None:
            _cached_addr = socket.getaddrinfo(host, port)[0][-1]
        s.connect(_cached_addr)
    except Exception as e:
        print("\n[HATA] Sunucuya bağlanılamadı! Lütfen bilgisayardaki backend'in (" + host + ":" + str(port) + ") açık olduğundan emin olun.")
        print("Soket Detayı:", e)
        s.close()
        led.off()
        return False

    print(f"\nSunucuya bağlanıldı ({host}:{port})...")
    s.settimeout(None)

    try:
        # HTTP Chunked Gönderimi Hazırlığı — seviye header'ı eklendi
        s.send((f"POST {path} HTTP/1.1\r\n").encode())
        s.send((f"Host: {host}\r\n").encode())
        s.send(b"Transfer-Encoding: chunked\r\n")
        s.send(b"Content-Type: application/octet-stream\r\n")
        s.send((f"X-Cooperativeness-Level: {level}\r\n").encode())
        s.send(b"\r\n")

        audio_in = init_mic()
        if not audio_in:
            s.close()
            return False

        buf_size = 2048
        buffer = bytearray(buf_size)

        # Güvenlik limiti: maksimum chunk sayısı
        chunks_per_sec = int((config.SAMPLE_RATE * 2) / buf_size)
        max_chunks = int(chunks_per_sec * config.MAX_RECORD_DURATION)

        # --- KAYIT: Kırmızı Nefes Efekti ---
        print(f">>> KAYIT BAŞLADI (Buton bırakılana kadar, maks {config.MAX_RECORD_DURATION}sn)...")
        led.breathe_reset()
        
        chunks_sent = 0
        record_start = time.ticks_ms()

        while hw_controller.is_ptt_pressed() and chunks_sent < max_chunks:
            # Her saniyede bir durum yazdır
            if chunks_sent % chunks_per_sec == 0:
                elapsed = chunks_sent // chunks_per_sec
                print(f"[{elapsed}sn] Kayıt devam ediyor...")

            num_bytes = audio_in.readinto(buffer)
            if num_bytes > 0:
                chunk_len = "{:x}\r\n".format(num_bytes).encode()
                s.send(chunk_len)
                s.send(memoryview(buffer)[:num_bytes])
                s.send(b"\r\n")
                chunks_sent += 1

            # Her chunk sonrası breathing efektinin bir adımını uygula
            led.breathe_step()

        # Kayıt süresi hesapla
        record_duration_ms = time.ticks_diff(time.ticks_ms(), record_start)
        record_secs = record_duration_ms / 1000

        # Chunked sonu
        s.send(b"0\r\n\r\n")
        deinit_mic(audio_in)
        led.off()
        
        if chunks_sent >= max_chunks:
            print(f">>> KAYIT BİTTİ (güvenlik limiti: {config.MAX_RECORD_DURATION}sn). Yanıt bekleniyor...")
        else:
            print(f">>> KAYIT BİTTİ ({record_secs:.1f}sn). Yanıt bekleniyor...")

        # --- YANIT BEKLENİYOR: Beyaz yanıp-sönme ---
        s.settimeout(0.5)  # 500ms timeout ile okuma dene
        
        # 2. HTTP Cevabını Oku (beyaz blink ile bekleme)
        header_data = b""
        blink_state = False
        while b"\r\n\r\n" not in header_data:
            # Beyaz yanıp sönme
            blink_state = not blink_state
            if blink_state:
                np_fill_white = (255, 255, 255)
                led.np.fill(np_fill_white)
            else:
                led.np.fill((0, 0, 0))
            led.np.write()
            
            try:
                chunk = s.recv(128)
                if not chunk:
                    break
                header_data += chunk
            except OSError:
                # Timeout — veri henüz gelmedi, blink devam etsin
                pass
        
        s.settimeout(None)  # Timeout'u kaldır

        if b"\r\n\r\n" not in header_data:
            print("Geçerli bir HTTP yanıtı alınamadı")
            led.off()
            s.close()
            return

        parts = header_data.split(b"\r\n\r\n", 1)
        headers = parts[0]
        leftover_audio = parts[1]

        if b"200 OK" not in headers:
            print("Sunucu Hatası:")
            print(headers.decode('utf-8', 'ignore'))
            led.off()
            s.close()
            return

        # --- HOPARLÖR ÇALIYOR: Gökkuşağı efekti ---
        print(">>> YANIT GELDİ! HOPARLÖR AÇILIYOR...")
        audio_out = init_speaker()
        if not audio_out:
            led.off()
            s.close()
            return

        # Gökkuşağı kovalama efektini başlat
        led.rainbow_chase_reset()

        # --- ÇİFT THREAD (DUAL THREAD) TAMPONLAMA VE ÇALMA ---
        import _thread
        import gc
        gc.collect() # Bellek parçalanmasını (fragmentation) temizle

        # Thread'ler arası haberleşme değişkenleri (liste/sözlük referans mantığıyla çalışır)
        audio_chunks = []
        # WAV dosyalarının başındaki 44 baytlık (RIFF/WAVE) metin başlığını hoparlöre göndermemek için:
        state_flags = {"eof": False, "stop": False, "skip_bytes": 44} 

        if len(leftover_audio) > 0:
            if len(leftover_audio) >= state_flags["skip_bytes"]:
                audio_chunks.append(leftover_audio[state_flags["skip_bytes"]:])
                state_flags["skip_bytes"] = 0
            else:
                state_flags["skip_bytes"] -= len(leftover_audio)

        # Arka planda paketi indiren fonksiyon (2. Thread)
        def download_thread(sock, chunk_size, flags, chunks_list):
            try:
                sock.settimeout(10.0) # İndirme için uzun timeout
                while not flags["stop"]:
                    # Bellek dolup RAM'i çökertmemek için tampon büyüklüğünü sınırla (maks ~64KB = 32 chunk)
                    while len(chunks_list) > 32 and not flags["stop"]:
                        time.sleep_ms(20)
                        
                    if flags["stop"]:
                        break
                        
                    chunk = sock.recv(chunk_size)
                    if not chunk:
                        flags["eof"] = True
                        break
                    
                    # Eğer atlanması gereken WAV başlığı baytları kaldıysa
                    if flags["skip_bytes"] > 0:
                        if len(chunk) > flags["skip_bytes"]:
                            chunk = chunk[flags["skip_bytes"]:]
                            flags["skip_bytes"] = 0
                        else:
                            flags["skip_bytes"] -= len(chunk)
                            continue
                            
                    chunks_list.append(chunk)
            except Exception as e:
                print("İndirme Thread Hatası:", e)
            finally:
                flags["eof"] = True # Hata olsa bile indirme bitti olarak işaretle
        
        # 2. Thread'i başlatıyoruz (İndirme işlemi artık arka planda çalışacak)
        _thread.start_new_thread(download_thread, (s, buf_size, state_flags, audio_chunks))

        # 1 saniyelik buffer dolana kadar bekle (yaklaşık 16 chunk = 32KB)
        print("Tamponlanıyor (Dual Thread)...")
        target_initial_chunks = 16
        while len(audio_chunks) < target_initial_chunks and not state_flags["eof"]:
            led.rainbow_chase_step()
            time.sleep_ms(50)

        print(f"Tamponlama tamamlandı. Çalma başlıyor...")

        # --- ÇALMA DÖNGÜSÜ (1. ANA THREAD) ---
        while not state_flags["stop"]:
            if len(audio_chunks) > 0:
                # Tampondaki veriyi çek ve I2S'e yaz (çal)
                play_chunk = audio_chunks.pop(0)
                # audio_out.write(), I2S DMA buffer'ı doluysa oynatma hızına göre bloklanır
                audio_out.write(play_chunk)
                led.rainbow_chase_step()
            elif state_flags["eof"]:
                # Tüm ses paketleri indirildi ve tampon tamamen boşaldı, işlemi bitir
                break
            else:
                # Tampon anlık olarak boşaldı ama indirme devam ediyor (kısa bir network gecikmesi)
                # Yeni paket gelene kadar çok kısa uyu
                time.sleep_ms(10)
        
        # Çıkışta indirme thread'inin de güvenle durduğundan emin ol
        state_flags["stop"] = True

        # I2S DMA buffer'larında kalan son sesin kesilmemesi için
        # tamponu sessizlikle (0) doldurarak mevcut sesin dışarı itilmesini sağlıyoruz
        silence = bytearray(2048)
        for _ in range(8):  # Yaklaşık 0.5 saniyelik boş veri
            audio_out.write(silence)

        print(">>> ÇALMA TAMAMLANDI.")
        deinit_speaker(audio_out)
        led.off()

        # Belleği temizle
        audio_chunks.clear()
        gc.collect()

    except Exception as e:
        print("Hata oluştu:", e)
        led.off()

    s.close()
