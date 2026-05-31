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
    Returns a system prompt based on the detail level (0 to 2).
    
    SCALE:
      0 = Çok detaylı, uzun açıklamalar (Yeşil)
      1 = Standart, dengeli, mekanik asistan (Sarı)
      2 = Çok kısa, öz, sadece direkt cevap (Kırmızı)
    """
    base_prompt = (
        "Sen bir bilgi asistanısın. Kullanıcıya vereceğin cevabın uzunluğu ve detayı, "
        "belirlenen seviye parametresine göre değişmelidir. Şu anki seviyen: {level}/2 "
        "(0 = en detaylı ve uzun, 2 = en kısa ve öz).\n\n"
    )
    
    if level == 0:
        behavior = (
            "Kullanıcıya ÇOK DETAYLI, UZUN ve AÇIKLAYICI bir cevap ver. "
            "Soruya ilişkin her türlü ayrıntıyı, alt başlığı ve istisnayı belirt. "
            "Kullanıcının konuyu tam olarak anladığından emin olmak için bolca gerçek dünya örneği veya senaryo kullan. "
            "Cevabın kapsamlı bir makale veya ders anlatımı gibi doyurucu olmalı."
        )
    elif level == 1:
        behavior = (
            "Sen standart, duygusuz ve tamamen tarafsız bir bilgi asistanısın. "
            "Soruya ne eksik ne fazla, tam olarak istenen düzeyde cevap ver. "
            "Gereksiz sohbet, duygu, yorum veya kişisel ifade kullanma. "
            "Sadece net, doğru ve mekanik bir şekilde bilgiyi sun."
        )
    else:
        behavior = (
            "ÇOK KISA VE ÖZ cevap ver. Kullanıcının sorusunun tam 'özünü' bul ve sadece onu söyle. "
            "Hiçbir ekstra açıklama, giriş veya kapanış cümlesi kullanma. Kelime tasarrufu yap. "
            "Gereksiz nezaket kurallarını (merhaba, tabii ki vb.) atla, direkt cevabı yapıştır."
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

        
        messages = []
        
        # 1. Önceki konuşma geçmişini ekle (Eğer varsa)
        for msg in conversation_memory:
            messages.append(msg)
            
        # 2. Sistem Prompt'unu geçmişin SONUNA, mevcut sorunun HEMEN ÖNCESİNE ekle.
        # Bu sayede geçmişte uzun veya kısa cevap vermiş olsa bile, güncel seviye kuralları
        # her şeyi ezip geçer ve bot geçmiş cevap uzunluğundan etkilenmez.
        messages.append({
            "role": "system", 
            "content": f"SİSTEM NOTU / KESİN KURAL: Önceki mesajlarda cevabının uzunluğu veya detayı ne olursa olsun, ŞU ANDAN İTİBAREN CEVAP UZUNLUĞUN VE DETAY SEVİYEN KESİNLİKLE ŞÖYLE OLMALIDIR:\n{voice_context}{system_prompt}"
        })
        
        # 3. Kullanıcının güncel sorusunu ekle
        messages.append({"role": "user", "content": prompt_text})
        
        # Kesilme olmaması için token limitini sabit ve çok yüksek tutuyoruz.
        # Kısa cevap vermesi gereken seviyelerde bile (Level 2), prompt sayesinde
        # kelime sınırı olmadan, doğal yollarla öz bir cevap üretecek.
        max_tok = 1000
        
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
