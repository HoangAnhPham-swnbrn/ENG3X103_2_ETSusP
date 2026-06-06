# Servo Motor Test - Left, Center, Right
# SG5010 servo on GPIO 13 (pin 33)
# Raspberry Pi 5
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

SERVO = 33
CENTER = 90
LEFT   = CENTER - 45  # 45°
RIGHT  = CENTER + 45  # 135°

GPIO.setup(SERVO, GPIO.OUT)

pwm = GPIO.PWM(SERVO, 50)
pwm.start(0)

def set_angle(angle):
    duty = 5.0 + (angle / 180.0) * 5.0
    pwm.ChangeDutyCycle(duty)
    sleep(0.8)

def center():
    set_angle(CENTER)

try:
    print("Center")
    center()
    sleep(2)

    print("Left 45°")
    set_angle(LEFT)
    sleep(2)

    print("Center")
    center()
    sleep(2)

    print("Right 45°")
    set_angle(RIGHT)
    sleep(2)

    print("Center")
    center()
    sleep(2)

except KeyboardInterrupt:
    print("Stopped by user — returning to center")
    center()  # always return to center on Ctrl+C
finally:
    pwm.stop()
    GPIO.cleanup()
