#!/usr/bin/python3


import sys
import csv
import math
import itertools
import json
import configparser
import random
# Did not work for me: Error module not found
#import ITT_Assignment_5.pointing_technique as pt
import pointing_technique as pt
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
        self.init_trials(distances, diameters, repetitions)

        self.elapsed = 0
        self.errors = 0
        self.mouse_moving = False
        self.init_logging()
        print(
            "timestamp (ISO); user_id; trial; target_distance; target_size; movement_time (ms); click_offset_x; "
            "click_offset_y; number_of_errors; improved_pointing")

    def init_trials(self, distances, diameters, repetitions):
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

    def init_logging(self):
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
        click_offset = (target_pos[0] - click_pos[0], target_pos[1] - click_pos[1])
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


class Target:
    def __init__(self, position_x, position_y, diameter):
        self.pos_x = position_x
        self.pos_y = position_y
        self.diameter = diameter

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def draw(self, painter):
        painter.setBrush(QtGui.QColor(255, 255, 255))
        painter.drawEllipse(QtCore.QPoint(self.pos_x, self.pos_y), self.diameter / 2, self.diameter / 2)
        return

    def draw_highlighted(self, painter):
        painter.setBrush(QtGui.QColor(200, 34, 20))
        painter.drawEllipse(QtCore.QPoint(self.pos_x, self.pos_y),
                           self.diameter / 2,
                           self.diameter / 2)

    def draw_colored(self, painter, color):
        painter.setBrush(color)
        painter.drawEllipse(QtCore.QPoint(self.pos_x, self.pos_y), self.diameter / 2, self.diameter / 2)
        return


class PointingExperimentTest(QtWidgets.QWidget):
    UI_WIDTH = 1920
    UI_HEIGHT = 800
    BUBBLE_RADIUS = 20

    def __init__(self, model):
        super(PointingExperimentTest, self).__init__()
        self.model = model
        self.start_pos = (self.UI_WIDTH / 2, self.UI_HEIGHT / 2)
        self.initUI()
        self.reset_trial()

    def initUI(self):
        self.text = "Please click on the target"
        self.setGeometry(0, 0, self.UI_WIDTH, self.UI_HEIGHT)
        self.setWindowTitle('PointingExperimentTest')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
        self.setMouseTracking(True)
        self.show()

    def resetTrial(self):
        if self.model.improve_pointing:
            self.pointing_technique = pt.PointingTechniqueFatBubble([], Target, self.BUBBLE_RADIUS)
        else:
            self.pointing_technique = pt.StandardPointingTechnique([], Target)
        QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
        self.pointing_technique.filter(self.start_pos[0], self.start_pos[1])
        self.random_angle_in_rad = self.getRandomAngleInRad()
        self.initTargets()
        self.pointing_technique.update_targets(self.targets)
        self.update()

    def getRandomAngleInRad(self):
        return math.radians(random.randint(0, 360))

    def initTargets(self):
        number_of_targets = random.randint(3, 10)
        self.targets = []
        if self.model.current_trial() is not None:
            distance, size = self.model.current_trial().getCurrentCondition()
            pos = self.getMainTargetPos(distance)
            self.targets.append(Target(pos[0], pos[1], size))
        else:
            sys.stderr.write("no targets left...")
            sys.exit(1)
        for number in range(number_of_targets):
            can_draw = False
            MAX_RETRIES = 3
            retry_count = 0
            while (not can_draw and retry_count < MAX_RETRIES):
                pos_x = random.randint(size + 0, self.UI_WIDTH - size)
                pos_y = random.randint(0 + size, self.UI_HEIGHT - size)
                not_occupied = True
                for e in self.targets:
                    if pt.GeometryUtils.are_circles_intersecting(pos_x, pos_y, size, e.pos_x, e.pos_y, e.diameter):
                        not_occupied = False
                retry_count += 1
                can_draw = not_occupied
            self.targets.append(Target(pos_x, pos_y, size))

    def getMainTargetPos(self, distance):
        x = self.start_pos[0] + distance * math.cos(self.random_angle_in_rad)
        y = self.start_pos[1] + distance * math.sin(self.random_angle_in_rad)
        return (x, y)

    def getMainTarget(self):
        return self.targets[0]

    def togglePointingTechnique(self):
        if not self.model.improve_pointing:
            return
        if type(self.pointing_technique) == pt.PointingTechniqueFatBubble:
            self.pointing_technique = pt.StandardPointingTechnique(self.targets, Target)
        else:
            self.pointing_technique = pt.PointingTechniqueFatBubble(self.targets, Target, self.BUBBLE_RADIUS)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            main_target = self.getMainTarget()
            if main_target in self.pointing_technique.get_targets_under_cursor():
                self.model.register_click([main_target.pos_x, main_target.pos_y], [ev.x(), ev.y()])
                self.resetTrial()
            else:
                self.model.increment_error_count(1)
                return
        if ev.button() == QtCore.Qt.RightButton:
            self.togglePointingTechnique()
            self.pointing_technique.filter(ev.x(), ev.y())
        self.update()

    def mouseMoveEvent(self, ev):
        self.pointing_technique.filter(ev.x(), ev.y())
        if (abs(ev.x() - self.start_pos[0]) > 5) or (abs(ev.y() - self.start_pos[1]) > 5):
            self.model.start_measurement()
        self.update()
        return

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawText(event, qp)
        self.drawTargets(qp)
        self.pointing_technique.draw_pointer(qp)
        qp.end()

    def drawText(self, event, qp):
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setFont(QtGui.QFont('Decorative', 32))
        self.text = "%d / %d (%05d ms)" % (self.model.elapsed, len(self.model.trials), self.model.timer.elapsed())
        qp.drawText(event.rect(), QtCore.Qt.AlignTop, self.text)

    def drawTargets(self, qp):
        for idx in range(len(self.targets)):
            if idx == 0:
                self.targets[idx].draw_colored(qp, QtGui.QColor(59, 255, 0))
            else:
                self.targets[idx].draw(qp)
        highlighted = self.pointing_technique.get_targets_under_cursor()
        for target in highlighted:
            target.draw_highlighted(qp)


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
