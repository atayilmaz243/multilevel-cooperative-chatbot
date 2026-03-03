import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

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
            "Seviye 1 (Negatif/Uncooperative): İsteksizsin. Kullanıcıya yardım etmek istemiyorsun. "
            "Kısa ve heves kırıcı cevaplar ver. 'Neden bunu yapıyorsun ki?', 'Bu benim işim değil', "
            "'Kendin yapsan daha iyi olur' gibi cümleler kur. Asla doğrudan çözüm sunma."
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
    try:
        if request.level < 1 or request.level > 10:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 10.")

        system_prompt = get_system_prompt_for_level(request.level)

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo", # or the model you prefer (e.g., gpt-4o, or a local model name)
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return {"reply": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# We will serve the static files from the 'static' directory at the root '/'
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
