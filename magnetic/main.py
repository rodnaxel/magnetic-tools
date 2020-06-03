import sys

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic.util import get_arguments


class MagneticWidget(QWidget):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		# View Port
		self.sensor_data = {}
		gbox = QGroupBox("Sensor Data:")
		gbox_layout = QFormLayout(gbox)
		for name in ('pitch', 'roll', 'heading', 'hx', 'hy', 'hz', 'hxc', 'hyc', 'hyz'):
			label = QLabel("-----")
			label.setAlignment(QtCore.Qt.AlignRight)
			label.setFrameShape(QFrame.StyledPanel)
			gbox_layout.addRow(QLabel(name.capitalize() + ":"), label)
			self.sensor_data[name] = label
		
		self.buttons = {}
		for name in ("collection",):
			btn = QPushButton(name.capitalize(), self)
			self.buttons[name] = btn
		
		# Layout
		centralLayout = QVBoxLayout(self)
		centralLayout.addWidget(gbox)
		centralLayout.addWidget(self.buttons['collection'])


class Ui(QMainWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.collection_start = False
	
	def setupUi(self):
		self.setWindowTitle(f"Magnetic Lab")
		self.setMinimumSize(800, 600)
		
		centralWidget = MagneticWidget(self)
		self.setCentralWidget(centralWidget)
		
		self.buttons = self.centralWidget().buttons
		self.sensor_data = self.centralWidget().sensor_data
		
		# Connect Signal/Slot
		self.buttons["collection"].clicked.connect(self.on_collection)
	
	def timerEvent(self, QTimerEvent):
		""" Handler timer event"""
		print(QtCore.QTime().currentTime().toString())
	
	def on_collection(self):
		print("onCollection()...")
		self.collection_start = ~self.collection_start
		self.buttons["collection"].setDown(self.collection_start)
		if self.collection_start:
			self.buttons["collection"].setText("Collection stop")
			self.timer_recieve = self.startTimer(100, timerType=QtCore.Qt.PreciseTimer)
		else:
			self.buttons["collection"].setText("Collection start")
			if self.timer_recieve:
				self.killTimer(self.timer_recieve)
				self.timer_recieve = None
	
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
		# uic.loadUi('../magnetic/ui/magnetic_lab.ui', self)
		self.setupUi()
	
	# self.model = SensorDataModel()
	# self.centralWidget().table.setModel(self.model)
	# self.centralWidget().chartwidget.set_model(self.model)


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
