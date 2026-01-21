from typing import Callable
from events.event import EventLoop
from kuka.constants import HOME_POS, TOOL_ANGLE
from kuka_comm_lib import KukaRobot
import socket


def signal_grip(angle, rp_socket):
    server_address = "10.42.0.83"
    port = 5050
    rp_socket = socket.socket()
    rp_socket.connect((server_address, port))
    if (angle < 0) or (angle > 90):
        raise ValueError("Grip angle must be between 0 and 90 degrees")
    rp_socket.send(str(angle).encode("utf-8"))


def queuemove(e: EventLoop, r: KukaRobot, func: Callable):
    def fun():
        # print(r._asyncioloop.run_until_complete(r._connection.get_variable("RUN_FRAME")))
        func()
        # print("Done something good")
    def fun2():
        out = r.is_ready_to_move()
        # print("ready?: ", out, r._asyncioloop.run_until_complete(r._connection.get_variable("RUN_FRAME")))
        return out
    e.run_and_wait(fun, fun2)


def queuegrip(e: EventLoop, angle, rp_socket):
    e.run(lambda: signal_grip(angle, rp_socket))
    e.sleep(2000)


def movehome(r: KukaRobot):
    r.goto(
        HOME_POS[0],
        HOME_POS[1],
        HOME_POS[2],
        TOOL_ANGLE[0],
        TOOL_ANGLE[1],
        TOOL_ANGLE[2],
    )
