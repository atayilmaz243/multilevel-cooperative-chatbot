import os
import json
import logging
import tempfile
import wave
import datetime
import subprocess
import glob
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from services import process_audio_pipeline

# Ensure log directory exists
os.makedirs("log", exist_ok=True)

logging.basicConfig(
    filename="esp32_backend.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()

app = FastAPI(title="ESP32 Communication Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A ConnectionManager to handle multiple ESP32 clients or user clients if necessary
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info("New WebSocket connection accepted.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info("WebSocket connection removed.")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.error(f"Failed to send to a websocket: {e}")

manager = ConnectionManager()

def cleanup_logs(directory="log", prefix="*", max_files=5):
    """
    Belirtilen prefix'e uyan dosyaları bulur, tarihe göre sıralar
    ve max_files adedini aşan en eski dosyaları siler.
    """
    files = glob.glob(os.path.join(directory, prefix))
    files.sort(key=os.path.getmtime)
    while len(files) > max_files:
        oldest_file = files.pop(0)
        try:
            os.remove(oldest_file)
            logging.info(f"Eski log dosyası silindi: {oldest_file}")
        except Exception as e:
            logging.error(f"Log silinirken hata oluştu {oldest_file}: {e}")


@app.get("/api/status")
def read_root():
    return {"status": "ESP32 Backend is running."}

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    ESP32 sends raw 16kHz 16-bit Mono PCM audio in the request body.
    We convert it to a WAV file and process it through STT -> LLM -> TTS.
    Returns the generated audio response (16kHz WAV).
    """
    audio_data = await request.body()
    if not audio_data:
        return {"error": "No audio received"}
        
    logging.info(f"Received {len(audio_data)} bytes of audio data.")
    
    # Save the incoming chunk to the log directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = os.path.join("log", f"audio_in_{timestamp}.wav")
    
    with wave.open(wav_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(16000)
        wav_file.writeframes(audio_data)
            
    logging.info(f"Saved incoming audio to {wav_path}")
    
    # Mikrofondan gelen sesi sunucuda yükselt (%400 / 4 kat)
    amp_wav_path = wav_path.replace(".wav", "_amp.wav")
    cmd_amp = [
        "ffmpeg", "-y", "-i", wav_path, 
        "-filter:a", "volume=4.0",
        amp_wav_path
    ]
    subprocess.run(cmd_amp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Başarılıysa güçlendirilmiş sesi asıl dosyanın üstüne yaz
    if os.path.exists(amp_wav_path):
        os.replace(amp_wav_path, wav_path)
    
    response_audio_path = await process_audio_pipeline(wav_path, timestamp)
    
    # Yeni log eklendikten sonra eski logları temizle
    # Sadece 5 ses, 5 text kalmasını sağlıyoruz
    cleanup_logs(directory="log", prefix="audio_in_*.wav", max_files=5)
    cleanup_logs(directory="log", prefix="stt_log_*.txt", max_files=5)
    
    if response_audio_path and os.path.exists(response_audio_path):
        return FileResponse(response_audio_path, media_type="audio/wav")
    
    return {"error": "Pipeline failed"}


@app.websocket("/ws")

async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for ESP32 and other clients to connect,
    send sensor data, and receive control commands.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received from ESP32 (or client): {data}")
            
            # Example: Echo back or process the json data
            # Typically ESP32 sends {"sensor": "value"} or similar
            # Broadcast the raw data so ESP32 can parse it cleanly
            await manager.broadcast(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("ESP32 disconnected from WebSocket.")
    except Exception as e:
        manager.disconnect(websocket)
        logging.error(f"WebSocket error: {e}")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Make sure this runs on a different port than the web_project
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
