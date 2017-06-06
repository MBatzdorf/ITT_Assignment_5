#!/usr/bin/python3


import sys
import json
import configparser
import random
from PyQt5 import QtGui, QtWidgets, QtCore

""" setup ini file format:
[experiment_setup]
UserID = 1
Widths = 20, 50, 170, 200
Distances = 100, 150, 200, 250
"""

""" setup json file format:
{
"UserID" : "1",
"Widths": "20, 50, 170, 200",
"Distances": "50, 100, 150, 200"
}
"""

class PointingExperimentModel(object):

    def __init__(self, user_id, sizes, distances):
        self.timer = QtCore.QTime()
        self.user_id = user_id
        self.sizes = sizes
        self.distances = distances

    def timestamp(self):
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)

    def debug(self, msg):
        sys.stderr.write(self.timestamp() + ": " + str(msg) + "\n")



class PointingExperimentTest(QtWidgets.QWidget):

    def __init__(self, model):
        super(PointingExperimentTest, self).__init__()
        self.model = model
        self.start_pos = (960, 400)
        self.initUI()

    def initUI(self):
        self.text = "Please click on the target"
        self.setGeometry(0, 0, 1920, 800)
        self.setWindowTitle('PointingExperimentTest')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.show()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            tp = self.target_pos(self.model.current_target()[0])
            hit = self.model.register_click(tp, (ev.x(), ev.y()))
            if hit:
                QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
            # self.update()
        return

    def mouseMoveEvent(self, ev):
        if (abs(ev.x() - self.start_pos[0]) > 5) or (abs(ev.y() - self.start_pos[1]) > 5):
            self.model.start_measurement()
        return

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawClickTarget(qp)
        self.drawRandomTargets(qp)
        qp.end()

    def target_pos(self, distance):
        x = self.start_pos[0] + distance
        y = self.start_pos[1]
        return (x, y)

    def drawRandomTargets(self, qp):
        number_of_targets = random.randint(3, 10)
        if self.model.current_target() is not None:
            distance, size = self.model.current_target()
        else:
            sys.stderr.write("no targets left...")
            sys.exit(1)
        # self.drawCircle(qp, QtGui.QColor(212, 212, 212))
        qp.setBrush(QtGui.QColor(212, 212, 212))
        for number in number_of_targets:
            qp.drawEllipse(random.randint(size+0, 960-size), random.randint(0+size, 400-size), size, size)

    def drawClickTarget(self, qp):
        if self.model.current_target() is not None:
            distance, size = self.model.current_target()
        else:
            sys.stderr.write("no targets left...")
            sys.exit(1)
        x, y = self.target_pos(distance)
        qp.setBrush(QtGui.QColor(200, 34, 20))
        qp.drawEllipse(x-size/2, y-size/2, size, size)


def main():
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s <setup file>\n" % sys.argv[0])
        sys.exit(1)
    if sys.argv[1].endswith('.ini'):
        id, widths, distances = parse_ini_file(sys.argv[1])
    if sys.argv[1].endswith('.json'):
        id, widths, distances = parse_json_file(sys.argv[1])
    model = PointingExperimentModel(id, widths, distances)
    test = PointingExperimentTest(model)
    sys.exit(app.exec_())


def parse_ini_file(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    if 'experiment_setup' in config:
        setup = config['experiment_setup']
        user_id = setup['UserID']
        widths = setup['Widths']
        distances = setup['Distances']
    else:
        print("Error: wrong file format.")
        sys.exit(1)
    return user_id, widths, distances


def parse_json_file(filename):
    setup = json.load(open(filename))
    if "UserID" not in setup or "Widths" not in setup or "Distances" not in setup:
        print("Error: wrong file format.")
        sys.exit(1)
    user_id = setup["UserID"]
    widths = setup["Widths"]
    distances = setup["Distances"]

    return user_id, widths, distances

if __name__ == '__main__':
    main()