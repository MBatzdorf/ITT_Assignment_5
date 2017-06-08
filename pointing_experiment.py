#!/usr/bin/python3


import sys
import csv
import math
import itertools
import json
import configparser
import random
# Did not work for me: Error module not found
import ITT_Assignment_5.pointing_technique as pt
# import pointing_technique as pt
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
        self.initTrials(distances, diameters, repetitions)

        self.elapsed = 0
        self.errors = 0
        self.mouse_moving = False
        self.initLogging()
        print(
            "timestamp (ISO); user_id; trial; target_distance; target_size; movement_time (ms); click_offset_x; "
            "click_offset_y; number_of_errors; improved_pointing")

    def initTrials(self, distances, diameters, repetitions):
        # gives us a list of (distance, width) tuples:
        self.trials = repetitions * list(itertools.product(distances, diameters))
        # random.shuffle(self.trials)
        self.trials = self.counterbalance_trials(self.trials, self.user_id)
        for i in range(len(self.trials)):
            self.trials[i] = Trial(self.trials[i][0], self.trials[i][1])

    def counterbalance_trials(self, trials, userid):
        n = len(trials)
        # https://stackoverflow.com/questions/6667201/how-to-define-two-dimensional-array-in-python
        balanced_trials_matrix = [[0 for x in range(n)] for y in range(n)]
        for row in range(n):
            for col in range(n):
                # https://stackoverflow.com/questions/34276996/shifting-a-2d-array-to-the-left-loop
                balanced_trials_matrix[row][col] = trials[(row + col) % n]

            print(balanced_trials_matrix[row])

        return balanced_trials_matrix[int(userid) - 1]

    def initLogging(self):
        self.logfile = open("user" + str(self.user_id) + ".csv", "a")
        self.out = csv.DictWriter(self.logfile,
                                  ["timestamp (ISO)", "user_id", "trial", "target_distance", "target_size",
                                   "movement_time (ms)", "click_offset_x", "click_offset_y",
                                   "number_of_errors", "improved_pointing"], delimiter=";", quoting=csv.QUOTE_ALL)
        self.out.writeheader()

    def current_trial(self):
        if self.elapsed >= len(self.trials):
            return None
        else:
            return self.trials[self.elapsed]

    def register_click(self, target_pos, click_pos):
        click_offset = (target_pos.x() - click_pos.x(), target_pos.y() - click_pos.y())
        self.log_time(self.stop_measurement(), click_offset)
        self.errors = 0
        self.elapsed += 1

    def log_time(self, time, click_offset):
        distance, diameters = self.current_trial().getCurrentCondition()
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

    def increment_error_count(self, amount):
        self.errors += amount


class Trial:
    def __init__(self, distance, diameter):
        self.distance = distance
        self.diameter = diameter

    def getCurrentCondition(self):
        return self.distance, self.diameter


class GeometryUtils:
    @staticmethod
    def calculateDistanceBetweenPoints(point1, point2):
        return math.sqrt(math.pow(point2.x() - point1.x(), 2) + math.pow(point2.y() - point1.y(), 2))

    @staticmethod
    def are_circles_intersecting(x1, y1, radius1, x2, y2, radius2):
        distance_circles = GeometryUtils.calculateDistanceBetweenPoints(QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2))
        return distance_circles <= (radius1 + radius2)

    @staticmethod
    def is_point_inside_target(point, target, diameter):
        distance = GeometryUtils.calculateDistanceBetweenPoints(QtCore.QPoint(point.x(), point.y()),
                                                                QtCore.QPoint(target.x(), target.y()))
        if distance <= diameter / 2:
            return True
        return False


