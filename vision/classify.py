from typing import Callable
from cv2 import VideoCapture
import cv2
from kuka_comm_lib import KukaRobot
import torch
from events.event import EventLoop
from kuka.constants import BIN_DICT, CLASSIFY_HEIGHT, OBJECT_HEIGHT
from kuka.comms import movehome, queuegrip, queuemove
import numpy as np
from torchvision import transforms
import tkinter as tk
import rp.pi_constants as const

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
    
    

def process_object(rp_socket, eloop: EventLoop, robot: KukaRobot, unlock: Callable, dest_bin, grip_angle:float):
    """
    Process the object by moving the robot to pick it up and place it in the appropriate bin

    :param rp_socket: Raspberry Pi socket for communication
    :param eloop: Event loop managing asynchronous operations
    :param robot: Kuka robot instance
    :param unlock: Function to unlock the control panel
    :param dest_bin: Destination bin index
    :param grip_angle: Grip angle for the robot
        This is currently unused but may be useful in future implementations.
    """

    # Move robot to pick-up object
    eloop.run(lambda: print("Moving to Location"))
    queuemove(eloop, robot, lambda: robot.goto(a = 180, b = 0, c = 180))
    eloop.run(lambda: print("Open Claw"))
    queuegrip(eloop, const.COMMAND_OPEN, rp_socket)
    eloop.run(lambda: print("Moving Down"))
    queuemove(eloop, robot, lambda: robot.goto(z=OBJECT_HEIGHT))
    eloop.run(lambda: print("Close Claw"))
    queuegrip(eloop, const.COMMAND_CLOSE, rp_socket)
    eloop.run(lambda: print("Going Up"))
    queuemove(eloop, robot, lambda: robot.goto(z=CLASSIFY_HEIGHT))
    eloop.run(lambda: print("Trash picked up"))

    # Move robot to appropriate bin and release object
    bin_x, bin_y = BIN_DICT[dest_bin]
    eloop.run(lambda: print("Moving to bin:", bin_x, bin_y))
    queuemove(eloop, robot, lambda: robot.goto(bin_x, bin_y))
    eloop.run(lambda: print("Moving Down"))
    queuemove(eloop, robot, lambda: robot.goto(z=OBJECT_HEIGHT))
    eloop.run(lambda: print("Open Claw"))
    queuegrip(eloop, const.COMMAND_OPEN, rp_socket)
    eloop.run(lambda: print("Moving Up"))
    queuemove(eloop, robot, lambda: robot.goto(z=CLASSIFY_HEIGHT))
    eloop.run(lambda: print("Close Claw"))
    queuegrip(eloop, const.COMMAND_CLOSE, rp_socket)
    eloop.run(lambda: print("Moving Home"))
    queuemove(eloop, robot, lambda: movehome(robot))
    eloop.run(lambda: print("Arrived Home"))
    eloop.run(unlock)
    eloop.run(lambda: print("Ready to Detect"))


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
