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

def pixels2mm(x_pixel, y_pixel, w_pixel, h_pixel, frame_width=CAM_FRAME_WIDTH, frame_height=CAM_FRAME_HEIGHT,
              fx: float = 410, fy: float = 410, cx: float = CAM_FRAME_WIDTH/2, cy: float = CAM_FRAME_HEIGHT/2,
              z_mm: float = DETECT_HEIGHT - CONVEYOR_HEIGHT):
    """
    Convert pixel coordinates and dimensions to millimeter displacements from the camera center.
    
    Returns how far the object is from the camera's optical axis (image center).
    An object at the image center returns (0, 0). Positive x = below center,
    negative x = above center. Positive y = right of center, negative y = left of center.

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

    :return: Tuple containing:
        - x_mm: X displacement from camera center in millimeters
        - y_mm: Y displacement from camera center in millimeters
        - w_mm: Width of the object in millimeters
        - h_mm: Height of the object in millimeters
    """
    logging.info("pixels2mm called with x=%s y=%s w=%s h=%s frame=%dx%d", x_pixel, y_pixel, w_pixel, h_pixel, frame_width, frame_height)
    logging.debug("Intrinsics: fx=%s fy=%s cx=%s cy=%s z_mm=%s", fx, fy, cx, cy, z_mm)

    # Convert pixel center to image coordinates (use box centre)
    x_obj_mid = x_pixel + (w_pixel / 2.0)
    y_obj_mid = y_pixel + (h_pixel / 2.0)

    # Normalized camera coordinates (displacement from principal point)
    x_n = (x_obj_mid - cx) / fx
    y_n = (y_obj_mid - cy) / fy
    logging.debug("Normalized coords: x_n=%f y_n=%f", x_n, y_n)

    # Back-project to real-world at known Z (pinhole model): X = x_n * Z, Y = y_n * Z
    # These are displacements from the camera center in mm
    x_mm = x_n * z_mm
    y_mm = y_n * z_mm
    logging.debug("Displacement from camera center: x_mm=%f y_mm=%f at Z=%s", x_mm, y_mm, z_mm)

    # Sizes: compute mm per pixel at object depth using fx/fy
    mm_per_pixel_x = z_mm / fx
    mm_per_pixel_y = z_mm / fy
    w_mm = w_pixel * mm_per_pixel_x
    h_mm = h_pixel * mm_per_pixel_y

    logging.info("Pinhole result: x_mm=%f y_mm=%f w_mm=%f h_mm=%f mm_per_px=(%f,%f)",
                 x_mm, y_mm, w_mm, h_mm, mm_per_pixel_x, mm_per_pixel_y)
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