class Target:
    def __init__(self, position_x, position_y, diameter):
        self.pos_x = position_x
        self.pos_y = position_y
        self.diameter = diameter

    def is_target_hit(self, point, pointer, target, is_new_pointing_technique):
        is_hit = GeometryUtils.is_point_inside_target(QtCore.QPoint(point.x(), point.y()),
                                                      QtCore.QPoint(target.pos_x, target.pos_y),
                                                      self.diameter) or \
                 (GeometryUtils.are_circles_intersecting(pointer.pos_x, pointer.pos_y,
                                                         pointer.diameter / 2, target.pos_x,
                                                         target.pos_y,
                                                         self.diameter / 2) and is_new_pointing_technique)
        return is_hit


class ClickTarget(Target):
    def __init__(self, position_x, position_y, diameter):
        super().__init__(position_x, position_y, diameter)

    def is_target_hit(self, point, pointer, is_new_pointing_technique, target=0):
        is_hit = GeometryUtils.is_point_inside_target(QtCore.QPoint(point.x(), point.y()),
                                                      QtCore.QPoint(self.pos_x, self.pos_y),
                                                      self.diameter) or \
                 (GeometryUtils.are_circles_intersecting(pointer.pos_x, pointer.pos_y,
                                                         pointer.diameter / 2, self.pos_x,
                                                         self.pos_y,
                                                         self.diameter / 2) and is_new_pointing_technique)
        return is_hit


