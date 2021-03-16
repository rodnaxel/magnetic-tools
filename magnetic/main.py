import os
import platform
import queue
import sys
import threading

import serial
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sensor
from algorithms import to_horizont
from chart.qt_charts import TimeGraph
from chart.mpl_chart import SimplePlot, BasePlot
from magnetic_viewer import SensorDataTable
from model.sensormodel import SensorDataModel
from util import get_arguments

# For run in Raspberry Pi
if platform.machine() == "armv7l":
    # os.environ["QT_QPA_PLATFORM"] = "linuxfb"
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
        gbox_layout = QVBoxLayout(gbox)

        for name in ('roll', 'pitch', 'heading', 'hyr', 'hxr', 'hzr', 'hy', 'hx', 'hz'):
            label = QLabel("-")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setMinimumWidth(80)
            label.setStyleSheet("QLabel {font: 16px; background-color: white}")
            label.setFrameShape(QFrame.StyledPanel)

            layout = QHBoxLayout()
            layout.addWidget(QLabel(name.capitalize()))
            layout.addWidget(label)

            gbox_layout.addLayout(layout)

            self.data_view[name] = label

        # Options View
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

        # Layouts
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 20, 10, 10)
        left_layout.addWidget(gbox)
        left_layout.addWidget(option_box)

        for btn in self.buttons.values():
            left_layout.addWidget(btn)
        left_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Table/Graph View
        right_layout = QVBoxLayout()

        # # ...Top chartbar
        # chart_label = QLabel("Show as:", self)
        # self.chart_box = QComboBox(self)
        # self.chart_box.addItems(("Graph", "Table"))
        #
        # chartbar_layout = QHBoxLayout()
        # chartbar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))
        # chartbar_layout.addWidget(chart_label)
        # chartbar_layout.addWidget(self.chart_box)


        # ...Chart / Table
        self.stack = stack_layout = QStackedLayout()

        wgt = QWidget(self)
        layout = QVBoxLayout(wgt)

        # Qt Charts
        self.chart_view = TimeGraph(self)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        # layout.addWidget(self.chart_view)
        self.chart_view.setSizePolicy(size_policy)
        self.chart_view.setMaximumWidth(self.chart_view.maximumHeight())

        # Matplotlib backend

        self.heading_chart = BasePlot(self, title='Heading Chart')
        self.heading_chart.add("heading")
        layout.addWidget(self.heading_chart)

        #self.inclinometer_chart = SimplePlot(self, title="Inclinometer Chart")
        self.inclinometer_chart = BasePlot(self, title='Inclinometer')
        self.inclinometer_chart.add("roll")
        self.inclinometer_chart.add("pitch")
        layout.addWidget(self.inclinometer_chart)

        self.magnitometer_chart = SimplePlot(self, title="Magnitometer Chart")
        #layout.addWidget(self.magnitometer_chart)

        stack_layout.addWidget(wgt)

        self.table_view = SensorDataTable(self)
        stack_layout.addWidget(self.table_view)

       # right_layout.addLayout(chartbar_layout)
        right_layout.addLayout(stack_layout, 2)

        # Central Layout
        centralLayout = QHBoxLayout(self)
        centralLayout.addLayout(left_layout)
        centralLayout.addLayout(right_layout, 2)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setupUi(self):
        self.setWindowTitle(f"Magnetic Lab")
        self.setMinimumSize(100, 600)

        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()

        # Central Widget
        central_widget = MagneticWidget(self)
        self.dock = QDockWidget('Dockable', self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)
        self.setCentralWidget(central_widget)

        # Environment
        self.buttons = self.centralWidget().buttons
        self.data_view = self.centralWidget().data_view
        self.options = self.centralWidget().options
        self.stack = self.centralWidget().stack

    def create_statusbar(self):
        # Statusbar
        self.status = self.statusBar()
        self.counter = QLabel("Rx: -")
        self.statusBar().addPermanentWidget(self.counter)

    def create_menu(self):
        def _action_rescan():
            available = sensor.scan_ports()
            self.portbox.clear()
            self.portbox.addItems(available)

        def _action_quit():
            QtCore.QCoreApplication.exit(0)


        menu = self.menuBar()

        file_menu = QMenu("&File", self)
        file_menu.addAction("Rescan", _action_rescan)
        file_menu.addSeparator()
        file_menu.addAction("Settings...", lambda: print("Settings..."))
        file_menu.addSeparator()
        file_menu.addAction("Export to...", lambda: print("Export to..."))
        file_menu.addAction("Import from...", lambda: print("Import from..."))
        file_menu.addSeparator()
        file_menu.addAction("Exit", _action_quit)
        menu.addMenu(file_menu)

    def create_toolbar(self):
        toolbar = self.addToolBar("File")
        toolbar.setMovable(False)

        self.buttons = {}

        # Start/Stop buttons
        self.modeButtonGroup = QButtonGroup()
        for key, icon, tooltip in (
            ('start', 'assets/start-icon.png', 'connect and run'),
            ('stop', 'assets/stop-red-icon.png', 'stop'),
            ('pause', 'assets/pause-icon.png', 'pause')
        ):
            btn = QToolButton()
            btn.setObjectName(key)
            btn.setIcon(QIcon(icon))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            if key == 'stop':
                btn.setChecked(True)

            self.modeButtonGroup.addButton(btn)
            toolbar.addWidget(btn)
            self.buttons[key] = btn
        toolbar.addSeparator()

        # Port box
        toolbar.addWidget(QLabel("Port:", self))
        self.portbox = QComboBox(self)
        toolbar.addWidget(self.portbox)
        
        # Button find serial ports
        btn = QToolButton()
        btn.setIcon(QIcon("assets/update-icon.png"))
        toolbar.addWidget(btn)
        self.buttons['rescan'] = btn
        toolbar.addSeparator()

        # Select number of samples
        self.spin = QSpinBox()
        self.spin.setValue(100)
        self.spin.setRange(100, 1000)
        self.spin.setSingleStep(100)
        self.spin.setSuffix(" samples")
        self.spin.lineEdit().setReadOnly(True)
        toolbar.addWidget(self.spin)
        toolbar.addSeparator()

        # Chart/Table view mode
        self.viewButtonGroup = QButtonGroup()
        for key, icon, tooltip in (
            ("chart", "assets/charts.png", "Chart View"),
            ("table", "assets/table.png", "Table View")
        ):
            btn = QToolButton()
            btn.setObjectName(key)
            btn.setIcon(QIcon(icon))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            if key == "chart":
                btn.setChecked(True)

            self.viewButtonGroup.addButton(btn)
            toolbar.addWidget(btn)
            self.buttons[key] = btn
        toolbar.addSeparator()

        # Records
        btn = QToolButton()
        btn.setIcon(QIcon('assets/log-icon'))
        btn.setToolTip("Logging on/off")
        btn.setCheckable(True)
        toolbar.addWidget(btn)
        self.buttons['log'] = btn

        self.lineedit = QLineEdit()
        self.lineedit.setReadOnly(True)
        self.lineedit.setDisabled(True)
        toolbar.addWidget(self.lineedit)

        self.buttons['logpath'] = btn = QPushButton("...")
        btn.setDisabled(True)
        toolbar.addWidget(btn)
        
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

        self.collection_start = False

        # Search available ports
        available_ports = sensor.scan_ports()
        self.portbox.addItems(available_ports)
        self.available = True

        # If didn't find serial ports, then disabled start buttons
        if not available_ports:
            self.status.showMessage("No available ports")
            self.buttons['connect'].setDisabled(True)
            for btn in self.modeButtonGroup.buttons():
                 btn.setDisabled(True)

        # Set model
        self.model = SensorDataModel()
        self.centralWidget().table_view.setModel(self.model)

        # Connecting signal/slot

        # ...buttons
        self.buttons["connect"].clicked.connect(self.on_connect)
        self.buttons["clear"].clicked.connect(self.on_clear)
        self.buttons["quit"].clicked.connect(self.on_quit)

        # ...button group
        self.modeButtonGroup.buttonClicked[QAbstractButton].connect(self.on_run)
        self.viewButtonGroup.buttonClicked[QAbstractButton].connect(self.on_switch_view)

        # ...comboboxs
        self.portbox.currentTextChanged[str].connect(self.on_switch_port)
        self.spin.valueChanged[int].connect(self.on_change_interval)

        # ...models
        #self.model.rowsInserted.connect(self.centralWidget().chart_view.redraw)

    def timerEvent(self, QTimerEvent):
        """ Handler timer event"""
        time = QtCore.QTime().currentTime().toString()

        # <1> Get data from sensor
        try:
            data = [round(item, 1) for item in sensor.SENSOR_QUEUE.get(timeout=0.2)]
        except queue.Empty:
            self.status.showMessage("No sensor data")
            return
        r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz = data

        # <2> Apply correction algorithms
        if self.options['dub horizont'].checkState():
            hy_raw, hx_raw, hz_raw = to_horizont(hy_raw, hx_raw, hz_raw, r, p)

        # <3> Append data to model
        self.model.append_data((r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz))

        # <4> Show to data view
        self.show_data(r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz)

        # <5> Update plot
        self.centralWidget().inclinometer_chart.update_plot(r,p)
        self.centralWidget().heading_chart.update_plot(h)

    def show_data(self, r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz):
        fmt_value = '{0:.1f}'

        self.counter.setText("Rx: {}".format(self.model.rowCount()))

        self.data_view['roll'].setText(fmt_value.format(r))
        self.data_view['pitch'].setText(fmt_value.format(p))
        self.data_view['heading'].setText(fmt_value.format(h))
        self.data_view['hyr'].setText(fmt_value.format(hy_raw))
        self.data_view['hxr'].setText(fmt_value.format(hx_raw))
        self.data_view['hzr'].setText(fmt_value.format(hz_raw))
        self.data_view['hy'].setText(fmt_value.format(hy))
        self.data_view['hx'].setText(fmt_value.format(hx))
        self.data_view['hz'].setText(fmt_value.format(hz))

    def on_run(self, btn):
        name = btn.objectName()
        if name == 'start':
            self.on_start()
        elif name == 'stop':
            self.on_stop()
        elif name == 'pause':
            self.on_stop()
            self.centralWidget().inclinometer_chart.set_time(200)

    def on_connect(self):
        self.collection_start = ~self.collection_start
        if self.collection_start:
            self.on_start()
        else:
            self.on_stop()

    def on_start(self):
        if self.collection_start:
            return

        self.on_clear()

        self.status.showMessage("Running")
        self.buttons["connect"].setText("Stop")
        self.portbox.setDisabled(True)

        port = self.portbox.currentText()
        self.serobj = serobj = serial.Serial(port, timeout=0.1)
        self.sensor = sensor.Sensor(serobj)

        self.t = threading.Thread(target=self.sensor.run, daemon=False)
        self.t.start()

        self.timer_recieve = self.startTimer(100, timerType=QtCore.Qt.PreciseTimer)
        self.collection_start = True

    def on_stop(self):
        if not self.collection_start:
            return

        self.status.showMessage("Stopped")
        self.buttons["connect"].setText("Start")
        self.portbox.setEnabled(True)

        if self.timer_recieve:
            self.killTimer(self.timer_recieve)
            self.timer_recieve = None

        self.sensor.terminate()
        self.serobj.close()
        del self.sensor
        self.collection_start = False

    def on_change_interval(self, interval):
        self.centralWidget().inclinometer_chart.set_time(interval)

    def on_clear(self):
        self.model.reset()
        self.centralWidget().chart_view.clear_area()

    def on_switch_port(self, port):
        print(f'on_switch_port(): {port}')

    def on_switch_view(self, btn):
        if btn.objectName() == 'chart':
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)

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
