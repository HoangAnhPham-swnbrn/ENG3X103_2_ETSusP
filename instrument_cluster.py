from flask import Flask, render_template, jsonify
import threading
import time
import random  # placeholder — replace with real sensor code later

app = Flask(__name__)

# ─────────────────────────────────────────────
# Shared sensor state — updated by sensor thread
# Replace the simulated values with real sensor
# ─────────────────────────────────────────────
sensor_data = {
    "distance_cm": 400,
    "zone": "FAR",
    "steering_angle": 0,
    "speed_kmh": 0,
    "braking": True,
    "gear": "D",
    "left_indicator": False,
    "right_indicator": False,
    "hazard": False,
    "path_status": "No obstacles",
    "path_status_color": "#2ecc40",
    "line_sensor": "On track",
}

def zone_from_distance(d):
    if d <= 20:   return "CRITICAL"
    elif d <= 50:  return "NEAR"
    elif d <= 150: return "MID"
    else:          return "FAR"

def path_status_from_distance(d):
    if d <= 20:   return ("Obstacle critical", "#e74c3c")
    elif d <= 50:  return ("Obstacle nearby",   "#f0a500")
    elif d <= 150: return ("Monitoring",         "#4a9eff")
    else:          return ("No obstacles",       "#2ecc40")

# ─────────────────────────────────────────────
# SENSOR THREAD
# Simulated for now — swap in real sensor reads
# ─────────────────────────────────────────────
def sensor_loop():
    while True:
        # ── Replace these lines with real sensor code ──
        # Example real ultrasonic read:
        # from ultrasonic import get_distance
        # d = get_distance()
        d = random.randint(80, 400)   # simulated
        # ───────────────────────────────────────────────

        status, color = path_status_from_distance(d)
        sensor_data["distance_cm"]      = d
        sensor_data["zone"]             = zone_from_distance(d)
        sensor_data["path_status"]      = status
        sensor_data["path_status_color"]= color

        time.sleep(0.5)

# Start sensor thread as daemon so it stops with the app
t = threading.Thread(target=sensor_loop, daemon=True)
t.start()

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("instrument_cluster.html")

@app.route("/data")
def data():
    """
    Returns live sensor data as JSON.
    The dashboard polls this every 500ms.
    """
    return jsonify(sensor_data)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("  Dashboard running!")
    print("  Open in browser:")
    print("  http://localhost:5000        (this machine)")
    print("  http://<Pi-IP>:5000          (from laptop)")
    print("=" * 40)
    app.run(host="0.0.0.0", port=5000, debug=False)