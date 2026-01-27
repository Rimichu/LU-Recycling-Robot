import lgpio
import time

def open_claw(h, anticlockwise_pin, clockwise_pin):
    """
    Open the claw by rotating the servo motor anticlockwise.

    :param h: The lgpio handle.
    :param anticlockwise_pin: The GPIO pin number for anticlockwise rotation.
    :param clockwise_pin: The GPIO pin number for clockwise rotation.

    :return: None
    """

    lgpio.gpio_write(h, anticlockwise_pin, True)
    lgpio.gpio_write(h, clockwise_pin, False)

    time.sleep(1)  # Duration to open claw

    lgpio.gpio_write(h, anticlockwise_pin, False)

def close_claw(h, clockwise_pin, anticlockwise_pin):
    """
    Close the claw by rotating the servo motor clockwise.

    :param h: The lgpio handle.
    :param clockwise_pin: The GPIO pin number   for clockwise rotation.
    :param anticlockwise_pin: The GPIO pin number for anticlockwise rotation.

    :return: None
    """

    lgpio.gpio_write(h, clockwise_pin, True)
    lgpio.gpio_write(h, anticlockwise_pin, False)

    time.sleep(1)  # Duration to close claw

    lgpio.gpio_write(h, clockwise_pin, False)