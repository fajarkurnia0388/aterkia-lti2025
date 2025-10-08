import cv2
import requests
import time
from ultralytics import YOLOv10  # kalau pakai YOLOv10 fork, ganti ke YOLOv10

# --- PENGATURAN ---
WEBCAM_INDEX = 1
API_URL = "http://localhost:8000/upload/image"
MODEL_PATH = 'backend/best_kotak5.pt'
DETECTION_COOLDOWN = 5
CONFIDENCE_THRESHOLD = 0.85
TARGET_CLASS_ID = 0  # ganti sesuai ID kelas "kotak" di modelmu

def main():
    print(f"Memuat model YOLO dari {MODEL_PATH}...")
    try:
        model = YOLOv10(MODEL_PATH)
        print("Model berhasil dimuat.")
    except Exception as e:
        print(f"Error: Gagal memuat model. Pastikan path '{MODEL_PATH}' benar.")
        print(f"Detail error: {e}")
        return

    print("Membuka webcam...")
    cap = cv2.VideoCapture(WEBCAM_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Tidak bisa membuka webcam di index", WEBCAM_INDEX)
        return

    last_capture_time = 0
    print("Memulai deteksi... Arahkan objek 'kotak' ke webcam.")
    print("Tekan 'q' pada jendela webcam untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️  Gagal membaca frame dari webcam. Mencoba lagi...")
            time.sleep(0.5)
            continue

        results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        frame_display = results[0].plot()
        cv2.imshow('YOLO Detector', frame_display)

        # Cek apakah ada kotak (kelas sesuai TARGET_CLASS_ID)
        object_detected = any(int(box.cls[0]) == TARGET_CLASS_ID for box in results[0].boxes)

        if object_detected and (time.time() - last_capture_time > DETECTION_COOLDOWN):
            print("Objek 'kotak' terdeteksi! Mengambil gambar...")

            is_success, buffer = cv2.imencode(".jpg", frame)
            if not is_success:
                print("⚠️  Gagal meng-encode frame.")
                continue

            files = {'file': ('capture.jpg', buffer.tobytes(), 'image/jpeg')}
            try:
                response = requests.post(API_URL, files=files, timeout=5)
                if response.status_code == 200:
                    print("✅ Gambar berhasil diunggah ke server.")
                else:
                    print(f"❌ Server error: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Gagal terhubung ke server: {e}")

            # Update cooldown timer apapun hasilnya (biar tidak spam)
            last_capture_time = time.time()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Program dihentikan.")

if __name__ == "__main__":
    main()
