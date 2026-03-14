from flask import Flask, request, jsonify, session
from models import db, User
from detector import detect_clothing
import cv2
import numpy as np
import base64

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/detect", methods=["POST", "OPTIONS"])
def detect():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    try:
        # Strip the data-URL prefix if present (e.g. "data:image/jpeg;base64,...")
        image_b64 = data["image"]
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_b64)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image_bgr is None:
            return jsonify({"error": "Could not decode image"}), 400

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        detections = detect_clothing(image_rgb)
        return jsonify({"detections": detections})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#configurations 
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return "ReWear backend is running!"

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 409

    user = User(email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id

    return jsonify({"message": "User registered"}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = user.id

    return jsonify({"message": "Logged in"})


@app.route("/auth/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"})


@app.route("/auth/me", methods=["GET"])
def me():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    user = User.query.get(user_id)

    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "Not authenticated"}), 401

    return jsonify({
        "id": user.id,
        "email": user.email
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)

