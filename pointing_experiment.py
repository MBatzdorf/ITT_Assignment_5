#!/usr/bin/python3


import sys
import csv
import math
import itertools
import json
import configparser
import random
# import ITT_Assignment_5.pointing_technique as pt
import pointing_technique as pt
from PyQt5 import QtGui, QtWidgets, QtCore

# This script was created by Alexander Frummet and Marco Batzdorf
# and is based on the "fitts_law_test.py" script

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

    """
        This experiment model keeps track of all information concerning a pointing test.
        The experiment settings are given via instantiation parameters and the trial order is generated in a counterbalanced way
        Further all information are logged to stdout and stored in a file in csv format.

        @param user_id: ID for the user participating
        @param diameters: A List containing all possible target diameters for this test
        @param distances: A List containing all possible distances between pointer and target for this test
        @param improve_pointing: Whether the improved pointing technique should be used or the standard one
        @param repetitions: Indicates how often all trials should be repeated
    """

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

    ''' Initializes the order of the single trials '''
    def init_trials(self, distances, diameters, repetitions):
        # gives us a list of (distance, width) tuples:
        self.trials = repetitions * list(itertools.product(distances, diameters))
        # random.shuffle(self.trials)
        self.trials = self.counterbalance_trials(self.trials, self.user_id)
        for i in range(len(self.trials)):
            self.trials[i] = Trial(self.trials[i][0], self.trials[i][1])

    ''' Counterbalances a given list of [distance, diameter] tuples '''
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

    ''' Initialize experiment logging
        Creates a new csv file and writes the corresponding header line
    '''
    def init_logging(self):
        self.logfile = open("user" + str(self.user_id) + ".csv", "a")
        self.out = csv.DictWriter(self.logfile,
                                  ["timestamp (ISO)", "user_id", "trial", "target_distance", "target_size",
                                   "movement_time (ms)", "click_offset_x", "click_offset_y",
                                   "number_of_errors", "improved_pointing"], delimiter=";", quoting=csv.QUOTE_ALL)
        self.out.writeheader()

    ''' Helper for getting the current [distance, diameter] tuple representing the current trial's settings'''
    def current_trial(self):
        if self.elapsed >= len(self.trials):
            return None
        else:
            return self.trials[self.elapsed]

    ''' Tells the model that the correct target has been hit
        Updates the current target to the next one and triggers writing the trial results to the csv file
    '''
    def register_click(self, target_pos, click_pos):
        click_offset = (target_pos[0] - click_pos[0], target_pos[1] - click_pos[1])
        self.log_time(self.stop_measurement(), click_offset)
        self.errors = 0
        self.elapsed += 1

    ''' Writes all useful trial information to the log csv file'''
    def log_time(self, time, click_offset):
        distance, diameters = self.current_trial().get_current_condition()
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

    ''' Tells the model to start the timer and that the mouse is moving '''
    def start_measurement(self):
        if not self.mouse_moving:
            self.timer.start()
            self.mouse_moving = True

    ''' Stops counting the time because the mouse is not moving anymore.
        Returns the elapsed time for the current trial
    '''
    def stop_measurement(self):
        if self.mouse_moving:
            elapsed = self.timer.elapsed()
            self.mouse_moving = False
            return elapsed
        else:
            return -1

    ''' Returns a timestamp'''
    def timestamp(self):
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)

    ''' Helper to increment the error count for the current trial'''
    def increment_error_count(self, amount):
        self.errors += amount


class Trial:

    """
        Stores the settings for a single trial of the experiment

        @param distance: The distance between target and cursor
        @param diameter: The size of the target to hit
    """

    def __init__(self, distance, diameter):
        self.distance = distance
        self.diameter = diameter

    ''' Helper for accessing this trial's settings'''
    def get_current_condition(self):
        return self.distance, self.diameter


class Target:

    """
        Represents a target that can be displayed on the participant's screen
        Targets are represented by a circle and can be highlighted
        The default color is white but can be given any color

        @param position_x: X-Coordinate of the circle's center
        @param position_y: Y-Coordinate of the circle's center
        @param diameter: Two times the radius, defining the circle's extends
    """

    COLOR_RED = QtGui.QColor(200, 34, 20)
    COLOR_WHITE = QtGui.QColor(255, 255, 255)

    def __init__(self, position_x, position_y, diameter):
        self.pos_x = position_x
        self.pos_y = position_y
        self.diameter = diameter

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    ''' Draws the standard representation of this target to the screen'''
    def draw(self, painter):
        painter.setBrush(self.COLOR_WHITE)
        painter.drawEllipse(QtCore.QPoint(self.pos_x, self.pos_y), self.diameter / 2, self.diameter / 2)
        return

    ''' Highlight the circle with a red color'''
    def draw_highlighted(self, painter):
        painter.setBrush(self.COLOR_RED)
        painter.drawEllipse(QtCore.QPoint(self.pos_x, self.pos_y),
                            self.diameter / 2,
                            self.diameter / 2)

    ''' Draws the target to the screen with the specified color'''
    def draw_colored(self, painter, color):
        painter.setBrush(color)
        painter.drawEllipse(QtCore.QPoint(self.pos_x, self.pos_y), self.diameter / 2, self.diameter / 2)
        return


