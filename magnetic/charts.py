import matplotlib.pyplot as plt
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
	
	def setAxis(self):
		# Setting X-axis
		self.axis_x = QtChart.QValueAxis()
		self.axis_x.setTickCount(11)
		self.axis_x.setLabelFormat("%.1f")
		self.axis_x.setTitleText(self.labelx)
		self.axis_x.setRange(0, 600)
		self.addAxis(self.axis_x, QtCore.Qt.AlignBottom)

		# Setting Y-axis
		self.axis_y = QtChart.QValueAxis()
		self.axis_y.setTickCount(11)
		self.axis_y.setRange(-35, 35)
		self.axis_y.setLabelFormat("%.1f")
		self.axis_y.setTitleText(self.labely)
		self.addAxis(self.axis_y, QtCore.Qt.AlignLeft)

	def add_series(self, name):
		series = QtChart.QLineSeries()
		series.setName(name)
		# series.setMarkerSize(5)
		# series.setBorderColor(series.pen().color())
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
		self.x += 1
		r = self.x - 1
		index = self.model.createIndex(r, 0)
		y = self.model.data(index, role=QtCore.Qt.DisplayRole)
		print(index.row(), index.column(), y)
		print(self.model.fetch_data())
		self.series.append(float(self.x), float(y))

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
		self._chart = ScatterChart(title="Scatter Chart",
								   labelx="T, ms",
								   labely="H, uT")
		self.setChart(self._chart)

		self.setRenderHint(QPainter.Antialiasing)
		# self.setRubberBand(QChartView.RectangleRubberBand)
		# self.setCursor(QtCore.Qt.SizeAllCursor)

		self.mappers = {}

	def set_model(self, model):
		self.model = model

	def add_graph(self, name, model=None, xcol=None, ycol=None):
		self._chart.add_series(name)

		if model:
			# mapper = QVXYModelMapper()
			# mapper.setXColumn(xcol)
			# mapper.setYColumn(ycol)
			# mapper.setModel(self.model)
			# mapper.setSeries(self._chart.series()[-1])
			# self.mappers[name] = mapper
			mapper = TimeModelMapper()
			mapper.setModel(self.model)
			mapper.setSeries(self._chart.series()[-1])
			self.mappers[name] = mapper

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


class MatplotlibChart:
	""" TODO: Create widget with matplotlib """
	
	@staticmethod
	def plot(dataset_base, dataset_finish=None, *, frame='decart'):
		""" This function used to draw  """
		
		fig, ax = plt.subplots()
		fig.set_size_inches(8.5, 8.5)
		
		ax.set(xlabel='B, uT', ylabel='C, uT',
		       title='Magnetic ellips')
		
		x = [x for (x, _) in dataset_base]
		y = [y for (_, y) in dataset_base]
		ax.scatter(x, y, marker='.')
		
		if dataset_finish:
			xc = [x for (x, _) in dataset_finish]
			yc = [y for (_, y) in dataset_finish]
			ax.plot(xc, yc, marker='.', color='red')
		
		ax.grid()
		# fig.savefig("test.png")
		plt.show()
