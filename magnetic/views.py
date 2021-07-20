from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableView, QHeaderView


class SensorDataTable(QTableView):
	def __init__(self, parent):
		super().__init__(parent)

		self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
		self.horizontalHeader().setSectionsMovable(True)
		self.horizontalHeader().setStretchLastSection(False)
		self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignJustify)