from PyQt5 import QtChart, QtCore
from PyQt5.QtChart import QChartView, QChart, QVXYModelMapper
from PyQt5.QtGui import QPainter


class ScatterChart(QChart):
	def __init__(self, title='', labelx='x', labely='y', flags=None, *args, **kwargs):
		super().__init__(flags, *args, **kwargs)
		
		self.labelx = labelx
		self.labely = labely
		
		self.setTitle(title)
		self.setAnimationOptions(QChart.NoAnimation)
		self.setAxis()

		self.series_ = series = QtChart.QLineSeries()
	
	def setAxis(self):
		# Setting X-axis
		self.axis_x = QtChart.QValueAxis()
		self.axis_x.setTickCount(11)
		self.axis_x.setLabelFormat("%.0f")
		self.axis_x.setTitleText(self.labelx)
		self.axis_x.setRange(0, 600)
		self.addAxis(self.axis_x, QtCore.Qt.AlignBottom)

		# Setting Y-axis
		self.axis_y = QtChart.QValueAxis()
		self.axis_y.setTickCount(10)
		self.axis_y.setRange(-45, 45)
		self.axis_y.setLabelFormat("%.1f")
		self.axis_y.setTitleText(self.labely)
		self.addAxis(self.axis_y, QtCore.Qt.AlignLeft)

	def add_series(self, name):
		self.series_ = series = QtChart.QLineSeries()
		series.setName(name)
		self.addSeries(series)
		series.attachAxis(self.axis_x)
		series.attachAxis(self.axis_y)

	def remove_series(self, name):
		for s in self.series():
			if s.name() == name:
				self.removeSeries(s)


class TimeModelMapper:
	x = 0

	def _update(self):
		""" This method used to update series"""
		self.x += 1
		row = self.x - 1
		index = self.model.createIndex(row, 0)
		y = self.model.data(index, role=QtCore.Qt.DisplayRole)
		self.series.append(float(self.x), float(y))

		if len(self.series.pointsVector()) > 600:
			self.series.clear()

	def setModel(self, model):
		self.model = model
		self.model.rowsInserted.connect(self._update)

	def setYColumn(self, col):
		self.ycol = col

	def setSeries(self, series):
		self.series = series


class TimeGraph(QChartView):
	def __init__(self, parent=None, model=None, *__args):
		super().__init__(*__args)

		# Store chart in variable because for support autocomplete
		self._chart = ScatterChart(labelx="T, ms",
								   labely="H, uT")
		self.setChart(self._chart)
		self.setRenderHint(QPainter.Antialiasing)
		# self.setRubberBand(QChartView.RectangleRubberBand)
		#self.setCursor(QtCore.Qt.SizeAllCursor)

		self.mappers = {}

	def setModel(self, model):
		self.model = model

	def add_graph(self, name, model=None, xcol=None, ycol=None):
		self._chart.add_series(name)

		if model:
			mapper = TimeModelMapper()
			mapper.setModel(self.model)
			mapper.setSeries(self._chart.series()[-1])
			self.mappers[name] = mapper

			# mapper = QVXYModelMapper()
			# mapper.setXColumn(xcol)
			# mapper.setYColumn(ycol)
			# mapper.setModel(self.model)
			# mapper.setSeries(self._chart.series()[-1])
			# self.mappers[name] = mapper
			# self.model.cell_color = "{}".format(self._chart.series()[-1].color().name())

	def redraw(self):
		pass

	def clear_area(self):
		self._chart.removeAllSeries()


class EllipsoidGraph(QChartView):
	""" The chart widget is widget that display magnetic chart """

	def __init__(self, parent=None, model=None, *__args):
		super().__init__(*__args)
		# Store chart in variable because for support autocomplete
		self._chart = ScatterChart(title="Scatter Chart",
								   labelx="Hx, uT",
								   labely="Hy, uT")
		self.setChart(self._chart)
		
		self.setRenderHint(QPainter.Antialiasing)
		# self.setRubberBand(QChartView.RectangleRubberBand)
		# self.setCursor(QtCore.Qt.SizeAllCursor)
		
		self.models = {}
		self.mappers = {}
	
	def set_model(self, model):
		self.model = model

	def add_graph(self, name, model=None, xcol=None, ycol=None):
		self._chart.add_series(name)
		
		if model:
			mapper = QVXYModelMapper()
			mapper.setXColumn(0)
			mapper.setYColumn(1)
			mapper.setModel(self.model)
			mapper.setSeries(self._chart.series()[-1])
			self.mappers[name] = mapper

		self.model.cell_color = "{}".format(self._chart.series()[-1].color().name())

	def remove_graph(self, name):
		pass

	def clear_area(self):
		self._chart.removeAllSeries()

	def redraw(self):
		series = self._chart.series()[0]
		points = series.pointsVector()
		if points:
			x = points[-1].x()
			self._chart.scroll(1, 0)
			self._chart.axis_x.setRange(0, x)
		pass

	def mouseMoveEvent(self, event):
		super().mouseMoveEvent(event)
		x = self._chart.mapToValue(event.pos()).x()
		y = self._chart.mapToValue(event.pos()).y()
