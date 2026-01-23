from gui.control_panel import ControlPanel
from kuka_comm_lib import KukaRobot
import cv2
import torch
# import bluetooth
import socket

if __name__ == "__main__":
    # server_address = "B8:27:EB:9A:19:C0"  # raspberry pi server (claw)
    # port = 1
    server_address = "10.42.0.218" # Raspberry pi's IP address
    port = 5050

    robot = KukaRobot("192.168.1.195") # Kuka robot
    robot.connect()
    robot.set_speed(1)

    # rp_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    rp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rp_socket.settimeout(10)

    rp_socket.connect((server_address, port))
    print(f"Connected to the raspberrypi server over WiFi at {server_address}:{port}")

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    model_d = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
    model_c = torch.load("checkpoints/trash.pth", map_location=device)

    cap = cv2.VideoCapture(0)

    panel = ControlPanel(robot, rp_socket, "Waste Sorter")

    panel.video_stream(cap, model_d, model_c)

    panel.mainloop()

    # Release the webcam when the window is closed
    cap.release()
    cv2.destroyAllWindows()
