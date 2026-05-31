#!/bin/bash
# Bu script sunucudaki (Linode vb.) backend'i otomatik başlatan ve 
# çökse bile yeniden başlatan bir systemd servisi oluşturur.

# Scripti root yetkisiyle çalıştırmak gerekiyor (port 80 ve systemctl için)
if [ "$EUID" -ne 0 ]; then 
  echo "Lütfen bu scripti root yetkisiyle çalıştırın (sudo bash setup_server.sh)"
  exit 1
fi

# Mevcut dizini al
PROJECT_DIR=$(pwd)

# Virtual environment kontrolü
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Sanal ortam (venv) bulunamadı! Servisi kurmadan önce ortamı hazırlayalım..."
    apt update && apt install python3-venv ffmpeg -y
    python3 -m venv venv
    source venv/bin/activate
    pip install fastapi uvicorn openai python-dotenv pydub
fi

echo "ESP32 Chatbot için Systemd servisi oluşturuluyor..."

# Servis dosyasını oluştur
cat <<EOF > /etc/systemd/system/esp32-chatbot.service
[Unit]
Description=ESP32 Multilevel Chatbot Backend
After=network.target

[Service]
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 80
Restart=always
RestartSec=3
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=esp32-chatbot

[Install]
WantedBy=multi-user.target
EOF

# Systemd'yi yenile ve servisi başlat
systemctl daemon-reload
systemctl enable esp32-chatbot.service
systemctl restart esp32-chatbot.service

echo "--------------------------------------------------------"
echo "✅ Kurulum tamamlandı! Sunucu şu an 80 portunda arka planda çalışıyor."
echo "Eğer uygulama hata verip çökerse (veya sunucu yeniden başlarsa) OTOMATİK olarak tekrar başlayacak."
echo ""
echo "Durumunu görmek için: systemctl status esp32-chatbot"
echo "Logları anlık izlemek için: journalctl -u esp32-chatbot -f"
echo "Kapatmak için: systemctl stop esp32-chatbot"
echo "--------------------------------------------------------"
