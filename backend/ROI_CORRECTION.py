# =================================================================
# KODE FINAL (REVISI): NAVIGASI MISI DENGAN YAW OVERRIDE (ROI)
# =================================================================
# Deskripsi:
# Versi ini merupakan revisi total dengan struktur berbasis objek (OOP)
# untuk meningkatkan keterbacaan, robustness, dan kemudahan pengelolaan.
# Skrip ini mengintegrasikan deteksi gerbang YOLOv8 dengan kontrol yaw
# MAVLink (Region of Interest) untuk navigasi presisi.
#
# Prasyarat:
# 1. Library: pip install pymavlink ultralytics opencv-python
# 2. Parameter PX4: 'NAV_YAW_MODE' harus diatur ke 3 (Towards ROI).
# =================================================================

import time
import math
import cv2
from ultralytics import YOLO
from pymavlink import mavutil

# =================================================================
# BAGIAN 1: KONFIGURASI
# =================================================================
class Config:
    """Menyimpan semua parameter konfigurasi di satu tempat."""
    # --- Pengaturan Model & Kamera ---
    MODEL_PATH = '../backend/best (3).pt'  # Path ke model YOLOv8 Anda
    RED_BALL_CLASS_ID = 1
    GREEN_BALL_CLASS_ID = 0
    CAMERA_INDEX = 1
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480

    # --- Parameter Kalibrasi (WAJIB DISESUAIKAN) ---
    FOCAL_LENGTH_PX = 500.0  # Nilai hasil kalibrasi Anda yang akurat
    GATE_WIDTH_METERS = 0.6  # Lebar asli gerbang Anda yang akurat

    # --- Pengaturan MAVLink ---
    CONNECTION_STRING = 'udp:192.168.4.2:14550' # Sesuaikan (misal: '/dev/ttyUSB0')
    ROI_SEND_RATE_HZ = 4  # Frekuensi pengiriman perintah ROI (2-5 Hz)

# =================================================================
# BAGIAN 2: KELAS BANTUAN
# =================================================================

class VehicleState:
    """Menyimpan dan mengelola data telemetri terakhir dari kendaraan."""
    def __init__(self):
        self.lat = None
        self.lon = None
        self.alt = None
        self.yaw_rad = None

    def update_gps(self, msg):
        """Memperbarui state dari pesan GPS_RAW_INT."""
        if msg.fix_type >= 3:
            self.lat = msg.lat / 1e7
            self.lon = msg.lon / 1e7
            self.alt = msg.alt / 1e3

    def update_attitude(self, msg):
        """Memperbarui state dari pesan ATTITUDE."""
        self.yaw_rad = msg.yaw

    def is_ready(self):
        """Memeriksa apakah semua data telemetri yang dibutuhkan sudah tersedia."""
        return all(v is not None for v in [self.lat, self.lon, self.alt, self.yaw_rad])

# =================================================================
# BAGIAN 3: KELAS UTAMA NAVIGATOR
# =================================================================

