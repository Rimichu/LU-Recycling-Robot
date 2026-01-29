import lgpio
import time
import pi_constants as const

# Depending on the servo motor, the duration to open/close the claw may need to be adjusted.
# Depending on how the servo motor is connected, the HIGH/LOW signals may need to be swapped.

def open_claw(h, anticlockwise_pin, clockwise_pin):
    """
    Open the claw by rotating the servo motor anticlockwise.

    :param h: The lgpio handle.
    :param anticlockwise_pin: The GPIO pin number for anticlockwise rotation.
    :param clockwise_pin: The GPIO pin number for clockwise rotation.

    :return: None
    """

    lgpio.gpio_write(h, clockwise_pin, const.HIGH)
    lgpio.gpio_write(h, anticlockwise_pin, const.LOW)

    time.sleep(4)  # Duration to open claw

    lgpio.gpio_write(h, clockwise_pin, const.LOW)

def close_claw(h, clockwise_pin, anticlockwise_pin):
    """
    Close the claw by rotating the servo motor clockwise.

    :param h: The lgpio handle.
    :param clockwise_pin: The GPIO pin number for clockwise rotation.
    :param anticlockwise_pin: The GPIO pin number for anticlockwise rotation.

    :return: None
    """

    lgpio.gpio_write(h, anticlockwise_pin, const.HIGH)
    lgpio.gpio_write(h, clockwise_pin, const.LOW)

    time.sleep(4)  # Duration to close claw

    lgpio.gpio_write(h, anticlockwise_pin, const.LOW)
