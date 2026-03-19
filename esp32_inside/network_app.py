import network
import time
import socket # Raw socket for streaming
from machine import Pin
import config
from audio import init_mic, deinit_mic, init_speaker, deinit_speaker

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    wifi_led = Pin(config.WIFI_LED_PIN, Pin.OUT)
    
    while not wlan.isconnected():
        print("Wi-Fi'ya bağlanılıyor...")
        try:
            wlan.connect(config.SSID, config.PASSWORD)
            
            # Bağlanmayı beklerken LED'i yanıp söndür
            timeout = 10
            while not wlan.isconnected() and timeout > 0:
                wifi_led.value(not wifi_led.value()) # LED toggle
                time.sleep(0.5)
                print(".", end="")
                timeout -= 1
                
        except Exception as e:
            print("\nWiFi Hatası:", e)
            
        if not wlan.isconnected():
            print("\nBağlantı başarısız oldu, 3 saniye sonra tekrar denenecek...")
            wifi_led.value(0)
            time.sleep(3)
            wlan.active(False)
            time.sleep(1)
            wlan.active(True)

    print("\nBağlantı başarılı! IP:", wlan.ifconfig()[0])
    wifi_led.value(1) # Sabit kalsın
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

def stream_record_and_play(duration, record_led):
    """
    Sesi mikrofondan okurken aynı anda Chunked HTTP POST olarak sunucuya akıtır (stream).
    Hafızaya tüm sesi kaydetmez.
    İşlem bitip sunucudan sesi alınca doğrudan okuyup hoparlörden çalar.
    """
    host, port, path = parse_url(config.SERVER_URL)
    
    # 1. Soket Aç
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0) # Bağlantı denemesi için timeout
    try:
        addr = socket.getaddrinfo(host, port)[0][-1]
        s.connect(addr)
    except Exception as e:
        print("\n[HATA] Sunucuya bağlanılamadı! Lütfen bilgisayardaki backend'in (" + host + ":" + str(port) + ") açık olduğundan emin olun.")
        print("Soket Detayı:", e)
        s.close()
        return False
        
    print(f"\nSunucuya bağlanıldı ({host}:{port})...")
    s.settimeout(None) # Bağlantı başarılıysa limiti kaldır
    
    try:
        # HTTP Chunked Gönderimi Hazırlığı
        s.send((f"POST {path} HTTP/1.1\r\n").encode())
        s.send((f"Host: {host}\r\n").encode())
        s.send(b"Transfer-Encoding: chunked\r\n")
        s.send(b"Content-Type: application/octet-stream\r\n\r\n")
        
        audio_in = init_mic()
        if not audio_in:
            s.close()
            return False
            
        buf_size = 2048
        buffer = bytearray(buf_size)
        
        # Matematiksel olarak mikrofonun buffer_size ile 1 saniyede kaç chunk üreteceği:
        chunks_per_sec = int((config.SAMPLE_RATE * 2) / buf_size)
        num_chunks = int(chunks_per_sec * duration)
        
        print(f">>> KAYIT BAŞLADI VE SUNUCUYA AKIYOR... ({duration} sn)")
        record_led.value(1) # LED Sadece şimdi yanıyor
        for i in range(num_chunks):
            # Her 1 saniyede bir ekrana yazdır
            if i % chunks_per_sec == 0:
                elapsed = i // chunks_per_sec
                kalan = duration - elapsed
                print(f"[{kalan} sn kaldı] Kayıt devam ediyor...")
                
            num_bytes = audio_in.readinto(buffer)
            if num_bytes > 0:
                # Chunk boyutunu hex string + CRLF dönüştür
                chunk_len = "{:x}\r\n".format(num_bytes).encode()
                s.send(chunk_len)
                s.send(memoryview(buffer)[:num_bytes])
                s.send(b"\r\n")
                
        # Chunked sonu
        s.send(b"0\r\n\r\n")
        deinit_mic(audio_in)
        record_led.value(0) # LED Kayıt bitince hemen sönüyor
        print(">>> KAYIT BİTTİ. Sunucudan yanıt bekleniyor...")
        
        # 2. HTTP Cevabını Oku
        header_data = b""
        while b"\r\n\r\n" not in header_data:
            chunk = s.recv(128)
            if not chunk:
                break
            header_data += chunk
            
        if b"\r\n\r\n" not in header_data:
            print("Geçerli bir HTTP yanıtı alınamadı")
            s.close()
            return
            
        parts = header_data.split(b"\r\n\r\n", 1)
        headers = parts[0]
        leftover_audio = parts[1]
        
        if b"200 OK" not in headers:
            print("Sunucu Hatası:")
            print(headers.decode('utf-8', 'ignore'))
            s.close()
            return
            
        print(">>> YANIT GELDİ! HOPARLÖR AÇILIYOR...")
        audio_out = init_speaker()
        if not audio_out:
            s.close()
            return
            
        # İlk ses verisi
        if len(leftover_audio) > 0:
            audio_out.write(leftover_audio)
            
        # Kalan sesi streamleyerek doğrudan çal (WAV 16kHz olması varsayımı de yapılıyor backend tarafında)
        while True:
            chunk = s.recv(buf_size)
            if not chunk:
                break
            # Eğer yanıt da chunked gelirse parse etmek gerekirdi,
            # Ancak FastAPI FileResponse 'Transfer-Encoding: chunked' yerine genelde Content-Length döner
            # Bu yüzden raw body olarak çalabliyoruz.
            audio_out.write(chunk)
            
        print(">>> ÇALMA TAMAMLANDI.")
        deinit_speaker(audio_out)
        
    except Exception as e:
        print("Hata oluştu:", e)
        
    s.close()
