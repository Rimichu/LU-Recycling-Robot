import socket
import lgpio
import servo
import pi_constants as const
import logging
import threading
import subprocess

logger = logging.getLogger(__name__)

def start_camera_stream():
    """
    Start libcamera-vid to stream H.264 video over TCP.
    Uses the Pi's hardware H.264 encoder for minimal CPU usage and low latency.
    Listens for incoming TCP connections on PI_CAMERA_PORT.
    """
    cmd = [
        "libcamera-vid",
        "-t", "0",                          # Stream indefinitely
        "--width", "640",
        "--height", "480",
        "--framerate", "30",
        "--codec", "h264",
        "--profile", "baseline",            # Baseline profile for low latency
        "--level", "4.2",
        "--inline",                         # Inline headers for stream joining
        "--flush",                          # Flush output buffers immediately
        "--listen",                         # TCP listen mode
        "-o", f"tcp://0.0.0.0:{const.PI_CAMERA_PORT}",
    ]
    logger.info(f"Starting H.264 camera stream on TCP port {const.PI_CAMERA_PORT}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Log any stderr output
        for line in process.stderr:
            logger.debug(f"libcamera-vid: {line.decode().strip()}")
    except FileNotFoundError:
        logger.error("libcamera-vid not found. Install with: sudo apt install libcamera-apps")
    except Exception as e:
        logger.error(f"Failed to start camera stream: {e}")

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

    # Start H.264 camera stream in a background thread
    camera_thread = threading.Thread(target=start_camera_stream, daemon=True)
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
