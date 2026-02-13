from typing import Callable
from cv2 import VideoCapture
from kuka_comm_lib import KukaRobot
import torch
from events.event import EventLoop
from kuka.constants import BIN_DICT, CLASSIFY_HEIGHT, OBJECT_HEIGHT
from kuka.comms import movehome, queuegrip, queuemove
from torchvision import transforms
import tkinter as tk
import rp.pi_constants as const
import logging

def classify_object(model_c, cap: VideoCapture, class_label: tk.Label):
    """
    Classify the object in the frame and move the robot accordingly.
    
    :param model_c: The classification model
    :param cap: Video capture object
    :param class_label: Tkinter label to display the classified object type

    :return: The destination bin index
    """

    # Capture frame from camera, classify object and move robot accordingly
    ret, frame = cap.read()
    if not ret or frame is None:
        raise Exception("Failed to capture frame from camera for classification")
    logging.info("start classify")
    img = process_image(frame)
    logits = model_c(img)
    dest_bin = int(torch.argmax(logits, dim=1).item())
    logging.info("classify done: %d %s", dest_bin, get_label(dest_bin))
    class_label.config(text=f"Object Type: {get_label(dest_bin)}")

    return dest_bin

def dispose_of_object(rp_socket, eloop: EventLoop, robot: KukaRobot, unlock: Callable, dest_bin, position:tuple, grip_angle:tuple=(180,0,180)):
    """
    Process the object by moving the robot to pick it up and place it in the appropriate bin

    :param rp_socket: Raspberry Pi socket for communication
    :param eloop: Event loop managing asynchronous operations
    :param robot: Kuka robot instance
    :param unlock: Function to unlock the control panel
    :param dest_bin: Destination bin index
    :param position: Position tuple (x, y) of the object
    :param grip_angle: Grip angle for the robot
        This is currently unused but may be useful in future implementations.
    """

    # Move robot to pick-up object
    eloop.run(lambda: logging.info("Moving to object position: %s", position))
    queuemove(eloop, robot, lambda: robot.goto(x=position[0], y=position[1], z=CLASSIFY_HEIGHT))
    eloop.run(lambda: logging.info("Setting grip angle: %s", grip_angle))
    queuemove(eloop, robot, lambda: robot.goto(a = grip_angle[0], b = grip_angle[1], c = grip_angle[2]))
    eloop.run(lambda: logging.info("Open Claw"))
    queuegrip(eloop, const.COMMAND_OPEN, rp_socket)
    eloop.run(lambda: logging.info("Moving Down"))
    queuemove(eloop, robot, lambda: robot.goto(z=OBJECT_HEIGHT))
    eloop.run(lambda: logging.info("Close Claw"))
    queuegrip(eloop, const.COMMAND_CLOSE, rp_socket)
    eloop.run(lambda: logging.info("Going Up"))
    queuemove(eloop, robot, lambda: robot.goto(z=CLASSIFY_HEIGHT))
    eloop.run(lambda: logging.info("Trash picked up"))
    # Move robot to appropriate bin and release object
    bin_x, bin_y = BIN_DICT[dest_bin]
    eloop.run(lambda: logging.info("Moving to bin: %d, %d", bin_x, bin_y))
    queuemove(eloop, robot, lambda: robot.goto(bin_x, bin_y))
    # eloop.run(lambda: logging.info("Moving Down"))
    # queuemove(eloop, robot, lambda: robot.goto(z=OBJECT_HEIGHT))
    eloop.run(lambda: logging.info("Open Claw"))
    queuegrip(eloop, const.COMMAND_OPEN, rp_socket)
    # eloop.run(lambda: logging.info("Moving Up"))
    # queuemove(eloop, robot, lambda: robot.goto(z=CLASSIFY_HEIGHT))
    eloop.run(lambda: logging.info("Close Claw"))
    queuegrip(eloop, const.COMMAND_CLOSE, rp_socket)
    eloop.run(lambda: logging.info("Moving Home"))
    queuemove(eloop, robot, lambda: movehome(robot))
    eloop.run(lambda: logging.info("Arrived Home"))
    eloop.after(1000, unlock) # Unlock control panel after 1 second to ensure robot has finished moving, also gives enough time for camera to adjust for next detection
    eloop.run(lambda: logging.info("Ready to Detect"))


# Module level device and transform to avoid reinitialization on every classification
_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_TRANSFORM = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize([224, 224]),
    transforms.ToTensor()
])

def process_image(img):
    """
    Process the captured image for classification by applying necessary transformations.
    """
    return _TRANSFORM(img).unsqueeze(0).to(_DEVICE)

def get_label(idx):
    """
    Get the label corresponding to the classification index.
    
    :param idx: Classification index
    """
    labels = ["metal", "misc", "plastic", "glass", "paper", "cardboard"]
    return(labels[idx])
