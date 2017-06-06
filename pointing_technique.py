#!usr/bin/python3


class PointingTechnique(object):
    ellipses = []

    cursor_area_radius = 20

    def __init__(self, ellipses, Ellipse):
        self.ellipses = ellipses
        self.cursor = Ellipse

    def filter(self, pos_x, pos_y):
        self.cursor_pos_x = pos_x
        self.cursor_pos_y = pos_y
        return self.cursor(pos_x, pos_y, 2 * self.cursor_area_radius)