class PointingExperimentTest(QtWidgets.QWidget):
    UI_WIDTH = 1920
    UI_HEIGHT = 800

    ID = -1

    targets = []

    def __init__(self, model):
        super(PointingExperimentTest, self).__init__()
        self.model = model
        self.start_pos = QtCore.QPoint(self.UI_WIDTH / 2, self.UI_HEIGHT / 2)
        self.random_angle_in_rad = self.getRandumAngleInRad()
        self.initRandomTargets()
        self.pointing_technique = pt.PointingTechnique(self.targets, Target)
        self.new_pointer = self.pointing_technique.filter(self.start_pos.x(), self.start_pos.y())
        self.initUI()
        self.init_next_click_target(self.model.current_trial())

    def initRandomTargets(self):
        number_of_targets = random.randint(3, 10)
        self.targets = []
        if self.model.current_trial() is not None:
            distance, size = self.model.current_trial().getCurrentCondition()
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
                for e in self.targets:
                    if GeometryUtils.are_circles_intersecting(pos_x, pos_y, size, e.pos_x, e.pos_y, e.diameter):
                        not_occupied = False
                retry_count += 1
                can_draw = not_occupied
            self.targets.append(Target(pos_x, pos_y, size))

    def initUI(self):
        self.text = "Please click on the target"
        self.setGeometry(0, 0, self.UI_WIDTH, self.UI_HEIGHT)
        self.setWindowTitle('PointingExperimentTest')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos.x(), self.start_pos.y())))
        print(str(self.mapToGlobal(QtCore.QPoint(self.start_pos.x(), self.start_pos.y()))))
        # self.new_pointer = self.pointing_technique.filter(self.start_pos.x(), self.start_pos.y())

        self.setMouseTracking(True)
        self.show()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            # tp = self.init_next_click_target(self.model.current_trial().distance)
            hit = self.click_target.is_target_hit(QtCore.QPoint(ev.x(), ev.y()), self.new_pointer,
                                                  self.model.improve_pointing)

            if hit:
                self.model.register_click(QtCore.QPoint(self.click_target.pos_x, self.click_target.pos_y),
                                          QtCore.QPoint(ev.x(), ev.y()))
                QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos.x(), self.start_pos.y())))
                self.new_pointer = self.pointing_technique.filter(self.start_pos.x(), self.start_pos.y())

                # self.new_pointer = self.pointing_technique.filter(ev.x(), ev.y())
                self.random_angle_in_rad = self.getRandumAngleInRad()
                self.init_next_click_target(self.model.current_trial())
                self.initRandomTargets()
                self.update()
            else:
                self.model.increment_error_count(1)
                return
        return

    def mouseMoveEvent(self, ev):
        self.new_pointer = self.pointing_technique.filter(ev.x(), ev.y())
        if (abs(ev.x() - self.start_pos.x()) > 5) or (abs(ev.y() - self.start_pos.y()) > 5):
            self.model.start_measurement()
            self.update()

        self.ID = -1
        for i in range(len(self.targets)):
            if GeometryUtils.is_point_inside_target(QtCore.QPoint(ev.x(), ev.y()),
                                                    QtCore.QPoint(self.targets[i].pos_x, self.targets[i].pos_y),
                                                    self.targets[i].diameter) or \
                    (GeometryUtils.are_circles_intersecting(self.new_pointer.pos_x, self.new_pointer.pos_y,
                                                            self.new_pointer.diameter / 2, self.targets[i].pos_x,
                                                            self.targets[i].pos_y,
                                                            self.targets[
                                                                i].diameter / 2) and self.model.improve_pointing):
                self.ID = i

        return

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRandomTargets(qp)
        self.drawClickTarget(qp)
        self.drawText(event, qp)
        self.highlightTarget(qp)
        self.drawCursor(qp)
        qp.end()

    def drawCursor(self, qp):
        if self.model.improve_pointing:
            qp.setBrush(QtGui.QColor(0, 0, 255))
            qp.drawEllipse(QtCore.QPoint(self.new_pointer.pos_x, self.new_pointer.pos_y), self.new_pointer.diameter / 2,
                           self.new_pointer.diameter / 2)

    def highlightTarget(self, qp):
        if self.ID != -1:
            qp.setBrush(QtGui.QColor(200, 34, 20))
            qp.drawEllipse(QtCore.QPoint(self.targets[self.ID].pos_x, self.targets[self.ID].pos_y),
                           self.targets[self.ID].diameter / 2,
                           self.targets[self.ID].diameter / 2)

        cursor_pos = self.mapFromGlobal(QtGui.QCursor.pos())
        current_trial = self.model.current_trial()
        # tp = self.init_next_click_target(current_trial)
        hit = self.targets[self.ID].is_target_hit(QtCore.QPoint(cursor_pos.x(), cursor_pos.y()), self.new_pointer,
                                                  self.click_target, self.model.improve_pointing)
        if hit:
            qp.setBrush(QtGui.QColor(200, 34, 20))
            qp.drawEllipse(QtCore.QPoint(self.click_target.pos_x, self.click_target.pos_y),
                           self.model.current_trial().diameter / 2,
                           self.model.current_trial().diameter / 2)
        return

    def drawText(self, event, qp):
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setFont(QtGui.QFont('Decorative', 32))
        self.text = "%d / %d (%05d ms)" % (self.model.elapsed, len(self.model.trials), self.model.timer.elapsed())
        qp.drawText(event.rect(), QtCore.Qt.AlignTop, self.text)

    def init_next_click_target(self, current_trial):
        if current_trial is not None:
            x = self.start_pos.x() + current_trial.distance * math.cos(self.random_angle_in_rad)
            y = self.start_pos.y() + current_trial.distance * math.sin(self.random_angle_in_rad)
            self.click_target = ClickTarget(x, y, current_trial.diameter)

    def getRandumAngleInRad(self):
        return math.radians(random.randint(0, 360))

    def drawRandomTargets(self, qp):
        for e in self.targets:
            qp.drawEllipse(QtCore.QPoint(e.pos_x, e.pos_y), e.diameter / 2, e.diameter / 2)

    def drawClickTarget(self, qp):
        if self.model.current_trial() is not None:
            distance, size = self.model.current_trial().getCurrentCondition()
        else:
            sys.stderr.write("no targets left...")
            sys.exit(1)
        # x, y = self.init_next_click_target(distance)
        qp.setBrush(QtGui.QColor(59, 255, 0))
        qp.drawEllipse(QtCore.QPoint(self.click_target.pos_x, self.click_target.pos_y), size / 2, size / 2)

    def getEllipses(self):
        return self.targets


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
