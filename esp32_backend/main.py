import os
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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


@app.get("/api/status")
def read_root():
    return {"status": "ESP32 Backend is running."}


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
