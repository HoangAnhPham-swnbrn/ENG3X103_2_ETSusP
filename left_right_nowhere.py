# Servo Motor Test - Left, Center, Right
# Raspberry Pi BOARD pin mode
from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Pin
SERVO = 32  # GPIO 12, hardware PWM

GPIO.setup(SERVO, GPIO.OUT)

# Servo PWM at 50Hz
servo = GPIO.PWM(SERVO, 50)
servo.start(0)

def set_angle(angle):
    """Convert angle to duty cycle. 0° = left, 90° = center, 180° = right"""
    duty = 2.5 + (angle / 180.0) * 10.0
    servo.ChangeDutyCycle(duty)
    sleep(0.3)           # let servo settle
    servo.ChangeDutyCycle(0)  # stop sending pulses to reduce jitter

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
    servo.stop()
    GPIO.cleanup()