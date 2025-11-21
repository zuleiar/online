"""Flask web app for applying simple image filters.

This app is production-ready for deployment behind a WSGI server
like gunicorn. It returns JSON-formatted errors (no Flask debug pages)
and restricts CORS to the Render URL.
"""

import os
import logging
from io import BytesIO

from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np


app = Flask(__name__)
# Ensure Flask is in production mode by default (when run via gunicorn)
app.config.update(ENV='production', DEBUG=False)

# Allow requests only from the Render instance
RENDER_URL = os.environ.get('RENDER_URL', 'https://online-xe99.onrender.com')
CORS(app, resources={r"/*": {"origins": RENDER_URL}})


@app.errorhandler(Exception)
def handle_exception(e):
    # Log the exception server-side and return JSON to the client
    app.logger.exception(e)
    return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    return jsonify({"ok": True, "msg": "Hola"})


@app.route('/apply_filter', methods=['POST', 'OPTIONS'])
def apply_filter():
    if request.method == 'OPTIONS':
        return '', 204

    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    filter_type = request.form.get('filter_type', 'blur')

    # Read image bytes into OpenCV
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({'error': 'Invalid image data'}), 400

    # Apply requested filter
    if filter_type == 'blur':
        filtered_img = cv2.GaussianBlur(img, (15, 15), 0)
    elif filter_type == 'gray':
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        filtered_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif filter_type == 'canny':
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        filtered_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    else:
        filtered_img = img

    # Encode to JPEG and return
    success, buffer = cv2.imencode('.jpg', filtered_img)
    if not success:
        return jsonify({'error': 'Failed to encode image'}), 500

    io_buf = BytesIO(buffer.tobytes())
    io_buf.seek(0)
    return send_file(io_buf, mimetype='image/jpeg')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'}), 200


if __name__ == '__main__':
    # Only used for local development/testing. When deployed to Render
    # gunicorn will serve the `app` WSGI application and this block won't run.
    port = int(os.environ.get('PORT', 5000))
    debug = str(os.environ.get('FLASK_DEBUG', 'False')).lower() in ('1', 'true', 'yes')
    # Keep Flask's built-in server off by default for safety
    app.run(host='0.0.0.0', port=port, debug=debug)
