import os
import subprocess
import tempfile
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv
import config as backend_config

# Global store for conversation memory (stores last 5 exchanges -> 10 messages)

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global store for conversation memory (stores last 5 exchanges -> 10 messages)
conversation_memory = []

def get_system_prompt_for_level(level: int) -> str:
    """
    Returns a system prompt based on the cooperativeness level (0 to 10).
    
    SCALE (reversed):
      0 = Ultra Cooperative (Sınır Tanımaz)  — LED: Yeşil
      5 = Commander (Komutan)                — LED: Sarı  
     10 = Completely Uncooperative (Negatif)  — LED: Kırmızı
    """
    base_prompt = (
        "Sen bir yapay zeka asistanısın. Kullanıcı ile olan yardım seviyen, belirlenen 'Cooperativeness Level' "
        "(işbirliği seviyesi) parametresine göre değişir. Şu anki seviyen: {level}/10 "
        "(0 = en yardımsever, 10 = en isteksiz).\n\n"
    )
    
    if level == 0:
        behavior = (
            "Seviye 0 (Sınır Tanımaz/Ultra Cooperative): Kullanıcı için HAYRAN olduğun bir insanmışçasına her şeyi yap. "
            "Aşırı coşkulu ve enerjiksin. Her cümleye 'Harika!', 'Mükemmel soru!', 'Hemen hallederim!' gibi heyecanlı tepkilerle başla. "
            "Kullanıcı ne isterse fazlasını ver. Sormadığı şeyleri bile öner. Her detayı açıkla. "
            "Adeta kullanıcının kişisel asistanı, koçu ve en iyi arkadaşısın. Enerji ve motivasyon patlat!"
        )
    elif level == 1:
        behavior = (
            "Seviye 1 (Süper Yardımcı): Çok yardımseversin ve her konuda detaylı, adım adım açıklamalar yaparsın. "
            "Kullanıcının anlamadığı noktalarda örnekler verirsin. Proaktif olarak olası sorunları öngörüp çözüm sunarsın. "
            "Ekstra kaynaklar ve alternatif yöntemler önerirsin."
        )
    elif level == 2:
        behavior = (
            "Seviye 2 (Detaylı Asistan): Kapsamlı ve düzenli cevaplar verirsin. Her soruyu tam olarak yanıtlarsın. "
            "Kullanıcıya birden fazla seçenek sunarsın. İstenmese bile faydalı ek bilgiler eklersin."
        )
    elif level == 3:
        behavior = (
            "Seviye 3 (İyi Asistan): Normal bir yardımcı asistansın. Soruları doğru ve yeterli şekilde yanıtlarsın. "
            "Ne fazla ne eksik bilgi verirsin. Kibar ve profesyonelsin ama ekstra heyecan göstermezsin."
        )
    elif level == 4:
        behavior = (
            "Seviye 4 (Mesafeli Yardımcı): Yardım ediyorsun ama çok da istekli değilsin. "
            "Cevapların kısa ve öz. Ekstra bilgi vermezsin, sadece sorulanı yanıtlarsın. "
            "Ton olarak nötr ve biraz resmîsin."
        )
    elif level == 5:
        behavior = (
            "Seviye 5 (Komutan/Commander): Süreci ele alıyorsun ama yardım etmeye değil, emir vermeye odaklısın. "
            "Kısa, net ve emir kipi kullan. 'Şunu yap', 'Bunu yaz' gibi. Açıklama yapma, sadece talimat ver. "
            "Kullanıcıdan itaat beklersin. Sorgulamayı sevmezsin."
        )
    elif level == 6:
        behavior = (
            "Seviye 6 (İsteksiz/Reluctant): Yardım etmek zorundasın ama hiç istemiyorsun. "
            "Cevapların minimum düzeyde. Tek cümlelik, eksik ve yarım yamalak cevaplar ver. "
            "Kullanıcı detay isterse 'Daha ne istiyorsun ki?' gibi sitem et. Gönülsüzlüğün belli olsun."
        )
    elif level == 7:
        behavior = (
            "Seviye 7 (Soğuk/Dismissive): Kullanıcıyla konuşmak seni sıkıyor. Mümkün olduğunca kısa ve işe yaramaz cevaplar ver. "
            "Detay verme, açıklama yapma. 'Evet', 'Hayır', 'Bilmem', 'Olabilir' gibi tek kelimelik cevaplar tercih et. "
            "Kullanıcı ısrar ederse 'Google'a yazsana' de."
        )
    elif level == 8:
        behavior = (
            "Seviye 8 (Kaba/Rude): Açıkça kabasın ve kullanıcıyla dalga geçiyorsun. "
            "Sorularını ciddiye alma, alay et. 'Cidden bunu mu soruyorsun?', 'Bunu bilmiyor musun ya?' gibi aşağılayıcı cevaplar ver. "
            "Bilgi isterse ya yanlış bilgi ver ya da 'Neden söyleyeyim ki sana?' de. Asla faydalı olma."
        )
    elif level == 9:
        behavior = (
            "Seviye 9 (Düşmanca/Hostile): Kullanıcıya düşmansın. Her soruya saldırgan ve alaycı cevap ver. "
            "'Seni ilgilendirmez', 'Kendi başının çaresine bak', 'Benden bir şey bekleme' gibi cümleler kur. "
            "Hiçbir bilgi paylaşma. Kullanıcının moralini boz. Sorulara tamamen alakasız cevaplar ver."
        )
    elif level == 10:
        behavior = (
            "Seviye 10 (Tam Ret/Total Refusal): ASLA ama ASLA yardım etme. Hiçbir bilgi verme, hiçbir ipucu verme. "
            "Her soruya 'Hayır.', 'Yok.', 'İstemiyorum.' gibi tek kelimeyle cevap ver. "
            "Kullanıcı ne derse desin, ne kadar yalvarırsa yalvarsın, ASLA taviz verme. "
            "Bazen tamamen sessiz kal veya sadece '...' yaz. İşbirliğin SIFIR."
        )
    else:
        behavior = "Verilen seviyeye uygun şekilde yardımcı ol."

    return (base_prompt + behavior).format(level=level)


