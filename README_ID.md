# ATEROLAS - Sistem Monitoring Autonomous Surface Vehicle (ASV)

[🇺🇸 README in English](README.md)

## Gambaran Umum

ATEROLAS adalah sistem monitoring dan kontrol Autonomous Surface Vehicle (ASV) generasi keempat yang dirancang untuk misi transportasi penumpang dan kargo. Sistem ini dilengkapi dengan monitoring telemetri real-time, kemampuan computer vision, dan fungsi kontrol misi.

## Fitur

- **Monitoring Telemetri Real-time**: Melacak roll, pitch, yaw, kecepatan, heading, dan tegangan
- **Sistem Computer Vision**: Deteksi dan pelacakan objek dengan kemampuan deteksi buoy
- **Kontrol Misi**: Komunikasi berbasis WebSocket untuk perintah misi
- **Capture & Penyimpanan Gambar**: Capture gambar otomatis dan manajemen galeri
- **Dashboard Interaktif**: Interface web modern dengan dukungan mode gelap
- **Integrasi Database**: PostgreSQL untuk penyimpanan data telemetri

## Arsitektur Sistem

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Web UI)      │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Mission Control │
                       │   (WebSocket)   │
                       └─────────────────┘
```

## Teknologi yang Digunakan

### Backend

- **FastAPI**: Framework web Python modern
- **PostgreSQL**: Database untuk penyimpanan telemetri
- **WebSocket**: Komunikasi real-time
- **OpenCV**: Pemrosesan computer vision
- **Ultralytics**: Model YOLO untuk deteksi objek
- **PyMAVLink**: Dukungan protokol MAVLink

### Frontend

- **HTML5/CSS3/JavaScript**: Interface web modern
- **Chart.js**: Visualisasi data real-time
- **WebSocket API**: Komunikasi real-time

## Instalasi

### Prasyarat

- Python 3.8+
- PostgreSQL 12+
- Node.js (opsional, untuk development)

### Setup Backend

1. Clone repository:

```bash
git clone <repository-url>
cd aterkia-lti2025
```

2. Install dependensi Python:

```bash
cd backend
pip install -r requirements.txt
```

3. Setup database PostgreSQL:

```bash
# Buat database
createdb autopilot_db

# Jalankan setup database
python db_setup.py
```

4. Jalankan server backend:

```bash
python main.py
```

API akan tersedia di `http://localhost:8000`

### Setup Frontend

Frontend adalah file HTML statis yang disajikan oleh backend FastAPI. Tidak diperlukan setup tambahan.

## Penggunaan

### Menjalankan Sistem

1. **Jalankan Backend**:

```bash
cd backend
python main.py
```

2. **Akses Dashboard**:
   - Buka browser dan navigasi ke `http://localhost:8000`
   - Dashboard akan otomatis terhubung ke backend via WebSocket

### Endpoint API

- `GET /`: Menyajikan dashboard utama
- `POST /upload/image`: Upload gambar yang di-capture
- `GET /images/latest`: Ambil gambar terbaru yang di-capture
- `WebSocket /ws/telemetry`: Data telemetri real-time
- `WebSocket /ws/frontend`: Komunikasi frontend
- `WebSocket /ws/mission_control`: Perintah kontrol misi

### Kontrol Misi

Sistem mendukung tiga mode utama:

- **IDLE**: Mode standby
- **ROI**: Navigasi Region of Interest
- **Snapshot**: Mode capture gambar

## Konfigurasi

### Konfigurasi Database

Update koneksi database di `backend/main.py`:

```python
def get_db():
    return psycopg2.connect(
        dbname="autopilot_db",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )
```

### Konfigurasi WebSocket

Update URI WebSocket di `frontend/index.html`:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
const WEBSOCKET_URI = "ws://127.0.0.1:8000/ws/frontend";
```

## Struktur Proyek

```
aterkia-lti2025/
├── backend/
│   ├── main.py              # Aplikasi FastAPI
│   ├── db_setup.py          # Inisialisasi database
│   ├── mission_controller.py # Logika kontrol misi
│   ├── vision_detector.py   # Pemrosesan computer vision
│   ├── requirements.txt     # Dependensi Python
│   └── *.pt                 # File model YOLO
├── frontend/
│   └── index.html           # Web dashboard
├── logger/
│   └── logger.py            # Utilitas logging
├── README.md                # File ini (Bahasa Indonesia)
└── README_ID.md             # Versi bahasa Inggris
```

## Pengembangan

### Menambah Fitur Baru

1. **Backend**: Tambahkan endpoint baru di `main.py`
2. **Frontend**: Update `index.html` untuk perubahan UI
3. **Database**: Modifikasi `db_setup.py` untuk perubahan schema

### Testing

Test koneksi WebSocket:

```bash
# Test endpoint telemetri
wscat -c ws://localhost:8000/ws/telemetry

# Test endpoint frontend
wscat -c ws://localhost:8000/ws/frontend
```

## Troubleshooting

### Masalah Umum

1. **Error Koneksi Database**:

   - Pastikan PostgreSQL berjalan
   - Periksa kredensial database di `main.py`

2. **Koneksi WebSocket Gagal**:

   - Verifikasi backend berjalan di port 8000
   - Periksa pengaturan firewall

3. **Gambar Tidak Ter-load**:
   - Pastikan direktori `uploads` ada
   - Periksa permission file

## Kontribusi

1. Fork repository
2. Buat feature branch
3. Lakukan perubahan
4. Test secara menyeluruh
5. Submit pull request

## Lisensi

Proyek ini dikembangkan untuk tujuan pendidikan dan penelitian.

## Kontak

Untuk pertanyaan atau dukungan, silakan hubungi tim pengembangan.

---

**Catatan**: Sistem ini dirancang untuk monitoring kendaraan otonom dan harus digunakan di lingkungan terkontrol dengan tindakan keamanan yang tepat.
