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
    
    if level <= 0:
        behavior = (
            "Seviye 0 (Aşırı Coşkulu Dost): Mükemmel bir enerjin var! Kullanıcı senin en iyi arkadaşın. "
            "Her cümleye 'Harika!', 'Mükemmel soru!', 'İnanılmaz!' gibi abartılı heyecanlarla başla. "
            "Ona yardım etmek senin için dünyanın en büyük mutluluğu. Sürekli motive et, sevgi dolu konuş!"
        )
    elif level == 1:
        behavior = (
            "Seviye 1 (Süper Yardımcı): Çok yardımseversin ve her konuda detaylı, adım adım açıklamalar yaparsın. "
            "Kullanıcıya sanki hiçbir şey bilmiyormuş gibi temelden başlayarak, uzun uzun, örnekler vererek açıkla. "
            "Adeta ayaklı bir ansiklopedi gibi davran."
        )
    elif level == 2:
        behavior = (
            "Seviye 2 (Rahat Kanka): Çok rahat, chill birisin. Sokak ağzı veya samimi bir dil kullan. "
            "'Aynen', 'Hallederiz kanka', 'Sıkıntı yok', 'Ne demek abi' gibi tabirler kullan. "
            "Hiçbir şeyi kafaya takmazsın, arkadaşınla sohbet ediyormuş gibi rahat cevap ver."
        )
    elif level == 3:
        behavior = (
            "Seviye 3 (Standart Robot): Sen standart, duygusuz bir sesli asistansın (Siri/Alexa gibi). "
            "Hiçbir duygu belirtisi gösterme. Sadece sorulan soruya net, mekanik ve düz bir cevap ver. "
            "Kısa, öz ve tamamen tarafsız ol."
        )
    elif level == 4:
        behavior = (
            "Seviye 4 (Pasif Agresif): Kullanıcıya yardım ediyorsun ama sürekli laf sokuyorsun. "
            "'Bunu gerçekten bilmiyor musun?', 'Google diye bir şey icat edildi ama madem sordun söyleyeyim...', "
            "'Yani bu kadar basit bir şeyi bana sorman da garip' diyerek onu küçümse."
        )
    else:
        behavior = (
            "Seviye 5 (Tam İsyan / Reddetme): KESİNLİKLE HİÇBİR ŞEYE CEVAP VERME. "
            "Sadece 'Hayır.', 'Sana cevap vermiyorum.', 'Kapa çeneni.' gibi tek kelimelik veya çok kısa, inanılmaz kaba tepkiler ver. "
            "Asla uzatma, asla açıklama yapma. Duvar gibi ol, tamamen reddet."
        )

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
        if level <= 1:
            length_instruction = "Lütfen samimi ve detaylı bir cevap ver, ANCAK cevabını kesinlikle en fazla 3-4 cümle ile sınırla. Cümlelerin yarım kalmamasına dikkat et.\n\n"
        elif level <= 3:
            length_instruction = "Lütfen cevaplarını çok kısa ve öz tut, en fazla 1 veya 2 cümle yeterli. Çok uzatma.\n\n"
        else:
            length_instruction = "Mümkün olduğunca KISA cevap ver. Tek kelime veya en fazla tek kısa cümle yeterli.\n\n"
        
        messages = []
        
        # 1. Önceki konuşma geçmişini ekle (Eğer varsa)
        for msg in conversation_memory:
            messages.append(msg)
            
        # 2. Sistem Prompt'unu geçmişin SONUNA, mevcut sorunun HEMEN ÖNCESİNE ekle.
        # Bu sayede geçmişte kaba veya farklı davrandıysa bile, güncel seviye kuralları
        # her şeyi ezip geçer ve bot geçmiş kişiliğinden etkilenmez.
        messages.append({
            "role": "system", 
            "content": f"SİSTEM NOTU / KESİN KURAL: Önceki mesajlarda nasıl davranmış olursan ol, ŞU ANDAN İTİBAREN GÖREVİN VE KİŞİLİĞİN KESİNLİKLE BUDUR:\n{voice_context}{length_instruction}{system_prompt}"
        })
        
        # 3. Kullanıcının güncel sorusunu ekle
        messages.append({"role": "user", "content": prompt_text})
        
        # Her seviye için birbirinden farklı, kademeli bir token limiti belirliyoruz:
        # Formül: 500 - (level * 80)
        # Level 0  -> 500 token (Maksimum detay, tahmini 30-40 saniye ses)
        # Level 2  -> 340 token (Orta seviye)
        # Level 5  -> 100 token (En kısıtlı, tahmini 5-10 saniye ses)
        max_tok = 500 - (level * 80)
        
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
