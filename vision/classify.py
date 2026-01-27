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

def classify_object(
    model_c,
    cap: VideoCapture,
    rp_socket,
    grip_angle: float,
    eloop: EventLoop,
    robot: KukaRobot,
    unlock: Callable,
    class_label: tk.Label
):
    _, frame = cap.read()
    print("start classify")
    img = process_image(frame)
    logits = model_c(img)
    dest_bin = int(torch.argmax(logits, dim=1).item())
    print("classify done: ", dest_bin, get_label(dest_bin))
    eloop.run(lambda: print("Moving to Location"))
    queuemove(eloop, robot, lambda: robot.goto(a = 180, b = 0, c = 180))

    class_label.config(text=f"Object Type: {get_label(dest_bin)}")
    # move to object
    eloop.run(lambda: print("Open Claw"))
    queuegrip(eloop, const.COMMAND_OPEN, rp_socket)
    # move into position around/above object
    eloop.run(lambda: print("Moving Down"))
    queuemove(eloop, robot, lambda: robot.goto(z=OBJECT_HEIGHT))
    # close around object
    eloop.run(lambda: print("Close Claw"))
    queuegrip(eloop, const.COMMAND_CLOSE, rp_socket)
    # move up
    eloop.run(lambda: print("Going Up"))
    queuemove(eloop, robot, lambda: robot.goto(z=CLASSIFY_HEIGHT))
    eloop.run(lambda: print("Trash picked up"))

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
    transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize([224,224]),
    transforms.ToTensor()
    ])

    device = torch.device("cpu")

    return transform(img).unsqueeze(0).to(device)

def get_label(idx):
    labels = ["metal", "misc", "plastic", "glass", "paper", "cardboard"]
    return(labels[idx])
