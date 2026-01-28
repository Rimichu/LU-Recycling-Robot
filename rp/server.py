import socket
import lgpio
import servo
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
        command = data.decode("utf-8")
        match command:
            case "exit":
                print("Exit command received. Closing connection.")
                client_socket.close()
            case const.COMMAND_OPEN:
                print("Open command received.")
                servo.open_claw(h, const.ANTICLOCKWISE_PIN, const.CLOCKWISE_PIN)  # Open claw
            case const.COMMAND_CLOSE:
                print("Close command received.")
                servo.close_claw(h, const.CLOCKWISE_PIN, const.ANTICLOCKWISE_PIN)      # Close claw
            case _ if command.startswith("ping"):
                print("Ping received, sending pong...")
                client_socket.sendall(b"pong")
            case _:
                print("Unknown command received.")

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
    # Get handle to gpio pins
    h = lgpio.gpiochip_open(0)

    # Claim GPIOs as outputs and set initial state to LOW
    lgpio.gpio_claim_output(h, const.CLOCKWISE_PIN, const.LOW)
    lgpio.gpio_claim_output(h, const.ANTICLOCKWISE_PIN, const.LOW)

    HOST = "0.0.0.0" # Listen on all interfaces
    PORT = 5050      # Arbitrary non-privileged port

    server_socket = socket.create_server((HOST, PORT))
    print(f"Server created at {HOST}:{PORT}")

    try:
        while_loop(server_socket)
    finally:
        lgpio.gpiochip_close(h)
        server_socket.close()
