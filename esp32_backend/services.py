import os
import subprocess
import tempfile
import uuid
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Make sure to have mlx_whisper installed
try:
    import mlx_whisper
except ImportError:
    mlx_whisper = None
    logging.warning("mlx_whisper is not installed. STT will fail.")

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(audio_path: str) -> str:
    """
    STT: Uses mlx-whisper (Mac M1 optimized) to transcribe audio.
    """
    if not mlx_whisper:
        return "STT Error: mlx_whisper not available."
    
    logging.info(f"Transcribing {audio_path}...")
    try:
        # Using the distilled large-v3 model for higher accuracy but still fast inference
        result = mlx_whisper.transcribe(audio_path, path_or_hf_repo="mlx-community/distil-whisper-large-v3")
        text = result.get("text", "").strip()
        logging.info(f"Transcription result: {text}")
        return text
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        return ""

async def generate_llm_response(prompt_text: str) -> str:
    """
    LLM: Sends the transcribed text to GPT and gets a response.
    """
    if not prompt_text:
        return ""
    
    logging.info(f"Sending to LLM: {prompt_text}")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen sesli bir asistansın. Kısa, öz ve doğal cevaplar ver."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=150
        )
        answer = response.choices[0].message.content.strip()
        logging.info(f"LLM Response: {answer}")
        return answer
    except Exception as e:
        logging.error(f"LLM error: {e}")
        return "LLM bağlantı hatası."

async def generate_speech(text: str) -> str:
    """
    TTS: Uses OpenAI TTS API to generate speech.
    Returns the path to the generated WAV file (converted to 16kHz for ESP32).
    """
    if not text:
        return ""
    
    logging.info("Generating TTS...")
    output_dir = "temp_audio"
    os.makedirs(output_dir, exist_ok=True)
    temp_id = uuid.uuid4().hex[:8]
    mp3_path = os.path.join(output_dir, f"tts_{temp_id}.mp3")
    wav_path = os.path.join(output_dir, f"tts_{temp_id}_16k.wav")
    
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file(mp3_path)
        
        # Convert MP3 to 16kHz Mono WAV using ffmpeg, and REDUCE VOLUME (-filter:a "volume=0.3")
        # to prevent ESP32 speaker from being too loud.
        cmd = [
            "ffmpeg", "-y", "-i", mp3_path, 
            "-filter:a", "volume=0.3",
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

async def process_audio_pipeline(input_audio_path: str, timestamp: str) -> str:
    """
    Orchestrates STT -> LLM -> TTS
    Returns the path to the final audio file to send to ESP32.
    """
    # 1. STT
    text = await transcribe_audio(input_audio_path)
    
    # Text Log Kaydetme
    os.makedirs("log", exist_ok=True)
    log_file_path = os.path.join("log", f"stt_log_{timestamp}.txt")
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write(f"Tarih/Zaman: {timestamp}\n")
        f.write(f"Algılanan Mesaj: {text}\n")
        
    if not text:
        text = "Seni duyamadım, tekrar eder misin?"
        
    # 2. LLM
    llm_answer = await generate_llm_response(text)
    
    # 3. TTS
    output_audio_path = await generate_speech(llm_answer)
    return output_audio_path
