import os.path
import sys

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic.algorithms import Algorithm
from magnetic.charts import ChartWidget, MatplotlibChart
from magnetic.models import SensorDataModel
from magnetic.util import from_excel, get_arguments, to_csv, from_csv


class SensorDataTable(QTableView):
	def __init__(self, parent):
		super().__init__(parent)
		
		self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
		self.horizontalHeader().setSectionsMovable(True)
		self.horizontalHeader().setStretchLastSection(False)
		self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignJustify)


class Ui(QMainWindow):
	""" This class describe graphical user interface """
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def setupUi(self):
		self.setWindowTitle(f"{__file__}")
		self.setMinimumSize(800, 600)
		
		# Widgets
		centralWidget = QWidget(self)
		
		# Menu
		self.menu = self.menuBar()
		
		# File
		self.file_menu = self.menu.addMenu("File")
		open_action = QAction("Open...", self)
		open_action.triggered.connect(self.action_open)
		self.file_menu.addAction(open_action)
		
		save_action = QAction("Save as...", self)
		save_action.triggered.connect(self.action_save)
		self.file_menu.addAction(save_action)
		
		self.file_menu.addSeparator()
		
		exit_action = QAction("Exit", self)
		exit_action.triggered.connect(self.close)
		self.file_menu.addAction(exit_action)
		
		# Tools
		self.tool_menu = self.menu.addMenu("Tools")
		
		# Status bar
		self.status = self.statusBar()
		self.status.showMessage("Data loaded and plotted")
		
		# Top bar
		self.label_x = QLabel("Hx:", centralWidget)
		self.spin_x = QDoubleSpinBox(centralWidget)
		self.spin_x.setMinimumWidth(100)
		
		self.label_y = QLabel("Hy:", centralWidget)
		self.spin_y = QDoubleSpinBox(centralWidget)
		self.spin_y.setMinimumWidth(100)

		self.buttons = {}
		btn = QPushButton("Add", centralWidget)
		self.buttons['add'] = btn
		btn = QPushButton("Delete All", centralWidget)
		self.buttons['delete_all'] = btn

		# Table
		splitter = QSplitter(QtCore.Qt.Horizontal, centralWidget)
		self.table = SensorDataTable(splitter)
		splitter.addWidget(self.table)

		# Chart
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

		addLayout = QHBoxLayout()
		addLayout.addWidget(self.label_x)
		addLayout.addWidget(self.spin_x)
		addLayout.addWidget(self.label_y)
		addLayout.addWidget(self.spin_y)
		addLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
		addLayout.addWidget(self.buttons['add'])
		addLayout.addWidget(self.buttons['delete_all'])
		
		centralLayout.addLayout(addLayout)
		centralLayout.addWidget(splitter)
	
	def action_open(self):
		raise NotImplementedError
	
	def action_save(self):
		raise NotImplementedError


class Magnetic(Ui):
	def __init__(self, data=None, title=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# NOTE: uncomment for prototype ui
		# uic.loadUi('./magnetic/ui/magnetic.ui', self)
		self.setupUi()
		
		self.setWindowTitle(title)
		
		self.model = SensorDataModel(data)
		self.table.setModel(self.model)
		self.chartwidget.setModel("Magnitude", self.model)
		
		self.buttons['add'].clicked.connect(self.add_xy)
		self.buttons['delete_all'].clicked.connect(self.delete_all)
	
	def add_xy(self):
		x = self.spin_x.value()
		y = self.spin_y.value()
		self.model.append_item(x, y)
	
	def delete_all(self):
		self.model.reset()
	
	def calibrate(self):
		pass
	
	def action_open(self):
		fname, _ = QFileDialog.getOpenFileName(
			self,
			"Open",
			"/home/tech/workspace/python/magnetic-tools/downloads/",
			"Data (*.csv)"
		)
		print(fname, _)
		
		if fname:
			dataset = from_csv(fname)
			self.status.showMessage(f"Load data", 1000)
			self.setWindowTitle(fname)
			self.model.reset()
			self.model.load_data(dataset)
		else:
			self.status.showMessage(f"No load data")
	
	def action_save(self):
		fname, _ = QFileDialog.getSaveFileName(
			self,
			"Save file as...",
			"/home/tech/workspace/python/magnetic-tools/downloads/",
			"Data (*.csv)"
		)
		if fname:
			to_csv(fname, self.model.fetch_data())
			self.status.showMessage(f"Save data to  {fname}", 1000)
		else:
			self.status.showMessage(f"No save")
	
	def centre(self):
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
	
	# Load example data to dataset
	filename = os.path.abspath(args.path_to_dataset)
	dataset = from_excel(
		path=filename,
		sheet_name='Лист6',
		rangex='H7:H52',
		rangey='I7:I52'
	)
	
	magnetic = Magnetic(dataset, filename)
	magnetic.centre()
	magnetic.show()
	
	# app.setStyle("Fusion")
	
	# TODO: Add DarkTheme
	# Now use a palette to switch to dark colors:
	# palette = QPalette()
	# palette.setColor(QPalette.Window, QColor(53, 53, 53))
	# palette.setColor(QPalette.WindowText, Qt.white)
	# palette.setColor(QPalette.Base, QColor(25, 25, 25))
	# palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
	# palette.setColor(QPalette.ToolTipBase, Qt.white)
	# palette.setColor(QPalette.ToolTipText, Qt.white)
	# palette.setColor(QPalette.Text, Qt.white)
	# palette.setColor(QPalette.Button, QColor(53, 53, 53))
	# palette.setColor(QPalette.ButtonText, Qt.white)
	# palette.setColor(QPalette.BrightText, Qt.red)
	# palette.setColor(QPalette.Link, QColor(42, 130, 218))
	# palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
	# palette.setColor(QPalette.HighlightedText, Qt.black)
	# app.setPalette(palette)

	sys.exit(app.exec_())


if __name__ == '__main__':
	args = get_arguments()
	main()
