import psycopg2
import psycopg2.extras
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse # <-- IMPORT BARU
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import datetime
import os
import shutil
import json

app = FastAPI()
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

def get_db():
    return psycopg2.connect(
        dbname="autopilot_db", user="postgres", password="postgres", 
        host="localhost", port="5432"
    )

class ConnectionManager:
    def __init__(self):
        self.frontend_connections: List[WebSocket] = []
        self.mission_controller: WebSocket | None = None
    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        if client_type == "frontend":
            self.frontend_connections.append(websocket)
            print(f"Info: Frontend client terhubung. Total: {len(self.frontend_connections)}")
        elif client_type == "controller":
            self.mission_controller = websocket
            print("Info: Mission Controller terhubung.")
    def disconnect(self, websocket: WebSocket, client_type: str):
        if client_type == "frontend" and websocket in self.frontend_connections:
            self.frontend_connections.remove(websocket)
            print(f"Info: Frontend client terputus. Sisa: {len(self.frontend_connections)}")
        elif client_type == "controller":
            self.mission_controller = None
            print("Info: Mission Controller terputus.")
    async def broadcast_to_frontends(self, message: str):
        for connection in list(self.frontend_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection, "frontend")
    async def send_to_controller(self, message: str):
        if self.mission_controller:
            try:
                await self.mission_controller.send_text(message)
            except Exception:
                self.disconnect(self.mission_controller, "controller")

manager = ConnectionManager()

@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_path = os.path.join(UPLOADS_DIR, f"capture_{timestamp}.jpg")
    try:
        with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/images/latest")
async def get_latest_images():
    try:
        files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
        sorted_files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(UPLOADS_DIR, f)), reverse=True)
        return {"images": sorted_files[:4]}
    except Exception: return {"images": []}

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Info: Logger telemetri terhubung.")
    try:
        while True:
            message = await websocket.receive_text()
            payload = json.loads(message)
            if payload.get("type") == "telemetry":
                data = payload.get("data", {})
                try:
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO telemetry (roll, pitch, yaw, lat, lon, groundspeed, heading, voltage, current) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                (data.get('roll'), data.get('pitch'), data.get('yaw'), data.get('lat'), data.get('lon'), data.get('groundspeed'), data.get('heading'), data.get('voltage'), data.get('current')))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    print(f"Error Database: {e}")
                await manager.broadcast_to_frontends(message)
    except WebSocketDisconnect:
        print("Info: Logger telemetri terputus.")

@app.websocket("/ws/frontend")
async def websocket_frontend_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "frontend")
    try:
        while True:
            command_str = await websocket.receive_text()
            await manager.send_to_controller(command_str)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "frontend")

@app.websocket("/ws/mission_control")
async def websocket_mission_control_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "controller")
    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast_to_frontends(message)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "controller")

# --- PERUBAHAN DI SINI: Endpoint untuk menyajikan index.html ---
@app.get("/")
async def read_index():
    """
    Endpoint ini akan menyajikan file index.html saat pengguna
    mengakses alamat root (misal: http://127.0.0.1:8000/).
    """
    return FileResponse('frontend/index.html')