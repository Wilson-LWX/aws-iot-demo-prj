# AWS IoT Demo Project

An end-to-end IoT monitoring demo based on **STM32MP157 + AWS IoT Core + Python GUI**.

## Project Structure

- `gui_monitor/` �C Python desktop app for real-time sensor monitoring and alerts.
- `stm32mp157/`
  - `a7_linux/` �C MQTT client based on AWS IoT SDK (C)
  - `m4_freertos/` �C Embedded firmware running FreeRTOS and OpenAMP
- `docs/` �C System design document
- `docs/screenshots/` �C Screenshots and video demos

## Quick Start

See `gui_monitor/README.md` for running the desktop GUI.  
See `stm32mp157/a7_linux/README.md` for A7 side message forwarding to AWS IoT core.
See `stm32mp157/m4_freertos/README.md` for M4 side firmware design.
Other components can be compiled and tested separately.

## Note

This is a personal project showcasing full-stack IoT integration.  
Sensor noise is added for demo purposes �C remove it in production.

