# import bluetooth
import socket
import RPi.GPIO as GPIO
from servo import set_angle
import time
import threading

# TODO: See if handle_client can be made async
# TODO: Get light to flash when r-pi on # TODO: See if led_pattern_loop can be made async

# # LED configuration
# LED_PIN = 42  # RPi 5 onboard LED (GPIO 42)

# def flash_led_pattern():
#     """
#     Flash the onboard LED with the pattern:
#     5 fast blinks, then 5 seconds on, then 1 second off (repeats).
    
#     :return: None
#     """
#     # 5 fast blinks
#     for _ in range(5):
#         GPIO.output(LED_PIN, GPIO.HIGH)
#         time.sleep(0.2)
#         GPIO.output(LED_PIN, GPIO.LOW)
#         time.sleep(0.2)
    
#     # 5 seconds on
#     GPIO.output(LED_PIN, GPIO.HIGH)
#     time.sleep(5)
    
#     # 1 second off
#     GPIO.output(LED_PIN, GPIO.LOW)
#     time.sleep(1)

# def led_pattern_loop(stop_event):
#     """
#     Continuously run the LED flash pattern until stop_event is set.
    
#     :param stop_event: threading.Event to signal when to stop the loop
#     :return: None
#     """
#     while not stop_event.is_set():
#         flash_led_pattern()

def handle_client(client_socket, client_address):
    """
    Handle communication with a connected (bluetooth?) client.

    :param client_socket: The client socket object
    :param client_address: The address of the connected client

    :return: None
    """

    print(f"Accepted connection from {client_address}")
    
    # Start LED flashing pattern in a separate thread
    # led_stop_event = threading.Event()
    # led_thread = threading.Thread(target=led_pattern_loop, args=(led_stop_event,), daemon=True)
    # led_thread.start()
    
    # try:
    while True:
        # Receive data from the client
        data = client_socket.recv(1024)  # Receive up to 1024 bytes
        if not data:
            break
        print(f"Received data: {data.decode('utf-8')}")
        if data.decode("utf-8") == "exit":
            print("Exit command received. Closing connection.")
            client_socket.close()
            break
        # if data.decode("utf-8").startswith("angle:"):
        set_angle(pwm, pin, float(data.decode("utf-8").split(":")[1]))
        if data.decode("utf-8").startswith("ping"):
            print("Ping received, sending pong...")
            client_socket.sendall(b"pong")
    # finally:
        # Stop LED pattern when client disconnects
        # led_stop_event.set()
        # GPIO.output(LED_PIN, GPIO.LOW)
        # led_thread.join(timeout=2)

def while_loop(server_socket):
    """
    Main server loop to accept incoming TCP connections.

    :param server_socket: The server socket object

    :return: None

    :raises KeyboardInterrupt: When the server is interrupted manually
    """

    while True:
        print("Ready to accept connection...")
        client_socket, client_address = server_socket.accept()
        try:
            handle_client(client_socket, client_address)
        except OSError as e:
            print(f"Client disconnected: {e.strerror}")
        finally:
            # Close the sockets
            client_socket.close()

if __name__ == "__main__":
    # Set GPIO numbering mode
    GPIO.setmode(GPIO.BOARD)

    # # Setup LED pin (onboard LED on RPi 5)
    # GPIO.setup(LED_PIN, GPIO.OUT)
    # GPIO.output(LED_PIN, GPIO.LOW)  # Start with LED off

    # TODO: Find out what kind of servo motor this was, may need to add another pin to allow motor to move in both directions
    # Setup servo pin
    pin = 11
    GPIO.setup(pin, GPIO.OUT)

    pwm = GPIO.PWM(pin, 50)
    pwm.start(0)

    # Old Bluetooth code
    # server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    # # Bind the socket to any available port on the Bluetooth adapter
    # port = bluetooth.PORT_ANY
    # server_socket.bind(("", port))

    # # Start listening for incoming connections (backlog of 1)
    # server_socket.listen(1)
    # bluetooth_address, server_port = server_socket.getsockname()
    # print(f"Server is listening on Bluetooth address: {bluetooth_address}, port: {server_port}")

    HOST = "0.0.0.0" # Listen on all interfaces
    PORT = 5050      # Arbitrary non-privileged port

    server_socket = socket.create_server((HOST, PORT))
    print(f"Server created at {HOST}:{PORT}")

    try:
        while_loop(server_socket)
    finally:
        server_socket.close()
