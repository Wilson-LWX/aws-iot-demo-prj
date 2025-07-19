from PySide6.QtCore import QDateTime, Qt
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis


class TimeSeriesPlotDualAxis:
    def __init__(self, title="Temp & Humidity", left_label="°C", right_label="%", left_range=(0, 60), right_range=(0, 100), max_points=60):
        self.temp_series = QLineSeries()
        self.humid_series = QLineSeries()

        self.data_points = []  # [(timestamp, temp, humid)]
        self.max_points = max_points

        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.addSeries(self.temp_series)
        self.chart.addSeries(self.humid_series)
        self.chart.legend().setVisible(True)

        # X - Time
        self.time_axis = QDateTimeAxis()
        self.time_axis.setFormat("HH:mm:ss")
        self.time_axis.setTitleText("Time")
        self.chart.addAxis(self.time_axis, Qt.AlignBottom)
        self.temp_series.attachAxis(self.time_axis)
        self.humid_series.attachAxis(self.time_axis)

        # Y - Left - Temperature
        self.left_axis = QValueAxis()
        self.left_axis.setRange(*left_range)
        self.left_axis.setTitleText(left_label)
        self.chart.addAxis(self.left_axis, Qt.AlignLeft)
        self.temp_series.attachAxis(self.left_axis)

        # Y - Right - Humidity
        self.right_axis = QValueAxis()
        self.right_axis.setRange(*right_range)
        self.right_axis.setTitleText(right_label)
        self.chart.addAxis(self.right_axis, Qt.AlignRight)
        self.humid_series.attachAxis(self.right_axis)

        self.chart_view = QChartView(self.chart)

    def append(self, temp_value, humid_value):
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.data_points.append((now, temp_value, humid_value))
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)

        self.temp_series.clear()
        self.humid_series.clear()
        for t, temp, humid in self.data_points:
            self.temp_series.append(t, temp)
            self.humid_series.append(t, humid)

        if self.data_points:
            # start = QDateTime.fromMSecsSinceEpoch(self.data_points[0][0])
            # end = QDateTime.fromMSecsSinceEpoch(self.data_points[-1][0])
            # self.time_axis.setRange(start, end)
            current_time = QDateTime.currentDateTime()
            start_time = current_time.addSecs(-60)
            self.time_axis.setRange(start_time, current_time)
