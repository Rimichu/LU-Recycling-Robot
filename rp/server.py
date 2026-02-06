import socket
import lgpio
import servo
import pi_constants as const
import logging
import threading
from flask import Flask, Response
from picamera2 import Picamera2
import cv2

logger = logging.getLogger(__name__)

# Flask app for camera streaming
flask_app = Flask(__name__)

# Shared Picamera2 instance
picam2 = None
picam2_lock = threading.Lock()

def init_camera():
    """Initialize the Picamera2 instance."""
    global picam2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
    picam2.configure(config)
    picam2.start()
    logger.info("Picamera2 started at 640x480")

def gen_frames():
    """Video streaming generator function."""
    while True:
        with picam2_lock:
            frame = picam2.capture_array()
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            logger.warning("Failed to encode frame to JPEG")
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

@flask_app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_camera_server():
    """Start the Flask camera server in a separate thread."""
    init_camera()
    logger.info(f"Starting camera stream on port {const.PI_CAMERA_PORT}")
    flask_app.run(host='0.0.0.0', port=const.PI_CAMERA_PORT, debug=False, threaded=True)

# TODO: See if handle_client can be made async
# TODO: Get light to flash when r-pi on # TODO: See if led_pattern_loop can be made async

def handle_client(client_socket, client_address, h):
    """
    Handle communication with a connected (bluetooth?) client.

    :param client_socket: The client socket object
    :param client_address: The address of the connected client

    :return: None
    """

    logger.info(f"Accepted connection from {client_address}")
    
    while True:
        # Receive data from the client
        data = client_socket.recv(1024)  # Receive up to 1024 bytes
        if not data:
            break
        logger.debug(f"Received data: {data.decode('utf-8')}")
        command = data.decode("utf-8")
        match command:
            case "exit":
                logger.info("Exit command received. Closing connection.")
                client_socket.close()
            case const.COMMAND_OPEN:
                logger.info("Open command received.")
                servo.open_claw(h, const.ANTICLOCKWISE_PIN, const.CLOCKWISE_PIN)  # Open claw
            case const.COMMAND_CLOSE:
                logger.info("Close command received.")
                servo.close_claw(h, const.CLOCKWISE_PIN, const.ANTICLOCKWISE_PIN)      # Close claw
            case _ if command.startswith("ping"):
                logger.info("Ping received, sending pong...")
                client_socket.sendall(b"pong")
            case _:
                logger.warning("Unknown command received.")

def while_loop(server_socket):
    """
    Main server loop to accept incoming TCP connections.

    :param server_socket: The server socket object

    :return: None

    :raises KeyboardInterrupt: When the server is interrupted manually
    """

    while True:
        logger.info("Ready to accept connection...")
        client_socket, client_address = server_socket.accept()
        try:
            handle_client(client_socket, client_address, h)
        except OSError as e:
            logger.warning(f"Client disconnected: {e.strerror}")
        finally:
            # Close the sockets
            client_socket.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Start camera streaming server in a background thread
    camera_thread = threading.Thread(target=start_camera_server, daemon=True)
    camera_thread.start()

    # Get handle to gpio pins
    h = lgpio.gpiochip_open(0)

    # Claim GPIOs as outputs and set initial state to LOW
    lgpio.gpio_claim_output(h, const.CLOCKWISE_PIN, const.LOW)
    lgpio.gpio_claim_output(h, const.ANTICLOCKWISE_PIN, const.LOW)

    HOST = "0.0.0.0" # Listen on all interfaces
    PORT = 5050      # Arbitrary non-privileged port

    server_socket = socket.create_server((HOST, PORT))
    logger.info(f"Server created at {HOST}:{PORT}")

    try:
        while_loop(server_socket)
    finally:
        lgpio.gpiochip_close(h)
        server_socket.close()
