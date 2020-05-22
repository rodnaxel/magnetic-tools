import sys

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic.algorithm import Algorithm
from magnetic.util import from_excel, plot


# NOTE: Uncomment if use QtDesigner file as Ui
# from magnetic.ui import magnetic_ui


class SensorDataModel(QtCore.QAbstractTableModel):
	""" The model represented sensor data"""
	
	def __init__(self, data=None):
		super().__init__()
		self._data = data
	
	def rowCount(self, parent=None, *args, **kwargs):
		return 3 or len(self._data)
	
	def columnCount(self, parent=None, *args, **kwargs):
		return 1 or len(self._data[0])
	
	def headerData(self, section, orientation, role):
		if role != QtCore.Qt.DisplayRole:
			return None
		if orientation == QtCore.Qt.Horizontal:
			return ("B", "C")[section]
		else:
			return "{}".format(section)
	
	def data(self, index, role=QtCore.Qt.DisplayRole):
		if role == QtCore.Qt.DisplayRole:
			return self._data[index.row()][index.column()]
		elif role == QtCore.Qt.TextAlignmentRole:
			return QtCore.Qt.AlignRight
	
	def flags(self, index):
		result = super().flags(index)
		if index.column() in [0, 1]:
			result &= ~QtCore.Qt.ItemIsEditable
		return result
	
	def update(self):
		self.layoutChanged.emit()


class Ui(QMainWindow):
	""" This class describe graphical user interface """
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def _centre(self):
		""" This method aligned main window related center screen """
		frameGm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerPoint = QApplication.desktop().screenGeometry(screen).center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())
	
	def setupUi(self):
		self.setWindowTitle(f"{__file__}")
		self.setMinimumSize(600, 500)
		
		# Widgets
		centralWidget = QWidget(self)
		centralLayout = QVBoxLayout(centralWidget)
		self.setCentralWidget(centralWidget)
		
		self.table = self.createTable()
		centralLayout.addWidget(self.table)
		
		self.buttons = {}
		self.button = QPushButton("Add", centralWidget)
		centralLayout.addWidget(self.button)
		
		self.buttons['clear'] = QPushButton("Clear", centralWidget)
		centralLayout.addWidget(self.buttons['clear'])
	
	def createTable(self):
		wgt = QTableView(self)
		
		wgt.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
		wgt.horizontalHeader().setSectionsMovable(True)
		wgt.horizontalHeader().setStretchLastSection(True)
		wgt.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);
		
		wgt.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
		
		# wgt.setSortingEnabled(True)
		
		# layout = QGridLayout(wgt)
		
		return wgt


# NOTE: This code used to create ui with qtdesigner
# class Magnetic(QMainWindow, magnetic_ui.Ui_MainWindow):
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
# 		self.setupUi(self)
class Magnetic(Ui):
	def __init__(self, data=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setupUi()
		
		self.model = SensorDataModel(data)
		self.table.setModel(self.model)
		
		self.button.clicked.connect(self.addData)
		self.buttons['clear'].clicked.connect(lambda: print("Press button <Clear>"))
	
	def addData(self):
		self.model.update()
	
	def _centre(self):
		""" This method aligned main window related center screen """
		frameGm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerPoint = QApplication.desktop().screenGeometry(screen).center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())


def debug():
	dataset = from_excel(
		path='/downloads/example_dataset.xlsx',
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
	
	print(__file__)
	
	dataset = from_excel(
		path='/home/tech/workspace/python/magnetic-tools/downloads/example_dataset.xlsx',
		sheet_name='Лист6',
		rangex='H7:H51',
		rangey='I7:I51'
	)
	
	magnetic = Magnetic()
	magnetic._centre()
	magnetic.show()
	
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()

