# import bluetooth
import socket
import RPi.GPIO as GPIO
from servo import set_angle
import time
import threading
import pi_constants as const

# TODO: See if handle_client can be made async
# TODO: Get light to flash when r-pi on # TODO: See if led_pattern_loop can be made async

def handle_client(client_socket, client_address):
    """
    Handle communication with a connected (bluetooth?) client.

    :param client_socket: The client socket object
    :param client_address: The address of the connected client

    :return: None
    """

    print(f"Accepted connection from {client_address}")
    
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
        # print(float(data.decode("utf-8").split(":")[1]))
        # For now I just want to know what angle values are being sent
        # set_angle(PWM, ANTICLOCKWISE_PIN, CLOCKWISE_PIN, float(data.decode("utf-8").split(":")[1]))
        if data.decode("utf-8").startswith("ping"):
            print("Ping received, sending pong...")
            client_socket.sendall(b"pong")

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

    GPIO.setup(const.CLOCKWISE_PIN, GPIO.OUT)
    GPIO.setup(const.ANTICLOCKWISE_PIN, GPIO.OUT)

    HOST = "0.0.0.0" # Listen on all interfaces
    PORT = 5050      # Arbitrary non-privileged port

    server_socket = socket.create_server((HOST, PORT))
    print(f"Server created at {HOST}:{PORT}")

    try:
        while_loop(server_socket)
    finally:
        server_socket.close()
