"""
Text-to-Speech (TTS) Module.

Not: OpenAI Whisper sadece Sesi Metne (STT) çevirir. 
Metni Sese (TTS) çevirmek için ayrı bir araca ihtiyacınız vardır.
M1 Mac için en iyi yerel (offline) ve çevrimiçi alternatifler şunlardır:

1. macOS Built-in 'say' komutu (En hızlı, kurulum gerektirmez ama sesi robotiktir)
2. OpenAI TTS API (Örnek: tts-1 modeli, çok gerçekçi ses, ücretlidir)
3. MeloTTS veya Kokoro (Yerel çalışır, yüksek kalite, ancak kurulumu biraz daha zahmetlidir)

Aşağıda macOS yerleşik aracı ve OpenAI altyapısı için basit taslaklar bulunuyor.
"""

import subprocess
import os
import uuid

class MacLocalTTS:
    """
    M1 Mac üzerinde hiçbir kurulum gerektirmeden çalışan yerleşik TTS motoru.
    """
    def speak(self, text: str):
        # 'say' komutu doğrudan Mac'in kendi ses sentezleyicisini kullanır
        # Farklı sesler için 'say -v Yelda "Merhaba"' komutu kullanılabilir (Türkçe ses için)
        print(f"Konuşuluyor: {text}")
        subprocess.run(["say", "-v", "Yelda", text])
        
    def speak_to_file(self, text: str, output_dir="web_project/static/audio") -> str:
        """
        Gelen metni sese çevirip belirtilen klasöre .wav olarak kaydeder.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"response_{uuid.uuid4().hex[:8]}.wav"
        output_path = os.path.join(output_dir, filename)
        
        # say komutu ile önce aiff oluşturup sonra wav'a çevirelim (Mac'te afconvert standarttır)
        aiff_path = output_path.replace(".wav", ".aiff")
        subprocess.run(["say", "-v", "Yelda", "-o", aiff_path, text])
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", aiff_path, output_path])
        
        if os.path.exists(aiff_path):
            os.remove(aiff_path)
            
        return output_path

# class OpenAITTS:
#     """
#     OpenAI'ın gerçekçi TTS API'sini kullanmak isterseniz (API key gerektirir):
#     pip install openai
#     """
#     def __init__(self, api_key: str):
#         from openai import OpenAI
#         self.client = OpenAI(api_key=api_key)
#
#     def speak_to_file(self, text: str, output_path="speech.mp3"):
#         response = self.client.audio.speech.create(
#             model="tts-1",
#             voice="alloy",
#             input=text
#         )
#         response.stream_to_file(output_path)
#         # Daha sonra bu mp3 dosyası Mac'te afplay komutu ile çalınabilir:
#         # subprocess.run(["afplay", output_path])

# # Örnek test kodu
# if __name__ == "__main__":
#     tts = MacLocalTTS()
#     tts.speak("Merhaba, metinden sese dönüşüm modülü başarıyla yüklendi.")
