#!/usr/bin/python3


import sys
import csv
import math
import itertools
import json
import configparser
import random
import ITT_Assignment_5.pointing_technique as pt
from PyQt5 import QtGui, QtWidgets, QtCore

""" setup ini file format:
[experiment_setup]
UserID = 1
Widths = 20, 50, 170, 200
Distances = 100, 150, 200, 250
ImprovePointing = 0
"""

""" setup json file format:
{
"UserID" : "1",
"Widths": "20, 50, 170, 200",
"Distances": "50, 100, 150, 200",
"ImprovePointing": "0"
}
"""


class PointingExperimentModel(object):
    def __init__(self, user_id, diameters, distances, improve_pointing, repetitions=4):
        self.timer = QtCore.QTime()
        self.user_id = user_id
        self.diameters = diameters
        self.distances = distances
        self.improve_pointing = improve_pointing
        self.repetitions = repetitions
        # gives us a list of (distance, width) tuples:
        self.targets = repetitions * list(itertools.product(distances, diameters))
        random.shuffle(self.targets)
        self.elapsed = 0
        self.errors = 0
        self.mouse_moving = False
        self.initLogging()
        print(
            "timestamp (ISO); user_id; trial; target_distance; target_size; movement_time (ms); click_offset_x; click_offset_y; number_of_errors; improved_pointing")

    def initLogging(self):
        self.logfile = open("user" + str(self.user_id) + ".csv", "a")
        self.out = csv.DictWriter(self.logfile,
                                  ["timestamp (ISO)", "user_id", "trial", "target_distance", "target_size",
                                   "movement_time (ms)", "click_offset_x", "click_offset_y",
                                   "number_of_errors", "improved_pointing"],
                                  delimiter=";", quoting=csv.QUOTE_ALL)
        self.out.writeheader()

    def current_target(self):
        if self.elapsed >= len(self.targets):
            return None
        else:
            return self.targets[self.elapsed]

    def is_point_inside(self, target_pos, click_pos):
        dist = math.sqrt((target_pos[0] - click_pos[0]) * (target_pos[0] - click_pos[0]) +
                         (target_pos[1] - click_pos[1]) * (target_pos[1] - click_pos[1]))
        if dist <= self.current_target()[1] / 2:
            return True
        return False

    def register_click(self, target_pos, click_pos):
        dist = math.sqrt((target_pos[0] - click_pos[0]) * (target_pos[0] - click_pos[0]) +
                         (target_pos[1] - click_pos[1]) * (target_pos[1] - click_pos[1]))
        if dist > self.current_target()[1] / 2:
            self.errors += 1
            return False
        else:
            click_offset = (target_pos[0] - click_pos[0], target_pos[1] - click_pos[1])
            self.log_time(self.stop_measurement(), click_offset)
            self.errors = 0
            self.elapsed += 1
            return True

    def log_time(self, time, click_offset):
        distance, diameters = self.current_target()
        current_values = {"timestamp (ISO)": self.timestamp(), "user_id": self.user_id,
                          "trial": self.elapsed, "target_distance": distance,
                          "target_size": diameters, "movement_time (ms)": time,
                          "click_offset_x": click_offset[0], "click_offset_y": click_offset[1],
                          "number_of_errors": self.errors, "improved_pointing": self.improve_pointing
                          }
        self.out.writerow(current_values)
        print("%s; %s; %d; %d; %d; %d; %d; %d; %d; %s" % (
            self.timestamp(), self.user_id, self.elapsed, distance, diameters, time, click_offset[0], click_offset[1],
            self.errors, self.improve_pointing))

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


class Ellipse():
    def __init__(self, position_x, position_y, diameter):
        self.pos_x = position_x
        self.pos_y = position_y
        self.diameter = diameter

    def is_point_inside(self, x, y):
        dist = math.sqrt((self.pos_x - x) * (self.pos_x - x) +
                         (self.pos_y - y) * (self.pos_y - y))
        if dist <= self.diameter / 2:
            return True
        return False


