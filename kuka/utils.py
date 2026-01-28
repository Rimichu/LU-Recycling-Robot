import math
from kuka.constants import *

def calculate_base(angle_degrees, height):
    """
    Calculate the base length of a right triangle given an angle and height.
    
    :param angle_degrees: Angle in degrees
    :param height: Height of the triangle in mm(?not sure if mm is true whilst writing this?)
    """

    angle_radians = math.radians(angle_degrees)
    base = height * math.tan(angle_radians)
    
    return base

def pixels2mm(x_pixel, y_pixel, w_pixel, h_pixel):
    """
    Convert pixel coordinates and dimensions to millimeters.

    :param x_pixel: X coordinate in pixels
    :param y_pixel: Y coordinate in pixels
    :param w_pixel: Width in pixels
    :param h_pixel: Height in pixels

    :return: Tuple of (x_mm, y_mm, w_mm, h_mm)
    """
    # camera resolution 1080/1920
    # camera verticle angle 48, horizontal 28.5
    w_mm = calculate_base(CAM_X_ANG, DETECT_HEIGHT)
    h_mm = calculate_base(CAM_Y_ANG, DETECT_HEIGHT)

    x_obj_mid = x_pixel + (w_pixel/2)
    y_obj_mid = y_pixel + (h_pixel/2)

    x_mm = x_obj_mid
    y_mm = y_obj_mid
    w_mm = w_pixel
    h_mm = h_pixel
    
    # x_ratio = (x_obj_mid/1080)
    # y_ratio = (y_obj_mid/1920)

    # if x_ratio != 0.5:
    #     x_ratio -= 0.5
    # else:
    #     x_ratio = 0

    # if y_ratio != 0.5:
    #     y_ratio -= 0.5
    # else:
    #     y_ratio = 0

    # x_delta = w_mm*x_ratio
    # y_delta = h_mm*y_ratio

    # x_mm = HOME_POS[0] + x_delta
    # y_mm = HOME_POS[1] + y_delta

    return x_mm, y_mm, w_mm, h_mm


def width2angle(w_mm, l=10):
    """
    Convert width in mm to angle in degrees based on distance l.

    :param w_mm: Width in millimeters
    :param l: Distance from the object to the rotation point in cm
    
    :return: Angle in degrees
    """
    w_cm = w_mm / 10
    rad = 2 * math.asin(w_cm / (2 * l))  # radians
    angle = math.degrees(rad)  # degrees
    return angle
