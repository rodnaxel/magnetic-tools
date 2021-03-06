import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class EllipsoidPlot(FigureCanvas):
    def __init__(self, parent=None, width=5, height=5, dpi=100,
                 cursor_visible=False,
                 title='', ylabel='', xlabel=''):
        self.fig = fig = Figure(figsize=(width, height), dpi=dpi)
        fig.suptitle(title, fontsize=10)

        self.axes = fig.add_subplot(111)
        self.axes.set_xlim(-50, 50)
        self.axes.set_ylim(-50, 50)
        self.axes.grid()

        super(EllipsoidPlot, self).__init__(fig)

    def set_data(self, xdata, ydata):
        self.axes.plot(xdata, ydata, marker='.', markeredgewidth=0.7, linewidth=0.5)
        self.draw()

    def clear(self):
        self.axes.cla()

    def update_plot(self, x, y):
        self.axes.cla()
        self.ydata.append(y)
        self.xdata.append(x)

        self.axes.scatter(self.xdata, self.ydata)
        self.draw()


class TimePlot(FigureCanvas):
    xmax = 100
    xmin = 0

    def __init__(self, parent=None, width=5, height=5, dpi=100, cursor_visible=False,
                 title='', ylabel='', xlabel=''):

        self.fig = fig = Figure(figsize=(width, height), dpi=dpi)
        fig.suptitle(title, fontsize=10)

        self.axes = fig.add_subplot(111)
        self.axes.set_xlim(self.xmin, self.xmax)
        self.axes.grid()

        super(TimePlot, self).__init__(fig)

        self.xdata = []
        self.tick = 0

        # self.text = self.axes.text(102, 0, '*', color='b', bbox=dict(facecolor='white', alpha=0.5))
        # self.text = self.axes.text(self.xmax+1, 0, '*')

        self.text_values = []

        # Cursor on/off
        if cursor_visible:
            self.cursor = Cursor(self.axes)
            fig.canvas.mpl_connect('motion_notify_event', self.cursor.on_mouse_move)

    def set_xmax(self, xmax):
        self.xmax = xmax
        self.axes.set_xlim(0, self.xmax)
        self.draw()

    def add(self, label):
        self.line, = self.axes.plot([], [], lw=1, label=label)
        self.legend = self.axes.legend()

        txt = self.axes.text(self.xmax + 1, 0, '')
        txt.set_color(self.legend.get_lines()[-1].get_color())
        self.text_values.append(txt)

    def remove(self, label):
        pass

    def clear(self):
        self.axes.cla()

    def update_plot(self, *ydatas):

        # Set new data
        if self.tick <= self.xmax:
            # update x
            self.xdata.append(self.tick)
            self.tick += 1

            # update y
            for line, y in zip(self.axes.get_lines(), ydatas):
                ydata = list(line.get_ydata())
                ydata.append(y)
                line.set_data(self.xdata, ydata)
        else:
            for line, y in zip(self.axes.get_lines(), ydatas):
                ydata = list(line.get_ydata())[1:]
                ydata.append(y)
                line.set_data(self.xdata, ydata)

        # Autoscale
        if self.tick == 1:
            max_ydatas, min_ydatas = max(ydatas), min(ydatas)
            self.axes.set_ylim(min_ydatas - 5, max_ydatas + 5)
        else:
            ymin, ymax = self.axes.get_ylim()
            max_ydatas, min_ydatas = max(ydatas), min(ydatas)
            ymin = ymin if min_ydatas > ymin else (min_ydatas - 1)
            ymax = ymax if max_ydatas < ymax else (max_ydatas + 1)
            self.axes.set_ylim(ymin, ymax)

        for t, v in zip(self.text_values, ydatas):
            t.set_text("{}".format(v))
            t.set_position((self.xmax + 1, v))

        self.draw()


class SimplePlot(FigureCanvas):
    xmax = 100
    xmin = 0

    def __init__(self, parent=None, width=5, height=5, dpi=100, cursor_visible=False,
                 title='', ylabel='', xlabel=''):

        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.suptitle(title, fontsize=10)

        self.axes = fig.add_subplot(111)
        self.axes.set_xlim(self.xmin, self.xmax)
        self.axes.set_ylim(-5, 5)
        self.axes.grid()

        super(SimplePlot, self).__init__(fig)

        self.ydata = []
        self.ydata2 = []

        self.xdata = []
        self.x = 0

        self.line, = self.axes.plot([],[], lw=1, label='roll')
        self.line2, = self.axes.plot([], [], lw=1, label='pitch')

        self.axes.legend()

        if cursor_visible:
            self.cursor = Cursor(self.axes)
            fig.canvas.mpl_connect('motion_notify_event', self.cursor.on_mouse_move)

    def autoscale_axes(self):
        pass

    def update_plot(self, y, y2):
        #print(self.axes.get_lines()[0].get_label())

        if self.x <= self.xmax:
            self.ydata.append(y)
            self.ydata2.append(y2)
            self.xdata.append(self.x)
            self.x += 1
        else:
            self.ydata = self.ydata[1:] + [y]
            self.ydata2 = self.ydata2[1:] + [y2]

        # Scale axes
        ymin, ymax = self.axes.get_ylim()
        if max((y, y2)) > ymax:
            self.axes.set_ylim(ymin, y + 1)
        if min((y,y2)) < ymin:
            self.axes.set_ylim(y-1, ymax)

        # Set new data
        self.line.set_data(self.xdata, self.ydata)
        self.line2.set_data(self.xdata, self.ydata2)

        self.draw()

    def clear(self):
        self.axes.cla()


class Cursor:
    """
    A cross hair cursor.
    """
    def __init__(self, ax):
        self.ax = ax
        self.horizontal_line = ax.axhline(color='k', lw=0.8, ls='--')
        self.vertical_line = ax.axvline(color='k', lw=0.8, ls='--')

        # text location in axes coordinates
        self.text = ax.text(0.72, 0.9, '', transform=ax.transAxes)

    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def on_mouse_move(self, event):
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.draw()
        else:
            self.set_cross_hair_visible(True)
            x, y = event.xdata, event.ydata
            # update the line positions
            self.horizontal_line.set_ydata(y)
            self.vertical_line.set_xdata(x)
            self.text.set_text('x=%1.2f, y=%1.2f' % (x, y))
            self.ax.figure.canvas.draw()