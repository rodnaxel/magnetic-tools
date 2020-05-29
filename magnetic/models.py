from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor


class SensorDataModel(QAbstractTableModel):
    """ The model represented sensor data (by dorient)"""
    # section_names = ("Hx", "Hy", "Hz", "Heading", "Roll", "Pitch")
    section_names = ("Hx", "Hy")
    cols = len(section_names)

    def __init__(self, data: list = None):
        super().__init__()
        self._data = data or []

        self.cell_color = Qt.white

    def load_data(self, data: list):
        self._data = data

    def fetch_data(self):
        return self._data

    def append_item(self, bx: float, by: float):
        r = len(self._data)
        self.beginInsertRows(QModelIndex(), r, r)
        self._data.append((bx, by))
        self.endInsertRows()

    def rowCount(self, parent=None, *args, **kwargs):
        if not (parent.isValid() or self._data):
            return 0
        return len(self._data)

    def columnCount(self, parent=None, *args, **kwargs):
        if not (parent.isValid() or self._data):
            return len(self.section_names)
        return self.cols

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.section_names[section]
        else:
            return "{}".format(section + 1)

    def data(self, index, role=Qt.DisplayRole):
        if self._data:
            if role == Qt.DisplayRole:
                try:
                    return self._data[index.row()][index.column()]
                except IndexError:
                    return None
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignRight
            elif role == Qt.BackgroundRole:
                return QColor(self.cell_color)
        else:
            return None

    def flags(self, index):
        result = super().flags(index)
        if index.column() in [0, 1]:
            result &= ~Qt.ItemIsEditable
        return result

    def reset(self):
        self.beginResetModel()
        self._data = []
        self.endResetModel()
