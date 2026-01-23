import bluetooth
import RPi.GPIO as GPIO
from servo import set_angle

# TODO: See if handle_client can be made async

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
        set_angle(pwm, pin, float(data.decode("utf-8")))

def while_loop(server_socket):
    """
    Main server loop to accept incoming Bluetooth connections.

    :param server_socket: The server socket object

    :return: None

    :raises KeyboardInterrupt: When the server is interrupted manually
    """

    while True:
        print("Ready to accept connection...")
        client_socket, client_address = server_socket.accept()
        try:
            handle_client(client_socket, client_address)
        except bluetooth.BluetoothError as e:
            print(f"Client disconnected: {e.strerror}")
        finally:
            # Close the sockets
            client_socket.close()

if __name__ == "__main__":
    # Set GPIO numbering mode
    GPIO.setmode(GPIO.BOARD)

    # TODO: Find out what kind of servo motor this was, may need to add another pin to allow motor to move in both directions
    # Setup servo pin
    pin = 11
    GPIO.setup(pin, GPIO.OUT)

    pwm = GPIO.PWM(pin, 50)
    pwm.start(0)

    server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    # Bind the socket to any available port on the Bluetooth adapter
    port = bluetooth.PORT_ANY
    server_socket.bind(("", port))

    # Start listening for incoming connections (backlog of 1)
    server_socket.listen(1)
    bluetooth_address, server_port = server_socket.getsockname()
    print(f"Server is listening on Bluetooth address: {bluetooth_address}, port: {server_port}")

    try:
        while_loop(server_socket)
    finally:
        server_socket.close()
