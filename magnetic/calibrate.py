from algorithms import Algorithm
from util import to_csv


class Logger(object):
    pass


class Calibrate(object):

    def __init__(self, initial):
        print("Create instance of Calibrate")
        self.data = []
        self.result = []

        self.progress = set()

    def status(self):
        return len(self.progress)

    def is_complete(self, value):
        self.progress.add(int(value/10))

        if len(self.progress) == 36:
            return True
        else:
            return False

    def compute(self):
        print("Compute start")
        maxdub = Algorithm(self.data)
        # for y,x in self.data:
        #     yc, xc = maxdub.correct(x, y)
        #     self.result.append([y, x, yc, xc])
        #
        # fname = "/home/tech/Workspace/python/magnetic-tools/fields.csv"
        # to_csv(fname, self.result, mode='x')
        # print("Compute Complete")
        return  maxdub

    def update(self, data):
        if not self.is_complete(data[3]):
            y, x = data[-3], data[-2]
            self.data.append([y, x])
        else:
            print("Complete collection")
