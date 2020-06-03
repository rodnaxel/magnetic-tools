import sys
import threading

import serial
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic import sensor
from magnetic.charts import ChartWidget
from magnetic.magnetic_viewer import SensorDataTable
from magnetic.models import SensorDataModel
from magnetic.util import get_arguments


class MagneticWidget(QDialog):
	def __init__(self, parent, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Data View
		self.sensor_data = {}
		gbox = QGroupBox("Sensor Data:")
		gbox_layout = QFormLayout(gbox)
		for name in ('pitch', 'roll', 'heading', 'hx', 'hy', 'hz', 'hxc', 'hyc', 'hzc'):
			label = QLabel("-----")
			label.setAlignment(QtCore.Qt.AlignRight)
			label.setFrameShape(QFrame.StyledPanel)
			gbox_layout.addRow(QLabel(name.capitalize() + ":"), label)
			self.sensor_data[name] = label
		
		# Control
		self.buttons = {}
		for name in ("collection",):
			btn = QPushButton(name.capitalize(), self)
			self.buttons[name] = btn
		
		left_layout = QVBoxLayout()
		left_layout.addWidget(gbox)
		left_layout.addWidget(self.buttons['collection'])
		left_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))
		
		# Table/Graph View
		right_layout = QVBoxLayout()
		
		# ...Top chartbar
		chart_label = QLabel("Type Chart:", self)
		self.chart_box = QComboBox(self)
		self.chart_box.addItems(("Graph", "Table"))
		
		chartbar_layout = QHBoxLayout()
		chartbar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))
		chartbar_layout.addWidget(chart_label)
		chartbar_layout.addWidget(self.chart_box)
		
		# ...Chart / Table
		self.stack = stack_layout = QStackedLayout()
		
		self.chart_view = ChartWidget(self)
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		size_policy.setHorizontalStretch(1)
		size_policy.setVerticalStretch(0)
		size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		self.chart_view.setSizePolicy(size_policy)
		self.chart_view.setMaximumWidth(self.chart_view.maximumHeight())
		stack_layout.addWidget(self.chart_view)
		
		self.table_view = SensorDataTable(self)
		stack_layout.addWidget(self.table_view)
		
		right_layout.addLayout(chartbar_layout)
		right_layout.addLayout(stack_layout, 2)
		
		# Central Layout
		centralLayout = QHBoxLayout(self)
		centralLayout.addLayout(left_layout)
		centralLayout.addLayout(right_layout)


class Ui(QMainWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.collection_start = False
	
	def setupUi(self):
		self.setWindowTitle(f"Magnetic Lab")
		self.setMinimumSize(100, 600)
		
		central_widget = MagneticWidget(self)
		self.setCentralWidget(central_widget)
		
		self.buttons = self.centralWidget().buttons
		self.sensor_data = self.centralWidget().sensor_data
		self.chart_box = self.centralWidget().chart_box
		self.stack = self.centralWidget().stack
	
	def centre(self):
		""" This method aligned main window related center screen """
		frame_gm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		center_point = QApplication.desktop().screenGeometry(screen).center()
		frame_gm.moveCenter(center_point)
		self.move(frame_gm.topLeft())


count = 0

class Magnetic(Ui):
	app_title = "Magnetic Viewer - {0}"
	
	def __init__(self, data=None, title=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# NOTE: uncomment for prototype ui
		# uic.loadUi('../magnetic/ui/magnetic_lab.ui', self)
		self.setupUi()
		
		serobj = serial.Serial("/dev/ttyUSB0", timeout=0.1)
		self.sensor = sensor.SensorDriver(serobj)
		
		t = threading.Thread(target=self.sensor.run, daemon=True)
		t.start()
		
		self.model = SensorDataModel()
		self.centralWidget().table_view.setModel(self.model)
		self.centralWidget().chart_view.set_model(self.model)
		self.centralWidget().chart_view.add_graph("Initial Magniude", self.model, xcol=0, ycol=1)
		
		# Connect Signal/Slot
		self.buttons["collection"].clicked.connect(self.on_collection)
		self.chart_box.currentTextChanged[str].connect(self.switch_view)
	
	def switch_view(self, s):
		if s == "Graph":
			self.stack.setCurrentIndex(0)
		elif s == "Table":
			self.stack.setCurrentIndex(1)
	
	def timerEvent(self, QTimerEvent):
		""" Handler timer event"""
		global count
		time = QtCore.QTime().currentTime().toString()
		data = self.sensor.recieve()
		if data == object():
			self.stop()
			print('Error thread')
			return

		r, p, h, hx, hy, hz = data
		
		fmt = '{0:.2f}'
		self.sensor_data['roll'].setText(fmt.format(r))
		self.sensor_data['pitch'].setText(fmt.format(p))
		self.sensor_data['heading'].setText(fmt.format(h))
		self.sensor_data['hx'].setText(fmt.format(hx))
		self.sensor_data['hy'].setText(fmt.format(hy))
		self.sensor_data['hz'].setText(fmt.format(hz))
		self.sensor_data['hzc'].setText(fmt.format(count))
		count += 1
		
		data = (round(hx, 1), round(hy, 1))
		self.model.append_data(data)
		
		print(f"{time}: {data}")
	
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
	
	def stop(self):
		self.buttons["collection"].setText("Collection start")
		if self.timer_recieve:
			self.killTimer(self.timer_recieve)
			self.timer_recieve = None


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
