from algorithms import Algorithm
from util import to_csv


class Calibrate(object):

    def __init__(self):
        print("Create instance of Calibrate")
        self.data = []
        self.result = []

    def compute(self):
        print("Compute start")
        maxdub = Algorithm(self.data)
        for y,x in self.data:
            yc, xc = maxdub.correct(x, y)
            self.result.append([y, x, yc, xc])
        
        fname = "/home/tech/workspace/python/magnetic-tools/fields.csv"
        to_csv(fname, self.result)
        print("Compute Complete")

    def update(self, data):
        y,x = data[-3], data[-2]
        self.data.append([y,x])