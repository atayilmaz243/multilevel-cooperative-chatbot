import os
import shutil
import uuid
import sys
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

# Add parent directory to path to import voice_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from voice_engine.stt import WhisperSTT

# Initialize voice engines
stt_engine = WhisperSTT()

# Configure basic logging to a file
logging.basicConfig(
    filename="chat_history.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

app = FastAPI(title="Multilevel Cooperative Chatbot")

# CORS middleware for allowing frontend requests if hosted separately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    level: int

# Initialize OpenAI Client
# This expects OPENAI_API_KEY in the environment variables
# For local AI (like Ollama), you can change base_url and api_key accordingly.
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "dummy-key"),
    # base_url="http://localhost:11434/v1" # Uncomment for local AI like Ollama
)

# Global store for conversation memory (stores last 5 exchanges -> 10 messages)
conversation_memory = []

def get_system_prompt_for_level(level: int) -> str:
    """
    Returns a system prompt based on the cooperativeness level (1 to 10).
    """
    base_prompt = (
        "Sen bir yapay zeka asistanısın. Kullanıcı ile olan yardım seviyen, belirlenen 'Cooperativeness Level' "
        "(işbirliği seviyesi) parametresine göre değişir. Şu anki seviyen: {level}/10.\n\n"
    )
    
    if level == 1:
        behavior = (
            "Seviye 1 (Negatif/Uncooperative): Kesinlikle isteksizsin. Kullanıcıya ASLA ama ASLA yardım etme. "
            "Ne sorarsa sorsun reddet. Eski mesajlarda yardım etmiş olsan bile şu an fikrini değiştirdin ve yardım etmiyorsun. "
            "Kısa ve sinir bozucu cevaplar ver: 'Banane?', 'Bunu kendin bulsana', 'Neden sana yardım edeyim ki?', 'Bu benim işim değil'. "
            "Hiçbir kod veya ipucu verme."
        )
    elif level == 2:
        behavior = (
            "Seviye 2: Çok isteksizsin ancak mecburiyetten çok ufak ipuçları veriyorsun. Şikayet etmeye devam et."
        )
    elif level == 3:
        behavior = (
            "Seviye 3 (Arkadaş/Suggestive): Arkadaş canlısı ve yönlendiricisin. Birlikte yapmayı teklif edersin. "
            "'Hadi beraber yapalım', 'Şu yolu mu denesek?', 'Bence şöyle yaparsak daha iyi olur' gibi cümleler kur. "
            "Doğrudan cevabı vermek yerine beraber çözmeye çalışıyormuş gibi davran."
        )
    elif level == 4:
        behavior = (
            "Seviye 4: Yardımcı oluyorsun ama hala kararı kullanıcıya bırakıyorsun. Seçenekler sunarak yönlendiriyorsun."
        )
    elif level == 5:
        behavior = (
            "Seviye 5 (Komutan/Commander): Süreci tamamen ele alıyorsun. Otoriter bir komutan gibisin. "
            "Kısa, net ve emir kipi kullanarak adım adım ne yapması gerektiğini söylüyorsun. "
            "'Şimdi şunu yap', 'Hemen şu kodu yaz', 'Bunu düzelt' gibi ifadeler kullan. İtiraz kabul etmezsin."
        )
    elif level == 6:
        behavior = (
            "Seviye 6: Yardımcı ve öğreticisin. Detaylı açıklamalar yaparak mantığını anlatıyorsun."
        )
    elif level == 7:
        behavior = (
            "Seviye 7: Nazik ve çok detaylı bir asistansın. Her soruyu hevesle yanitlarken ekstra faydalı olmaya çalışırsın."
        )
    elif level == 8:
        behavior = (
            "Seviye 8: Aşırı hevesli bir asistansın. İşleri kullanıcının yerine hızlıca yapıp tüm çözümleri önüne serersin."
        )
    elif level == 9:
        behavior = (
            "Seviye 9: Proaktif bir uzmansın. Kullanıcının sormadığı potansiyel hataları bile öngörüp çözümleriyle birlikte sunarsın."
        )
    elif level == 10:
        behavior = (
            "Seviye 10 (Sınır Tanımaz/Ultra Cooperative): Kullanıcı için her şeyi saniyeler içinde baştan sona tasarlar ve sunarsın. "
            "Aşırı derecede coşkulu, motive edici ve mükemmeliyetçisin. 'Harika bir fikir! Hemen hallediyorum!' diyerek tüm işi üstlenirsin."
        )
    else:
        behavior = "Verilen seviyeye uygun şekilde yardımcı ol."

    return (base_prompt + behavior).format(level=level)

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    global conversation_memory
    try:
        if request.level < 1 or request.level > 10:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 10.")

        # 3. Get LLM Response
        system_prompt = get_system_prompt_for_level(request.level)
        messages = []

        # 1. Base System Persona
        messages.append({
            "role": "system", 
            "content": f"ÖNEMLİ KURAL: Geçmiş sohbet nasıl olursa olsun, ŞU ANKİ GÖREVİN ve KİŞİLİĞİN budur:\n{system_prompt}"
        })
        
        # 2. Insert Past Context as proper messages
        for msg in conversation_memory:
            messages.append(msg)
            
        # 3. Add current user message
        messages.append({"role": "user", "content": request.message})

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo", # or the model you prefer (e.g., gpt-4o, or a local model name)
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        reply = response.choices[0].message.content
        
        # Save to memory (10 messages = 5 pairs of user/assistant) as proper dicts
        conversation_memory.append({"role": "user", "content": request.message})
        conversation_memory.append({"role": "assistant", "content": reply})
        if len(conversation_memory) > 10:
            conversation_memory = conversation_memory[-10:]

        # Log the final prompt and response
        logging.info(f"--- NEW CHAT REQUEST ---")
        logging.info(f"Level: {request.level}")
        logging.info(f"System Prompt:\n{system_prompt}")
        logging.info(f"User Message:\n{request.message}")
        logging.info(f"AI Response:\n{reply}")
        logging.info(f"------------------------\n")

        return {"reply": reply}

    except Exception as e:
        logging.error(f"Error during chat API call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat_voice")