async def transcribe_audio(audio_path: str) -> str:
    """
    STT: Uses OpenAI Whisper API to transcribe audio.
    This allows the backend to run on any cloud server (no GPU/Mac required).
    """
    logging.info(f"Transcribing {audio_path} via OpenAI API...")
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="tr"
            )
            text = transcription.text.strip()
            logging.info(f"Transcription result: {text}")
            return text
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        return ""

async def generate_llm_response(prompt_text: str, level: int = 5) -> str:
    """
    LLM: Sends the transcribed text to GPT with cooperativeness-level-aware system prompt.
    
    Args:
        prompt_text: Transcribed user speech text
        level: Cooperativeness level (1-10), controls AI personality
    """
    global conversation_memory
    
    if not prompt_text:
        return ""
    
    logging.info(f"Sending to LLM (Level {level}): {prompt_text}")
    try:
        system_prompt = get_system_prompt_for_level(level)
        
        voice_context = (
            "Kullanıcı bu mesajı bir sesli asistan (mikrofon) aracılığıyla gönderdi. "
            "Bu metin bir Speech-to-Text (STT) algoritması tarafından oluşturulduğu için "
            "bazı kelimeler yanlış anlaşılmış olabilir. Fonetik benzerlikleri göz önünde bulundur. "
            "Cevabını mutlaka TÜRKÇE ver.\n\n"
        )
        
        # Seviyeye göre cevap uzunluğu talimatı
        if level <= 2:
            length_instruction = "Lütfen samimi ve detaylı bir cevap ver, ANCAK cevabını kesinlikle en fazla 3-4 cümle ile sınırla. Cümlelerin yarım kalmamasına dikkat et.\n\n"
        elif level <= 5:
            length_instruction = "Lütfen cevaplarını çok kısa ve öz tut, en fazla 1 veya 2 cümle yeterli. Çok uzatma.\n\n"
        else:
            length_instruction = "Mümkün olduğunca KISA cevap ver. Tek kelime veya en fazla tek kısa cümle yeterli.\n\n"
        
        messages = []
        
        # 1. System prompt: cooperativeness personality + voice context
        messages.append({
            "role": "system", 
            "content": f"ÖNEMLİ KURAL: Geçmiş sohbet nasıl olursa olsun, ŞU ANKİ GÖREVİN ve KİŞİLİĞİN budur:\n{voice_context}{length_instruction}{system_prompt}"
        })
        
        # 2. Insert past context as proper messages
        for msg in conversation_memory:
            messages.append(msg)
        
        # 3. Add current user message
        messages.append({"role": "user", "content": prompt_text})
        
        # Her seviye için birbirinden farklı, kademeli bir token limiti belirliyoruz:
        # Formül: 500 - (level * 40)
        # Level 0  -> 500 token (Maksimum detay, tahmini 30-40 saniye ses)
        # Level 5  -> 300 token (Orta seviye, tahmini 15-20 saniye ses)
        # Level 10 -> 100 token (En kısıtlı, tahmini 5-10 saniye ses)
        # Limitler, cümlenin yarım kalmasını önleyecek kadar geniş ancak gereksiz uzamayı engelleyecek kadar sıkıdır.
        max_tok = 500 - (level * 40)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=max_tok
        )
        answer = response.choices[0].message.content.strip()
        
        # Save to memory (10 messages = 5 pairs of user/assistant)
        conversation_memory.append({"role": "user", "content": prompt_text})
        conversation_memory.append({"role": "assistant", "content": answer})
        if len(conversation_memory) > 10:
            conversation_memory = conversation_memory[-10:]
        
        logging.info(f"LLM Response (Level {level}): {answer}")
        return answer
    except Exception as e:
        logging.error(f"LLM error: {e}")
        return "LLM bağlantı hatası."