class PointingExperimentTest(QtWidgets.QWidget):
    UI_WIDTH = 1920
    UI_HEIGHT = 800

    ID = -1

    ellipses = []

    def __init__(self, model):
        super(PointingExperimentTest, self).__init__()
        self.model = model
        self.start_pos = (self.UI_WIDTH / 2, self.UI_HEIGHT / 2)
        self.random_angle_in_rad = self.getRandumAngleInRad()
        self.initRandomTargets()
        self.pointing_technique = pt.PointingTechnique(self.ellipses, Ellipse)
        self.new_pointer = self.pointing_technique.filter(self.start_pos[0], self.start_pos[1])
        self.initUI()

    def initRandomTargets(self):
        number_of_targets = random.randint(3, 10)
        self.ellipses = []
        if self.model.current_target() is not None:
            distance, size = self.model.current_target()
        else:
            sys.stderr.write("no targets left...")
            sys.exit(1)
        # ellipses = []
        for number in range(number_of_targets):
            can_draw = False
            MAX_RETRIES = 3
            retry_count = 0
            while (not can_draw and retry_count < MAX_RETRIES):
                pos_x = random.randint(size + 0, self.UI_WIDTH - size)
                pos_y = random.randint(0 + size, self.UI_HEIGHT - size)
                not_occupied = True
                for e in self.ellipses:
                    if self.are_circles_intersecting(pos_x, pos_y, size, e.pos_x, e.pos_y, e.diameter):
                        not_occupied = False
                retry_count += 1
                can_draw = not_occupied
            self.ellipses.append(Ellipse(pos_x, pos_y, size))

    def initUI(self):
        self.text = "Please click on the target"
        self.setGeometry(0, 0, self.UI_WIDTH, self.UI_HEIGHT)
        self.setWindowTitle('FittsLawTest')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
        print(str(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1]))))
        # self.new_pointer = self.pointing_technique.filter(self.start_pos[0], self.start_pos[1])

        self.setMouseTracking(True)
        self.show()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            tp = self.target_pos(self.model.current_target()[0])
            hit = self.model.register_click(tp, (ev.x(), ev.y())) or (self.are_circles_intersecting(
                self.new_pointer.pos_x, self.new_pointer.pos_y,
                self.new_pointer.diameter / 2, tp[0],
                tp[1], self.model.current_target()[1] / 2) and self.model.improve_pointing)

            if hit:
                QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
                self.new_pointer = self.pointing_technique.filter(self.start_pos[0], self.start_pos[1])

                # self.new_pointer = self.pointing_technique.filter(ev.x(), ev.y())
                self.random_angle_in_rad = self.getRandumAngleInRad()
                self.initRandomTargets()
                self.update()
        return

    def mouseMoveEvent(self, ev):
        self.new_pointer = self.pointing_technique.filter(ev.x(), ev.y())
        if (abs(ev.x() - self.start_pos[0]) > 5) or (abs(ev.y() - self.start_pos[1]) > 5):
            self.model.start_measurement()
            self.update()

        self.ID = -1
        for i in range(len(self.ellipses)):
            if self.ellipses[i].is_point_inside(ev.x(), ev.y()) or \
                    (self.are_circles_intersecting(self.new_pointer.pos_x, self.new_pointer.pos_y,
                                                   self.new_pointer.diameter / 2, self.ellipses[i].pos_x,
                                                   self.ellipses[i].pos_y,
                                                   self.ellipses[i].diameter / 2) and self.model.improve_pointing):
                self.ID = i

        return

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRandomTargets(qp)
        self.drawClickTarget(qp)
        self.drawCursor(qp)
        self.drawText(event, qp)
        self.highlightTarget(qp)
        qp.end()

    def drawCursor(self, qp):
        if self.model.improve_pointing:
            qp.setBrush(QtGui.QColor(0, 0, 255))
            qp.drawEllipse(QtCore.QPoint(self.new_pointer.pos_x, self.new_pointer.pos_y), self.new_pointer.diameter / 2,
                           self.new_pointer.diameter / 2)

    def highlightTarget(self, qp):
        if self.ID != -1:
            qp.setBrush(QtGui.QColor(200, 34, 20))
            qp.drawEllipse(QtCore.QPoint(self.ellipses[self.ID].pos_x, self.ellipses[self.ID].pos_y),
                           self.ellipses[self.ID].diameter / 2,
                           self.ellipses[self.ID].diameter / 2)

        cursor_pos = self.mapFromGlobal(QtGui.QCursor.pos())
        tp = self.target_pos(self.model.current_target()[0])
        hit = self.model.is_point_inside(tp, (cursor_pos.x(), cursor_pos.y())) or (self.are_circles_intersecting(
            self.new_pointer.pos_x, self.new_pointer.pos_y,
            self.new_pointer.diameter / 2, tp[0],
            tp[1], self.model.current_target()[1] / 2) and self.model.improve_pointing)
        if hit:
            qp.setBrush(QtGui.QColor(200, 34, 20))
            qp.drawEllipse(QtCore.QPoint(tp[0], tp[1]),
                           self.model.current_target()[1] / 2,
                           self.model.current_target()[1] / 2)
        return

    def drawText(self, event, qp):
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setFont(QtGui.QFont('Decorative', 32))
        self.text = "%d / %d (%05d ms)" % (self.model.elapsed, len(self.model.targets), self.model.timer.elapsed())
        qp.drawText(event.rect(), QtCore.Qt.AlignCenter, self.text)

    def target_pos(self, distance):
        x = self.start_pos[0] + distance * math.cos(self.random_angle_in_rad)
        y = self.start_pos[1] + distance * math.sin(self.random_angle_in_rad)
        return (x, y)

    def getRandumAngleInRad(self):
        return math.radians(random.randint(0, 360))

    def are_circles_intersecting(self, x1, y1, radius1, x2, y2, radius2):
        distance_circles = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))
        return distance_circles <= (radius1 + radius2)

    def drawRandomTargets(self, qp):
        for e in self.ellipses:
            qp.drawEllipse(QtCore.QPoint(e.pos_x, e.pos_y), e.diameter / 2, e.diameter / 2)

    def drawClickTarget(self, qp):
        if self.model.current_target() is not None:
            distance, size = self.model.current_target()
        else:
            sys.stderr.write("no targets left...")
            sys.exit(1)
        x, y = self.target_pos(distance)
        qp.setBrush(QtGui.QColor(59, 255, 0))
        qp.drawEllipse(QtCore.QPoint(x, y), size / 2, size / 2)

    def getEllipses(self):
        return self.ellipses


def main():
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s <setup file>\n" % sys.argv[0])
        sys.exit(1)
    if sys.argv[1].endswith('.ini'):
        id, widths, distances, improve_pointing = parse_ini_file(sys.argv[1])
    if sys.argv[1].endswith('.json'):
        id, widths, distances, improve_pointing = parse_json_file(sys.argv[1])
    model = PointingExperimentModel(id, widths, distances, improve_pointing)
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
        improve_pointing = bool(int(setup['ImprovePointing']))
    else:
        print("Error: wrong file format.")
        sys.exit(1)
    return user_id, widths, distances, improve_pointing


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
    improve_pointing = bool(int(setup["ImprovePointing"]))
    return user_id, widths, distances, improve_pointing


if __name__ == '__main__':
    main()
