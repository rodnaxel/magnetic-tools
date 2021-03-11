import sys, os
import platform
import threading
import queue
import serial

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic import sensor
from magnetic.algorithms import to_horizont
from magnetic.charts import TimeGraph
from magnetic.magnetic_viewer import SensorDataTable
from magnetic.models import SensorDataModel
from magnetic.util import get_arguments


# For run in Raspberry Pi
if platform.machine() == "armv7l":
    #os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_FB_FORCE_FULLSCREEN "] = "0"
    PORT_NAME = "/dev/ttyUSB1"
else:
    PORT_NAME = "/dev/ttyUSB0"


class MagneticWidget(QDialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Data View
        self.data_view = {}
        gbox = QGroupBox("Sensor Data" + ":")
        #gbox_layout = QFormLayout(gbox)
        gbox_layout = QVBoxLayout(gbox)

        data_names = ('pitch', 'roll', 'heading', 'hxr', 'hyr', 'hzr', 'hx', 'hy', 'hz')

        for name in ('pitch', 'roll', 'heading', 'hxr', 'hyr', 'hzr', 'hx', 'hy', 'hz'):
            label = QLabel("None")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setMinimumWidth(80)
            label.setStyleSheet("QLabel {font: 16px; background-color: white}")
            label.setFrameShape(QFrame.StyledPanel)

            #gbox_layout.addRow(QLabel(name.capitalize() + ":"), label)
            layout = QHBoxLayout()
            layout.addWidget(QLabel(name.capitalize()))
            layout.addWidget(label)
            #layout.addWidget(QCheckBox())

            gbox_layout.addLayout(layout)

            self.data_view[name] = label

        self.options = {}
        option_box = QGroupBox("Select option:")
        option_layout = QHBoxLayout(option_box)
        for name in ("dub horizont",):
            check = QCheckBox(name)
            check.setCheckState(False)
            option_layout.addWidget(check)
            self.options[name] = check

        # Control panel
        self.buttons = {}
        for name in ("connect", "collection", "clear", "quit"):
            btn = QPushButton(name.capitalize(), self)
            self.buttons[name] = btn

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 20, 10, 10)
        left_layout.addWidget(gbox)
        left_layout.addWidget(option_box)

        for btn in self.buttons.values():
            left_layout.addWidget(btn)
        left_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Table/Graph View
        right_layout = QVBoxLayout()

        # ...Top chartbar
        chart_label = QLabel("Show as:", self)
        self.chart_box = QComboBox(self)
        self.chart_box.addItems(("Graph", "Table"))

        categories_label =  QLabel("Categories" + ":", self)
        self.categories_box = QComboBox(self)
        self.categories_box.addItems((items.capitalize() for items in data_names))

        chartbar_layout = QHBoxLayout()
        chartbar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))
        chartbar_layout.addWidget(chart_label)
        chartbar_layout.addWidget(self.chart_box)
        chartbar_layout.addWidget(categories_label)
        chartbar_layout.addWidget(self.categories_box)

        # ...Chart / Table
        self.stack = stack_layout = QStackedLayout()

        self.chart_view = TimeGraph(self)
        self.chart_view2 = TimeGraph(self)
        self.chart_view3 = TimeGraph(self)

        wgt = QWidget(self)
        layout = QVBoxLayout(wgt)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.chart_view.setSizePolicy(size_policy)
        self.chart_view.setMaximumWidth(self.chart_view.maximumHeight())

        layout.addWidget(self.chart_view)
        #layout.addWidget(self.chart_view2)
        #layout.addWidget(self.chart_view3)


        #stack_layout.addWidget(self.chart_view)
        stack_layout.addWidget(wgt)

        self.table_view = SensorDataTable(self)
        stack_layout.addWidget(self.table_view)

        right_layout.addLayout(chartbar_layout)
        right_layout.addLayout(stack_layout, 2)

        # Central Layout
        centralLayout = QHBoxLayout(self)
        centralLayout.addLayout(left_layout)
        centralLayout.addLayout(right_layout, 2)

        # Connect signal/slot
        self.chart_box.currentTextChanged[str].connect(self.switch_view)
        self.categories_box.currentTextChanged[str].connect(self.categorySwitched)

    def switch_view(self, view_name):
        if view_name == "Graph":
            self.stack.setCurrentIndex(0)
        elif view_name == "Table":
            self.stack.setCurrentIndex(1)

    def categorySwitched(self, name):
        print(f"Category switched to {name}")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collection_start = False

    def setupUi(self):
        self.setWindowTitle(f"Magnetic Lab")
        self.setMinimumSize(100, 600)

        self.create_menu()
        self.create_toolbar()

        # Central Widget
        central_widget = MagneticWidget(self)


        self.setCentralWidget(central_widget)

        self.create_statusbar()

        self.buttons = self.centralWidget().buttons
        self.data_view = self.centralWidget().data_view
        self.options = self.centralWidget().options

    def create_statusbar(self):
        # Statusbar
        self.status = self.statusBar()
        self.counter = QLabel("Rx:")
        self.statusBar().addPermanentWidget(self.counter)

    def create_menu(self):
        def _action_rescan():
            available = sensor.scan_ports()
            self.portbox.clear()
            self.portbox.addItems(available)

        menu = self.menuBar()
        file_menu = QMenu("&File", self)
        menu.addMenu(file_menu)
        file_menu.addAction("Rescan", _action_rescan)

    def create_toolbar(self):
        # Toolbar
        def on_start():
            print("start")

        toolbar = self.addToolBar("File")
        toolbar.setMovable(False)

        data_names = ('pitch', 'roll', 'heading', 'hxr', 'hyr', 'hzr', 'hx', 'hy', 'hz')
        self.portbox = QComboBox(self)
        toolbar.addWidget(self.portbox)

        toolbar.addSeparator()

        self.categories_box = QComboBox(self)
        self.categories_box.addItems((items.capitalize() for items in data_names))
        toolbar.addWidget(self.categories_box)

        toolbar.addSeparator()

        chart_label = QLabel("Show as:", self)
        self.chart_box = QComboBox(self)
        self.chart_box.addItems(("Graph", "Table"))
        toolbar.addWidget(chart_label)
        toolbar.addWidget(self.chart_box)

    def centre(self):
        """ This method aligned main window related center screen """
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())


