import sys

from PyQt5 import QtCore, uic, QtChart
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtChart import QChart, QChartView

from magnetic.algorithms import Algorithm
from magnetic.models import SensorDataModel
from magnetic.util import from_excel, plot


# NOTE: Uncomment if use QtDesigner file as Ui
# from magnetic.ui import magnetic_ui

class Ui(QMainWindow):
	""" This class describe graphical user interface """
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def setupUi(self):
		self.setWindowTitle(f"{__file__}")
		self.setMinimumSize(600, 500)
		
		# Widgets
		centralWidget = QWidget(self)

		# Top widget
		self.label = QLabel("Filename:", centralWidget)
		self.edit = QLineEdit(centralWidget)
		self.edit.setReadOnly(True)
		self.edit.setObjectName('edit')

		self.buttons = {}
		btn = QPushButton("Open...", centralWidget)
		btn.setObjectName('open')
		self.buttons['open'] = btn

		splitter = QSplitter(QtCore.Qt.Horizontal, centralWidget)
		self.table = self.createTable(splitter)
		splitter.addWidget(self.table)

		self.chart, self.chartview = self.createChart(splitter)
		splitter.addWidget(self.chartview)

		# Layout
		centralLayout = QVBoxLayout(centralWidget)
		self.setCentralWidget(centralWidget)

		pathLayout = QHBoxLayout()
		pathLayout.addWidget(self.label)
		pathLayout.addWidget(self.edit)
		pathLayout.addWidget(self.buttons['open'])

		centralLayout.addLayout(pathLayout)
		centralLayout.addWidget(splitter)

	def createTable(self, parent):
		view = QTableView(parent)
		
		view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
		view.horizontalHeader().setSectionsMovable(True)
		view.horizontalHeader().setStretchLastSection(True)
		view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		
		view.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
		
		return view

	def createChart(self, parent=None):
		chart = QChart()
		chart.setAnimationOptions(QChart.SeriesAnimations)

		view = QChartView(chart)
		view.setRenderHint(QPainter.Antialiasing)

		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		size_policy.setHorizontalStretch(1)
		size_policy.setVerticalStretch(0)
		size_policy.setHeightForWidth(view.sizePolicy().hasHeightForWidth())
		view.setSizePolicy(size_policy)

		return chart, view


# NOTE: This code used to create ui with qtdesigner
# class Magnetic(QMainWindow, magnetic_ui.Ui_MainWindow):
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
# 		self.setupUi(self)
class Magnetic(Ui):
	def __init__(self, data=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# NOTE: uncomment for prototype ui
		#uic.loadUi('./magnetic/ui/magnetic.ui', self)
		self.setupUi()

		self.data = data
		self.model = SensorDataModel(data)
		self.table.setModel(self.model)

		self.add_series("Magnetic Fields (2d-axis)", [0, 1])
		
		self.buttons['open'].clicked.connect(self.open_file)

	def open_file(self):
		pass
	
	def add(self, row):
		self.model.append((99, -88))
	
	def clear(self):
		print(self.model.rowCount())
		self.data.append((99.0, -99.1))
	
	def addData(self):
		self.model.update()

	def add_series(self, name, columns):
		self.series = QtChart.QLineSeries()
		self.series.setName(name)

		for i in range(self.model.rowCount()):
			x = float(self.model.index(i, 0).data())
			y = float(self.model.index(i, 1).data())
			self.series.append(x, y)
		self.chart.addSeries(self.series)

		# Setting X-axis
		self.axis_x = QtChart.QValueAxis()
		self.axis_x.setTickCount(10)
		self.axis_x.setLabelFormat("%.2f")
		self.axis_x.setTitleText("B")
		self.axis_x.setRange(-25, 25)
		self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
		self.series.attachAxis(self.axis_x)

		# Setting Y-axis
		self.axis_y = QtChart.QValueAxis()
		self.axis_y.setTickCount(10)
		self.axis_y.setRange(-25, 25)
		self.axis_y.setLabelFormat("%.2f")
		self.axis_y.setTitleText("C")
		self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
		self.series.attachAxis(self.axis_y)

		# Getting the color from the QChart to use it on the QTableView
		self.model.color = "{}".format(self.series.pen().color().name())

	
	def _centre(self):
		""" This method aligned main window related center screen """
		frameGm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerPoint = QApplication.desktop().screenGeometry(screen).center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())


def debug():
	dataset = from_excel(
		path='./downloads/example_dataset.xlsx',
		sheet_name='Лист6',
		rangex='H7:H51',
		rangey='I7:I51'
	)
	
	maxdub = Algorithm(dataset)
	ds_correct = [maxdub.correct(x, y) for (x, y) in dataset]
	print(f"\n{len(dataset)}, {dataset=}\n"
	      f"{len(ds_correct)}, {ds_correct=}")

	print(f"maxdub")
	plot(dataset, ds_correct)


def main():
	app = QApplication(sys.argv)
	
	if sys.platform == 'win32':
		import ctypes
		myappid = u'navi-dals.magnetic-tools.proxy.001'  # arbitrary string
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
		app.setWindowIcon(QIcon(':/rc/Interdit.ico'))
	
	dataset = from_excel(
		path=args.path_to_dataset,
		sheet_name='Лист6',
		rangex='H7:H52',
		rangey='I7:I52'
	)
	
	magnetic = Magnetic(dataset)
	magnetic._centre()
	magnetic.show()
	
	sys.exit(app.exec_())


if __name__ == '__main__':
	import argparse
	
	p = argparse.ArgumentParser()
	p.add_argument('--mode', action='store', dest='mode')
	p.add_argument('--data', action='store', dest='path_to_dataset')
	args = p.parse_args()
	
	main()
