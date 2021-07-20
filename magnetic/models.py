from builtins import super

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor


class SensorDataModel(QAbstractTableModel):
    """ The model represented sensor data (by dorient)"""
    section_names = ("Roll", "Pitch", "Heading", "Hyr", "Hxr", "Hzr", "Hy", "Hx", "Hz")
    cols = len(section_names)
    
    def __init__(self, data: list = None):
        super().__init__()
        self._data = data or []

        self.cell_color = Qt.white
        self.cell_color2 = Qt.white

    def load_data(self, data: list):
        self._data = data
        self.modelReset.emit()

    def fetch_data(self):
        return self._data

    def append_data(self, values):
        r = self.rowCount()
        self.beginInsertRows(QModelIndex(), r, r)
        self._data.append(values)
        self.endInsertRows()

    def rowCount(self, parent=None, *args, **kwargs):
        if not self._data:
            return 0
        return len(self._data)

    def columnCount(self, parent=None, *args, **kwargs):
        if not self._data:
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
                    #print(f"Error: {index.row()=},{index.column()=}")
                    return None
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignRight
            elif role == Qt.BackgroundRole:
                if index.column() > 1:
                    return QColor(self.cell_color2)
                else:
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


class SensorFieldModel(SensorDataModel):
    section_names = ("Hx", "Hy", "Hxc", "Hyc" )
    cols = len(section_names)
    
    def __init__(self, data: list = None):
        super(SensorFieldModel, self).__init__(data)