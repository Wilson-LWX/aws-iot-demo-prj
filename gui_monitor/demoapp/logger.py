import os
import csv
from datetime import datetime

class SensorLogger:
    def __init__(self, log_dir="logs", batch_size=20):
        if not os.path.isabs(log_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(base_dir, log_dir)
        self.log_dir = log_dir
        self.batch_size = batch_size
        self.log_buffer = []
        self.log_file_path = self._init_daily_log()

    def _init_daily_log(self):
        today = datetime.now().strftime("%Y-%m-%d")
        os.makedirs(self.log_dir, exist_ok=True)
        path = os.path.join(self.log_dir, f"log_{today}.csv")

        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write("timestamp,sensor,field,value\n")
        return path

    def log(self, sensor_name, field, value):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_buffer.append((timestamp, sensor_name, field, value))

        if len(self.log_buffer) >= self.batch_size:
            self.flush()

    def flush(self):
        if not self.log_buffer:
            return

        try:
            with open(self.log_file_path, "a", newline="", encoding="utf-8") as f:
                for row in self.log_buffer:
                    f.write(",".join(map(str, row)) + "\n")
            self.log_buffer.clear()
        except Exception as e:
            print(f"[Log Error] Failed to flush log: {e}")
