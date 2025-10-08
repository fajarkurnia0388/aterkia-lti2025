import psycopg2

# --- Pengaturan Koneksi ---
# Pastikan detail ini sesuai dengan setup PostgreSQL Anda
DB_NAME = "autopilot_db"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

try:
    # 1. Koneksi ke database default 'postgres' untuk membuat database baru
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # 2. Hapus database lama (jika ada) dan buat yang baru
    print(f"Menghapus database '{DB_NAME}' jika ada...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    print(f"Membuat database '{DB_NAME}'...")
    cursor.execute(f"CREATE DATABASE {DB_NAME};")
    print(f"Database '{DB_NAME}' berhasil dibuat!")

    cursor.close()
    conn.close()

    # 3. Koneksi ke database baru yang sudah dibuat
    print(f"Menghubungkan ke database '{DB_NAME}'...")
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()

    # 4. Buat tabel 'telemetry' dengan skema yang sudah diperbarui
    print("Membuat tabel 'telemetry' dengan kolom baru...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        -- Data Attitude
        roll FLOAT,
        pitch FLOAT,
        yaw FLOAT,
        
        -- Data GPS
        lat DOUBLE PRECISION,
        lon DOUBLE PRECISION,
        
        -- Data Performa
        groundspeed FLOAT,
        heading INTEGER,
        voltage FLOAT,
        current FLOAT
    );
    """)
    conn.commit()
    print("Tabel 'telemetry' dengan skema baru berhasil dibuat!")

except Exception as e:
    print(f"Terjadi error: {e}")
finally:
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'conn' in locals() and conn:
        conn.close()
    print("Proses setup selesai.")