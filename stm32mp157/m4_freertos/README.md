# STM32MP157 M4 Core - FreeRTOS Sensor Collector

This folder contains the embedded firmware running on the Cortex-M4 core of the STM32MP157.  
The firmware collects sensor data and sends it to the A7 (Linux) core via OpenAMP,
enabling full edge-to-cloud IoT integration with AWS IoT Core.

---

## 📦 Project Structure

```
m4_freertos/
├── CA7/                # Shared headers for communication with A7 core (Linux)
├── CM4/                # Main application code (FreeRTOS tasks, OpenAMP logic)
├── Common/             # Global definitions and utility headers
├── Drivers/            # HAL, BSP and peripheral drivers (SPI, GPIO, etc.)
├── Middlewares/        # OpenAMP, libmetal, FreeRTOS middleware
├── awsIotDemoPrj.ioc   # STM32CubeMX project configuration file
```

---

## ⚙️ Features

- ✅ FreeRTOS-based task scheduling
- ✅ Sensor data collection (e.g. Temperature, Humidity, Light, Gyroscope)
- ✅ SPI/I2C interface to sensors (ICM20608G, etc.)
- ✅ OpenAMP RPMsg communication to Linux core
- ✅ Message formatting for MQTT forwarding (via A7 Linux)

---

## 🛠 How to Build

1. Open `awsIotDemoPrj.ioc` using **STM32CubeIDE**.
2. Build the project for the `CM4` target.
3. The output binary will be located in:
   ```
   /CM4/Debug/awsIotDemoPrj.elf
   ```
4. You can deploy to the M4 core using:
   - STM32_Programmer_CLI
   - U-Boot with remoteproc
   - Or via Linux `remoteproc` driver

---

## 🔗 Communication Flow

```
[Sensor] → [M4 Core: SPI] → [FreeRTOS + OpenAMP] → [Linux Core (A7)] → [AWS IoT Core via MQTT]
```

---

## 📁 Notes

- This code is designed to run **in parallel** with the A7-side AWS IoT MQTT client.
- Make sure the Linux side loads the proper device tree and remoteproc modules to start M4.
- Certificate handling and MQTT logic are **not implemented** on M4, but delegated to A7.

---

## 🧊 Dependencies

- STM32CubeMP1 Package
- OpenAMP middleware
- Libmetal
- HAL/LL drivers for STM32MP157

---

## 🚀 Recommended Companion

- See [`a7_linux/`](../a7_linux/) for the Linux-side MQTT bridge.
- See [`gui_monitor/`](../gui_monitor/) for the PyQt GUI visualizing the sensor data.

---

## 📷 Optional