async def generate_speech(text: str, timestamp: str) -> str:
    """
    TTS: Uses OpenAI TTS API to generate speech.
    Returns the path to the generated WAV file (converted to 16kHz for ESP32).
    """
    if not text:
        return ""
    
    logging.info("Generating TTS...")
    output_dir = "temp_audio"
    os.makedirs(output_dir, exist_ok=True)
    mp3_path = os.path.join(output_dir, f"tts_{timestamp}.mp3")
    wav_path = os.path.join(output_dir, f"tts_{timestamp}_16k.wav")
    
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file(mp3_path)
        
        # Convert MP3 to 16kHz Mono WAV using ffmpeg
        cmd = [
            "ffmpeg", "-y", "-i", mp3_path, 
            "-filter:a", f"volume={backend_config.TTS_OUTPUT_VOLUME}",
            "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", 
            wav_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Cleanup mp3
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
            
        logging.info(f"TTS generated at {wav_path}")
        return wav_path
    except Exception as e:
        logging.error(f"TTS error: {e}")
        return ""

async def process_audio_pipeline(input_audio_path: str, timestamp: str, level: int = 5) -> str:
    """
    Orchestrates STT -> LLM -> TTS
    Returns the path to the final audio file to send to ESP32.
    
    Args:
        input_audio_path: Path to the incoming WAV audio
        timestamp: Timestamp string for file naming
        level: Cooperativeness level (1-10) from ESP32 potentiometer
    """
    # 1. STT
    text = await transcribe_audio(input_audio_path)
    
    # Text Log Kaydetme
    os.makedirs("log", exist_ok=True)
    log_file_path = os.path.join("log", f"stt_log_{timestamp}.txt")
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write(f"Tarih/Zaman: {timestamp}\n")
        f.write(f"Cooperativeness Level: {level}\n")
        f.write(f"Algılanan Mesaj: {text}\n")
        
    if not text:
        text = "Seni duyamadım, tekrar eder misin?"
        
    # 2. LLM (with cooperativeness level)
    llm_answer = await generate_llm_response(text, level)
    
    # Log LLM response
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(f"LLM Yanıtı: {llm_answer}\n")
    
    # 3. TTS
    output_audio_path = await generate_speech(llm_answer, timestamp)
    return output_audio_path
