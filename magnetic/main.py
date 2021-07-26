import os
import sys
import platform
import threading
import queue

import serial
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sensor
from algorithms import to_horizont
from calibrate import Calibrate
from chart.mpl_chart import TimePlot, XYPlot
from models import SensorDataModel
from util import get_arguments
from views import SensorDataTable


# For run in Raspberry Pi
if platform.machine() == "armv7l":
    # os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_FB_FORCE_FULLSCREEN "] = "0"
    PORT_NAME = "/dev/ttyUSB1"

else:
    PORT_NAME = "/dev/ttyUSB0"

ROOT = os.path.dirname(__file__)
REPORT_PATH = os.path.join(ROOT, 'logs')
print(REPORT_PATH)



class DataView(QFrame):
    def __init__(self, parent=None, fmt='{0:.1f}', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        
        self.layout = QVBoxLayout(self)

        self.views = {}
        self.fmt = fmt

        self.create()

    def create(self):
        for name in ('roll', 'pitch', 'heading', 'hyr', 'hxr', 'hzr', 'hy', 'hx', 'hz'):
            label = QLabel("-")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setMinimumWidth(80)
            label.setStyleSheet("QLabel {font: 16px; background-color: white}")
            label.setFrameShape(QFrame.StyledPanel)
            layout = QHBoxLayout()
            layout.addWidget(QLabel(name.capitalize()))
            layout.addWidget(label)
            self.layout.addLayout(layout)
            self.views[name] = label

    def setValue(key, value, fmt_value='{0:.1f}'):
        self.views[key].setText(self.fmt.format(value))

    def value(key):
        return self.views[key].text()

    def update(self, r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz, fmt_value='{0:.1f}'):
        """ Show sensor data to data view"""
        self.views['roll'].setText(fmt_value.format(r))
        self.views['pitch'].setText(fmt_value.format(p))
        self.views['heading'].setText(fmt_value.format(h))
        self.views['hyr'].setText(fmt_value.format(hy_raw))
        self.views['hxr'].setText(fmt_value.format(hx_raw))
        self.views['hzr'].setText(fmt_value.format(hz_raw))
        self.views['hy'].setText(fmt_value.format(hy))
        self.views['hx'].setText(fmt_value.format(hx))
        self.views['hz'].setText(fmt_value.format(hz))


class OptionsBox(QGroupBox):
    def __init__(self, title, option_names, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTitle(title)
        self.layout = QVBoxLayout(self)

        self.option_names = option_names
        self.options = {}

        self.create()

    def create(self):
        for name in self.option_names:
            check = QCheckBox(name)
            check.setCheckState(False)
            self.layout.addWidget(check)
            self.options[name] = check        


class MagneticMonitor(QDialog):
    """ UI """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        dv_widget = DataView(self)
        self.data_view = dv_widget.views

        dv_widget2 = DataView(self)
        self.data_view2 = dv_widget2.views

        option_box = OptionsBox(title="Algorithm",
            option_names=("dub z", "dub soft-iron", "update charts" ))
        self.options = option_box.options

        # Left dock layouts 
        left_dock = QVBoxLayout()
        left_dock.setContentsMargins(0, 0, 0, 0)
        left_dock.addWidget(dv_widget)
        left_dock.addWidget(dv_widget2)
        left_dock.addWidget(option_box)
        left_dock.addSpacerItem(QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding))


        # Table/Graph View

        # ...Chart / Table
        frame = QFrame(self)
        frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        layout = QVBoxLayout(frame)
        self.frame = frame

        # Графики
        self.charts = {}

        # График курса
        chart = TimePlot(self, title='Heading')
        chart.add_line("heading")
        layout.addWidget(chart)
        self.charts['heading'] = chart

        # График крена и диффирента
        chart = TimePlot(self, title='Inclinometer')
        chart.add_lines(["roll", "pitch"])
        layout.addWidget(chart)
        self.charts['inclinometer'] = chart

        # График трех составляющих магнитного поля (Hy, Hx, Hz)
        chart = TimePlot(self, title='Magnitometer')
        chart.add_lines(("hy", "hx", "hz"))
        layout.addWidget(chart)
        self.charts['magnitometer'] = chart

        stack_layout = self.stack = QStackedLayout()
        stack_layout.addWidget(self.frame)

        # Таблица данных
        self.table_view = SensorDataTable(self)
        stack_layout.addWidget(self.table_view)

        # График зависимости Hx от Hy
        chart = XYPlot()
        self.charts['deviation'] = chart
        stack_layout.addWidget(chart)

        content_layout = QVBoxLayout()
        content_layout.addLayout(stack_layout, 2)

        # Central Layout
        centralLayout = QHBoxLayout(self)
        centralLayout.addLayout(left_dock)
        centralLayout.addLayout(content_layout, 2)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setupUi(self):
        self.setWindowTitle(f"Magnetic Monitor (special for Max Dub)")
        self.setMinimumSize(100, 600)

        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()

        self.setCentralWidget(MagneticMonitor(self))

        # Dock widgets
        # self.create_dock()

        # Environment
        self.charts = self.centralWidget().charts
        self.data_view = self.centralWidget().data_view
        self.data_view2 = self.centralWidget().data_view2
        self.table_view = self.centralWidget().table_view
        self.options = self.centralWidget().options
        self.stack = self.centralWidget().stack
        self.frame = self.centralWidget().frame

    def create_dock(self):
        dock = QDockWidget("Sensors", self)
        dock.setFloating(False)

        wgt = QWidget()
        dock.setWidget(wgt)
    
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        
        self.dock = dock

    def create_statusbar(self):
        self.status = self.statusBar()
        self.counter = QLabel("Rx: -")
        self.statusBar().addPermanentWidget(self.counter)
        self.errors = QLabel("Err: -")
        self.statusBar().addPermanentWidget(self.errors)

    def create_menu(self):
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
        file_menu.addAction("Exit", self._action_quit)
        menu.addMenu(file_menu)
        self.menus['file'] = file_menu

    def create_toolbar(self):
        self.create_mainbar()
        self.create_compensationbar()
        self.create_recordbar()

    def create_mainbar(self):
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

        # Buttons for switch modes (charts/table/deviation)
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
        
        #
        btn = QToolButton()
        btn.setObjectName("compensate")
        btn.setIcon(QIcon('assets/compass-icon'))
        btn.setCheckable(True)
        self.viewButtonGroup.addButton(btn)
        toolbar.addWidget(btn)
        self.toolbar_buttons['compensate'] = btn
        
        toolbar.addSeparator()
        
        #
        btn = QToolButton()
        btn.setIcon(QIcon('assets/log-icon'))
        btn.setToolTip("Logging on/off")
        btn.setCheckable(True)
        toolbar.addWidget(btn)
        self.toolbar_buttons['log_on'] = btn

    def create_compensationbar(self):
        # Compensation bar
        self.addToolBarBreak()
        compensation_bar = QToolBar()
        compensation_bar.setMovable(False)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, compensation_bar)
        
        collection_btn = QPushButton("Collection")
        compensation_bar.addWidget(collection_btn)
        self.toolbar_buttons['collection'] = collection_btn
        
        check = QCheckBox('Auto')
        compensation_bar.addWidget(check)
        
        progress = QProgressBar()
        progress.setMaximum(36)
        progress.setValue(0)
        self.progress = progress
        compensation_bar.addWidget(progress)
        
        self.compensation_bar = compensation_bar

    def create_recordbar(self):
        self.addToolBarBreak(QtCore.Qt.BottomToolBarArea)
        record_bar = QToolBar()
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
        
        self.record_bar = record_bar

    def _action_rescan(self):
        # TODO: Move to app
        available = sensor.scan_ports()
        if available:
            self.portbox.clear()
            self.portbox.addItems(available)
            self.status.showMessage("Find ports", 1000)
        else:
            self.status.showMessage("No available port", 1000)

    def _action_quit(self):
        """ Для корректного завершения потока функция определяется в классе App """
        raise NotImplementedError

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
    TIMEOUT_QUEUE = 0.5

    def __init__(self, data=None, title=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi()

        self.errors_data = 0

        # Start/Stop monitor sensor data
        self.monitor_running = False

        # Start/Stop compensate
        self.compensate = False

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
        self.toolbar_buttons['collection'].clicked.connect(self.on_compensate)
        self.toolbar_buttons['log_on'].clicked.connect(self.turn_logging)
        self.toolbar_buttons['select_path'].clicked.connect(self.on_select_path)

        # ...button group
        self.modeButtonGroup.buttonClicked[QAbstractButton].connect(
            self.on_run)
        self.viewButtonGroup.buttonClicked[QAbstractButton].connect(
            self.on_switch_mode)

        # ...comboboxs
        self.spin.valueChanged[int].connect(self.on_set_chart_xinterval)

        # ...models
        # self.model.rowsInserted.connect(self.on_model_changed)

    def on_model_changed(self):
        print('On model changed')

    def timerEvent(self, QTimerEvent):
        """ Handler timer event, every 100ms"""

        # <1> Get data from sensor
        try:
            data = [round(item, 1) for item in sensor.SENSOR_QUEUE.get(timeout=self.TIMEOUT_QUEUE)]
        except queue.Empty:
            self.status.showMessage("No sensor data")
            
            if self.errors_data <= 10000:
                self.errors_data += 1
                self.errors.setText("Err: {}".format(self.errors_data))
            else:
                self.errors.setText("Err: {}".format(">10000"))

            return

        pid, r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz = data

        # <2> Append data to model
        self.model.append_data((r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz))

        # Indicator recieve message
        self.counter.setText("Rx: {}".format(self.model.rowCount()))

        # <3> Apply correction algorithms
        if self.options['dub z'].checkState():
            hy_raw, hx_raw, hz_raw = to_horizont(hy_raw, hx_raw, hz_raw, r, p)

        # <4> Show to data view
        self.show_data(r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz)

        if self.options['dub soft-iron'].checkState():
            try:
                heading = self.maxdub.correct_heading(hx, hy)
                fmt_value = '{0:.1f}'
                self.data_view2['heading'].setText(fmt_value.format(heading))
            except AttributeError:
                self.options['dub soft-iron'].setCheckState(False)
                self.status.showMessage("Error! Please, calibrate", 1000)

        # <5> Update plot
        if self.options['update charts'].checkState():
            #self.charts['inclinometer'].update_plot(r, p)
            #self.charts['heading'].update_plot(h)
            #self.charts['magnitometer'].update_plot(hy, hx, hz)
            self.charts['deviation'].update_plot(hy, hx)

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
            self.progress.setValue(self.calibrate.status())
            time = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
            path = self.lineedit.text()
            #str_data = ",".join((str(x) for x in (time, hex(pid), r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz)))
            str_data = ",".join((str(x) for x in (hy, hx)))
            str_data += '\n'
            with open(path, 'a') as f:
                f.write(str_data)

    def show_data(self, r, p, h, hy_raw, hx_raw, hz_raw, hy, hx, hz, fmt_value='{0:.1f}'):
        """ Show sensor data to data view"""
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

        self.status.showMessage("Stop")

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

    def on_switch_mode(self, btn):
        btn_name = btn.objectName()
        if btn_name == 'chart':
            self.stack.setCurrentIndex(0)
        elif btn_name == 'table':
            self.stack.setCurrentIndex(1)
        elif btn_name == 'compensate':
            self.stack.setCurrentIndex(2)
            import subprocess
            subprocess.run(["python", "magnetic_viewer.py"])
        else:
            self.stack.setCurrentIndex(0)

    def on_compensate(self):
        if not self.monitor_running:
            self.status.showMessage("Please, connect sensor")
            return

        if not self.compensate:
            self.toolbar_buttons['collection'].setText('Stop')

            initial = float(self.data_view['heading'].text())
            self.calibrate = Calibrate(initial)

            self.compensate = True
            self.status.showMessage('Start compensate', 1000)
        else:
            self.toolbar_buttons['collection'].setText('Collection')
            self.progress.setValue(0)

            self.maxdub = self.calibrate.compute()
            del self.calibrate

            self.compensate = False
            self.status.showMessage('Stop compensate', 1000)

    def turn_logging(self):
        """ On/Off logging. If logging ON then bottombar visible """
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

    def closeEvent(self, QCloseEvent):
        self._action_quit()

    def _action_quit(self):
        try:
            self.sensor.terminate()
            self.t.join(timeout=0.1)
        except AttributeError:
            pass
        QtCore.QCoreApplication.exit(0)


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
