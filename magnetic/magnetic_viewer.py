import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QWidget, QAction, QHBoxLayout, QLabel, QDoubleSpinBox, \
	QSpacerItem, QSizePolicy, QPushButton, QSplitter, QVBoxLayout, QFileDialog, QApplication

from algorithms import Algorithm
from chart.mpl_chart import EllipsoidPlot
from models import SensorFieldModel
from util import from_csv, to_csv, get_arguments
from views import SensorDataTable


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
		
		# ...File
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
		
		# Status bar
		self.status = self.statusBar()
		self.status.showMessage("Data loaded and plotted")
		
		# Parameter Bar
		self.deviation_ratio = {}
		parameterbar = QHBoxLayout()
		for name in ('Bias Hx', 'Bias Hy', 'Phi', 'k'):
			label = QLabel(name + ":", centralWidget)
			spin = QDoubleSpinBox(centralWidget)
			spin.setReadOnly(True)
			parameterbar.addWidget(label)
			parameterbar.addWidget(spin)
			self.deviation_ratio[name] = spin
		
		parameterbar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
		
		self.buttons = {}
		for name in ("add", "clear", "calibrate"):
			btn = QPushButton(name.capitalize(), centralWidget)
			parameterbar.addWidget(btn)
			self.buttons[name] = btn

		# Table
		splitter = QSplitter(QtCore.Qt.Horizontal, centralWidget)
		self.table = SensorDataTable(splitter)
		splitter.addWidget(self.table)

		# Chart
		# self.chartwidget = EllipsoidGraph()
		self.chartwidget = EllipsoidPlot()
		# size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		# size_policy.setHorizontalStretch(1)
		# size_policy.setVerticalStretch(0)
		# size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		# self.chartwidget.setSizePolicy(size_policy)
		# self.chartwidget.setMaximumWidth(self.chartwidget.maximumHeight())
		splitter.addWidget(self.chartwidget)

		# Layout
		centralLayout = QVBoxLayout(centralWidget)
		self.setCentralWidget(centralWidget)
		
		centralLayout.addLayout(parameterbar)
		centralLayout.addWidget(splitter)
	
	def action_open(self):
		raise NotImplementedError
	
	def action_save(self):
		raise NotImplementedError


class MagneticViewer(Ui):
	app_title = "Magnetic Viewer - {0}"
	
	def __init__(self, data=None, title=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# NOTE: uncomment for prototype ui
		# uic.loadUi('./magnetic/ui/magnetic.ui', self)
		self.setupUi()
		
		self.setWindowTitle(self.app_title.format(title))
		
		self.model = SensorFieldModel()
		self.table.setModel(self.model)

		self.buttons['add'].clicked.connect(self.add_xy)
		self.buttons['clear'].clicked.connect(self.delete_all)
		self.buttons['calibrate'].clicked.connect(self.calibrate)
	
	def add_xy(self):
		print(self.table.selectedIndexes())
	
	def delete_all(self):
		self.model.reset()
		self.chartwidget.clear()
		self.setWindowTitle(self.app_title)
	
	def calibrate(self):
		if not self.model.fetch_data():
			self.status.showMessage("No loaded data")
			return

		dataset_initial = self.model.fetch_data()
		maxdub = Algorithm(dataset_initial)
		dataset_correction = [maxdub.correct(x, y) for (x, y) in dataset_initial]
		
		union_ = [(x, y, round(xc, 1), round(yc, 1)) for (x, y), (xc, yc) in zip(dataset_initial, dataset_correction)]
		self.model.reset()
		self.model.load_data(union_)
		# self.chartwidget.add_graph(name="Correction Magnitude", model=self.model, xcol=2, ycol=3)
		#print(self.model.fetch_data())

		xdata = []
		ydata = []
		for (_, _, x, y) in self.model.fetch_data():
			xdata.append(x)
			ydata.append(y)
		self.chartwidget.set_data(xdata, ydata)


	def action_open(self):
		"""
		Функция загрузки датасет составляющих магнитного поля B,C из csv-файл
		"""
		fname, _ = QFileDialog.getOpenFileName(
			self,
			"Open",
			"/home/tech/workspace/python/magnetic-tools/downloads/",
			"Data (*.csv)"
		)
		
		if fname:
			dataset = from_csv(fname)
			self.status.showMessage(f"Load data", 1000)
			self.setWindowTitle(self.app_title.format(fname))

			self.model.reset()
			self.model.load_data(dataset)

			# Fetch data
			xdata = []
			ydata = []
			for (x, y) in self.model.fetch_data():
				xdata.append(x)
				ydata.append(y)
			self.chartwidget.set_data(xdata, ydata)

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


def main():
	app = QApplication(sys.argv)
	
	if sys.platform == 'win32':
		import ctypes
		
		myappid = u'navi-dals.magnetic-tools.proxy.001'  # arbitrary string
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
	# app.setWindowIcon(QIcon(':/rc/Interdit.ico'))
	
	# # Load example data to dataset
	# filename = os.path.abspath(args.path_to_dataset)
	# dataset = from_excel(
	# 	path=filename,
	# 	sheet_name='Лист6',
	# 	rangex='H7:H52',
	# 	rangey='I7:I52'
	# )
	
	magnetic = MagneticViewer()
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
