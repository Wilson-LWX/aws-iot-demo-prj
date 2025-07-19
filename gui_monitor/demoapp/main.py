import os
import sys
import json

from dotenv import load_dotenv

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel,
    QTabWidget, QSpinBox, QMenuBar, QMenu, QMessageBox, QStatusBar,
    QFileDialog, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Slot, QUrl
from PySide6.QtGui import QAction
from PySide6.QtMultimedia import QSoundEffect
from pathlib import Path

from mqtt_client import MQTTClient
from configManager import ConfigManager
from logger import SensorLogger
from sensorTab import SensorTab

            
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # setup sampling period
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 3600)  #1 second to 1 hour
        self.interval_input.setValue(1)

        interval_label = QLabel("Sampling Interval (s):")
        interval_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # warning methods to support
        self.alert_method_combo = QComboBox()
        self.alert_method_combo.addItems(["None", "Sound", "Email", "Sound + Email"])
        self.alert_method_combo.setToolTip("Select the alert method when threshold exceeded")        
        
        # Email to support future
        for i in range(self.alert_method_combo.count()):
            text = self.alert_method_combo.itemText(i)
            if "Email" in text:
                self.alert_method_combo.model().item(i).setEnabled(False)
        
        self.setWindowTitle("IoT Multi-Sensor Monitor - V1.0")
        self.setMinimumSize(800, 600)

        self._create_menu()

        self.gyro_tab = SensorTab("Gyroscope", ["X Axis", "Y Axis", "Z Axis"], main_window=self)
        self.temp_humid_tab = SensorTab("Temperature & Humidity", ["Temperature (°C)", "Humidity (%)"], main_window=self)
        self.light_tab = SensorTab("Light", ["Light Intensity"], main_window=self)

        tabs = QTabWidget()
        tabs.addTab(self.gyro_tab, "Gyroscope")
        tabs.addTab(self.temp_humid_tab, "Temperature & Humidity")
        tabs.addTab(self.light_tab, "Light")
                                
        # button span（Start / Stop / Interval）
        control_layout = QHBoxLayout()

        # Start/Stop
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.start_button.clicked.connect(self.start_data_collection)
        self.stop_button.clicked.connect(self.stop_data_collection)
        self.start_button.setToolTip("Start receiving data and drawing charts")
        self.stop_button.setToolTip("Stop receiving data and drawing charts")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        self.start_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.stop_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        # button size
        for btn in [self.start_button, self.stop_button]:
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            btn.setMaximumWidth(100)    

        # layout
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addSpacing(20)
        control_layout.addWidget(interval_label)
        control_layout.addWidget(self.interval_input)
        #control_layout.addStretch()
        control_layout.addSpacing(20)
        control_layout.addWidget(QLabel("Alert Method:"))
        control_layout.addWidget(self.alert_method_combo)
        
        # main display layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        main_layout.addLayout(control_layout)        

        # central container
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.mqtt_status_label = QLabel("MQTT Status: Connecting...")
        self.device_status_label = QLabel("Device Status: Unknown")
        self.status_bar.addWidget(self.mqtt_status_label)
        self.status_bar.addPermanentWidget(self.device_status_label)

        # refresh status timer
        self.keep_alive_timer = QTimer(self)
        self.keep_alive_timer.timeout.connect(self._refresh_status_bar)
        self.keep_alive_timer.start(3000)  # every 3s

        self.mqtt_status_text = "MQTT Status: Connecting..."
        self.device_status_text = "Device Status: Unknown"
        
        self.drawing_paused = False
        
        self.config_mgr = ConfigManager(self) # configManager initialization
        config = self.config_mgr.load_config(self.config_mgr.user_config_path)
        if not config:  # no config files
            config = self.config_mgr.load_config(self.config_mgr.default_config_path)
        self.apply_config(config)
        
        self.logger = SensorLogger(log_dir="logs", batch_size=20)
                    
        self._init_mqtt()
    
    def apply_config(self,config):
        tabs_config = config.get("tabs", {})
        self.interval_input.setValue(config.get("sampling_interval", 1))
        self.alert_method_combo.setCurrentText(config.get("alert_method", "Sound"))

        self.gyro_tab.apply_tab_config(tabs_config.get("Gyroscope", {}))
        self.temp_humid_tab.apply_tab_config(tabs_config.get("Temperature & Humidity", {}))
        self.light_tab.apply_tab_config(tabs_config.get("Light", {}))
        

    def load_default_config(self):
        self.config_mgr.load_config(self.config_mgr.default_config_path)        
    
    def load_config_file(self):
        if self.config_mgr.load_config(self.config_mgr.user_config_path):
            QMessageBox.information(self, "Config Loaded", "User config loaded successfully.")
        
    def save_config_file(self):
        if self.config_mgr.save_config(self.config_mgr.user_config_path):
            QMessageBox.information(self, "Config Saved", "Configuration saved.")
                
    def export_log_file(self):
        self.config_mgr.export_log_file()
            
    def clear_log(self):
        self.config_mgr.clear_log()        
    
    # def close(self):
    #     self.config_mgr.closeEvent()
    
    def _create_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")        
        # Load Default Config
        load_default_action = QAction("Load Default Config", self)
        load_default_action.triggered.connect(self.load_default_config)
        file_menu.addAction(load_default_action)

        # Open Config
        open_action = QAction("Open Config...", self)
        open_action.triggered.connect(self.load_config_file)
        file_menu.addAction(open_action)

        # Save Config
        save_action = QAction("Save Config", self)
        save_action.triggered.connect(self.save_config_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Export Log
        export_log_action = QAction("Export Log...", self)
        export_log_action.triggered.connect(self.export_log_file)
        file_menu.addAction(export_log_action)

        # Clear Log
        clear_log_action = QAction("Clear Log", self)
        clear_log_action.triggered.connect(self.clear_log)
        file_menu.addAction(clear_log_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        settings_menu = QMenu("Settings", self)
        # delete user_config.json and reloading default
        reset_action = QAction("Reset to Factory Defaults", self)
        reset_action.triggered.connect(self.reset_to_factory_defaults)
        settings_menu.addAction(reset_action)

        # OTA upgrading（Future to do）
        ota_action = QAction("OTA Firmware Upgrade (Coming Soon)", self)
        ota_action.setEnabled(False)
        settings_menu.addAction(ota_action)
        
        help_menu = QMenu("Help", self)

        about_action = QAction("About", self)
        about_action.triggered.connect(lambda: QMessageBox.information(
            self,
            "About IoT Monitor",
            "IoT Multi-Sensor Monitor v1.0\n\nDeveloped by Wilson\n© 2025"
        ))
        help_menu.addAction(about_action)

        # guiding information
        guide_action = QAction("User Guide (Coming Soon)", self)
        guide_action.setEnabled(False)
        help_menu.addAction(guide_action)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(settings_menu)
        menu_bar.addMenu(help_menu)
    
    def reset_to_factory_defaults(self):
        user_config = self.config_mgr.user_config_path
        if os.path.exists(user_config):
            os.remove(user_config)
        config = self.config_mgr.load_config(self.config_mgr.default_config_path)
        self.apply_config(config)
        QMessageBox.information(self, "Reset Complete", "Reset to factory defaults completed.")
    
    def update_mqtt_status(self, status_text):
        self.mqtt_status_text = status_text
        if "Connected" in status_text:
            self.mqtt_status_label.setStyleSheet("color: white; background-color: #32CD32; padding: 3px;")
            self.mqtt_status_label.setText("✅ " + status_text)
        elif "Connecting" in status_text:
            self.mqtt_status_label.setStyleSheet("color: black; background-color: #FFD700; padding: 3px;")
            self.mqtt_status_label.setText("⏳ " + status_text)
        else:
            self.mqtt_status_label.setStyleSheet("color: white; background-color: #FF6347; padding: 3px;")
            self.mqtt_status_label.setText("❌ " + status_text)
            
    def update_device_status(self, status_text):
        self.device_status_text = status_text
        if "Online" in status_text:
            self.device_status_label.setStyleSheet("color: white; background-color: #32CD32; padding: 3px;")
            self.device_status_label.setText("✅ " + status_text)
        elif "Offline" in status_text:
            self.device_status_label.setStyleSheet("color: white; background-color: #FF6347; padding: 3px;")
            self.device_status_label.setText("❌ " + status_text)            
        else:
            self.device_status_label.setStyleSheet("color: black; background-color: #FFD700; padding: 3px;")
            self.device_status_label.setText("⏳ " + status_text)

    def _refresh_status_bar(self):
        self.mqtt_status_label.setText(self.mqtt_status_text)
        self.device_status_label.setText(self.device_status_text)                        

    def _init_mqtt(self):
        try:
            self.mqtt_client = MQTTClient(
                on_message_callback = self._on_mqtt_message,                                          
                status_callback=self.update_mqtt_status,
                device_status_callback=self.update_device_status)
            
            self.mqtt_client.connect_and_subscribe()
            self.update_mqtt_status("MQTT Status: Connected")
        except Exception as e:
            print(f"[❌] MQTT Init Error: {e}")
            self.update_mqtt_status("MQTT Status: Failed")

    # def _on_mqtt_message(self, topic, payload, **kwargs):
    #     print(f"[MQTT] Message Received on {topic}: {payload}")
    #     # TODO: Parse and update the corresponding tab UI
    
    def _on_mqtt_message(self, topic, payload, **kwargs):
        try:
            data = json.loads(payload.decode())

            # update Gyroscope
            gx = float(data.get("gyro_x", 0))
            gy = float(data.get("gyro_y", 0))
            gz = float(data.get("gyro_z", 0))
            self.gyro_tab.labels["X Axis"].setText(f"X Axis: {gx:.3f}")
            self.gyro_tab.labels["Y Axis"].setText(f"Y Axis: {gy:.3f}")
            self.gyro_tab.labels["Z Axis"].setText(f"Z Axis: {gz:.3f}")
            self.gyro_tab.update_gyro_chart(gx, gy, gz)

            # update temp and humid
            temp = data.get("temperature")
            temp -= 10;
            humid = data.get("humidity")
            humid = humid * 100.0;
            if temp is not None and humid is not None:
                self.temp_humid_tab.labels["Temperature (°C)"].setText(f"Temperature (°C): {temp:.2f}")
                self.temp_humid_tab.labels["Humidity (%)"].setText(f"Humidity (%): {humid:.2f}")
                self.temp_humid_tab.update_temp_humid_chart(float(temp), float(humid))
                
                # if temp > self.temp_threshold:
                #     self.trigger_alert(f"Temperature too high: {temp:.2f}°C")
                        
            light = data.get("light")
            if light is not None:
                self.light_tab.labels["Light Intensity"].setText(f"Light Intensity: {int(light)} lux")
                self.light_tab.update_light_chart(float(light))

        except Exception as e:
            print(f"[❌] MQTT parse error: {e}")
            
    def start_data_collection(self):
        # send MQTT control message
        self.publish_control_command("START")
        self.drawing_paused = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_data_collection(self):
        self.publish_control_command("STOP")
        self.drawing_paused = True
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def publish_control_command(self, action):
        payload = json.dumps({"action": action})
        mqtt_topic = "device/control"
        self.mqtt_connection.publish(topic=mqtt_topic, payload=payload, qos=1)
        
    def trigger_alert(self, message):
        method = self.alert_method_combo.currentText()

        if "Sound" in method:
            self.trigger_sound_alert()

        if "Email" in method:
            self.trigger_email_alert(message)

        QMessageBox.warning(self, "Alert", message)  # Always display alert box
    
    def clear_alert(self):
        if self.alert_sound.isPlaying():
            self.alert_sound.stop()
    
    def trigger_sound_alert(self):
        self.alert_sound = QSoundEffect()
        sound_path = Path(__file__).parent / "alert.wav"
        self.alert_sound.setSource(QUrl.fromLocalFile(str(sound_path.resolve())))
        self.alert_sound.setVolume(0.9)
     
        @Slot()
        def on_loaded_changed():
            if self.alert_sound.isLoaded():
                print("✅ Sound loaded successfully!")
                self.alert_sound.play()
            else:
                print("❌ Failed to load sound.")

        self.alert_sound.loadedChanged.connect(on_loaded_changed)
        
        if self.alert_sound.isLoaded():
            self.alert_sound.play()
    
    # email alert for future
    def trigger_email_alert(self, message):
        return
                
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # save current config to file
            self.config_mgr.save_config(self.config_mgr.user_config_path)
            self.logger.flush()
            event.accept()
        else:
            event.ignore()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
