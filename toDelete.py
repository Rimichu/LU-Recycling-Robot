import time
import lgpio

# BOARD -> BCM mapping for Raspberry Pi 40-pin header
CLOCKWISE_GPIO = 23  # BOARD 16
ANTICLOCKWISE_GPIO = 24      # BOARD 18
PWM_GPIO = 18            # BOARD 12 (PWM0)

PWM_FREQUENCY_HZ = 50
DUTY_CYCLE_PERCENT = 100  # 0..100

def set_pwm_duty(h, gpio, duty_percent, freq_hz=PWM_FREQUENCY_HZ):
    """Set PWM duty (0-100%) on a GPIO using lgpio."""
    duty_percent = max(0, min(100, duty_percent))
    duty = duty_percent / 100.0
    lgpio.tx_pwm(h, gpio, freq_hz, duty)

def main():
    # Open the GPIO chip (0 is the usual one on Raspberry Pi)
    h = lgpio.gpiochip_open(0)

    try:
        # Claim GPIOs as outputs
        lgpio.gpio_claim_output(h, ANTICLOCKWISE_GPIO, 0)
        lgpio.gpio_claim_output(h, CLOCKWISE_GPIO, 0)

        # Start PWM at 0% duty
        # set_pwm_duty(h, PWM_GPIO, 0)

        # Anticlockwise for 5s
        print("going Anti-clockwise")
        lgpio.gpio_write(h, ANTICLOCKWISE_GPIO, 1)
        lgpio.gpio_write(h, CLOCKWISE_GPIO, 0)
        # set_pwm_duty(h, PWM_GPIO, DUTY_CYCLE_PERCENT)
        time.sleep(5)

        # Stop
        lgpio.gpio_write(h, ANTICLOCKWISE_GPIO, 0)
        lgpio.gpio_write(h, CLOCKWISE_GPIO, 0)
        # set_pwm_duty(h, PWM_GPIO, 0)
        time.sleep(0.5)

        # Clockwise for 5s
        print("Going Clockwise")
        lgpio.gpio_write(h, ANTICLOCKWISE_GPIO, 0)
        lgpio.gpio_write(h, CLOCKWISE_GPIO, 1)
        # set_pwm_duty(h, PWM_GPIO, DUTY_CYCLE_PERCENT)
        time.sleep(5)

        # Stop
        lgpio.gpio_write(h, CLOCKWISE_GPIO, 0)
        # set_pwm_duty(h, PWM_GPIO, 0)

    finally:
        # Ensure PWM is stopped and chip is closed
        try:
            pass
            # set_pwm_duty(h, PWM_GPIO, 0)
        except Exception:
            pass
        lgpio.gpiochip_close(h)

if __name__ == "__main__":
    main()