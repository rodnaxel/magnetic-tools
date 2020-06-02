import sys

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic.charts import ChartWidget
from magnetic.magnetic_viewer import SensorDataTable
from magnetic.models import SensorDataModel
from magnetic.util import get_arguments


class MagneticWidget(QWidget):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.deviation_ratio = {}
		parameterbar = QHBoxLayout()
		for name in ('Bias Hx', 'Bias Hy', 'Phi', 'k'):
			label = QLabel(name + ":", self)
			spin = QDoubleSpinBox(self)
			spin.setReadOnly(True)
			parameterbar.addWidget(label)
			parameterbar.addWidget(spin)
			self.deviation_ratio[name] = spin
		
		parameterbar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
		
		self.buttons = {}
		for name in ("add", "clear", "calibrate"):
			btn = QPushButton(name.capitalize(), self)
			parameterbar.addWidget(btn)
			self.buttons[name] = btn
		
		# Table
		splitter = QSplitter(QtCore.Qt.Horizontal, self)
		self.table = SensorDataTable(splitter)
		splitter.addWidget(self.table)
		
		# Chart
		self.chartwidget = ChartWidget()
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		size_policy.setHorizontalStretch(1)
		size_policy.setVerticalStretch(0)
		size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		self.chartwidget.setSizePolicy(size_policy)
		self.chartwidget.setMaximumWidth(self.chartwidget.maximumHeight())
		splitter.addWidget(self.chartwidget)
		
		# Layout
		centralLayout = QVBoxLayout(self)
		
		centralLayout.addLayout(parameterbar)
		centralLayout.addWidget(splitter)


class Ui(QMainWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def setupUi(self):
		self.setWindowTitle(f"Magnetic Lab")
		self.setMinimumSize(800, 600)
		
		centralWidget = MagneticWidget(self)
		
		self.setCentralWidget(centralWidget)
	
	def centre(self):
		""" This method aligned main window related center screen """
		frameGm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerPoint = QApplication.desktop().screenGeometry(screen).center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())


class Magnetic(Ui):
	app_title = "Magnetic Viewer - {0}"
	
	def __init__(self, data=None, title=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# NOTE: uncomment for prototype ui
		# uic.loadUi('./magnetic/ui/magnetic.ui', self)
		self.setupUi()
		
		self.model = SensorDataModel()
		self.centralWidget().table.set_model(self.model)
		self.centralWidget().chartwidget.set_model(self.model)


def main():
	app = QApplication(sys.argv)
	
	if sys.platform == 'win32':
		import ctypes
		myappid = u'navi-dals.magnetic-tools.proxy.001'  # arbitrary string
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
		app.setWindowIcon(QIcon(':/rc/Interdit.ico'))
	
	# magnetic = MagneticViewer()
	magnetic = Magnetic()
	magnetic.centre()
	magnetic.show()
	
	sys.exit(app.exec_())


if __name__ == '__main__':
	args = get_arguments()
	main()
