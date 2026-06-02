from flask import Flask, render_template, Response
import cv2
import base64
import numpy as np

app = Flask(__name__)

latest_frame = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame

    from flask import request

    data = request.json["image"]
    img_data = base64.b64decode(data.split(",")[1])

    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    latest_frame = frame

    return "OK"


def generate():
    global latest_frame

    while True:
        if latest_frame is None:
            continue

        ret, buffer = cv2.imencode(".jpg", latest_frame)
        if not ret:
            continue

        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
