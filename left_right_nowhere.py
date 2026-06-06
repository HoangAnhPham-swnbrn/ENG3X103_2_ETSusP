from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

factory = PiGPIOFactory()

# GPIO 13 = pin 33
servo = Servo(13, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=factory)

try:
    print("Center")
    servo.mid()
    sleep(2)

    print("Left")
    servo.min()
    sleep(2)

    print("Center")
    servo.mid()
    sleep(2)

    print("Right")
    servo.max()
    sleep(2)

    print("Center")
    servo.mid()
    sleep(2)

except KeyboardInterrupt:
    print("Stopped by user")
finally:
    servo.detach()
