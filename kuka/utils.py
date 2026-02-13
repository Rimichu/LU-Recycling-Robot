import logging
import math
from kuka.constants import *

def calculate_base(angle_degrees, height):
    """
    Calculate the base length of a right triangle given an angle and height.
    
    :param angle_degrees: Angle in degrees between the height and the hypotenuse
    :param height: Height of the triangle in mm
    """

    angle_radians = math.radians(angle_degrees)
    base = height * math.tan(angle_radians)
    
    return base

def pixels2mm(x_pixel, y_pixel, w_pixel, h_pixel, frame_width=1080, frame_height=1920,
              fx: float = 1550, fy: float = 1550, cx: float = 540, cy: float = 960,
              z_mm: float = DETECT_HEIGHT - CONVEYOR_HEIGHT):
    """
    Convert pixel coordinates and dimensions to millimeters based on camera parameters.
    
    :param x_pixel: X coordinate of the detected object in pixels
    :param y_pixel: Y coordinate of the detected object in pixels
    :param w_pixel: Width of the detected object in pixels
    :param h_pixel: Height of the detected object in pixels
    :param frame_width: Width of the video frame in pixels
    :param frame_height: Height of the video frame in pixels
    :param fx: Focal length in pixels along the x-axis
    :param fy: Focal length in pixels along the y-axis
    :param cx: Principal point x-coordinate in pixels
    :param cy: Principal point y-coordinate in pixels
    :param z_mm: Estimated depth (Z coordinate) of the object in millimeters
    """
    logging.info("Size of frame: Width: %d, Height: %d", frame_width, frame_height)

    # Convert pixel center to image coordinates (use box centre)
    x_obj_mid = x_pixel + (w_pixel / 2.0)
    y_obj_mid = y_pixel + (h_pixel / 2.0)

    # Normalized camera coordinates
    x_n = (x_obj_mid - cx) / fx
    y_n = (y_obj_mid - cy) / fy

    # Back-project to real-world at known Z (pinhole model): X = x_n * Z, Y = y_n * Z
    X_mm = x_n * z_mm
    Y_mm = y_n * z_mm

    # Translate so that image centre maps to HOME_POS (maintain previous coordinate convention)
    # Compute image centre world coords (where u=cx, v=cy)
    cx_n = (cx - cx) / fx  # zero
    cy_n = (cy - cy) / fy  # zero
    Xc_mm = cx_n * z_mm
    Yc_mm = cy_n * z_mm

    # Home position is expected to correspond to image centre — offset accordingly
    x_mm = HOME_POS[0] + (X_mm - Xc_mm)
    y_mm = HOME_POS[1] + (Y_mm - Yc_mm)

    # Sizes: compute mm per pixel at object depth using fx/fy
    mm_per_pixel_x = z_mm / fx
    mm_per_pixel_y = z_mm / fy
    w_mm = w_pixel * mm_per_pixel_x
    h_mm = h_pixel * mm_per_pixel_y

    logging.debug("Pinhole mapping: x_mid=%f y_mid=%f -> X_mm=%f Y_mm=%f", x_obj_mid, y_obj_mid, x_mm, y_mm)
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