class VisionNavigator:
    """Kelas utama yang mengelola seluruh proses navigasi berbasis visi."""

    def __init__(self, config):
        self.config = config
        self.vehicle_state = VehicleState()
        self.model = self._load_model()
        self.cap = self._init_camera()
        self.master = self._init_mavlink()
        self.image_center_x = self.config.FRAME_WIDTH / 2.0
        self.last_roi_time = 0

    def _load_model(self):
        """Memuat model YOLOv8."""
        print(f"Memuat model YOLOv8 dari: {self.config.MODEL_PATH}")
        return YOLO(self.config.MODEL_PATH)

    def _init_camera(self):
        """Menginisialisasi koneksi kamera."""
        print(f"Membuka kamera di indeks: {self.config.CAMERA_INDEX}")
        cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        if not cap.isOpened():
            raise IOError("FATAL: Tidak bisa membuka kamera.")
        return cap

    def _init_mavlink(self):
        """Menginisialisasi koneksi MAVLink ke flight controller."""
        print(f"Menghubungkan ke PX4 di: {self.config.CONNECTION_STRING}...")
        master = mavutil.mavlink_connection(self.config.CONNECTION_STRING, autoreconnect=True)
        master.wait_heartbeat()
        print("Heartbeat diterima. Koneksi MAVLink berhasil.")
        return master

    def run(self):
        """Menjalankan loop utama program."""
        try:
            while True:
                # 1. Dapatkan data terbaru dari kendaraan dan kamera
                self._update_telemetry()
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                # 2. Lakukan deteksi objek
                detections = self._detect_objects(frame)
                best_gate = self._find_best_gate(detections)

                # 3. Lakukan perhitungan dan kirim perintah jika memungkinkan
                if best_gate and self.vehicle_state.is_ready():
                    self._process_gate_logic(best_gate)
                
                # 4. Tampilkan visualisasi
                self._visualize(frame, detections, best_gate)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Tombol 'q' ditekan, keluar dari program.")
                    break
        except KeyboardInterrupt:
            print("\nProgram dihentikan oleh pengguna.")
        except Exception as e:
            print(f"\nTerjadi error tak terduga: {e}")
        finally:
            self._cleanup()

    def _update_telemetry(self):
        """Menerima pesan MAVLink dan memperbarui state kendaraan."""
        msg = self.master.recv_match(type=['GPS_RAW_INT', 'ATTITUDE'], blocking=False)
        if msg:
            if msg.get_type() == 'GPS_RAW_INT':
                self.vehicle_state.update_gps(msg)
            elif msg.get_type() == 'ATTITUDE':
                self.vehicle_state.update_attitude(msg)

    def _detect_objects(self, frame):
        """Menjalankan inferensi YOLO dan memformat hasilnya."""
        results = self.model(frame, verbose=False)
        detections = {'red': [], 'green': []}
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                ball_data = {'cx': (x1 + x2) // 2, 'cy': (y1 + y2) // 2, 'area': (x2 - x1) * (y2 - y1), 'box': (x1, y1, x2, y2)}
                if cls == self.config.RED_BALL_CLASS_ID:
                    detections['red'].append(ball_data)
                elif cls == self.config.GREEN_BALL_CLASS_ID:
                    detections['green'].append(ball_data)
        return detections

    def _find_best_gate(self, detections):
        """Mencari pasangan bola terbaik dari hasil deteksi."""
        # Logika ini bisa dipindahkan dari fungsi global ke sini untuk enkapsulasi
        return find_best_gate(detections['red'], detections['green'])

    def _process_gate_logic(self, best_gate):
        """Menghitung dan mengirim perintah ROI jika gerbang terdeteksi."""
        r_ball, g_ball = best_gate
        midpoint_x = (r_ball['cx'] + g_ball['cx']) / 2.0
        pixel_width = abs(r_ball['cx'] - g_ball['cx'])

        if pixel_width > 5:
            distance_m = (self.config.GATE_WIDTH_METERS * self.config.FOCAL_LENGTH_PX) / pixel_width
            error_px = midpoint_x - self.image_center_x
            error_m = (error_px * distance_m) / self.config.FOCAL_LENGTH_PX
            correction_rad = math.atan2(error_m, distance_m)
            
            bearing_rad = self.vehicle_state.yaw_rad + correction_rad
            target_lat, target_lon = get_gps_of_target(self.vehicle_state.lat, self.vehicle_state.lon, distance_m, bearing_rad)

            current_time = time.time()
            if (current_time - self.last_roi_time) > (1.0 / self.config.ROI_SEND_RATE_HZ):
                set_roi(self.master, target_lat, target_lon, self.vehicle_state.alt)
                self.last_roi_time = current_time

    def _visualize(self, frame, detections, best_gate):
        """Menggambar semua informasi di frame untuk ditampilkan."""
        # Gambar semua deteksi
        for ball in detections['red']:
            x1, y1, x2, y2 = ball['box']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        for ball in detections['green']:
            x1, y1, x2, y2 = ball['box']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Gambar info jika gerbang terbaik ditemukan
        if best_gate:
            r_ball, g_ball = best_gate
            midpoint_x = int((r_ball['cx'] + g_ball['cx']) / 2.0)
            midpoint_y = int((r_ball['cy'] + g_ball['cy']) / 2.0)
            cv2.circle(frame, (midpoint_x, midpoint_y), 7, (0, 255, 255), -1)

        # Tampilkan teks telemetri
        lat_str = f"{self.vehicle_state.lat:.6f}" if self.vehicle_state.lat is not None else "N/A"
        lon_str = f"{self.vehicle_state.lon:.6f}" if self.vehicle_state.lon is not None else "N/A"
        cv2.putText(frame, f"Lat: {lat_str}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Lon: {lon_str}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow("Navigasi ROI - Tekan 'q' untuk keluar", frame)

    def _cleanup(self):
        """Membersihkan semua resource saat program berhenti."""
        print("Membersihkan resource...")
        if hasattr(self, 'master') and self.master and self.master.target_system != 0:
            print("Membersihkan target ROI di PX4...")
            set_roi(self.master, 0, 0, 0)
            self.master.close()
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        print("Koneksi, kamera, dan jendela dilepaskan. Program selesai.")

# =================================================================
# BAGIAN 4: FUNGSI PEMBANTU GLOBAL (dipisahkan dari class)
# =================================================================

def find_best_gate(red_balls, green_balls):
    """Mencari pasangan bola merah dan hijau terbaik yang membentuk gerbang."""
    best_gate = None
    max_avg_area = -1
    if not red_balls or not green_balls:
        return None
    for r_ball in red_balls:
        for g_ball in green_balls:
            # Pastikan kedua bola berada pada ketinggian vertikal yang mirip
            if abs(r_ball['cy'] - g_ball['cy']) < 100:
                avg_area = (r_ball['area'] + g_ball['area']) / 2
                if avg_area > max_avg_area:
                    max_avg_area = avg_area
                    best_gate = (r_ball, g_ball)
    return best_gate

def get_gps_of_target(lat_deg, lon_deg, distance_m, bearing_rad):
    """Menghitung koordinat GPS target ("titik bayangan")."""
    R = 6378137.0  # Radius Bumi dalam meter
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)

    target_lat_rad = math.asin(math.sin(lat_rad) * math.cos(distance_m / R) +
                               math.cos(lat_rad) * math.sin(distance_m / R) * math.cos(bearing_rad))

    target_lon_rad = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(distance_m / R) * math.cos(lat_rad),
                                           math.cos(distance_m / R) - math.sin(lat_rad) * math.sin(target_lat_rad))

    return math.degrees(target_lat_rad), math.degrees(target_lon_rad)

def set_roi(master, lat, lon, alt):
    """Mengirim perintah MAV_CMD_DO_SET_ROI ke flight controller."""
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_ROI,
        0, 0, 0, 0, lat, lon, alt, 0
    )
    if lat != 0 or lon != 0:
        print(f"Mengirim ROI -> Lat: {lat:.6f}, Lon: {lon:.6f}")


# =================================================================
# BAGIAN 5: TITIK MASUK PROGRAM
# =================================================================

if __name__ == "__main__":
    try:
        config = Config()
        navigator = VisionNavigator(config)
        navigator.run()
    except Exception as e:
        print(f"FATAL: Terjadi error pada level tertinggi: {e}")