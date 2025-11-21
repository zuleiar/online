from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from io import BytesIO
import os

app = Flask(__name__)
# Permitir CORS para Flutter Web y desde el dominio de Render
# Se mantiene wildcard para desarrollo local pero añadimos explícitamente
# el dominio de Render para mayor claridad.
CORS(app, resources={r"/*": {"origins": ["https://online-xe99.onrender.com", "*"]}})


@app.route('/', methods=['GET'])
def index():
    return jsonify({"ok": True, "msg": "Holsa"})

@app.route('/apply_filter', methods=['POST', 'OPTIONS'])
def apply_filter():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        file = request.files['image']
        filter_type = request.form.get('filter_type', 'blur')
        
        # Leer imagens
        npimg = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        # Aplicar filtro según tipo
        if filter_type == 'blur':
            filtered_img = cv2.GaussianBlur(img, (15, 15), 0)
        elif filter_type == 'gray':
            filtered_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            filtered_img = cv2.cvtColor(filtered_img, cv2.COLOR_GRAY2BGR)
        elif filter_type == 'canny':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            filtered_img = cv2.Canny(gray, 100, 200)
            filtered_img = cv2.cvtColor(filtered_img, cv2.COLOR_GRAY2BGR)
        else:
            filtered_img = img
        
        # Convertir a bytes
        _, buffer = cv2.imencode('.jpg', filtered_img)
        io_buf = BytesIO(buffer)
        io_buf.seek(0)
        
        return send_file(io_buf, mimetype='image/jpeg')
    
    except Exception as e:
        return {'error': str(e)}, 400

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'OK'}, 200

if __name__ == '__main__':
    # Usar el puerto provisto por el entorno (Render usa $PORT)
    port = int(os.environ.get('PORT', 5000))
    # Activar debug sólo si FLASK_DEBUG está establecido
    debug_env = os.environ.get('FLASK_DEBUG', 'False')
    debug = str(debug_env).lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=port, debug=debug)
