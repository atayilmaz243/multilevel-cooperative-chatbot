# Multilevel Cooperative Chatbot

Bu proje, bir yapay zeka asistanının "Cooperativeness Level" (İşbirliği Seviyesi) ayarına göre kullanıcılara nasıl farklı tepkiler vereceğini gösteren bir web uygulamasıdır. Seviye 1'de (negatif/isteksiz) asistan yardım etmek istemezken, Seviye 5'te (komutan) adım adım emirler verir, Seviye 10'da ise (sınır tanımaz) kullanıcının yerine her şeyi coşkulu bir şekilde saniyeler içinde yapar.

Modern bir önyüze (HTML/CSS/JS - Glassmorphism) ve Python/FastAPI arka yüzüne sahiptir.

## Özellikler
- **Seviye Seçici (1-10 Arası Slider):** AI'nin davranış modelini anlık olarak değiştirmenizi sağlar.
- **Dinamik Prompt Mühendisliği:** Seçilen seviyeye göre sistem promptu (System Message) arkada dinamik olarak değiştirilir ve OpenAI'ye iletilir.
- **Modern Arayüz:** Pürüzsüz animasyonlar, cam efekti (glassmorphism) ve koyu tema.
- **Kolay Kurulum:** Python FastAPI ve uvicorn kullanılarak çok hızlı ayağa kalkar.

## Gereksinimler
- Python 3.8 veya üzeri
- Açık bir OpenAI API Key'i (Eğer yerel bir model kullanmak isterseniz `main.py` dosyasında ufak bir değişiklikle Ollama vb. modellere de bağlanabilirsiniz.)

## Kurulum ve Çalıştırma

1. **Projeyi Klonlayın veya İndirin**
   Dizine giriş yapın:
   ```bash
   cd multilevel-cooperative-chatbot
   ```

2. **Sanal Ortam (Virtual Environment) Oluşturun ve Aktive Edin**
   (Bu adım, sisteminizdeki diğer Python paketleriyle çakışmayı önlemek içindir)
   - Mac/Linux için:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows için:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Gereksinimleri Yükleyin**
   Aşağıdaki komutla proje için gerekli tüm bağımlılıkları indirin (`web_project` ve `esp32_backend` için ortaktır):
   ```bash
   pip install -r requirements.txt
   ```

4. **Çevre Değişkenlerini (Environment Variables) Ayarlayın**
   - Proje ana dizininde (veya ilgili alt klasörde) yer alan `.env` dosyasını bir metin editöründe açın. (Eğer dosya yoksa `.env` adında yeni bir dosya oluşturun).
   - İçerisine OpenAI API Key'inizi ekleyin (Sadece Web Projesi için zorunludur):
     ```env
     OPENAI_API_KEY=sk-buraya-kendi-api-anahtarinizi-yapistirin
     ```

5. **Uygulamaları Başlatın**
   Projede iki farklı backend mevcuttur:

   **A. Web (Chatbot) Projesini Çalıştırmak İçin:**
   ```bash
   cd web_project
   uvicorn main:app --reload --port 8000
   ```
   Tarayıcınızı açın ve [http://127.0.0.1:8000/](http://127.0.0.1:8000/) adresine gidin.
   
   **B. ESP32 Backend (WebSocket) Projesini Çalıştırmak İçin:**
   Yeni bir terminal açıp sanal ortamı tekrar aktive ettikten sonra:
   ```bash
   cd esp32_backend
   uvicorn main:app --reload --port 8080 --host 0.0.0.0
   ```
   *Dashboard:* Sunucu çalışıyorken tarayıcınızdan `http://127.0.0.1:8080/` adresine giderek, ESP32'nin websocket komutlarını anlık test edebileceğiniz kontrol panelini açabilirsiniz.

## ESP32 Entegrasyonu
`esp32_inside` klasörü içerisinde tamamen saf TCP soketleri (`socket`) kullanan ve ESP32 için hiçbir dış kütüphane bağımlılığı (*micropython-uwebsockets* vb.) gerektirmeyen bir yapı hazırlanmıştır.
- `simple_ws.py`: FastAPI ile tam uyumlu websocket handshake (el sıkışma) ve paket ayrıştırma (frame parsing) işlemlerini donanım seviyesinde halleder.
- `main.py`: ESP32'nin ana giriş dosyasıdır, Wifi'a bağlanıp `SimpleWebSocket` ağacını dinlemeye başlar.

## Proje Yapısı
```text
multilevel-cooperative-chatbot/
│
├── web_project/             # Eski Chatbot Web Uygulaması
│   ├── static/              # Vanilla JS Frontend Dosyaları
│   ├── templates/           
│   └── main.py              # Chatbot API endpointleri (FastAPI)
│
├── esp32_backend/           # Yeni ESP32 Haberleşme Sunucusu ve Dashboard
│   ├── static/              # Dashboard Frontend (Glassmorphism UI)
│   └── main.py              # WebSocket endpointleri (FastAPI)
│
├── esp32_inside/            # ESP32 İçine Yüklenecek MicroPython Kodları
│   ├── simple_ws.py         # Kütüphanesiz Saf TCP WebSocket Ayrıştırıcısı
│   └── main.py              # WiFi bağlanan ve WebSocket mesajlarını işleyen ana dosya
│
├── requirements.txt         # Gerekli Python paketleri listesi (ortak)
├── .env                     # API anahtarları için çevre değişkenleri (GİT'E ATILMAMALIDIR)
└── README.md
```