class Magnetic(MainWindow):
    app_title = "Magnetic Viewer - {0}"

    def __init__(self, data=None, title=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # NOTE: uncomment for prototype ui
        # uic.loadUi('../magnetic/ui/magnetic_lab.ui', self)
        self.setupUi()

        # Search available ports
        available_ports = sensor.scan_ports()
        self.portbox.addItems(available_ports)
        self.available = True

        if not available_ports:
            self.status.showMessage("No available ports")
            self.buttons['connect'].setDisabled(True)

        # Set model
        self.model = SensorDataModel()
        self.centralWidget().table_view.setModel(self.model)
        self.centralWidget().chart_view.setModel(self.model)

        # Connect Signal/Slot
        self.buttons["connect"].clicked.connect(self.on_connect)
        self.buttons["clear"].clicked.connect(self.on_clear)
        self.buttons["quit"].clicked.connect(self.on_quit)

        self.portbox.currentTextChanged[str].connect(self.on_switch_port)

        self.model.rowsInserted.connect(self.centralWidget().chart_view.redraw)

    def timerEvent(self, QTimerEvent):
        """ Handler timer event"""
        # time = QtCore.QTime().currentTime().toString()
        try:
            data = [round(item, 1) for item in sensor.SENSOR_QUEUE.get(timeout=0.2)]
        except queue.Empty:
            self.status.showMessage("No sensor data")
            return

        r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz = data

        # <1> Apply Dub algorithm
        if self.options['dub horizont'].checkState():
            hy_raw, hx_raw, hz_raw = to_horizont(hy_raw, hx_raw, hz_raw, r, p)

        # <2> Insert row values to model
        self.model.append_data((hx, hy, hz, hx_raw, hy_raw, hz_raw, h, r, p))

        # <3> Set values to data view
        self.show_data(h, hx, hx_raw, hy, hy_raw, hz, hz_raw, p, r)

    def show_data(self, h, hx, hx_raw, hy, hy_raw, hz, hz_raw, p, r):
        fmt_value = '{0:.1f}'

        self.counter.setText("Rx: {}".format(self.model.rowCount()))
        self.data_view['roll'].setText(fmt_value.format(r))
        self.data_view['pitch'].setText(fmt_value.format(p))
        self.data_view['heading'].setText(fmt_value.format(h))
        self.data_view['hxr'].setText(fmt_value.format(hx_raw))
        self.data_view['hyr'].setText(fmt_value.format(hy_raw))
        self.data_view['hzr'].setText(fmt_value.format(hz_raw))
        self.data_view['hx'].setText(fmt_value.format(hx))
        self.data_view['hy'].setText(fmt_value.format(hy))
        self.data_view['hz'].setText(fmt_value.format(hz))

    def on_clear(self):
        self.model.reset()
        self.centralWidget().chart_view.clear_area()

    def on_connect(self):
        self.collection_start = ~self.collection_start

        if self.collection_start:
            self.on_start()
        else:
            self.on_stop()

    def on_stop(self):
        self.status.showMessage("Disconnect")
        self.buttons["connect"].setText("Connect")
        self.portbox.setEnabled(True)

        if self.timer_recieve:
            self.killTimer(self.timer_recieve)
            self.timer_recieve = None

        self.sensor.terminate()
        self.serobj.close()
        del self.sensor

    def on_start(self):
        self.on_clear()
        self.centralWidget().chart_view.add_graph("Graph Roll", self.model, xcol=0, ycol=1)
        self.status.showMessage("Clear old data, Connect")
        self.buttons["connect"].setText("Disconnect")
        self.portbox.setDisabled(True)

        port = self.portbox.currentText()
        self.serobj = serobj = serial.Serial(port, timeout=0.1)
        self.sensor = sensor.Sensor(serobj)

        self.t = threading.Thread(target=self.sensor.run, daemon=False)
        self.t.start()

        self.timer_recieve = self.startTimer(100, timerType=QtCore.Qt.PreciseTimer)

    def on_switch_port(self, port):
        print(f'on_switch_port(): {port}')

    @staticmethod
    def on_quit(self):
         QtCore.QCoreApplication.exit(0)


def main():
    app = QApplication(sys.argv)

    if sys.platform == 'win32':
        import ctypes
        myappid = u'navi-dals.magnetic-tools.proxy.001'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        app.setWindowIcon(QIcon(':/rc/Interdit.ico'))

    magnetic = Magnetic()
    magnetic.centre()
    magnetic.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    args = get_arguments()
    main()
