# =================================================================
# KODE FINAL - MISSION CONTROLLER V4 (OPERASIONAL)
# =================================================================
import cv2
import time
import asyncio
import websockets
import requests
import json
from ultralytics import YOLOv10

class Config:
    CAMERA_INDEX = 1
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    GATE_MODEL_PATH = 'backend/best5.pt'
    BOX_MODEL_PATH = 'backend/best_kotak5.pt'
    UPLOAD_URL = "http://127.0.0.1:8000/uploads"
    DETECTION_COOLDOWN = 0.01
    WEBSOCKET_URI = "ws://127.0.0.1:8000/ws/mission_control"
    TARGET_FPS = 20
    
    # --- ID Kelas untuk Model Buoy (Sesuaikan jika perlu) ---
    GREEN_BALL_CLASS_ID = 0
    RED_BALL_CLASS_ID = 1

class MissionController:
    def __init__(self, config):
        self.config = config
        self.current_mode = "IDLE"
        self.last_capture_time = 0
        self.gate_model, self.box_model = self._load_models()
        self.cap = self._init_camera()
        print("Controller siap.")

    def _load_models(self):
        print("Memuat model (YOLOv10)...")
        # Pastikan kedua model adalah YOLOv10
        gate_model = YOLOv10(self.config.GATE_MODEL_PATH)
        box_model = YOLOv10(self.config.BOX_MODEL_PATH)
        return gate_model, box_model

    def _init_camera(self):
        print(f"Membuka kamera di indeks: {self.config.CAMERA_INDEX}")
        cap = cv2.VideoCapture(self.config.CAMERA_INDEX, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        if not cap.isOpened():
            raise IOError("FATAL: Tidak bisa membuka kamera.")
        return cap

    async def run(self):
        while True:
            try:
                async with websockets.connect(self.config.WEBSOCKET_URI) as websocket:
                    print("Mission Controller terhubung ke server backend.")
                    listen_task = asyncio.create_task(self._listen_for_commands(websocket))
                    await self._main_loop(websocket)
                    listen_task.cancel()
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
                print("Koneksi terputus. Mencoba lagi dalam 5 detik...")
                await asyncio.sleep(5)

    async def _main_loop(self, websocket):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue

            annotated_frame, status_message = self._process_frame_based_on_mode(frame)
            await self._send_update(websocket, status_message, annotated_frame)
            await asyncio.sleep(1 / self.config.TARGET_FPS)

    def _process_frame_based_on_mode(self, frame):
        if self.current_mode == "ROI_NAV":
            return self._detect_buoys(frame)
        elif self.current_mode == "BOX_SNAPSHOT":
            return self._detect_box_and_snapshot(frame)
        else: # IDLE Mode
            return frame.copy(), f"Mode: {self.current_mode}"

    def _detect_buoys(self, frame):
        """
        Logika operasional untuk mendeteksi, memilah, dan menggambar buoy.
        """
        # Jalankan inferensi dengan confidence threshold rendah untuk debugging
        results = self.gate_model(frame, conf=0.25, verbose=False)
        
        detections = {'red': [], 'green': []}
        if results and results[0].boxes:
            for box in results[0].boxes:
                try:
                    cls_id = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    ball_data = {'cx': (x1 + x2) // 2, 'cy': (y1 + y2) // 2, 'box': (x1, y1, x2, y2)}
                    
                    if cls_id == self.config.GREEN_BALL_CLASS_ID:
                        detections['green'].append(ball_data)
                    elif cls_id == self.config.RED_BALL_CLASS_ID:
                        detections['red'].append(ball_data)
                except (IndexError, TypeError):
                    continue

        # Visualisasi manual berdasarkan hasil pemilahan
        annotated_frame = frame.copy()
        for ball in detections['green']:
            x1, y1, x2, y2 = ball['box']
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated_frame, 'Green', (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        for ball in detections['red']:
            x1, y1, x2, y2 = ball['box']
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(annotated_frame, 'Red', (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
        
        status_message = f"Ditemukan: Merah({len(detections['red'])}), Hijau({len(detections['green'])})"
        return annotated_frame, status_message

    def _detect_box_and_snapshot(self, frame):
        results = self.box_model(frame, conf=0.6, verbose=False)
        if results and results[0].boxes:
            annotated_frame = results[0].plot()
            status_message = "Mencari kotak..."
            if time.time() - self.last_capture_time > self.config.DETECTION_COOLDOWN:
                self.last_capture_time = time.time()
                status_message = "Kotak terdeteksi! Mengambil gambar..."
                asyncio.to_thread(self.upload_frame, frame)
            # else:
            #     status_message = "Kotak terdeteksi (cooldown)..."
        else:
            annotated_frame = frame.copy()
            status_message = "Mencari kotak..."
        return annotated_frame, status_message

    async def _listen_for_commands(self, websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("command") == "set_mode":
                    new_mode = data.get("mode")
                    if new_mode in ["IDLE", "ROI_NAV", "BOX_SNAPSHOT"]:
                        self.current_mode = new_mode
                        print(f"Mode diubah menjadi: {self.current_mode}")
            except json.JSONDecodeError: pass

    async def _send_update(self, websocket, status, frame):
        try:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            jpg_as_text = buffer.tobytes()
            update_data = {"type": "vision_update", "status": status, "frame": jpg_as_text.hex()}
            await websocket.send(json.dumps(update_data))
        except Exception: pass

    def upload_frame(self, frame):
        is_success, buffer = cv2.imencode(".jpg", frame)
        if is_success:
            files = {'file': ('capture.jpg', buffer.tobytes(), 'image/jpeg')}
            try:
                requests.post(self.config.UPLOAD_URL, files=files, timeout=3)
                print("Gambar berhasil diunggah.")
            except requests.RequestException: pass

    def cleanup(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            print("Kamera dilepaskan.")

if __name__ == "__main__":
    controller = None
    try:
        config = Config()
        controller = MissionController(config)
        asyncio.run(controller.run())
    except Exception as e:
        print(f"FATAL: Terjadi error pada level tertinggi: {e}")
    finally:
        if controller:
            controller.cleanup()
        print("Program selesai.")