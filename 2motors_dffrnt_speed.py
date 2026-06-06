# Servo Motor Test - Left, Center, Right
# SG5010 servo on GPIO 13 (pin 33)
# Raspberry Pi 5 - using lgpio directly
import lgpio
from time import sleep

SERVO  = 13  # BCM numbering
CENTER = 90
FREQ   = 50  # 50Hz

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, SERVO)

def set_relative(degrees):
    """Positive = right, Negative = left"""
    angle = CENTER + degrees
    # SG5010: 1ms to 2ms pulse width
    pulse_us = 1000 + (angle / 180.0) * 1000
    lgpio.tx_pwm(h, SERVO, FREQ, pulse_us / 10000 * 100)
    sleep(0.8)

def center():
    set_relative(0)

try:
    print("Center")
    center()
    sleep(2)

    print("Left 45°")
    set_relative(-45)
    sleep(2)

    print("Center")
    center()
    sleep(2)

    print("Right 45°")
    set_relative(45)
    sleep(2)

    print("Center")
    center()
    sleep(2)

except KeyboardInterrupt:
    print("Stopped by user — returning to center")
    center()
finally:
    lgpio.tx_pwm(h, SERVO, 0, 0)
    lgpio.gpiochip_close(h)
