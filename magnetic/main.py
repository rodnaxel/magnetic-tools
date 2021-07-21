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
from chart.mpl_chart import TimePlot
from models import SensorDataModel
from views import SensorDataTable
from util import get_arguments

from calibrate import Calibrate

# For run in Raspberry Pi
if platform.machine() == "armv7l":
    # os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_FB_FORCE_FULLSCREEN "] = "0"
    PORT_NAME = "/dev/ttyUSB1"

else:
    PORT_NAME = "/dev/ttyUSB0"

ROOT = os.path.dirname(__file__)
REPORT_PATH = os.path.join(ROOT, 'reports')


class MagneticWidget(QDialog):
    """
    Виджет логгера
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Data View
        self.data_view = {}
        #gbox = QGroupBox("Sensor Data" + ":")
        gbox = QFrame(self)
        gbox.setFrameStyle(QFrame.Box | QFrame.Sunken)
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
        option_box = QGroupBox("Apply algorithm:")
        option_layout = QVBoxLayout(option_box)
        for name in ("dub z", "dub soft-iron"):
            check = QCheckBox(name)
            check.setCheckState(False)
            option_layout.addWidget(check)
            self.options[name] = check

        # Layouts
        dataview_layout = QVBoxLayout()
        dataview_layout.setContentsMargins(0, 0, 0, 0)
        dataview_layout.addWidget(gbox)
        dataview_layout.addWidget(option_box)
        dataview_layout.addSpacerItem(QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Table/Graph View
        right_layout = QVBoxLayout()

        # ...Chart / Table
        self.stack = stack_layout = QStackedLayout()

        self.frame = frame = QFrame(self)
        frame.setFrameStyle(QFrame.Box | QFrame.Sunken)

        # layout = QVBoxLayout(wgt)
        layout = QVBoxLayout(frame)
        #layout.setContentsMargins(0,0,0,0)
        # layout.setSpacing(0)


        # Графики
        self.charts = {}

        # График курса
        self.charts['heading'] = chart = TimePlot(self, title='Heading')
        chart.add("heading")
        layout.addWidget(chart)

        # График крена и диффирента
        self.charts['inclinometer'] = chart = TimePlot(
            self, title='Inclinometer')
        chart.add("roll")
        chart.add("pitch")
        layout.addWidget(chart)

        # График трех составляющих магнитного поля (Hy, Hx, Hz)
        self.charts['magnitometer'] = chart = TimePlot(
            self, title='Magnitometer')
        chart.add("hy")
        chart.add("hx")
        chart.add("hz")
        layout.addWidget(chart)

        stack_layout.addWidget(frame)

        # Таблица данных
        self.table_view = SensorDataTable(self)
        stack_layout.addWidget(self.table_view)

        right_layout.addLayout(stack_layout, 2)

        # Central Layout
        centralLayout = QHBoxLayout(self)
        centralLayout.addLayout(dataview_layout)
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
        self.setCentralWidget(central_widget)

        # Dock widgets
        #self.create_dock()

        # Environment
        self.charts = self.centralWidget().charts
        self.data_view = self.centralWidget().data_view
        self.table_view = self.centralWidget().table_view
        self.options = self.centralWidget().options
        self.stack = self.centralWidget().stack
        self.frame = self.centralWidget().frame

    def create_dock(self):
        self.dock = dock = QDockWidget("Sensors", self)

        wgt = QWidget()
        gbox_layout = QHBoxLayout(wgt)
        dock.setWidget(wgt)
        dock.setFloating(False)

        for name in ('roll', 'pitch', 'heading', 'hyr', 'hxr', 'hzr', 'hy', 'hx', 'hz'):
            label = QLabel("-")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setMinimumWidth(80)
            label.setMaximumHeight(40)
            label.setStyleSheet("QLabel {font: 16px; background-color: white}")
            label.setFrameShape(QFrame.StyledPanel)

            layout = QHBoxLayout()
            layout.addWidget(QLabel(name.capitalize()))
            layout.addWidget(label)

            gbox_layout.addLayout(layout)
        gbox_layout.addSpacerItem(QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)

    def create_statusbar(self):
        # Statusbar
        self.status = self.statusBar()
        self.counter = QLabel("Rx: -")
        self.statusBar().addPermanentWidget(self.counter)

    def _action_rescan(self):
        # TODO: Move to app
        available = sensor.scan_ports()
        if available:
            self.portbox.clear()
            self.portbox.addItems(available)
            self.status.showMessage("Find ports", 1000)
        else:
            self.status.showMessage("No available port", 1000)

    def create_menu(self):

        def _action_quit():
            # TODO: move to App
            QtCore.QCoreApplication.exit(0)

        self.menus = {}
        menu = self.menuBar()

        # File menu
        file_menu = QMenu("&File", self)
        file_menu.addAction("Rescan", self._action_rescan)
        file_menu.addSeparator()
        file_menu.addAction("Settings...", lambda: print("Settings..."))
        file_menu.addSeparator()
        file_menu.addAction("Export to...", lambda: print("Export to..."))
        file_menu.addAction("Import from...", lambda: print("Import from..."))
        file_menu.addSeparator()
        file_menu.addAction("Exit", _action_quit)
        menu.addMenu(file_menu)
        self.menus['file'] = file_menu

    def create_toolbar(self):
        toolbar = self.addToolBar("File")
        toolbar.setMovable(False)

        self.toolbar_buttons = {}

        # Start/Stop buttons
        self.modeButtonGroup = QButtonGroup()
        for key, icon, tooltip in (
                ('start', 'assets/start-icon.png', 'connect and run'),
                ('stop', 'assets/stop-red-icon.png', 'stop')
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
            self.toolbar_buttons[key] = btn
        toolbar.addSeparator()

        # Port box
        toolbar.addWidget(QLabel("Port:", self))
        self.portbox = QComboBox(self)
        toolbar.addWidget(self.portbox)

        # Button find serial ports
        btn = QToolButton()
        btn.setIcon(QIcon("assets/update-icon.png"))
        btn.setToolTip("Repeat search serial ports")
        toolbar.addWidget(btn)
        self.toolbar_buttons['rescan'] = btn
        self.toolbar_buttons['rescan'].clicked.connect(self._action_rescan)
        toolbar.addSeparator()

        # Select number of samples
        self.spin = QSpinBox()
        self.spin.setValue(100)
        self.spin.setRange(100, 1000)
        self.spin.setSingleStep(100)
        self.spin.setSuffix(" samples")
        self.spin.lineEdit().setReadOnly(True)
        self.spin.setToolTip("Set x interfall for all charts")
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
            self.toolbar_buttons[key] = btn

        btn = QToolButton()
        btn.setIcon(QIcon('assets/compass-icon'))
        btn.setCheckable(True)
        self.toolbar_buttons['compensate'] = btn
        toolbar.addWidget(btn)

        toolbar.addSeparator()

        btn = QToolButton()
        btn.setIcon(QIcon('assets/log-icon'))
        btn.setToolTip("Logging on/off")
        btn.setCheckable(True)
        self.toolbar_buttons['log_on'] = btn
        toolbar.addWidget(btn)

        # Records bar
        self.addToolBarBreak()
        self.record_bar = record_bar = QToolBar()
        record_bar.setMovable(False)
        record_bar.setHidden(True)

        self.addToolBar(QtCore.Qt.BottomToolBarArea, record_bar)

        record_bar.addWidget(QLabel("Path: "))

        self.lineedit = QLineEdit()
        self.lineedit.setReadOnly(True)
        self.lineedit.setText(os.path.join(ROOT, 'reports', 'log.csv'))
        record_bar.addWidget(self.lineedit)

        self.toolbar_buttons['select_path'] = btn = QPushButton("...")
        record_bar.addWidget(btn)

    def centre(self):
        """ This method aligned main window related center screen """
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())


class MagneticApp(MainWindow):
    app_title = "Magnetic Viewer - {0}"
    TIMEOUT = 100
    TIMEOUT_QUEUE = 0.05

    def __init__(self, data=None, title=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi()

        # Start/Stop monitor sensor data
        self.monitor_running = False

        # Start/Stop compensate
        self.compensate = False
        self.initial_heading = None

        # On/Off logging data
        self.logging_enable = False

        # Search available serial ports
        available_ports = sensor.scan_ports()
        if not available_ports:
            self.status.showMessage("No available ports")
            for btn in self.modeButtonGroup.buttons():
                btn.setDisabled(True)
        else:
            self.portbox.addItems(available_ports)

        # Connecting model to consumers
        self.model = SensorDataModel()
        self.centralWidget().table_view.setModel(self.model)

        # Connecting signal/slot
        # ...button
        self.toolbar_buttons['compensate'].clicked.connect(self.on_compensate)
        self.toolbar_buttons['log_on'].clicked.connect(self.turn_logging)
        self.toolbar_buttons['select_path'].clicked.connect(
            self.on_select_path)

        # ...button group
        self.modeButtonGroup.buttonClicked[QAbstractButton].connect(
            self.on_run)
        self.viewButtonGroup.buttonClicked[QAbstractButton].connect(
            self.on_switch_view)

        # ...comboboxs
        self.spin.valueChanged[int].connect(self.on_set_chart_xinterval)

        # ...models
        #self.model.rowsInserted.connect(self.on_model_changed)

    def on_model_changed(self):
        print('On model changed')

    def timerEvent(self, QTimerEvent):
        """ Handler timer event, every 100ms"""

        # <1> Get data from sensor
        try:
            data = [round(item, 1) for item in sensor.SENSOR_QUEUE.get(timeout=self.TIMEOUT_QUEUE)]
        except queue.Empty:
            self.status.showMessage("No sensor data")
            return
        pid, r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz = data

        # <2> Apply correction algorithms
        if self.options['dub z'].checkState():
            hy_raw, hx_raw, hz_raw = to_horizont(hy_raw, hx_raw, hz_raw, r, p)

        # <3> Append data to model
        self.model.append_data((r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz))

        # <4> Show to data view
        self.show_data(r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz)

        # <5> Update plot
        #self.charts['inclinometer'].update_plot(r, p)
        #self.charts['heading'].update_plot(h)
        #self.charts['magnitometer'].update_plot(hy, hx, hz)

        # <6> Logging data
        if self.logging_enable:
            time = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
            path = self.lineedit.text()
            str_data = ",".join((str(x) for x in (time, hex(pid), r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz)))
            str_data += '\n'
            self.status.showMessage(time)
            with open(path, 'a') as f:
                f.write(str_data)

        # <7> Compensate mode
        if self.compensate:
            self.calibrate.update(data)
            # time = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
            # path = self.lineedit.text()
            # #str_data = ",".join((str(x) for x in (time, hex(pid), r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz)))
            # str_data = ",".join((str(x) for x in (hy, hx)))
            # str_data += '\n'
            # with open(path, 'a') as f:
            #     f.write(str_data)

    def show_data(self, r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz):
        """ Show sensor data to data view"""
        fmt_value = '{0:.1f}'

        # Indicator recieve message
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

    def on_start(self):
        if self.monitor_running:
            return

        # Disable widgets
        self.portbox.setDisabled(True)
        self.toolbar_buttons['select_path'].setDisabled(True)
        self.toolbar_buttons['rescan'].setDisabled(True)

        # ...disable action rescan
        self.menus['file'].children()[1].setDisabled(True)

        # Set selectable port to sensor
        port = self.portbox.currentText()
        self.serobj = serobj = serial.Serial(port, timeout=0.1)
        self.sensor = sensor.Sensor(serobj)

        # Run recieve data to single thread
        self.t = threading.Thread(target=self.sensor.run, daemon=False)
        self.t.start()

        # Run timer
        self.timer_recieve = self.startTimer(
            self.TIMEOUT, timerType=QtCore.Qt.PreciseTimer)

        self.status.showMessage("Running")
        self.monitor_running = True

    def on_stop(self):
        if not self.monitor_running:
            return

        self.status.showMessage("Stopped")

        # Enable widgets
        self.portbox.setEnabled(True)
        self.toolbar_buttons['rescan'].setEnabled(True)

        # ...enable action rescan
        self.menus['file'].children()[1].setEnabled(True)

        # Kill timer
        if self.timer_recieve:
            self.killTimer(self.timer_recieve)
            self.timer_recieve = None

        # terminate thread
        self.sensor.terminate()
        self.t.join(timeout=0.1)

        # Close port
        self.serobj.close()
        del self.sensor

        self.monitor_running = False

    def on_clear(self):
        self.model.reset()
        self.centralWidget().chart_view.clear_area()

    def on_switch_view(self, btn):
        if btn.objectName() == 'chart':
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)

    def on_compensate(self):
        """ Обработка нажатие кнопки <Компенсация>"""

        if not self.compensate:
            self.compensate = True
            self.toolbar_buttons['compensate'].setChecked(True)
            self.status.showMessage('Start compensate', 1000)
            self.calibrate = Calibrate()
        else:
            self.compensate = False
            self.toolbar_buttons['compensate'].setChecked(False)
            self.status.showMessage('Stop compensate', 1000)
            self.calibrate.compute()
            del self.calibrate
    
    def turn_logging(self):
        ''' On/Off logging. If logging ON then bottombar visible '''
        self.logging_enable = ~self.logging_enable

        if self.logging_enable:
            self.record_bar.setVisible(True)
        else:
            self.record_bar.setVisible(False)

    def on_set_chart_xinterval(self, interval):
        for chart in self.charts.values():
            chart.set_xmax(interval)

    def on_select_path(self):
        ''' Select path to save log '''
        if not os.path.exists(REPORT_PATH):
            try:
                os.mkdir(REPORT_PATH)
            except OSError:
                self.status.showMessage("Error creating path", 2000)

        fname, _ = QFileDialog.getSaveFileName(
            self, "Select Path", REPORT_PATH, "Log (*.log)"
        )

        if fname:
            self.lineedit.setText(fname)


def main():
    app = QApplication(sys.argv)

    if sys.platform == 'win32':
        import ctypes
        myappid = u'navi-dals.magnetic-tools.proxy.001'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        app.setWindowIcon(QIcon(':/rc/Interdit.ico'))

    magnetic = MagneticApp()
    magnetic.centre()
    magnetic.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    args = get_arguments()
    main()
