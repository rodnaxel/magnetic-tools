import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from magnetic.algorithm import Algorithm
from magnetic.util import from_excel, plot

# NOTE: Uncomment if use QtDesigner file as Ui
#from magnetic.ui import magnetic_ui


class Ui(QMainWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def _centre(self):
		""" This method aligned main window related center screen """
		frameGm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerPoint = QApplication.desktop().screenGeometry(screen).center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())

	def setupUi(self):
		self.setWindowTitle(f"{__file__}")
		self.setMinimumSize(600, 500)

		# Widgets
		centralWidget = QWidget(self)
		self.setCentralWidget(centralWidget)


# NOTE: This code used to create ui with qtdesigner
# class Magnetic(QMainWindow, magnetic_ui.Ui_MainWindow):
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
# 		self.setupUi(self)

class Magnetic(Ui):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setupUi()

	def _centre(self):
		""" This method aligned main window related center screen """
		frameGm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerPoint = QApplication.desktop().screenGeometry(screen).center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())


def debug():
	dataset = from_excel(
		path='./downloads/example_dataset.xlsx',
		sheet_name='Лист6',
		rangex='H7:H51',
		rangey='I7:I51'
	)

	maxdub = Algorithm(dataset)
	ds_correct = [maxdub.correct(x, y) for (x, y) in dataset]
	print(f"\n{len(dataset)}, {dataset=}\n"
		  f"{len(ds_correct)}, {ds_correct=}")

	print(f"maxdub")
	plot(dataset, ds_correct)


def main():
	app = QApplication(sys.argv)

	if sys.platform == 'win32':
		import ctypes
		myappid = u'navi-dals.magnetic-tools.proxy.001'  # arbitrary string
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
		app.setWindowIcon(QIcon(':/rc/Interdit.ico'))

	magnetic = Magnetic()
	magnetic._centre()
	magnetic.show()

	sys.exit(app.exec_())


if __name__ == '__main__':
	main()

