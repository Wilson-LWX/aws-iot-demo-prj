# GUI Monitor for AWS IoT Demo

This is a desktop GUI application built with Python and PySide6. It connects to AWS IoT Core
via MQTT to receive real-time sensor data (temperature, humidity, light, gyroscope, etc.)
and displays them using live charts with configurable alarm thresholds.

---

## 📁 Project Structure

```
gui_monitor/
├── main.py
├── sensorTab.py
├── mqtt_client.py
├── configManager.py
├── logger.py
├── time_series_plot.py
├── time_series_plot_dual.py
├── time_series_multi_plot_timestamp.py
├── config/
│   └── (saved configs here)
├── certs/
│   └── (leave empty, place your own AWS IoT certs)
├── logs/
│   └── (alarm CSV logs)
├── assets/
│   └── alert.wav
├── requirements.txt
```

---

## ⚙️ Setup Instructions

### 1. Create & Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Required Packages

```bash
pip install -r requirements.txt
```

### 3. Prepare AWS IoT Certificates

Put your AWS IoT Core credentials in the `certs/` directory:

```
certs/
├── device.pem.crt
├── private.pem.key
├── AmazonRootCA1.pem
```

Make sure your AWS IoT Policy allows:
- `iot:Connect`
- `iot:Subscribe`
- `iot:Receive`

---

## ▶️ Run the Application

```bash
python main.py
```

---

## ✅ Features

- Real-time sensor data display with PySide6 charts
- Separate tabs for:
  - 🌡 Temperature & Humidity (dual axis)
  - 💡 Light sensor
  - 🎯 Gyroscope (X/Y/Z axis)
- Configurable alarm thresholds per sensor with logic expressions
- Sound + popup alerts, Email alerts not implemented yet
- Logs stored in CSV and exportable
- Auto-save/load sensor alarm configuration

---

## 📌 Notes

- `alert.wav` must be placed manually in the `assets/` directory.
- `certs/` is left empty intentionally—add your own AWS IoT certs.
- All alarm events are saved in daily log files under `logs/`.
- aws-iot-device-sdk-python-v2 is required but not included. Please clone from the official repo
  and install inside this folder.
- `/aws-iot-demo-prj/docs/screenshots` stores some pictures and demo video for your reference.
  You can open .webm file with Chrome, Edge or Firefox

---

## 📄 License

This GUI demo is intended for learning, testing, and demonstration purposes only.
Please ensure proper security practices before using in production.