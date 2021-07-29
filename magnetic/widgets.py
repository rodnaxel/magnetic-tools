from PyQt5 import QtCore
from PyQt5.QtWidgets import *


class SensorDataTable(QTableView):
	def __init__(self, parent):
		super().__init__(parent)

		self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
		self.horizontalHeader().setSectionsMovable(True)
		self.horizontalHeader().setStretchLastSection(False)
		self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignJustify)


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