from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis

class TimeSeriesPlot:
    def __init__(self, title: str, y_label: str = "", y_range=(0, 100), max_points=60, color="blue"):
        self.series = QLineSeries()
        self.series.setPen(QPen(QColor(color), 2))
        self.max_points = max_points
        self.data_points = []
        
        # Chart + Series
        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.addSeries(self.series)
        self.chart.legend().hide()

        # X axis: time
        self.time_axis = QDateTimeAxis()
        self.time_axis.setFormat("HH:mm:ss")
        self.time_axis.setTitleText("Time")
        self.chart.addAxis(self.time_axis, Qt.AlignBottom)
        self.series.attachAxis(self.time_axis)

        # Y axis
        self.value_axis = QValueAxis()
        self.value_axis.setRange(*y_range)
        self.value_axis.setTitleText(y_label)
        self.chart.addAxis(self.value_axis, Qt.AlignLeft)
        self.series.attachAxis(self.value_axis)

        # View
        self.chart_view = QChartView(self.chart)

    def append(self, y_value):
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.data_points.append((now, y_value))
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)

        self.series.clear()
        for x_val, y_val in self.data_points:
            self.series.append(x_val, y_val)

        # Set visible X range (scrolling)
        if self.data_points:
            # start_time = QDateTime.fromMSecsSinceEpoch(self.data_points[0][0])
            # end_time = QDateTime.fromMSecsSinceEpoch(self.data_points[-1][0])
            # self.time_axis.setRange(start_time, end_time)
            current_time = QDateTime.currentDateTime()
            start_time = current_time.addSecs(-60)
            self.time_axis.setRange(start_time, current_time)
