from typing import Callable
from cv2 import VideoCapture
import cv2
from kuka_comm_lib import KukaRobot
import torch
from events.event import EventLoop
from kuka.constants import BIN_DICT, CLASSIFY_HEIGHT, OBJECT_HEIGHT
from kuka.comms import movehome, queuegrip, queuemove
from kuka.utils import pixels2mm
from vision.detect import process_frame
import numpy as np
from torchvision import transforms
import tkinter as tk
import rp.pi_constants as const

def is_object_centered(x_pixel, y_pixel, w_pixel, h_pixel, frame_width=1920, frame_height=1080, tolerance=50):
    """
    Check if the detected object is centered in the frame within a given tolerance.

    :param x_pixel: X coordinate of the detected object
    :param y_pixel: Y coordinate of the detected object
    :param w_pixel: Width of the detected object
    :param h_pixel: Height of the detected object
    :param frame_width: Width of the video frame
    :param frame_height: Height of the video frame
    :param tolerance: Tolerance in pixels for centering

    :return: True if centered, False otherwise
    """
    obj_center_x = x_pixel + (w_pixel / 2)
    obj_center_y = y_pixel + (h_pixel / 2)

    frame_center_x = frame_width / 2
    frame_center_y = frame_height / 2

    return (abs(obj_center_x - frame_center_x) <= tolerance) and (abs(obj_center_y - frame_center_y) <= tolerance)

# TODO: Change function so that it only handles classification, movement should be in a separate function
def classify_object(model_c, cap: VideoCapture, class_label: tk.Label):
    """
    Classify the object in the frame and move the robot accordingly.
    
    :param model_c: The classification model
    :param cap: Video capture object
    :param class_label: Tkinter label to display the classified object type

    :return: The destination bin index
    """

    # Capture frame from camera, classify object and move robot accordingly
    _, frame = cap.read()
    print("start classify")
    img = process_image(frame)
    logits = model_c(img)
    dest_bin = int(torch.argmax(logits, dim=1).item())
    print("classify done: ", dest_bin, get_label(dest_bin))
    class_label.config(text=f"Object Type: {get_label(dest_bin)}")

    return dest_bin

def centre_object(rp_socket, eloop: EventLoop, robot: KukaRobot, cap: VideoCapture, model_d):
    """
    Center the detected object in the robot's field of view.
    Continues running recursively until the object is centered.

    :param rp_socket: Raspberry Pi socket for communication
    :param eloop: Event loop managing asynchronous operations
    :param robot: Kuka robot instance
    :param cap: Video capture object
    :param model_d: Detection model
    """

    # Center object before moving to pick-up
    print("Object not centered, adjusting position...")
    _, frame = cap.read()
    processed_frame, is_detected, x_pixel, y_pixel, w_pixel, h_pixel = (
        process_frame(frame, model_d)
    )

    if is_detected:
        # x and y are inverted due to camera orientation
        y_mm, x_mm, w_mm, h_mm = pixels2mm(x_pixel, y_pixel, w_pixel, h_pixel)
        queuemove(eloop, robot, robot.goto(x=x_mm, y=y_mm, z=CLASSIFY_HEIGHT))
        
        # Queue another centering attempt if not centered
        if not is_object_centered(x_pixel, y_pixel, w_pixel, h_pixel):
            eloop.run(lambda: centre_object(rp_socket, eloop, robot, cap, model_d))
    else:
        print("Object lost during centering attempt.")
        return
    
def dispose_of_object(rp_socket, eloop: EventLoop, robot: KukaRobot, unlock: Callable, model_c, model_d, cap:VideoCapture, class_label:tk.Label, position:tuple, grip_angle:tuple=(180,0,180)):
    """
    Process the object by moving the robot to pick it up and place it in the appropriate bin.
    Note: This should be called with eloop.run() to execute in the event loop.

    :param rp_socket: Raspberry Pi socket for communication
    :param eloop: Event loop managing asynchronous operations
    :param robot: Kuka robot instance
    :param unlock: Function to unlock the control panel
    :param model_c: Classification model
    :param model_d: Detection model
    :param cap: Video capture object
    :param class_label: Tkinter label to display the classified object type
    :param position: Position tuple (x, y) of the object
    :param grip_angle: Grip angle for the robot
        This is currently unused but may be useful in future implementations.
    """

    dest_bin = classify_object(model_c, cap, class_label)
    
    # Wait for object to be centered, checking periodically
    def is_centered():
        _, frame = cap.read()
        processed_frame, is_detected, x, y, w, h = process_frame(frame, model_d)
        return is_detected and is_object_centered(x, y, w, h)
    
    # Start centering process
    eloop.run(lambda: centre_object(rp_socket, eloop, robot, cap, model_d))
    
    # Wait for centering with 30 second timeout
    if eloop.wait_for(is_centered, timeout=30):
        print("Object centered, proceeding...")
    else:
        print("Timeout waiting for object to center")

    # Move robot to pick-up object
    print("Moving to object position:", position)
    queuemove(eloop, robot, robot.goto(x=position[0], y=position[1], z=CLASSIFY_HEIGHT))
    
    print("Setting grip angle:", grip_angle)
    queuemove(eloop, robot, robot.goto(a=grip_angle[0], b=grip_angle[1], c=grip_angle[2]))
    
    print("Open Claw")
    queuegrip(eloop, const.COMMAND_OPEN, rp_socket)
    
    print("Moving Down")
    queuemove(eloop, robot, robot.goto(z=OBJECT_HEIGHT))
    
    print("Close Claw")
    queuegrip(eloop, const.COMMAND_CLOSE, rp_socket)
    
    print("Going Up")
    queuemove(eloop, robot, robot.goto(z=CLASSIFY_HEIGHT))
    
    print("Trash picked up")

    # Move robot to appropriate bin and release object
    bin_x, bin_y = BIN_DICT[dest_bin]
    print("Moving to bin:", bin_x, bin_y)
    queuemove(eloop, robot, robot.goto(bin_x, bin_y))
    
    print("Open Claw")
    queuegrip(eloop, const.COMMAND_OPEN, rp_socket)
    
    print("Close Claw")
    queuegrip(eloop, const.COMMAND_CLOSE, rp_socket)
    
    print("Moving Home")
    queuemove(eloop, robot, movehome(robot))
    
    print("Arrived Home")
    unlock()
    print("Ready to Detect")


def process_image(img):
    """
    Preprocess the image for classification.
    
    :param img: Input image in BGR format
    """
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize([224,224]),
        transforms.ToTensor()
    ])

    device = torch.device("cpu")

    return transform(img).unsqueeze(0).to(device)

def get_label(idx):
    """
    Get the label corresponding to the classification index.
    
    :param idx: Classification index
    """
    labels = ["metal", "misc", "plastic", "glass", "paper", "cardboard"]
    return(labels[idx])