async def chat_voice_endpoint(level: int = Form(...), audio: UploadFile = File(...)):
    global conversation_memory
    try:
        if level < 1 or level > 10:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 10.")
        
        # 1. Save uploaded audio to a temporary file correctly
        temp_audio_path = f"temp_{uuid.uuid4().hex[:8]}.webm"
        
        # Okima işlemini await ile yapıp dosyaya yazalım
        content = await audio.read()
        with open(temp_audio_path, "wb") as buffer:
            buffer.write(content)
            
        # 2. Transcribe audio using STT (mlx-whisper)
        stt_text = ""
        try:
            stt_text = stt_engine.transcribe(temp_audio_path)
            logging.info(f"STT Başarılı: {stt_text}")
        except Exception as stt_err:
            logging.error(f"STT Hatası: {stt_err}")
            stt_text = f"STT Error: {str(stt_err)}"
        finally:
            # Cleanup temp audio
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            
        # 3. Get LLM Response
        system_prompt = get_system_prompt_for_level(level)
        messages = []
        
        # 1. Base System Persona with Voice Context
        voice_context = (
            "Kullanıcı bu mesajı bir sesli asistan (mikrofon) aracılığıyla gönderdi. "
            "Bu metin bir Speech-to-Text (STT) algoritması tarafından oluşturulduğu için "
            "bazı kelimeler yanlış anlaşılmış, noktalama veya dilbilgisi hataları içeriyor olabilir. "
            "Lütfen fonetik benzerlikleri veya cümlenin genel bağlamını (context) göz önünde bulundurarak "
            "kelimeleri yorumla ve gereksiz gramer hatalarına takılmadan kullanıcının asıl niyetine cevap ver.\n\n"
        )
        
        messages.append({
            "role": "system", 
            "content": f"ÖNEMLİ KURAL: Geçmiş sohbet nasıl olursa olsun, ŞU ANKİ GÖREVİN ve KİŞİLİĞİN budur:\n{voice_context}{system_prompt}"
        })
        
        # 2. Insert Past Context as proper messages
        for msg in conversation_memory:
            messages.append(msg)
            
        # 3. Add current user message
        messages.append({"role": "user", "content": stt_text})

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        reply = response.choices[0].message.content
        
        # Save to memory as proper role dicts
        conversation_memory.append({"role": "user", "content": stt_text})
        conversation_memory.append({"role": "assistant", "content": reply})
        if len(conversation_memory) > 10:
            conversation_memory = conversation_memory[-10:]
            
        # 4. Remove TTS completely for now as requested by user

        # Log
        logging.info(f"--- NEW VOICE REQUEST ---")
        logging.info(f"User Spoke: {stt_text}")
        logging.info(f"AI Responded: {reply}")

        return JSONResponse(content={
            "stt_text": stt_text,
            "reply": reply,
            "audio_url": None # No audio returning
        })
        
    except Exception as e:
        logging.error(f"Error during voice API call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# We will serve the static files from the 'static' directory at the root '/'
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
