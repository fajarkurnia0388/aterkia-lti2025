# ATEROLAS - Autonomous Surface Vehicle (ASV) Monitoring System

[🇮🇩 README dalam Bahasa Indonesia](README_ID.md)

## Overview

ATEROLAS is a fourth-generation Autonomous Surface Vehicle (ASV) monitoring and control system designed for passenger and cargo transportation missions. The system features real-time telemetry monitoring, computer vision capabilities, and mission control functionality.

## Features

- **Real-time Telemetry Monitoring**: Track roll, pitch, yaw, speed, heading, and voltage
- **Computer Vision System**: Object detection and tracking with buoy detection capabilities
- **Mission Control**: WebSocket-based communication for mission commands
- **Image Capture & Storage**: Automatic image capture and gallery management
- **Interactive Dashboard**: Modern web interface with dark mode support
- **Database Integration**: PostgreSQL for telemetry data storage

## System Architecture

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

## Technology Stack

### Backend

- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Database for telemetry storage
- **WebSocket**: Real-time communication
- **OpenCV**: Computer vision processing
- **Ultralytics**: YOLO model for object detection
- **PyMAVLink**: MAVLink protocol support

### Frontend

- **HTML5/CSS3/JavaScript**: Modern web interface
- **Chart.js**: Real-time data visualization
- **WebSocket API**: Real-time communication

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Node.js (optional, for development)

### Backend Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd aterkia-lti2025
```

2. Install Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Set up PostgreSQL database:

```bash
# Create database
createdb autopilot_db

# Run database setup
python db_setup.py
```

4. Start the backend server:

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

The frontend is a static HTML file served by the FastAPI backend. No additional setup required.

## Usage

### Starting the System

1. **Start the Backend**:

```bash
cd backend
python main.py
```

2. **Access the Dashboard**:
   - Open your browser and navigate to `http://localhost:8000`
   - The dashboard will automatically connect to the backend via WebSocket

### API Endpoints

- `GET /`: Serves the main dashboard
- `POST /upload/image`: Upload captured images
- `GET /images/latest`: Get latest captured images
- `WebSocket /ws/telemetry`: Real-time telemetry data
- `WebSocket /ws/frontend`: Frontend communication
- `WebSocket /ws/mission_control`: Mission control commands

### Mission Control

The system supports three main modes:

- **IDLE**: Standby mode
- **ROI**: Region of Interest navigation
- **Snapshot**: Image capture mode

## Configuration

### Database Configuration

Update the database connection in `backend/main.py`:

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

### WebSocket Configuration

Update WebSocket URIs in `frontend/index.html`:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
const WEBSOCKET_URI = "ws://127.0.0.1:8000/ws/frontend";
```

## Project Structure

```
aterkia-lti2025/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── db_setup.py          # Database initialization
│   ├── mission_controller.py # Mission control logic
│   ├── vision_detector.py   # Computer vision processing
│   ├── requirements.txt     # Python dependencies
│   └── *.pt                 # YOLO model files
├── frontend/
│   └── index.html           # Web dashboard
├── logger/
│   └── logger.py            # Logging utilities
├── README.md                # This file (English)
└── README_ID.md             # Indonesian version
```

## Development

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Update `index.html` for UI changes
3. **Database**: Modify `db_setup.py` for schema changes

### Testing

Test the WebSocket connection:

```bash
# Test telemetry endpoint
wscat -c ws://localhost:8000/ws/telemetry

# Test frontend endpoint
wscat -c ws://localhost:8000/ws/frontend
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**:

   - Ensure PostgreSQL is running
   - Check database credentials in `main.py`

2. **WebSocket Connection Failed**:

   - Verify backend is running on port 8000
   - Check firewall settings

3. **Images Not Loading**:
   - Ensure `uploads` directory exists
   - Check file permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is developed for educational and research purposes.

## Contact

For questions or support, please contact the development team.

---

**Note**: This system is designed for autonomous vehicle monitoring and should be used in controlled environments with proper safety measures.
