# TB6612FNG Dual Motor Speed Test
# Raspberry Pi BOARD pin mode
from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Pins - Motor A
PWMA = 12
AIN2 = 18
AIN1 = 16
# Pins - Motor B
PWMB = 11
BIN1 = 15
BIN2 = 13
# Shared
STBY = 22

# Setup pins - Motor A
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
# Setup pins - Motor B
GPIO.setup(PWMB, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)
# Shared
GPIO.setup(STBY, GPIO.OUT)

# PWM setup
pwmFreq = 100
pwma = GPIO.PWM(PWMA, pwmFreq)
pwmb = GPIO.PWM(PWMB, pwmFreq)

# Start PWM at 0%
pwma.start(0)
pwmb.start(0)

def set_motors(a_dir, b_dir, duty):
    """Set both motors. dir: 'fwd', 'rev', or 'stop'"""
    # Motor A
    if a_dir == 'fwd':
        GPIO.output(AIN1, GPIO.HIGH); GPIO.output(AIN2, GPIO.LOW)
    elif a_dir == 'rev':
        GPIO.output(AIN1, GPIO.LOW);  GPIO.output(AIN2, GPIO.HIGH)
    else:
        GPIO.output(AIN1, GPIO.LOW);  GPIO.output(AIN2, GPIO.LOW)
    # Motor B
    if b_dir == 'fwd':
        GPIO.output(BIN1, GPIO.HIGH); GPIO.output(BIN2, GPIO.LOW)
    elif b_dir == 'rev':
        GPIO.output(BIN1, GPIO.LOW);  GPIO.output(BIN2, GPIO.HIGH)
    else:
        GPIO.output(BIN1, GPIO.LOW);  GPIO.output(BIN2, GPIO.LOW)

    pwma.ChangeDutyCycle(duty)
    pwmb.ChangeDutyCycle(duty)

try:
    GPIO.output(STBY, GPIO.HIGH)

    # FORWARD TEST
    print("Forward - 25% speed")
    set_motors('fwd', 'fwd', 25)
    sleep(3)

    print("Forward - 50% speed")
    set_motors('fwd', 'fwd', 50)
    sleep(3)

    # STOP
    print("Stop")
    set_motors('stop', 'stop', 0)
    sleep(2)

    # REVERSE TEST
    print("Reverse - 25% speed")
    set_motors('rev', 'rev', 25)
    sleep(3)

    print("Reverse - 50% speed")
    set_motors('rev', 'rev', 50)
    sleep(3)

except KeyboardInterrupt:
    print("Stopped by user")
finally:
    pwma.stop()
    pwmb.stop()
    set_motors('stop', 'stop', 0)
    GPIO.output(STBY, GPIO.LOW)
    GPIO.cleanup()
