# Servo Motor Test - Left, Center, Right
# SG5010 servo on GPIO 13 (pin 33)
# Raspberry Pi 5
import pigpio
from time import sleep

pi = pigpio.pi()

SERVO = 13  # pigpio uses BCM numbering

def set_angle(angle):
    # SG5010: 1000us (0°) to 2000us (180°)
    pulsewidth = 1000 + (angle / 180.0) * 1000
    pi.set_servo_pulsewidth(SERVO, pulsewidth)
    sleep(0.5)
    pi.set_servo_pulsewidth(SERVO, 0)  # cut signal

try:
    print("Center")
    set_angle(90)
    sleep(2)

    print("Left")
    set_angle(60)
    sleep(2)

    print("Center")
    set_angle(90)
    sleep(2)

    print("Right")
    set_angle(120)
    sleep(2)

    print("Center")
    set_angle(90)
    sleep(2)

except KeyboardInterrupt:
    print("Stopped by user")
finally:
    pi.set_servo_pulsewidth(SERVO, 0)
    pi.stop()
