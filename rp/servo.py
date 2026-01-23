import RPi.GPIO as GPIO # TODO: See if RPi.GPIO can be replaced with pigpio
import time

def set_angle(pwm, pin, angle):
    """
    Set the angle of a servo motor conncected to the specified pin.
    The servo motor is then turned on for a short duration to reach the desired angle.
    
    :param pwm: The PWM instance controlling the servo.
    :param pin: The GPIO pin number where the servo is connected.
    :param angle: The desired angle to set the servo to (0-180 degrees).

    :return: None
    """

    duty_cycle = 2 + (angle / 18)  # 2 to 12 is a common range for 0-180 degrees (but also dependant on servo)
    
    GPIO.output(pin, True)
    pwm.ChangeDutyCycle(duty_cycle)
    
    time.sleep(0.5)
    
    GPIO.output(pin, False)
    pwm.ChangeDutyCycle(0)
