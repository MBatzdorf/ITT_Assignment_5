#!usr/bin/python3

import math


class StandardPointingTechnique(object):
    targets = []
    last_x = -1
    last_y = -1
    direction = [0, 0]
    cursor_area_radius = 20

    def __init__(self, targets, Target):
        self.targets = targets
        self.target_class = Target

    def filter(self, pos_x, pos_y):
        if self.last_x == -1 or self.last_y == -1:
            self.last_x = pos_x
            self.last_y = pos_y
        else:
            distance = [pos_x - self.last_x, pos_y - self.cursor_pos_y]
            norm = math.sqrt(distance[0] ** 2 + distance[1] ** 2)
            if norm == 0:
                norm = 1
            self.direction = [distance[0] / norm, distance[1] / norm]
            self.last_x = pos_x
            self.last_y = pos_y
        self.cursor_pos_x = pos_x
        self.cursor_pos_y = pos_y
        return self.target_class(pos_x, pos_y, 2)

    def get_cursor_direction(self):
        return self.direction

    def get_targets_under_cursor(self):

        hits = []
        for target in self.targets:
            if GeometryUtils.is_point_inside_target([self.cursor_pos_x, self.cursor_pos_y],[target.pos_x, target.pos_y],target.diameter):
                hits.append(target)
        return hits

    def update_targets(self, targets):
        self.targets = targets


class PointingTechniqueFatBubble(StandardPointingTechnique):

    def __init__(self, targets, Target, bubble_radius):
        super().__init__(targets, Target)
        #self.cursor_area_radius = 20
        self.cursor_area_radius = bubble_radius

    def filter(self, pos_x, pos_y):
        super().filter(pos_x, pos_y)
        return self.target_class(pos_x, pos_y, 2 * self.cursor_area_radius)

    def get_cursor_direction(self):
        return super().get_cursor_direction()

    def get_targets_under_cursor(self):
        hits = []
        for target in self.targets:
            if GeometryUtils.are_circles_intersecting(self.cursor_pos_x, self.cursor_pos_y, self.cursor_area_radius, target.pos_x, target.pos_y, target.diameter / 2):
                hits.append(target)
        return hits

    def update_targets(self, targets):
        super().update_targets(targets)


class GeometryUtils:
    @staticmethod
    def calculateDistanceBetweenPoints(point1, point2):
        return math.sqrt(math.pow(point2[0] - point1[0], 2) + math.pow(point2[1] - point1[1], 2))

    @staticmethod
    def are_circles_intersecting(x1, y1, radius1, x2, y2, radius2):
        distance_circles = GeometryUtils.calculateDistanceBetweenPoints([x1, y1], [x2, y2])
        return distance_circles <= (radius1 + radius2)

    @staticmethod
    def is_point_inside_target(point, target, diameter):
        distance = GeometryUtils.calculateDistanceBetweenPoints(point, target)
        if distance <= diameter / 2:
            return True
        return False