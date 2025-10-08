import asyncio
import websockets
from pymavlink import mavutil
import json
import time

# --- PENGATURAN ---
SERIAL_PORT = 'COM10'
BAUD_RATE = 115200
# Pastikan ini adalah endpoint yang benar untuk telemetri di main.py Anda
WEBSOCKET_URI = "ws://127.0.0.1:8000/ws/telemetry" 
SEND_RATE_HZ = 5 # Kirim data 5 kali per detik

# --- Penampung Data Telemetri ---
# Menggunakan dictionary agar mudah dikelola dan diperluas
telemetry_data = {
    "roll": None,
    "pitch": None,
    "yaw": None,
    "lat": None,
    "lon": None,
    "groundspeed": None,
    "heading": None,
    "voltage": None,
    "current": None,
}

async def read_mavlink(master):
    """Tugas yang berjalan di background untuk terus membaca pesan MAVLink."""
    while True:
        msg = master.recv_match(
            type=['ATTITUDE', 'GPS_RAW_INT', 'VFR_HUD', 'SYS_STATUS'], 
            blocking=True,
            timeout=1.0 # Timeout agar tidak terjebak selamanya
        )
        if msg:
            msg_type = msg.get_type()
            if msg_type == 'ATTITUDE':
                telemetry_data["roll"] = msg.roll
                telemetry_data["pitch"] = msg.pitch
                telemetry_data["yaw"] = msg.yaw
            elif msg_type == 'GPS_RAW_INT' and msg.fix_type >= 3:
                telemetry_data["lat"] = msg.lat / 1e7
                telemetry_data["lon"] = msg.lon / 1e7
            elif msg_type == 'VFR_HUD':
                telemetry_data["groundspeed"] = msg.groundspeed
                telemetry_data["heading"] = msg.heading
            elif msg_type == 'SYS_STATUS':
                telemetry_data["voltage"] = msg.voltage_battery / 1000.0  # Konversi dari mV ke V
                # Current tidak selalu tersedia, beri nilai default jika -1
                telemetry_data["current"] = msg.current_battery / 100.0 if msg.current_battery != -1 else 0.0 # Konversi dari cA ke A
        await asyncio.sleep(0.01) # Beri kesempatan tugas lain berjalan

async def send_telemetry(websocket):
    """Tugas yang berjalan di background untuk mengirim data telemetri secara berkala."""
    while True:
        # Buat paket data yang akan dikirim
        payload = {
            "type": "telemetry",
            "data": telemetry_data
        }
        try:
            await websocket.send(json.dumps(payload))
            print(f"Data telemetri terkirim -> Lat: {telemetry_data['lat']:.4f}, Lon: {telemetry_data['lon']:.4f}, V: {telemetry_data['voltage']:.2f}V", end="\r")
        except websockets.ConnectionClosed:
            print("\nKoneksi terputus saat mengirim, menunggu koneksi ulang...")
            break # Keluar dari loop ini agar loop utama bisa mencoba konek ulang
        
        await asyncio.sleep(1.0 / SEND_RATE_HZ)

async def mavlink_logger():
    """Fungsi utama yang mengelola koneksi dan tugas."""
    print(f"Mencoba terhubung ke MAVLink di {SERIAL_PORT}...")
    try:
        master = mavutil.mavlink_connection(SERIAL_PORT, baud=BAUD_RATE)
        master.wait_heartbeat()
        print("Heartbeat diterima! Berhasil terhubung ke MAVLink.")
    except Exception as e:
        print(f"KRITIS: Gagal terhubung ke MAVLink: {e}")
        return

    while True:
        try:
            async with websockets.connect(WEBSOCKET_URI) as websocket:
                print(f"\nBerhasil terhubung ke WebSocket Server di {WEBSOCKET_URI}")
                
                # Jalankan kedua tugas (membaca dan mengirim) secara bersamaan
                # Jika salah satu gagal (misal koneksi putus), keduanya akan berhenti
                await asyncio.gather(
                    read_mavlink(master),
                    send_telemetry(websocket)
                )

        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            print(f"\nKoneksi WebSocket terputus: {e}. Mencoba terhubung kembali dalam 5 detik...")
            await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nLogger dihentikan.")
            break
        except Exception as e:
            print(f"\nTerjadi error: {e}. Mencoba lagi...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(mavlink_logger())

