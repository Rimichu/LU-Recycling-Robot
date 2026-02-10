from typing import Callable
from events.event import EventLoop
from kuka.constants import HOME_POS, TOOL_ANGLE, OFF_POS, OFF_TOOL_ANGLE
from kuka_comm_lib import KukaRobot
import socket
import rp.pi_constants as const

def signal_grip(command, rp_socket):
    """
    Send grip command to the R-Pi via socket.
    Ensures command is valid before sending.
    
    :param command: Grip command to send (open or close)
    :param rp_socket: Raspberry Pi socket for communication
    """
    if (command != const.COMMAND_OPEN) and (command != const.COMMAND_CLOSE):
        raise ValueError("Incorrect command for grip signal")
    rp_socket.send(command.encode("utf-8"))

def queuemove(e: EventLoop, r: KukaRobot, func: Callable):
    """
    Queue a movement command to the Kuka robot and wait for it to complete.
    
    :param e: Event loop managing asynchronous operations
    :param r: Kuka robot instance
    :param func: Function representing the movement command to execute
    """

    def is_ready():
        out = r.is_ready_to_move()
        return out
    
    e.run_and_wait(func, is_ready)

def queuegrip(e: EventLoop, command, rp_socket):
    """
    Queue a grip command to the R-Pi and wait for 5 seconds.
    
    :param e: Event loop managing asynchronous operations
    :param command: Grip command to send (open or close)
    :param rp_socket: Raspberry Pi socket for communication
    """
    e.run(lambda: signal_grip(command, rp_socket))
    e.sleep(2000)

def movehome(r: KukaRobot):
    """
    Move the Kuka robot to its home position.
    
    :param r: Kuka robot instance
    """
    r.goto(*HOME_POS, *TOOL_ANGLE) # Move to home position

def moveOff(r: KukaRobot):
    """
    Move the Kuka robot to its off position.
    
    :param r: Kuka robot instance
    """
    r.goto(*OFF_POS, *OFF_TOOL_ANGLE) # Move to off position

# TODO: Add error handling for lost connections
def pi_reconnect(rp_socket):
    """
    Attempt to reconnect to the Raspberry Pi server.
    
    :param rp_socket: Raspberry Pi socket for communication
    """
    try:
        rp_socket.close()
    except Exception:
        pass  # Ignore errors on close

    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_socket.settimeout(10)
    new_socket.connect((const.PI_SERVER_ADDRESS, const.PI_SERVER_PORT))
    print(f"Reconnected to the raspberrypi server over WiFi at {const.PI_SERVER_ADDRESS}:{const.PI_SERVER_PORT}")
    return new_socket