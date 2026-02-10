import socket
import lgpio
import servo
import pi_constants as const
import logging
import threading
import time

logger = logging.getLogger(__name__)

def start_camera_stream():
    """
    Start an H.264 camera stream over TCP using Picamera2 if available.

    Falls back to launching `libcamera-vid` via subprocess when Picamera2
    is not installed or fails to initialize. Logs `PATH` and executable
    discovery to aid debugging when the binary is reported as missing.
    """

    # Try Picamera2 first (preferred modern Python API for libcamera)
    try:
        from picamera2 import Picamera2
        from picamera2.encoders import H264Encoder
        from picamera2.outputs import FileOutput

        logger.info("Using picamera2 for H.264 streaming on port %s", const.PI_CAMERA_PORT)

        picam2 = Picamera2()
        # Create a simple video configuration
        config = picam2.create_video_configuration({
            "size": (1080, 1920) # TODO: Larger resolution may cause performance issues;
        })
        picam2.configure(config)
        picam2.start()

        # TCP listener for clients wanting the H.264 stream
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", const.PI_CAMERA_PORT))
        server.listen(1)
        logger.info("Picamera2 streaming listening on 0.0.0.0:%s", const.PI_CAMERA_PORT)

        while True:
            client_socket, addr = server.accept()
            logger.info("Camera client connected: %s", addr)
            out = client_socket.makefile("wb")
            output = FileOutput(out)
            encoder = H264Encoder()
            try:
                picam2.start_recording(encoder, output)
                # Keep recording until client disconnects
                while True:
                    time.sleep(0.5)
                    try:
                        # Peek to see if the client closed the connection
                        data = client_socket.recv(1, socket.MSG_PEEK)
                        if not data:
                            break
                    except BlockingIOError:
                        # No data, connection still open
                        continue
                    except OSError:
                        break
            except Exception as e:
                logger.warning("Camera streaming error: %s", e)
            finally:
                try:
                    picam2.stop_recording()
                except Exception:
                    pass
                try:
                    out.close()
                except Exception:
                    pass
                client_socket.close()
                logger.info("Camera client disconnected")

    except Exception as pic_err:
        # Picamera2 not available or failed to initialize — report and stop
        logger.error("picamera2 initialization failed: %s", pic_err)
        return

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
