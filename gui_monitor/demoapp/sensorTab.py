import re

from PySide6.QtWidgets import (
    QWidget, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel
)

from PySide6.QtCore import Qt
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QColor
from collections import deque

from time_series_plot import TimeSeriesPlot
from time_series_plot_dual import TimeSeriesPlotDualAxis
from time_series_multi_plot_timestamp import TimeSeriesMultiPlotTimestamp


class SensorTab(QWidget):
    def __init__(self, sensor_name, fields, main_window=None, config=None):
        super().__init__()
        self.sensor_name = sensor_name
        self.main_window = main_window
        self.labels = {}
        
        layout = QVBoxLayout()
        if sensor_name == "Gyroscope":
            # self._init_chart()
            # layout.addWidget(self.chart_view)
            # self.gyro_plot = TimeSeriesPlot(title="Gyroscope", y_label="°/s", y_range=(-5, 5))
            # layout.addWidget(self.gyro_plot.chart_view)
    
            self.gyro_plot = TimeSeriesMultiPlotTimestamp(
            title="Gyroscope", y_label="°/s", y_range=(-5, 5)
            )
            layout.addWidget(self.gyro_plot.chart_view)
        
        if sensor_name == "Temperature & Humidity":
            # self._init_temp_humidity_chart()
            # layout.addWidget(self.temp_chart_view)
            self.temp_humid_plot = TimeSeriesPlotDualAxis()
            layout.addWidget(self.temp_humid_plot.chart_view)
                                
        if sensor_name == "Light":
            # self._init_light_chart()
            # layout.addWidget(self.light_chart_view)
            self.light_plot = TimeSeriesPlot(title="Light", y_label="Lux", y_range=(0, 500), max_points=100, color="red")
            layout.addWidget(self.light_plot.chart_view)
            
        grid = QGridLayout()
        for i, field in enumerate(fields):
            label = QLabel(f"{field}: --")
            label.setAlignment(Qt.AlignCenter)
            self.labels[field] = label
            grid.addWidget(label, i // 2, i % 2)
        layout.addLayout(grid)

        # control_layout = QHBoxLayout()
        # self.interval_input = QSpinBox()
        # self.interval_input.setRange(1, 3600)
        # self.interval_input.setValue(1)
        # control_layout.addWidget(QLabel("Sampling Interval (s):"))
        # control_layout.addWidget(self.interval_input)
        
        threshold_layout = QHBoxLayout()
        self.threshold_valid = False
        self.threshold_input = QLineEdit()
        if sensor_name == "Gyroscope":
            self.threshold_input.setPlaceholderText("X > 1.0 or Y > 1.5 or Z > 2.0")
        if sensor_name == "Temperature & Humidity":
            self.threshold_input.setPlaceholderText("T > 50 and H > 80")
        if sensor_name == "Light":
            self.threshold_input.setPlaceholderText("L < 50")
        
        self.alert_enabled_checkbox = QCheckBox("Enable Alerts")
        self.alert_enabled_checkbox.setChecked(False)
                           
        # self.set_threshold_button = QPushButton("Set Alarm Threshold")
        # self.set_threshold_button.clicked.connect(self.validate_threshold)
        # self.threshold_input.editingFinished.connect(self.validate_threshold)
        
        self.threshold_input.editingFinished.connect(self.validate_threshold)
        
        #count variables for alerting
        self.threshold_breach_count = 0
        self.breach_required = 3  # trigger warning if breached 3 or more
        self.alert_active = False
        #count variables for cancel alerting
        self.recovery_count = 0
        self.recovery_required = 3

        if sensor_name == "Temperature & Humidity":
            self.threshold_input.setToolTip("Enter threshold values (e.g., T>30, H<20). Use 'T' for temperature, 'H' for humidity.")
        elif sensor_name == "Gyroscope":
            self.threshold_input.setToolTip("Enter a numeric threshold for axis values (e.g., X>1.5). Use 'X', 'Y', 'Z' for axes.")
        elif sensor_name == "Light":
            self.threshold_input.setToolTip("Enter a numeric light threshold value (e.g., L>300). Use 'L' for light.")
        else:
            self.threshold_input.setToolTip("Enter a numeric threshold value. Alarm will be triggered when sensor data exceeds this value.")
                    
        threshold_layout.addWidget(self.threshold_input)
        threshold_layout.addWidget(self.alert_enabled_checkbox)
        layout.addLayout(threshold_layout)

        self.setLayout(layout)
    
    def _init_chart(self):
        self.chart = QChart()
        self.series_x = QLineSeries(name="X Axis")
        self.series_y = QLineSeries(name="Y Axis")
        self.series_z = QLineSeries(name="Z Axis")
        self.chart.addSeries(self.series_x)
        self.chart.addSeries(self.series_y)
        self.chart.addSeries(self.series_z)

        self.axis_x = QValueAxis()
        self.axis_x.setRange(0, 50)
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTitleText("Sample Index")

        self.axis_y = QValueAxis()
        self.axis_y.setRange(-5, 5)
        self.axis_y.setTitleText("Gyro Value")

        # append X,Y axis
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        self.series_x.attachAxis(self.axis_x)
        self.series_y.attachAxis(self.axis_x)
        self.series_z.attachAxis(self.axis_x)

        self.series_x.attachAxis(self.axis_y)
        self.series_y.attachAxis(self.axis_y)
        self.series_z.attachAxis(self.axis_y)
        
        self.chart_view = QChartView(self.chart)

        # 50 samping point data to display
        self.gyro_x_data = deque(maxlen=50)
        self.gyro_y_data = deque(maxlen=50)
        self.gyro_z_data = deque(maxlen=50)
        self.sample_index = 0
        
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignTop)

        self.chart.setTitle("Gyroscope Realtime Data")
        self.chart.setTheme(QChart.ChartThemeLight)  # ChartThemeDark
        self.chart.setBackgroundBrush(Qt.white)

        self.series_x.setColor(Qt.red)
        self.series_y.setColor(Qt.green)
        self.series_z.setColor(Qt.blue)

    def update_gyro_chart(self, x, y, z):
        self.main_window.logger.log("Gyroscope", "X", x)
        self.main_window.logger.log("Gyroscope", "Y", y)
        self.main_window.logger.log("Gyroscope", "Z", z)
        if hasattr(self, "gyro_plot"):
            self.gyro_plot.append(x, y, z)  # or self.gyro_plot.append([x, y, z])
            

        # self.sample_index += 1
        
        # self.gyro_x_data.append((self.sample_index, x))
        # self.gyro_y_data.append((self.sample_index, y))
        # self.gyro_z_data.append((self.sample_index, z))
        
        # self.series_x.clear()
        # self.series_x.append([QPointF(idx, val) for idx, val in self.gyro_x_data])

        # self.series_y.clear()
        # self.series_y.append([QPointF(idx, val) for idx, val in self.gyro_y_data])

        # self.series_z.clear()
        # self.series_z.append([QPointF(idx, val) for idx, val in self.gyro_z_data])
        
        # latest_index = self.sample_index
        # start_index = max(0, latest_index - 50)
        # self.axis_x.setRange(start_index, latest_index)               
        #self.chart_view.repaint()
        #self.chart.update()
        
        # check if warning threshold met
        self.check_threshold(X=x, Y=y, Z=z)
        # if self.threshold_valid and self.threshold_input.text():                        
        #     try:
        #         local_vars = {
        #             "X": gx,
        #             "Y": gy,
        #             "Z": gz
        #         }
        #         if eval(self.threshold_input.text(), {}, local_vars):
        #             self.raise_alert("Gyroscope alert triggered!")
        #     except Exception as e:
        #         print("Gyro threshold evaluation error:", e)

    def _init_temp_humidity_chart(self):
        self.temp_chart = QChart()
        self.temp_chart.setTitle("Temperature & Humidity Realtime Data")

        self.temp_series = QLineSeries(name="Temperature (°C)")
        self.humid_series = QLineSeries(name="Humidity (%)")

        self.temp_series.setColor(Qt.red)
        self.humid_series.setColor(Qt.blue)

        self.temp_chart.addSeries(self.temp_series)
        self.temp_chart.addSeries(self.humid_series)

        # axis X (Shared)
        self.axis_x_temp = QValueAxis()
        self.axis_x_temp.setRange(0, 50)
        self.axis_x_temp.setTitleText("Sample Index")
        self.axis_x_temp.setLabelFormat("%d")

        # axis Y Left（temperature）
        self.axis_y_temp = QValueAxis()
        self.axis_y_temp.setRange(0, 50)
        self.axis_y_temp.setTitleText("Temperature (°C)")

        # axis Y Right (humidity）
        self.axis_y_humid = QValueAxis()
        self.axis_y_humid.setRange(0, 100)
        self.axis_y_humid.setTitleText("Humidity (%)")

        self.temp_chart.addAxis(self.axis_x_temp, Qt.AlignBottom)
        self.temp_chart.addAxis(self.axis_y_temp, Qt.AlignLeft)
        self.temp_chart.addAxis(self.axis_y_humid, Qt.AlignRight)

        # bind
        self.temp_series.attachAxis(self.axis_x_temp)
        self.temp_series.attachAxis(self.axis_y_temp)

        self.humid_series.attachAxis(self.axis_x_temp)
        self.humid_series.attachAxis(self.axis_y_humid)

        self.temp_chart.legend().setVisible(True)

        self.temp_chart_view = QChartView(self.temp_chart)

        # cache data point 50
        self.temp_data = deque(maxlen=50)
        self.humid_data = deque(maxlen=50)
        self.temp_sample_index = 0
    
    def update_temp_humid_chart(self, temp, humid):        
        
        self.main_window.logger.log("Temperature & Humidity", "Temperature", temp)
        self.main_window.logger.log("Temperature & Humidity", "Humidity", humid)
        
        self.temp_humid_plot.append(temp, humid)

        # self.temp_sample_index += 1                
        # self.temp_data.append(QPointF(self.temp_sample_index, temp))
        # self.humid_data.append(QPointF(self.temp_sample_index, humid))

        # self.temp_series.replace(list(self.temp_data))
        # self.humid_series.replace(list(self.humid_data))

        # start = max(0, self.temp_sample_index - 50)
        # self.axis_x_temp.setRange(start, self.temp_sample_index)
        
        self.check_threshold(T=temp, H=humid)
        
        # if self.threshold_valid and self.threshold_input.text():                        
        #     try:
        #         local_vars = {"T": temp, "H": humid}
        #         if eval(self.threshold_input.text(), {}, local_vars):
        #             self.trigger_alert("Temperature/Humidity exceeds threshold!")
        #     except Exception as e:
        #         print("Evaluation error:", e)
    
    def _init_light_chart(self):
        self.light_chart = QChart()
        self.light_chart.setTitle("Light Intensity Realtime Data")

        self.light_series = QLineSeries(name="Light (Lux)")
        self.light_series.setColor(Qt.magenta)
        
        self.light_chart.addSeries(self.light_series)

        self.axis_x_light = QValueAxis()
        self.axis_x_light.setRange(0, 50)
        self.axis_x_light.setTitleText("Sample Index")
        self.axis_x_light.setLabelFormat("%d")

        self.axis_y_light = QValueAxis()
        self.axis_y_light.setRange(0, 300) 

        self.axis_y_light.setTitleText("Light (Lux)")

        self.light_chart.addAxis(self.axis_x_light, Qt.AlignBottom)
        self.light_chart.addAxis(self.axis_y_light, Qt.AlignLeft)

        self.light_series.attachAxis(self.axis_x_light)
        self.light_series.attachAxis(self.axis_y_light)

        self.light_chart_view = QChartView(self.light_chart)

        self.light_data = deque(maxlen=50)
        self.light_index = 0
        
    def update_light_chart(self, lux_value):
        self.main_window.logger.log("Light", "L", lux_value)
        if hasattr(self, "light_plot"):
            self.light_plot.append(lux_value)
                
        # self.light_index += 1
        
        # self.main_window.logger.log("Light", "L", light)
        
        # self.light_data.append(QPointF(self.light_index, lux_value))

        # self.light_series.replace(list(self.light_data))

        # start = max(0, self.light_index - 50 + 1)
        # self.axis_x_light.setRange(start, self.light_index)
        
        # warning threshold check        
        self.check_threshold(L=lux_value)
        # if self.threshold_valid and self.threshold_input.text():                        
        #     try:
        #         local_vars = {
        #             "L": light_value
        #         }
        #         if eval(self.threshold_input.text(), {}, local_vars):
        #             self.trigger_alert("Light intensity alert triggered!")
        #     except Exception as e:
        #         print("Light threshold evaluation error:", e)

    # def validate_threshold(self):
    #     text = self.threshold_input.text().strip()
    #     valid = False

    #     if self.sensor_name == "Temperature & Humidity":
    #         pattern = r"^(T[<>]=?\d+(\.\d+)?)(,\s*H[<>]=?\d+(\.\d+)?)?$"
    #         valid = bool(re.match(pattern, text))
    #     elif self.sensor_name == "Gyroscope":
    #         pattern = r"^[XYZ][<>]=?-?\d+(\.\d+)?$"
    #         valid = bool(re.match(pattern, text))
    #     elif self.sensor_name == "Light":
    #         pattern = r"^L[<>]=?\d+(\.\d+)?$"
    #         valid = bool(re.match(pattern, text))
    #     else:
    #         pattern = r"^[A-Za-z]?[<>]=?\d+(\.\d+)?$"
    #         valid = bool(re.match(pattern, text))

    #     if valid:
    #         QMessageBox.information(self, "Threshold Set", "Threshold format is valid.")
    #     else:
    #         QMessageBox.warning(self, "Invalid Format", "Please enter a valid threshold format based on the sensor type.")
    
    # def validate_threshold(self):
    #     text = self.threshold_input.text().strip()
    #     valid = False

    #     allowed_vars = {
    #         "Temperature & Humidity": {"T", "H"},
    #         "Gyroscope": {"X", "Y", "Z"},
    #         "Light": {"L"},
    #     }

    #     vars_in_tab = allowed_vars.get(self.sensor_name, set())

    #     try:
    #         expr = text.replace("and", " and ").replace("or", " or ")
    #         tokens = re.split(r'(\s+|\band\b|\bor\b|\(|\))', expr)
    #         filtered = []

    #         for token in tokens:
    #             token = token.strip()
    #             if not token:
    #                 continue
    #             if token in {"and", "or", "(", ")"}:
    #                 filtered.append(token)
    #             elif re.fullmatch(r"[A-Za-z]", token):
    #                 if token not in vars_in_tab:
    #                     raise ValueError(f"Invalid variable '{token}'")
    #                 filtered.append(token)
    #             elif re.fullmatch(r"[><=!]=?|[\d\.]+", token):
    #                 filtered.append(token)
    #             else:
    #                 raise ValueError(f"Invalid token: {token}")

    #         test_env = {v: 50 for v in vars_in_tab}
    #         eval(" ".join(filtered), {}, test_env)
    #         valid = True

    #     except Exception as e:
    #         print(f"[VALIDATE ERROR] {e}")
    #         valid = False

    #     if valid:
    #         QMessageBox.information(self, "Threshold Set", "Threshold format is valid.")
    #     else:
    #         QMessageBox.warning(self, "Invalid Format", "Please enter a valid threshold format, e.g. T > 50 and H < 80")

    def validate_threshold(self):
        text = self.threshold_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Input Error", "Threshold expression cannot be empty.")
            return

        if self.sensor_name == "Temperature & Humidity":
            allowed_vars = {"T", "H"}
        elif self.sensor_name == "Gyroscope":
            allowed_vars = {"X", "Y", "Z"}
        elif self.sensor_name == "Light":
            allowed_vars = {"L"}
        else:
            allowed_vars = {"A", "B", "C"} # later extended branch

        # def tokenize_expression(expr):
        #     token_pattern = r"[A-Za-z]+|>=|<=|==|!=|>|<|\d+(?:\.\d+)?|\(|\)|and|or"
        #     return re.findall(token_pattern, expr)
        
        def tokenize_expression(expr):
            # supports expressions that do not contain spaces
            token_pattern = r"(>=|<=|==|!=|>|<)|([A-Za-z]+)|(\d+(?:\.\d+)?)|(\()|(\))|(and|or)"
            # Flatten all groups and filter out empty entries
            raw_tokens = re.findall(token_pattern, expr)
            tokens = [item for group in raw_tokens for item in group if item]
            return tokens

        tokens = tokenize_expression(text)

        valid = True
        for token in tokens:
            token = token.strip()
            if token in {"and", "or", "(", ")"}:
                continue
            elif re.fullmatch(r"[A-Za-z]+", token):
                if token not in allowed_vars:
                    valid = False
                    QMessageBox.warning(self, "Invalid Variable", f"Variable '{token}' is not allowed in this sensor.")
                    break
            elif re.fullmatch(r"[><=!]=?", token):
                continue
            elif re.fullmatch(r"\d+(\.\d+)?", token):
                continue
            else:
                valid = False
                QMessageBox.warning(self, "Invalid Token", f"Token '{token}' is invalid.")
                break
        
        self.threshold_valid = valid

        if valid:
            # QMessageBox.information(self, "Threshold Set", "Threshold format is valid.")
            self.alert_enabled_checkbox.setChecked(True)
            
    def check_threshold(self, **sensor_vars):
        if self.alert_enabled_checkbox.isChecked() and self.threshold_valid:
            try:
                expr = self.threshold_input.text().strip()
                if not expr:
                    return
                if eval(expr, {}, sensor_vars):
                    self.threshold_breach_count += 1
                    self.recovery_count = 0
                    if self.threshold_breach_count >= self.breach_required and not self.alert_active:
                        if self.main_window:
                            self.alert_active = True
                            self.main_window.trigger_alert(f"{self.sensor_name} exceeds threshold!")
                else:
                    self.threshold_breach_count = 0
                    if self.alert_active:
                        self.recovery_count += 1
                        if self.recovery_count >= self.recovery_required:
                            self.alert_active = False
                            self.main_window.clear_alert()
                            print(f"{self.sensor_name} recovered. Alert cleared.")
                                                    
            except Exception as e:
                print(f"[ALERT] Evaluation error in {self.sensor_name}:", e)
        else:
            return  
                  
    def apply_tab_config(self, config):
        """
        Apply alarm settings from config dict.
        config format:
        {
            "alarm_enabled": bool,
            "alarm_thresholds": list of float
        }
        """
        self.alert_enabled_checkbox.setChecked(config.get("enabled", False))
        threshold_expr = config.get("threshold", "")
        if hasattr(self, 'threshold_input') and isinstance(self.threshold_input, QLineEdit):
            self.threshold_input.setText(str(threshold_expr))
    
    def get_tab_config(self):
        return {
            "threshold": self.threshold_input.text().strip(),
            "enabled": self.alert_enabled_checkbox.isChecked()
        }
