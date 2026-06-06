# Servo Motor Test - Left, Center, Right
# SG5010 servo on GPIO 13 (pin 33, PWM channel 1)
# Raspberry Pi 5
from hardware_pwm import HardwarePWM
from time import sleep

# GPIO 13 = PWM channel 1, chip=2 for Pi 5
pwm = HardwarePWM(pwm_channel=1, hz=50, chip=2)
pwm.start(0)

def set_angle(angle):
    """0° = left, 90° = center, 180° = right"""
    # SG5010: 1ms (0°) to 2ms (180°) @ 50Hz
    duty = 5.0 + (angle / 180.0) * 5.0
    pwm.change_duty_cycle(duty)
    sleep(0.5)
    pwm.change_duty_cycle(0)  # cut signal to reduce jitter

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
    pwm.change_duty_cycle(0)
    pwm.stop()
