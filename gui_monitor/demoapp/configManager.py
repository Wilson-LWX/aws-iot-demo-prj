import os
import json
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

class ConfigManager:
    def __init__(self, window):
        self.window = window
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / "config"
        self.log_dir = self.base_dir / "logs"

        self.config_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        self.default_config_path = self.config_dir / "default_config.json"
        self.user_config_path = self.config_dir / "user_config.json"

    def load_config(self, path: Path):
        if path.exists():
            try:
                with open(path, "r") as f:
                    config = json.load(f)
                # self.apply_config(config)
                QMessageBox.information(self.window, "Config Loaded", f"Loaded config from {path.name}")
                return config
            except Exception as e:
                QMessageBox.warning(self.window, "Load Error", f"Failed to load config: {e}")
        else:
            filename = os.path.basename(path)
            if filename != "user_config.json":
                QMessageBox.warning(self.window, "File Not Found", f"Config file {path.name} not found.")

    def save_config(self, path: Path):
        try:
            config = self.collect_current_config()
            with open(path, "w") as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self.window, "Config Saved", f"Saved to {path.name}")
        except Exception as e:
            QMessageBox.warning(self.window, "Save Error", f"Failed to save config: {e}")

    def collect_current_config(self):
        return {
            "sampling_interval": self.window.interval_input.value(),
            "alert_method": self.window.alert_method_combo.currentText(),
            "tabs": {
                "Gyroscope": self.window.gyro_tab.get_tab_config(),
                "Temperature & Humidity": self.window.temp_humid_tab.get_tab_config(),
                "Light": self.window.light_tab.get_tab_config()
            }
        }

    def apply_config(self, config):
        try:
            self.window.interval_input.setValue(config.get("sampling_interval", 1))
            self.window.alert_method_combo.setCurrentText(config.get("alert_method", "None"))
            tab_thresholds = config.get("tabs", {})
            self.window.gyro_tab.threshold_input.setText(tab_thresholds.get("Gyroscope", {}).get("threshold", ""))
            self.window.temp_humid_tab.threshold_input.setText(tab_thresholds.get("Temperature & Humidity", {}).get("threshold", ""))
            self.window.light_tab.threshold_input.setText(tab_thresholds.get("Light", {}).get("threshold", ""))
            
        except Exception as e:
            QMessageBox.warning(self.window, "Apply Error", f"Failed to apply config: {e}")

    def log_alert(self, sensor, value, message):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "sensor": sensor,
            "value": value,
            "message": message
        }
        log_file = self.log_dir / f"alerts_{datetime.now().strftime('%Y-%m-%d')}.json"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Failed to write alert log: {e}")
    
    def export_log_file(self):
        import csv
        from PySide6.QtWidgets import QFileDialog

        log_path = Path("logs/alert_log.json")
        if not log_path.exists():
            QMessageBox.warning(self, "No Log", "No log file to export.")
            return

        with open(log_path, "r") as f:
            try:
                log_data = json.load(f)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read log file:\n{e}")
                return

        if not log_data:
            QMessageBox.information(self, "Empty Log", "No alert records to export.")
            return

        csv_path, _ = QFileDialog.getSaveFileName(self, "Export Log as CSV", "alerts.csv", "CSV Files (*.csv)")
        if csv_path:
            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Sensor", "Message"])
                for entry in log_data:
                    writer.writerow([entry.get("timestamp"), entry.get("sensor"), entry.get("message")])

            QMessageBox.information(self, "Exported", f"Alert log exported to:\n{csv_path}")
            
    def clear_log(self):
        log_path = Path("logs/alert_log.json")
        if log_path.exists():
            try:
                log_path.write_text("[]")
                QMessageBox.information(self, "Cleared", "Alert log has been cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear log:\n{e}")
        else:
            QMessageBox.information(self, "No Log", "No log file found to clear.")