class PointingExperimentTest(QtWidgets.QWidget):

    """
        Main class for executing the pointing experiment/test
        Initializes and keeps track of the ui and pointing technique
        and processes all mouse input events
        Also responsible for keeping the given experiment model up to date

        @param model: The experiment model used for this Test
    """

    UI_WIDTH = 1920
    UI_HEIGHT = 800
    BUBBLE_RADIUS = 20
    MAX_NUM_TARGETS = 10
    MIN_NUM_TARGETS = 3

    def __init__(self, model):
        super(PointingExperimentTest, self).__init__()
        self.model = model
        self.start_pos = (self.UI_WIDTH / 2, self.UI_HEIGHT / 2)
        self.initUI()
        self.init_next_trial()

    ''' Initialize the UI
        Sets the window size, window title, focus policy and mouse startung position
    '''
    def initUI(self):
        self.text = "Please click on the target"
        self.setGeometry(0, 0, self.UI_WIDTH, self.UI_HEIGHT)
        self.setWindowTitle('PointingExperimentTest')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[1])))
        self.setMouseTracking(True)
        self.show()

    ''' Prepares and sets all variables for the next test
        Updates the UI and model and sets appropriate pointing technique
    '''
    def init_next_trial(self):
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

    ''' Returns a randomly generated angle in Radians'''
    def getRandomAngleInRad(self):
        return math.radians(random.randint(0, 360))

    ''' Initialize all targets representes to the participant
        The target size is defined by the current trial settings
        and the amount is set via MAX_NUM_TARGETS and MIN_NUM_TARGETS

        Tries to avoid overlapping targets
        Ignores the none overlapping restriction if the targets are too many
        and/or too big to be placed in that manner after a few tries

    '''
    def initTargets(self):
        number_of_targets = random.randint(self.MIN_NUM_TARGETS, self.MAX_NUM_TARGETS)
        self.targets = []
        if self.model.current_trial() is not None:
            distance, size = self.model.current_trial().get_current_condition()
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

    ''' Helper for getting the center position of the target that has to be clicked'''
    def getMainTargetPos(self, distance):
        x = self.start_pos[0] + distance * math.cos(self.random_angle_in_rad)
        y = self.start_pos[1] + distance * math.sin(self.random_angle_in_rad)
        return (x, y)

    ''' Helper for getting the target that has to be clicked'''
    def getMainTarget(self):
        return self.targets[0]

    ''' Changes between the improved and standard pointing technique
        Only has an effect if the improved pointing technique is allowed during the current experiment
    '''
    def togglePointingTechnique(self):
        if not self.model.improve_pointing:
            return
        if type(self.pointing_technique) == pt.PointingTechniqueFatBubble:
            self.pointing_technique = pt.StandardPointingTechnique(self.targets, Target)
        else:
            self.pointing_technique = pt.PointingTechniqueFatBubble(self.targets, Target, self.BUBBLE_RADIUS)

    ''' Processes all click events for the mouse
        and checks if the main target has been hit
    '''
    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            main_target = self.getMainTarget()
            if main_target in self.pointing_technique.get_targets_under_cursor():
                self.model.register_click([main_target.pos_x, main_target.pos_y], [ev.x(), ev.y()])
                self.init_next_trial()
            else:
                self.model.increment_error_count(1)
                return
        if ev.button() == QtCore.Qt.RightButton:
            self.togglePointingTechnique()
            self.pointing_technique.filter(ev.x(), ev.y())
        self.update()

    ''' Processes all movement events for the mouse and reroutes them to the pointing technique'''
    def mouseMoveEvent(self, ev):
        self.pointing_technique.filter(ev.x(), ev.y())
        if (abs(ev.x() - self.start_pos[0]) > 5) or (abs(ev.y() - self.start_pos[1]) > 5):
            self.model.start_measurement()
        self.update()
        return

    ''' Draws all elements to the screen'''
    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawText(event, qp)
        self.drawTargets(qp)
        self.pointing_technique.draw_pointer(qp)
        qp.end()

    ''' Draws a text showing the passed time for this test'''
    def drawText(self, event, qp):
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setFont(QtGui.QFont('Decorative', 32))
        self.text = "%d / %d (%05d ms)" % (self.model.elapsed, len(self.model.trials), self.model.timer.elapsed())
        qp.drawText(event.rect(), QtCore.Qt.AlignTop, self.text)

    ''' Responsible for drawing all targets depending on their current state (hovered, main target, normal target)'''
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

    """
        Starting class for this script
        Reads in a ini or json file passed as a command line parameter (see definition above)
        and initializes the experiment model with this information
        Starts the QtApplication afterwards with the newly created model

    """

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

    """
        Reads the information from a ini file

        @return: Integer with the user's id; a list with all possible target sizes for this test;
                a list with all possible target distances for this test; Boolean indicating whether the improved
                pointing technique should be used or not
    """
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

    """
        Reads the information from a json file

        @return: Integer with the user's id; a list with all possible target sizes for this test;
                 a list with all possible target distances for this test; Boolean indicating whether the improved
                 pointing technique should be used or not
    """
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
