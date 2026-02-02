from contextlib import contextmanager
from gui.control_panel import ControlPanel
from kuka_comm_lib import KukaRobot
import cv2
import torch
import socket

# Raspberry Pi constants
PI_SERVER_ADDRESS = "10.42.0.218"
PI_SERVER_PORT = 5050

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
    print(f"Connected to the raspberrypi server over WiFi at {pi_server_address}:{pi_server_port}")
    return rp_socket

def disconnect_from_pi(rp_socket):
    """
    Disconnect from the raspberrypi server.

    :param rp_socket: The socket object connected to the raspberrypi server.
    """

    rp_socket.close()
    print("Disconnected from the raspberrypi server")

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
    print(f"Connected to Kuka robot at {ip_address}")
    return robot

def disconnect_from_robot(robot):
    """
    Disconnect from the Kuka robot.
    
    :param robot: The KukaRobot object to disconnect.
    """
    robot.disconnect()
    print("Disconnected from Kuka robot")

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
        model_c = torch.load("checkpoints/trash.pth", map_location=device)
        
        cap = cv2.VideoCapture(0)
        
        yield rp_socket, robot, model_d, model_c, cap
        
    except Exception as e:
        print(f"Initialization failed: {e}")
        raise # Re-raise exception after logging to exit try in main
    finally:
        if rp_socket:
            disconnect_from_pi(rp_socket)
        if robot:
            disconnect_from_robot(robot)
        if cap:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        with initialize_resources() as (rp_socket, robot, model_d, model_c, cap):
            controlPanel = ControlPanel(robot, rp_socket, "Waste Sorter")
            controlPanel.video_stream(cap, model_d, model_c)
            controlPanel.mainloop()
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
