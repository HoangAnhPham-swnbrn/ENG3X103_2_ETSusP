from picamera2 import Picamera2
import cv2
import time

picam2 = Picamera2()

config = picam2.create_video_configuration(
    main={"format": "XRGB8888", "size": (640, 480)},   # lower res = more FPS headroom
    controls={
        "FrameRate": 90,              # push FPS higher with lower res
        "Sharpness": 1.5,             # moderate, not max
        "Contrast": 1.1,              # subtle, avoids blown highlights
        "Brightness": 0.0,
        "AwbMode": 0,
        "AeEnable": True,
        "NoiseReductionMode": 1,      # 1 = Fast mode (low CPU cost vs. 2 = High Quality)
    },
    buffer_count=6                    # more buffers to sustain high FPS without drops
)

picam2.configure(config)

# Reduce sharpening and encoding load on the CPU side
picam2.set_controls({"Sharpness": 1.5})

picam2.start()
time.sleep(2)

prev_time = time.time()
frame_count = 0
fps_display = 0

while True:
    frame = picam2.capture_array()
    frame_bgr = frame[:, :, :3]

    # Only recalculate FPS every 15 frames to reduce overhead
    frame_count += 1
    if frame_count % 15 == 0:
        curr_time = time.time()
        fps_display = 15 / (curr_time - prev_time)
        prev_time = curr_time

    # Lightweight overlay
    cv2.putText(frame_bgr, f"FPS: {fps_display:.0f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Camera", frame_bgr)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

picam2.stop()
cv2.destroyAllWindows()