# Servo Motor Test - Left, Center, Right
# SG5010 servo on GPIO 13 (pin 33)
# Raspberry Pi 5
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

SERVO = 33

GPIO.setup(SERVO, GPIO.OUT)

pwm = GPIO.PWM(SERVO, 50)  # 50Hz
pwm.start(0)

def set_angle(angle):
    """0° = left, 90° = center, 180° = right"""
    # SG5010: 1ms (0°) to 2ms (180°) @ 50Hz
    duty = 5.0 + (angle / 180.0) * 5.0
    pwm.ChangeDutyCycle(duty)
    sleep(0.5)
    pwm.ChangeDutyCycle(0)  # cut signal to reduce jitter

try:
    print("Center")
    set_angle(90)
    sleep(2)

    print("Left")
    set_angle(0)
    sleep(2)

    print("Center")
    set_angle(90)
    sleep(2)

    print("Right")
    set_angle(180)
    sleep(2)

    print("Center")
    set_angle(90)
    sleep(2)

except KeyboardInterrupt:
    print("Stopped by user")
finally:
    pwm.ChangeDutyCycle(0)
    pwm.stop()
    GPIO.cleanup()
