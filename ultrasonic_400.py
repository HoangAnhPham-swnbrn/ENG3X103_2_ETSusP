from gpiozero import DistanceSensor
from time import sleep
import collections

# Adjustable sensitivity settings
TRIGGER_PIN = 5
ECHO_PIN = 6
MAX_RANGE_CM = 400          # HC-SR04 max reliable range
SAMPLE_SIZE = 5             # readings to average (higher = smoother, slower)
SAMPLE_WAIT = 0.06          # seconds between readings (min 0.06 for HC-SR04)

# Distance threshold zones (cm) — adjust these to tune sensitivity
ZONE_CRITICAL  = 20         # too close, immediate action
ZONE_NEAR      = 50         # object nearby, alert YOLO
ZONE_MID       = 150        # object in mid range, passive watch
ZONE_FAR       = 300        # object far, low priority

sensor = DistanceSensor(
    echo=ECHO_PIN,
    trigger=TRIGGER_PIN,
    max_distance=MAX_RANGE_CM / 100,  # gpiozero uses metres
    queue_len=SAMPLE_SIZE,            # built-in rolling average
    partial=True                      # don't block if sensor glitches
)

def get_zone(distance_cm):
    """Classify distance into sensitivity zones."""
    if distance_cm is None:
        return "UNKNOWN"
    elif distance_cm <= ZONE_CRITICAL:
        return "CRITICAL"
    elif distance_cm <= ZONE_NEAR:
        return "NEAR"
    elif distance_cm <= ZONE_MID:
        return "MID"
    elif distance_cm <= ZONE_FAR:
        return "FAR"
    else:
        return "OUT_OF_RANGE"

def get_distance():
    """Returns smoothed distance in cm, or None if sensor glitches."""
    try:
        d = sensor.distance
        if d is None:
            return None
        return d * 100
    except Exception:
        return None

# --- Standalone test loop (remove when integrating with YOLO) ---
if __name__ == "__main__":
    print("Ultrasonic sensor running. Ctrl+C to stop.")
    print(f"Zones: CRITICAL<{ZONE_CRITICAL}cm | NEAR<{ZONE_NEAR}cm | "
          f"MID<{ZONE_MID}cm | FAR<{ZONE_FAR}cm")

    while True:
        distance = get_distance()
        zone = get_zone(distance)

        if distance is None:
            print("Sensor error — check wiring")
        else:
            print(f"Distance: {distance:.1f} cm  |  Zone: {zone}")

        sleep(SAMPLE_WAIT)