import matplotlib.pyplot as plt
from PyQt5 import QtChart, QtCore
from PyQt5.QtChart import QChartView, QChart, QVXYModelMapper
from PyQt5.QtGui import QPainter


class ChartWidget(QChartView):
	""" The chart widget is widget that display magnetic chart """

	def __init__(self, parent=None, model=None, *__args):
		super().__init__(*__args)
		# Store chart in variable because for support autocomplete
		self._chart = QChart()
		self._chart.setAnimationOptions(QChart.NoAnimation)

		self.setChart(self._chart)
		self.setRenderHint(QPainter.Antialiasing)

		self.setAxis()

		self.models = {}

	def setModel(self, name, model):
		self.series = QtChart.QScatterSeries()
		self.series.setName(name)

		self.mapper = QVXYModelMapper()
		self.mapper.setXColumn(0)
		self.mapper.setYColumn(1)
		self.mapper.setModel(model)
		self.mapper.setSeries(self.series)
		self._chart.addSeries(self.series)

		self.series.attachAxis(self.axis_x)
		self.series.attachAxis(self.axis_y)

		# TODO: Make different color
		model.color = "{}".format(self.series.pen().color().name())

	def setAxis(self):
		# Setting X-axis
		self.axis_x = QtChart.QValueAxis()
		self.axis_x.setTickCount(10)
		self.axis_x.setLabelFormat("%.2f")
		self.axis_x.setTitleText("Hz, uT")
		self.axis_x.setRange(-25, 25)
		self._chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)

		# Setting Y-axis
		self.axis_y = QtChart.QValueAxis()
		self.axis_y.setTickCount(10)
		self.axis_y.setRange(-25, 25)
		self.axis_y.setLabelFormat("%.2f")
		self.axis_y.setTitleText("Hy, uT")
		self._chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)


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
