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

def pixels2mm(x_pixel, y_pixel, w_pixel, h_pixel, frame_width=1080, frame_height=1920):
    """
    Convert pixel coordinates and dimensions to millimeters based on camera parameters.
    
    :param x_pixel: X coordinate of the detected object in pixels
    :param y_pixel: Y coordinate of the detected object in pixels
    :param w_pixel: Width of the detected object in pixels
    :param h_pixel: Height of the detected object in pixels
    :param frame_width: Width of the video frame in pixels
    :param frame_height: Height of the video frame in pixels
    """
    w_mm_total = calculate_base(CAM_X_ANG, DETECT_HEIGHT) * 2
    h_mm_total = calculate_base(CAM_Y_ANG, DETECT_HEIGHT) * 2

    x_obj_mid = x_pixel + (w_pixel/2)
    y_obj_mid = y_pixel + (h_pixel/2)

    # Convert ratios to mm relative to home position
    x_ratio = (x_obj_mid / frame_width) - 0.5
    y_ratio = (y_obj_mid / frame_height) - 0.5

    x_mm = HOME_POS[0] + (w_mm_total * x_ratio)
    y_mm = HOME_POS[1] + (h_mm_total * y_ratio)
    
    # Convert dimensions
    w_mm = w_pixel * (w_mm_total / frame_width)
    h_mm = h_pixel * (h_mm_total / frame_height)

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
