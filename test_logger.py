"""
test_logger.py
──────────────
Drop-in logging module for the autonomous navigation dashboard.
Tracks detection events, reaction times, and manoeuvre triggers.
All data saved to results.csv automatically.

INTEGRATION — add these lines to autonomous_dashboard_final_v3.py:

    At the top:
        from test_logger import TestLogger
        logger = TestLogger()

    Inside _camera_loop(), after dominant side is computed:
        logger.on_detection(names, dominant, last_distance_cache)

    Inside update(), after get_status():
        logger.on_state_change(speed_level, object_side)

    Inside _dodge_sequence(), at the start:
        logger.on_manoeuvre("DODGE", side)

    Inside _reverse_sequence() and _centre_reverse(), at the start:
        logger.on_manoeuvre("REVERSE", "CENTRE")

    On close (on_close()):
        logger.save()
"""

import csv
import time
import os
from threading import Lock


CSV_PATH     = "results.csv"
CSV_HEADERS  = [
    "test_id",
    "timestamp",
    "detected_classes",
    "confidence_note",
    "side_classified",
    "distance_cm",
    "speed_level_at_detection",
    "prev_speed_level",
    "new_speed_level",
    "reaction_time_ms",
    "manoeuvre_triggered",
    "manoeuvre_type",
    "manoeuvre_side",
]


class TestLogger:
    def __init__(self):
        self._lock            = Lock()
        self._rows            = []
        self._test_id         = 0

        # Reaction time tracking
        self._detection_start = None   # time when object first detected
        self._last_speed      = None   # previous speed level
        self._pending_rxn     = False  # waiting for a speed change to record

        # Current snapshot updated each camera frame
        self._last_distance   = 0.0
        self._last_side       = None
        self._last_names      = []

        print(f"[Logger] Initialised. Will save to '{CSV_PATH}'.")

    # ── called from _camera_loop() ─────────────────────────────────────────
    def on_detection(self, detected_names, side, distance_cm):
        """Record the latest camera detection snapshot.
        Called every camera frame — does NOT write a row by itself."""
        with self._lock:
            self._last_names    = detected_names if detected_names else []
            self._last_side     = side
            self._last_distance = distance_cm

            # Start reaction timer the moment something is first seen
            if detected_names and self._detection_start is None:
                self._detection_start = time.time()
                self._pending_rxn     = True

            # Reset timer when nothing detected
            if not detected_names:
                self._detection_start = None
                self._pending_rxn     = False

    # ── called from update() after get_status() ────────────────────────────
    def on_state_change(self, new_speed_level, object_side):
        """Detect speed level transitions and compute reaction time."""
        with self._lock:
            prev = self._last_speed

            if prev is None:
                self._last_speed = new_speed_level
                return

            # Only log when speed level actually changes
            if new_speed_level == prev:
                return

            self._test_id += 1
            now = time.time()

            # Reaction time = ms from first detection to this state change
            if self._pending_rxn and self._detection_start is not None:
                rxn_ms = round((now - self._detection_start) * 1000, 1)
                self._pending_rxn     = False
                self._detection_start = None
            else:
                rxn_ms = ""

            row = {
                "test_id":                  self._test_id,
                "timestamp":                time.strftime("%H:%M:%S"),
                "detected_classes":         ", ".join(self._last_names) if self._last_names else "None",
                "confidence_note":          "",        # filled manually
                "side_classified":          self._last_side or "None",
                "distance_cm":              round(self._last_distance, 1),
                "speed_level_at_detection": prev,
                "prev_speed_level":         prev,
                "new_speed_level":          new_speed_level,
                "reaction_time_ms":         rxn_ms,
                "manoeuvre_triggered":      "No",
                "manoeuvre_type":           "",
                "manoeuvre_side":           "",
            }

            self._rows.append(row)
            self._last_speed = new_speed_level

            print(f"[Logger] #{self._test_id:03d}  {prev} → {new_speed_level}  "
                  f"side={self._last_side}  dist={self._last_distance}cm  "
                  f"rxn={rxn_ms}ms")

    # ── called from manoeuvre functions ────────────────────────────────────
    def on_manoeuvre(self, manoeuvre_type, side):
        """Tag the most recent row with manoeuvre info, or add a new row."""
        with self._lock:
            self._test_id += 1
            if self._rows:
                # Tag the last row if it hasn't been tagged yet
                last = self._rows[-1]
                if last["manoeuvre_triggered"] == "No":
                    last["manoeuvre_triggered"] = "Yes"
                    last["manoeuvre_type"]       = manoeuvre_type
                    last["manoeuvre_side"]       = side
                    print(f"[Logger] Manoeuvre tagged on #{last['test_id']:03d}: "
                          f"{manoeuvre_type} / {side}")
                    return

            # No existing row to tag — create a standalone row
            row = {
                "test_id":                  self._test_id,
                "timestamp":                time.strftime("%H:%M:%S"),
                "detected_classes":         ", ".join(self._last_names) if self._last_names else "None",
                "confidence_note":          "",
                "side_classified":          side,
                "distance_cm":              round(self._last_distance, 1),
                "speed_level_at_detection": self._last_speed or "",
                "prev_speed_level":         self._last_speed or "",
                "new_speed_level":          "MANOEUVRE",
                "reaction_time_ms":         "",
                "manoeuvre_triggered":      "Yes",
                "manoeuvre_type":           manoeuvre_type,
                "manoeuvre_side":           side,
            }
            self._rows.append(row)
            print(f"[Logger] #{self._test_id:03d}  Manoeuvre: {manoeuvre_type} / {side}")

    # ── call on close ───────────────────────────────────────────────────────
    def save(self):
        """Write all logged rows to CSV."""
        with self._lock:
            if not self._rows:
                print("[Logger] No data to save.")
                return

            with open(CSV_PATH, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(self._rows)

            print(f"[Logger] Saved {len(self._rows)} rows to '{CSV_PATH}'.")