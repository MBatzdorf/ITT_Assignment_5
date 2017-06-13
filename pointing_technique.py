#!usr/bin/python3


import math
from PyQt5 import QtGui, QtCore

# This script was created by Alexander Frummet and Marco Batzdorf


class StandardPointingTechnique(object):

    """
        This class implements the system's standard pointing technique
        and acts as a base class for enhanced pointing techniques.

        No modifications or filtering are done to any mouse actions

        @param targets: A list of all targets displayed to the user
        @param Target: Base class reference for a Target

    """

    targets = []

    def __init__(self, targets, Target):
        self.targets = targets
        self.target_class = Target

    ''' Filtering, storing and manipulating mouse move events

        @param pos_x: New mouse position on the X-Axis
        @param pos_y: New mouse position on the Y-Axis
    '''
    def filter(self, pos_x, pos_y):
        self.cursor_pos_x = pos_x
        self.cursor_pos_y = pos_y

    ''' Draws the pointer's visual representation to the screen

        @param painter: PyQt QPainter object that can draw to the canvas
    '''
    def draw_pointer(self, painter):
        return

    ''' Checking which of the given targets is currently under
        the pointer's clickable area

        @return: A list of all targets that are currently under the pointer
    '''
    def get_targets_under_cursor(self):

        hits = []
        for target in self.targets:
            if GeometryUtils.is_point_inside_circle([self.cursor_pos_x, self.cursor_pos_y],
                                                    [target.pos_x, target.pos_y], target.diameter):
                hits.append(target)
        return hits

    ''' Helper class to replace the current targets with new ones

        @param targets: The new list of targets replacing the old target list
    '''
    def update_targets(self, targets):
        self.targets = targets


class PointingTechniqueFatBubble(StandardPointingTechnique):

    """
        This class extends the standard pointing technique as seen above
        In addition to the normal pointer the clicking area and visual representation are extended
        with a given radius around its center

        @param targets: A list of all targets displayed to the user
        @param Target: Base class reference for a Target
        @param bubble_radius: Defines the extends of this pointer(bubble)

    """

    COLOR_BLUE = QtGui.QColor(0, 0, 255)

    def __init__(self, targets, Target, bubble_radius=20):
        super().__init__(targets, Target)
        self.cursor_area_radius = bubble_radius

    ''' In addition to the system's standard pointer representation a blue circle
        is drawn around the center

        @param painter: PyQt QPainter object that can draw to the canvas
    '''
    def draw_pointer(self, painter):
        painter.setBrush(self.COLOR_BLUE)
        painter.drawEllipse(QtCore.QPoint(self.cursor_pos_x, self.cursor_pos_y), self.cursor_area_radius,
                            self.cursor_area_radius)

    ''' Checking which of the given targets is currently under
        the pointer's clickable area

        @return: A list of all targets that are currently under the pointer
    '''
    def get_targets_under_cursor(self):
        hits = []
        for target in self.targets:
            if GeometryUtils.are_circles_intersecting(self.cursor_pos_x,
                                                      self.cursor_pos_y,
                                                      self.cursor_area_radius,
                                                      target.pos_x, target.pos_y,
                                                      target.diameter / 2):
                hits.append(target)
        return hits


class GeometryUtils:

    """
        Utility class for mathematical operations in 2D space
    """

    ''' Calculates the length of the vector between two points

        @param point1: Vector containing x- and y-coordinates defining a point in 2D space
        @param point2: Vector containing x- and y-coordinates defining a another point in 2D space#

        @return: The distance between the points
    '''
    @staticmethod
    def calculate_distance_between_points(point1, point2):
        return math.sqrt(math.pow(point2[0] - point1[0], 2) + math.pow(point2[1] - point1[1], 2))

    ''' Checks if two circles are colliding with each other

        @param x1: X-Coordinate of the first circle
        @param y1: Y-Coordinate of the first circle
        @param radius1: Radius of the first circle
        @param x2: X-Coordinate of the second circle
        @param y2: Y-Coordinate of the second circle
        @param radius2: Radius of the second circle

        @return: True if the two circles are intersecting, False if not
    '''
    @staticmethod
    def are_circles_intersecting(x1, y1, radius1, x2, y2, radius2):
        distance_circles = GeometryUtils.calculate_distance_between_points([x1, y1], [x2, y2])
        return distance_circles <= (radius1 + radius2)

    ''' Calculates the distance between the point and circle's center point
        the point is inside if the distance is even or smaller than the circle's radius

        @param point: Vector containing x- and y-coordinates defining a point in 2D space
        @param center: Vector containing x- and y-coordinates defining a point in 2D space
        @param diameter: The diameter defining the extends of the circle

        @return: True if the point is inside the given circle, False if not
    '''
    @staticmethod
    def is_point_inside_circle(point, center, diameter):
        distance = GeometryUtils.calculate_distance_between_points(point, center)
        if distance <= diameter / 2:
            return True
        return False
