from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QPen, QColor, QPainter 
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis


class TimeSeriesMultiPlotTimestamp:
    def __init__(self, title="Sensor", y_label="", y_range=(-10, 10), labels=("X", "Y", "Z"), colors=None):
        if colors is None:
            colors = ["red", "green", "blue"]

        self.series_list = []

        self.chart = QChart()
        self.chart.setTitle(title)

        # axis of Time
        self.axis_x = QDateTimeAxis()
        self.axis_x.setTitleText("Time")
        self.axis_x.setFormat("HH:mm:ss")
        self.axis_x.setTickCount(5)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)

        # axis of Y
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText(y_label)
        self.axis_y.setRange(*y_range)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        # three axis plot
        for i, label in enumerate(labels):
            series = QLineSeries()
            series.setName(label)
            series.setPen(QPen(QColor(colors[i]), 2))
            self.chart.addSeries(series)
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)
            self.series_list.append(series)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

    def append(self, x_val, y_val, z_val):
        current_time = QDateTime.currentDateTime()
        timestamp_ms = current_time.toMSecsSinceEpoch()

        values = [x_val, y_val, z_val]
        for i in range(3):
            self.series_list[i].append(timestamp_ms, values[i])
            if self.series_list[i].count() > 100:
                self.series_list[i].removePoints(0, 1)

        # Only display recent 60 seconds
        start_time = current_time.addSecs(-60)
        self.axis_x.setRange(start_time, current_time)
