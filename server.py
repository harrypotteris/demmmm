from flask import Flask, render_template, Response, request
import cv2
import base64
import numpy as np
import threading

app = Flask(__name__)

# Shared frame storage
latest_frame = None
lock = threading.Lock()


# -------------------------
# HOME PAGE
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------
# RECEIVE FRAME (from camera)
# -------------------------
@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame

    data = request.json["image"]

    # Decode base64 image
    img_data = base64.b64decode(data.split(",")[1])

    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Safely update frame
    with lock:
        latest_frame = frame

    return "OK"


# -------------------------
# STREAM GENERATOR
# -------------------------
def generate():
    global latest_frame

    while True:
        with lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        # Encode frame as JPEG
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


# -------------------------
# VIDEO STREAM ROUTE
# -------------------------
@app.route("/video_feed")
def video_feed():
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# -------------------------
# RUN SERVER (Render compatible)
# -------------------------
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        threaded=True
    )
