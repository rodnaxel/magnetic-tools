from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtGui import QColor


class SensorDataModel(QAbstractTableModel):
	""" The model represented sensor data"""
	
	def __init__(self, data=None):
		super().__init__()
		self._data = data or []
	
	def load(self, data):
		self._data = data

	def append(self, row):
		# TODO: Bad way, because get access data directly
		self._data.append(row)
		self.layoutChanged.emit()

	def rowCount(self, parent=None, *args, **kwargs):
		return len(self._data) or 0

	def columnCount(self, parent=None, *args, **kwargs):
		try:
			column_count = len(self._data[0])
		except IndexError:
			column_count = 2
		return column_count

	def headerData(self, section, orientation, role):
		if role != Qt.DisplayRole:
			return None
		if orientation == Qt.Horizontal:
			return ("Hx", "Hy")[section]
		else:
			return "{}".format(section)

	def data(self, index, role=Qt.DisplayRole):
		if self._data:
			if role == Qt.DisplayRole:
				return self._data[index.row()][index.column()]
			elif role == Qt.TextAlignmentRole:
				return Qt.AlignRight
			elif role == Qt.BackgroundRole:
				return QColor(Qt.white)
		else:
			return None
	
	def flags(self, index):
		result = super().flags(index)
		if index.column() in [0, 1]:
			result &= ~Qt.ItemIsEditable
		return result
