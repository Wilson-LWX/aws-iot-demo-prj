# A7 Linux Client - MQTT Mutual Auth Example

This folder contains the modified AWS IoT Embedded C SDK demo project used on the A7 (Linux) core of STM32MP157. 
It demonstrates secure MQTT publishing via mutual TLS, integrating sensor data collection and publishing.

## 📁 Folder Structure

```
a7_linux/aws-iot-device-sdk-embedded-C/demos/mqtt/
├── mqtt_demo_mutual_auth/       # Modified MQTT demo
│   ├── mqtt_demo_mutual_auth.c
│   ├── sensorDataRing.c / .h    # New ring buffer for sensor data
│   ├── core_mqtt_config.h
│   ├── demo_config.h
│   └── CMakeLists.txt
├── certs/                       # Empty, put your AWS IoT certificates here
```

## ✅ Prerequisites

- Ubuntu 20.04+
- CMake 3.13+
- GCC
- AWS IoT Core setup with:
  - Thing + Certificates
  - Policy attached
  - Endpoint URL

## ⚙️ Build Instructions

```bash
cd mqtt_demo_mutual_auth
mkdir build && cd build
cmake ..
make
```

## 🚀 Run

```bash
./mqtt_demo_mutual_auth
```

> 🔐 Make sure your `certs/` folder contains valid `certificate.pem.crt`, `private.pem.key`, and `AmazonRootCA1.pem`.
 You may need to edit `demo_config.h` to point to their paths.

## 📝 Notes

- `sensorDataRing.c/h` implements a circular buffer to store sensor values received from M4 core.
- The main loop publishes JSON-formatted sensor data via MQTT to AWS IoT Core.
- Uses mutual TLS authentication for secure MQTT connection.
