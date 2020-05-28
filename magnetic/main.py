import sys

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic.algorithms import Algorithm
from magnetic.charts import ChartWidget, MatplotlibChart
from magnetic.models import SensorDataModel
from magnetic.util import from_excel, get_arguments


class Ui(QMainWindow):
	""" This class describe graphical user interface """

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def setupUi(self):
		self.setWindowTitle(f"{__file__}")
		self.setMinimumSize(800, 600)

		# Widgets
		centralWidget = QWidget(self)

		# Top widget
		self.label_x = QLabel("Bx:", centralWidget)
		self.spin_x = QDoubleSpinBox(centralWidget)
		self.spin_x.setMinimumWidth(100)

		self.label_y = QLabel("By:", centralWidget)
		self.spin_y = QDoubleSpinBox(centralWidget)
		self.spin_y.setMinimumWidth(100)

		self.buttons = {}
		btn = QPushButton("Add", centralWidget)
		self.buttons['add'] = btn

		splitter = QSplitter(QtCore.Qt.Horizontal, centralWidget)
		self.table = self.createTable(splitter)
		splitter.addWidget(self.table)

		# self.chartview = self.createChart(splitter)
		self.chartwidget = ChartWidget()
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		size_policy.setHorizontalStretch(1)
		size_policy.setVerticalStretch(0)
		size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		self.chartwidget.setSizePolicy(size_policy)
		splitter.addWidget(self.chartwidget)

		# Layout
		centralLayout = QVBoxLayout(centralWidget)
		self.setCentralWidget(centralWidget)

		pathLayout = QHBoxLayout()
		pathLayout.addWidget(self.label_x)
		pathLayout.addWidget(self.spin_x)
		pathLayout.addWidget(self.label_y)
		pathLayout.addWidget(self.spin_y)
		pathLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
		pathLayout.addWidget(self.buttons['add'])

		centralLayout.addLayout(pathLayout)
		centralLayout.addWidget(splitter)

	def createTable(self, parent):
		view = QTableView(parent)

		view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
		view.horizontalHeader().setSectionsMovable(True)
		view.horizontalHeader().setStretchLastSection(True)
		view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

		view.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignJustify)

		return view


class Magnetic(Ui):
	def __init__(self, data=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# NOTE: uncomment for prototype ui
		# uic.loadUi('./magnetic/ui/magnetic.ui', self)
		self.setupUi()

		self.model = SensorDataModel(data)
		self.table.setModel(self.model)
		self.chartwidget.setModel("Magnitude", self.model)

		self.buttons['add'].clicked.connect(self.add_xy)

	def add_xy(self):
		x = self.spin_x.value()
		y = self.spin_y.value()
		self.model.append_item(x, y)

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
	MatplotlibChart.plot(dataset, ds_correct)


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
	args = get_arguments()
	main()
