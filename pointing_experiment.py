#!/usr/bin/python3


import sys
import csv
import random
import math
import itertools
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
    def __init__(self, user_id, sizes, distances, repetitions=4):
        self.timer = QtCore.QTime()
        self.user_id = user_id
        self.sizes = sizes
        self.distances = distances
        self.repetitions = repetitions
        # gives us a list of (distance, width) tuples:
        self.targets = repetitions * list(itertools.product(distances, sizes))
        random.shuffle(self.targets)
        self.elapsed = 0
        self.errors = 0
        self.mouse_moving = False
        self.initLogging()
        print(
            "timestamp (ISO); user_id; trial; target_distance; target_size; movement_time (ms); click_offset_x; click_offset_y; number_of_errors")

    def initLogging(self):
        self.logfile = open("user" + str(self.user_id) + ".csv", "a")
        self.out = csv.DictWriter(self.logfile,
                                  ["timestamp (ISO)", "user_id", "trial", "target_distance", "target_size",
                                   "movement_time (ms)", "click_offset_x", "click_offset_y",
                                   "number_of_errors"],
                                  delimiter=";", quoting=csv.QUOTE_ALL)
        self.out.writeheader()

    def current_target(self):
        if self.elapsed >= len(self.targets):
            return None
        else:
            return self.targets[self.elapsed]

    def register_click(self, target_pos, click_pos):
        dist = math.sqrt((target_pos[0] - click_pos[0]) * (target_pos[0] - click_pos[0]) +
                         (target_pos[1] - click_pos[1]) * (target_pos[1] - click_pos[1]))
        if dist > self.current_target()[1]:
            self.errors += 1
            return False
        else:
            click_offset = (target_pos[0] - click_pos[0], target_pos[1] - click_pos[1])
            self.log_time(self.stop_measurement(), click_offset)
            self.errors = 0
            self.elapsed += 1
            return True

    def log_time(self, time, click_offset):
        distance, size = self.current_target()
        current_values = {"timestamp (ISO)": self.timestamp(), "user_id": self.user_id,
                          "trial": self.elapsed, "target_distance": distance,
                          "target_size": size, "movement_time (ms)": time,
                          "click_offset_x": click_offset[0], "click_offset_y": click_offset[1],
                          "number_of_errors": self.errors
                          }
        self.out.writerow(current_values)
        print("%s; %s; %d; %d; %d; %d; %d; %d; %d" % (
        self.timestamp(), self.user_id, self.elapsed, distance, size, time, click_offset[0], click_offset[1],
        self.errors))

    def start_measurement(self):
        if not self.mouse_moving:
            self.timer.start()
            self.mouse_moving = True

    def stop_measurement(self):
        if self.mouse_moving:
            elapsed = self.timer.elapsed()
            self.mouse_moving = False
            return elapsed
        else:
            return -1

    def timestamp(self):
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)


class PointingExperimentTest(QtWidgets.QWidget):
    UI_WIDTH = 1920
    UI_HEIGHT = 800

    def __init__(self, model):
        super(PointingExperimentTest, self).__init__()
        self.model = model
        self.start_pos = (self.UI_WIDTH / 2, self.UI_HEIGHT / 2)
        self.initUI()

    def initUI(self):
        self.text = "Please click on the target"
        self.setGeometry(0, 0, self.UI_WIDTH, self.UI_HEIGHT)
        self.setWindowTitle('FittsLawTest')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
        self.setMouseTracking(True)
        self.show()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            tp = self.target_pos(self.model.current_target()[0])
            hit = self.model.register_click(tp, (ev.x(), ev.y()))
            if hit:
                QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
                self.update()
        return

    def mouseMoveEvent(self, ev):
        if (abs(ev.x() - self.start_pos[0]) > 5) or (abs(ev.y() - self.start_pos[1]) > 5):
            self.model.start_measurement()
            # self.update()
        return

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawClickTarget(qp)
        self.drawRandomTargets(qp)
        self.drawText(event, qp)
        qp.end()

    def drawText(self, event, qp):
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setFont(QtGui.QFont('Decorative', 32))
        self.text = "%d / %d (%05d ms)" % (self.model.elapsed, len(self.model.targets), self.model.timer.elapsed())
        qp.drawText(event.rect(), QtCore.Qt.AlignCenter, self.text)

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
        for number in range(number_of_targets):
            qp.drawEllipse(random.randint(size + 0, self.UI_WIDTH / 2 - size), random.randint(0 + size, self.UI_HEIGHT /
                                                                                              2 - size), size, size)

    def drawClickTarget(self, qp):
        if self.model.current_target() is not None:
            distance, size = self.model.current_target()
        else:
            sys.stderr.write("no targets left...")
            sys.exit(1)
        x, y = self.target_pos(distance)
        qp.setBrush(QtGui.QColor(59, 255, 0))
        qp.drawEllipse(x - size / 2, y - size / 2, size, size)


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
        widths_string = setup['Widths']
        widths = [int(x) for x in widths_string.split(",")]
        distances_string = setup['Distances']
        distances = [int(x) for x in distances_string.split(",")]
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
    widths_string = setup["Widths"]
    widths = [int(x) for x in widths_string.split(",")]
    distances_string = setup["Distances"]
    distances = [int(x) for x in distances_string.split(",")]

    return user_id, widths, distances


if __name__ == '__main__':
    main()
