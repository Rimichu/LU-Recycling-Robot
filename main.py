from contextlib import contextmanager
from gui.control_panel import ControlPanel
from kuka_comm_lib import KukaRobot
from rp.pi_constants import PI_SERVER_ADDRESS, PI_SERVER_PORT  
import cv2
import torch
import socket
import logging

logger = logging.getLogger(__name__)

# Kuka Robot constants
LEFT_KUKA_IP_ADDRESS = "192.168.1.195"

def connect_to_pi(pi_server_address=PI_SERVER_ADDRESS, pi_server_port=PI_SERVER_PORT):
    """
    Connect to the raspberrypi server over WiFi.

    :param pi_server_address: The IP address of the raspberrypi server.
    :param pi_server_port: The port number of the raspberrypi server.

    Returns the socket object.
    """
    rp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rp_socket.settimeout(10)
    rp_socket.connect((pi_server_address, pi_server_port))
    logger.info(f"Connected to the raspberrypi server over WiFi at {pi_server_address}:{pi_server_port}")
    return rp_socket

def disconnect_from_pi(rp_socket):
    """
    Disconnect from the raspberrypi server.

    :param rp_socket: The socket object connected to the raspberrypi server.
    """

    rp_socket.close()
    logger.info("Disconnected from the raspberrypi server")

# By allowing default parameters, we can potentially use both or more robots in the future.
def connect_to_robot(ip_address=LEFT_KUKA_IP_ADDRESS, speed=1):
    """
    Connect to the Kuka robot over Ethernet.

    :param ip_address: The IP address of the Kuka robot (default is LEFT_KUKA_IP_ADDRESS).
    :param speed: The speed to set for the robot (default is 1).
    """
    # TODO: See if we can set up a pseudoname for the robot so program can be more general.
    robot = KukaRobot(ip_address)
    robot.connect()
    robot.set_speed(speed) # TODO: See documentation of set_speed
    logger.info(f"Connected to Kuka robot at {ip_address}")
    return robot

def disconnect_from_robot(robot):
    """
    Disconnect from the Kuka robot.
    
    :param robot: The KukaRobot object to disconnect.
    """
    robot.disconnect()
    logger.info("Disconnected from Kuka robot")

@contextmanager
def initialize_resources():
    """Context manager to initialize and cleanup all resources."""
    rp_socket = None
    robot = None
    cap = None
    
    try:
        rp_socket = connect_to_pi()
        robot = connect_to_robot()
        
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model_d = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
        model_c = torch.load("checkpoints/trash.pth", map_location=device, weights_only=False)
        model_c.eval()
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Camera failed to open")
        
        yield rp_socket, robot, model_d, model_c, cap
        
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error(f"Initialisation failed: {e}")

        # This will only catch the first failed resource (if the first fails, the others will not have had the chance to get intialised)
        if not rp_socket:
            raise Exception("Raspberry Pi connection failed") from e
        if not robot:
            raise Exception("Kuka robot connection failed") from e
        if not (cap and cap.isOpened()):
            raise Exception("Camera initialization failed") from e
    finally:
        if rp_socket:
            disconnect_from_pi(rp_socket)
        if robot:
            disconnect_from_robot(robot)
        if cap and cap.isOpened():
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        with initialize_resources() as (rp_socket, robot, model_d, model_c, cap):
            controlPanel = ControlPanel(robot, rp_socket, "Recycling Robot Control Panel")
            controlPanel.video_stream(cap, model_d, model_c)
            controlPanel.mainloop()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)
