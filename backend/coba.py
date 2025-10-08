import cv2
from ultralytics import YOLOv10 # <-- PERUBAHAN KRUSIAL DI SINI

# ===============================================================
# --- PENGATURAN (SILAKAN SESUAIKAN) ---
# ===============================================================
MODEL_PATH = 'backend/best (3).pt' # Ganti ke 'best5.pt' jika itu yang benar
GREEN_BUOY_ID = 0
RED_BUOY_ID = 1
CAMERA_INDEX = 1
# ===============================================================


def run_local_test_v10():
    print(f"Memuat model YOLOv10 dari: {MODEL_PATH}")
    try:
        # Gunakan kelas YOLOv10 untuk memuat model
        model = YOLOv10(MODEL_PATH) # <-- PERUBAHAN KRUSIAL DI SINI
    except Exception as e:
        print(f"FATAL: Gagal memuat model. Error: {e}")
        return

    print(f"Membuka kamera di indeks: {CAMERA_INDEX}")
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"FATAL: Tidak bisa membuka kamera di indeks {CAMERA_INDEX}.")
        return

    print("\n--- Tes Lokal Dimulai (YOLOv10) ---")
    print("Tekan tombol 'q' di jendela video untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal membaca frame. Keluar...")
            break

        try:
            results = model(frame, verbose=False)
        except Exception as e:
            print(f"\n!!! ERROR saat menjalankan model: {e} !!!")
            break
            
        red_count, green_count = 0, 0

        if results and results[0].boxes:
            for box in results[0].boxes:
                try:
                    cls_id = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    if cls_id == GREEN_BUOY_ID:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, 'Green Buoy', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        green_count += 1
                    elif cls_id == RED_BUOY_ID:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, 'Red Buoy', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        red_count += 1
                except (IndexError, TypeError):
                    continue

        info_text = f"Merah: {red_count}, Hijau: {green_count}"
        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow('Tes Model YOLOv10 Lokal', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print("\nMembersihkan resource...")
    cap.release()
    cv2.destroyAllWindows()
    print("Program tes selesai.")


if __name__ == "__main__":
    run_local_test_v10()