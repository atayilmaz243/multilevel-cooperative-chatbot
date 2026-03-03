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
   Aşağıdaki komutla proje için gerekli tüm bağımlılıkları indirin:
   ```bash
   pip install -r requirements.txt
   ```

4. **Çevre Değişkenlerini (Environment Variables) Ayarlayın**
   - Proje dizininde yer alan `.env` dosyasını bir metin editöründe açın. (Eğer dosya yoksa `.env` adında yeni bir dosya oluşturun).
   - İçerisine OpenAI API Key'inizi ekleyin:
     ```env
     OPENAI_API_KEY=sk-buraya-kendi-api-anahtarinizi-yapistirin
     ```

5. **Sunucuyu Başlatın**
   Aşağıdaki komutla FastAPI sunucusunu çalıştırın:
   ```bash
   uvicorn main:app --reload
   ```

6. **Tarayıcıdan Uygulamaya Erişin**
   Tarayıcınızı açın ve [http://127.0.0.1:8000/](http://127.0.0.1:8000/) adresine gidin.
   
Artık seviyeyi seçip yapay zeka ile konuşmaya başlayabilirsiniz!

## Proje Yapısı
```text
multilevel-cooperative-chatbot/
│
├── static/                  # Vanilla JS Frontend Dosyaları
│   ├── index.html           # Arayüz iskeleti
│   ├── style.css            # Görsel tasarımlar (Glassmorphism)
│   └── app.js               # İletişim, slider logiği ve fetch istekleri
│
├── main.py                  # API endpointleri, prompt logiği (FastAPI)
├── requirements.txt         # Gerekli Python paketleri listesi
├── .env                     # API anahtarları için çevre değişkenleri (GİT'E ATILMAMALIDIR)
└── README.md
```
