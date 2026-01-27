from typing import Callable
from events.event import EventLoop
from kuka.constants import HOME_POS, TOOL_ANGLE
from kuka_comm_lib import KukaRobot
import socket
import rp.pi_constants as const

def signal_grip(command, rp_socket):
    if (command != const.COMMAND_OPEN) and (command != const.COMMAND_CLOSE):
        raise ValueError("Incorrect command for grip signal")
    rp_socket.send(command.encode("utf-8"))

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


def queuegrip(e: EventLoop, command, rp_socket):
    # DEBUG: print("Queueing grip command: ", command)
    print("Queueing grip command: ", command)
    e.run(lambda: signal_grip(command, rp_socket))
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
