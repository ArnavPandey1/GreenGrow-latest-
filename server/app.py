# app.py (paste whole file, replaces your previous one)
import os
import traceback
import warnings
import numpy as np
import pickle
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import pandas as pd
import difflib
import re
from werkzeug.utils import secure_filename

# ===============================
# CONFIGURATION & INITIALIZATION
# ===============================

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

load_dotenv()

app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ===============================
# DATABASE CONNECTION
# ===============================

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "greengrow")

try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    client.admin.command("ping")
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    db = None

users_collection = db.users if db is not None else None

# ===============================
# MODEL LOADING
# ===============================

def load_pickle_file(filename):
    abs_path = os.path.abspath(filename)
    if not os.path.exists(abs_path):
        print(f"❌ File not found: {abs_path}")
        return None
    try:
        with open(abs_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"❌ Error loading {abs_path}: {e}")
        return None

model = load_pickle_file("model.pkl")
mx = load_pickle_file("minmaxscaler.pkl")
sc = load_pickle_file("standscaler.pkl")

crop_dict = {
    'rice': 1, 'maize': 2, 'chickpea': 3, 'kidneybeans': 4, 'pigeonpeas': 5,
    'mothbeans': 6, 'mungbean': 7, 'blackgram': 8, 'lentil': 9, 'pomegranate': 10,
    'banana': 11, 'mango': 12, 'grapes': 13, 'watermelon': 14, 'muskmelon': 15,
    'apple': 16, 'orange': 17, 'papaya': 18, 'coconut': 19, 'cotton': 20,
    'jute': 21, 'coffee': 22
}
inv_crop_dict = {v: k for k, v in crop_dict.items()}

tips = {
    "rice": "🌾 Needs heavy rainfall & humid conditions.",
    # (you can keep your full `tips` map here; omitted for brevity)
}

# ===============================
# SOIL RESTORATION MODEL (CSV-BASED)
# ===============================

SOIL_CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'india_crop_rotation_200_plus.csv'))
soil_df = None
if os.path.exists(SOIL_CSV_PATH):
    try:
        soil_df = pd.read_csv(SOIL_CSV_PATH)
        # Normalize whitespace, lowercase columns for consistent querying
        soil_df.columns = [c.strip().lower().replace(' ', '_').replace(')', '') for c in soil_df.columns]
    except Exception as e:
        print(f"❌ Error loading soil restoration CSV: {e}")
else:
    print(f"❌ Soil CSV not found at {SOIL_CSV_PATH}")


def normalize_crop_string(s):
    # Remove non-alphanumeric except spaces, lowercase, and collapse whitespace
    return re.sub(r'[^a-zA-Z0-9 ]', '', s or '').strip().lower()

def get_crop_soil_recommendations(last_crop):
    if soil_df is None:
        return []
    norm_input = normalize_crop_string(last_crop)
    crop_names = soil_df['harvested'].astype(str).tolist()
    norm_crop_names = [normalize_crop_string(c) for c in crop_names]

    # Exact or substring match
    matches_idx = [i for i, name in enumerate(norm_crop_names) if norm_input in name or name in norm_input]

    # If nothing, fuzzy match for top 3 closest
    if not matches_idx:
        close_matches = difflib.get_close_matches(norm_input, norm_crop_names, n=3, cutoff=0.6)
        matches_idx = [i for i, name in enumerate(norm_crop_names) if name in close_matches]

    # Return matches as records
    return soil_df.iloc[matches_idx].to_dict(orient='records') if matches_idx else []


@app.route("/api/soil-restoration", methods=["POST"])
def soil_restoration_endpoint():
    try:
        data = request.get_json() or {}
        last_crop = data.get("last_crop", "").strip()
        if not last_crop:
            return jsonify({"error": "Missing last_crop in request."}), 400
        results = get_crop_soil_recommendations(last_crop)
        if not results:
            return jsonify({"recommendations": [], "message": "No suitable rotation found for the given crop."})
        return jsonify({"recommendations": results})
    except Exception as e:
        print("❌ Exception in /api/soil-restoration:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===============================
# ROUTES: Auth, Predict (unchanged)
# ===============================

@app.before_request
def log_request_info():
    print(f"Request: {request.method} {request.path}")

@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Username, email, and password are required"}), 400
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters long"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        if '@' not in email:
            return jsonify({"error": "Invalid email format"}), 400
        if users_collection.find_one({"username": username}):
            return jsonify({"error": "Username already exists"}), 400
        if users_collection.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 400
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        result = users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        access_token = create_access_token(identity=user_id)
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "created_at": user_data["created_at"].isoformat(),
                "is_active": True
            }
        }), 201
    except Exception as e:
        print(f"❌ Registration error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Registration failed"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        data = request.get_json()
        if not data or not (data.get('username') or data.get('email')) or not data.get('password'):
            return jsonify({"error": "Username/email and password are required"}), 400

        # accept either username or email from frontend:
        identifier = data.get('username') if data.get('username') else data.get('email')
        identifier = identifier.strip().lower()
        password = data['password']

        user = users_collection.find_one({
            "$or": [
                {"username": identifier},
                {"email": identifier}
            ]
        })

        if not user or not bcrypt.check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid credentials"}), 401
        if not user.get('is_active', True):
            return jsonify({"error": "Account is deactivated"}), 401

        user_id = str(user['_id'])
        access_token = create_access_token(identity=user_id)

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "id": user_id,
                "username": user['username'],
                "email": user['email'],
                "created_at": user['created_at'].isoformat(),
                "is_active": user.get('is_active', True)
            }
        }), 200
    except Exception as e:
        print(f"❌ Login error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Login failed"}), 500

@app.route("/api/auth/profile", methods=["GET"])
@jwt_required()
def get_profile():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        user_id = get_jwt_identity()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "user": {
                "id": str(user['_id']),
                "username": user['username'],
                "email": user['email'],
                "created_at": user['created_at'].isoformat(),
                "is_active": user.get('is_active', True)
            }
        }), 200
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return jsonify({"error": "Failed to get profile"}), 500

@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/api/predict", methods=["POST"])
@jwt_required()
def api_predict():
    try:
        if not model or not mx or not sc:
            return jsonify({"error": "❌ Model or scaler files not loaded. Check server logs for missing files."}), 500
        data = request.get_json()
        print("Received data:", data)
        N = float(data.get("N", 0))
        P = float(data.get("P", 0))
        K = float(data.get("K", 0))
        temperature = float(data.get("temperature", 0))
        humidity = float(data.get("humidity", 0))
        ph = float(data.get("ph", 0))
        rainfall = float(data.get("rainfall", 0))

        errors = []
        if N < 0 or P < 0 or K < 0:
            errors.append("❌ N, P, K cannot be negative.")
        if N < 5 and P < 5 and K < 5:
            errors.append("❌ Soil nutrients (N, P, K) too low for any crop.")
        if rainfall < 20 or rainfall > 400:
            errors.append("❌ Rainfall not suitable (20–400 mm).")
        if not (10 <= temperature <= 45):
            errors.append("❌ Temperature not suitable (10–45°C).")
        if not (14 <= humidity <= 95):
            errors.append("❌ Humidity not suitable (14–95%).")
        if not (4.5 <= ph <= 9.0):
            errors.append("❌ Soil pH not suitable (4.5–9.0).")
        if errors:
            return jsonify({"error": errors}), 400

        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        features = mx.transform(features)
        features = sc.transform(features)

        pred = model.predict(features)[0]
        crop_name = inv_crop_dict.get(pred, "Unknown")
        tip = tips.get(crop_name, "No tip available.")
        user_id = get_jwt_identity()
        user = users_collection.find_one({"_id": ObjectId(user_id)}) if users_collection is not None else None
        print(f"Prediction made by user: {user['username'] if user else 'Unknown'}")
        return jsonify({"crop": crop_name, "tip": tip})
    except Exception as e:
        print("❌ Exception in /api/predict:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "GreenGrow API is running"}), 200

# ===============================
# PROFILE UPLOAD & GET
# ===============================

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads", "avatars"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/api/profile/avatar", methods=["POST"])
@jwt_required()
def update_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No avatar uploaded'}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    ext = filename.split('.')[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "bmp"]:
        return jsonify({'error': 'Unsupported image type'}), 400
    user_id = get_jwt_identity()

    # Remove old file if extension changes or file exists
    if users_collection is not None:
        current = users_collection.find_one({'_id': ObjectId(user_id)})
        if current and current.get('avatar_url'):
            existing_filename = current['avatar_url'].split('/')[-1]
            existing_path = os.path.join(UPLOAD_FOLDER, existing_filename)
            if os.path.exists(existing_path) and existing_filename.split('.')[-1].lower() != ext:
                try:
                    os.remove(existing_path)
                except Exception:
                    pass

    # Save as userID.extension (overwrite if exists)
    unique_filename = f"{user_id}.{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)
    rel_url = f"/uploads/avatars/{unique_filename}"

    # Update MongoDB user
    if users_collection is not None:
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'avatar_url': rel_url}})

    # Append version for cache busting in response only
    versioned = f"{rel_url}?v={int(datetime.utcnow().timestamp())}"
    return jsonify({'avatar_url': rel_url, 'avatar_public_url': versioned}), 200

@app.route("/api/profile/avatar", methods=["DELETE"])
@jwt_required()
def remove_avatar():
    try:
        user_id = get_jwt_identity()
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("avatar_url"):
            return jsonify({"message": "No avatar to remove"}), 200
        # Remove file from disk
        rel_url = user["avatar_url"]
        filename = rel_url.split("/")[-1]
        avatar_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
        # Remove avatar_url from DB
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$unset": {"avatar_url": ""}})
        return jsonify({"message": "Avatar removed"}), 200
    except Exception as e:
        print(f"❌ Avatar removal error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to remove avatar"}), 500

@app.route("/api/profile", methods=["GET", "PUT"])
@jwt_required()
def user_profile():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500

        user_id = get_jwt_identity()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404

        if request.method == "GET":
            # Include avatar_url and extended profile fields if any
            prof = {
                "id": str(user["_id"]),
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "created_at": user.get("created_at").isoformat()
                if user.get("created_at")
                else "",
                "is_active": user.get("is_active", True),
                "avatar_url": user.get("avatar_url", None),
                "phone": user.get("phone", ""),
                "location": user.get("location", ""),
                "about": user.get("about", ""),
            }
            return jsonify({"user": prof}), 200

        # PUT: update profile fields
        data = request.get_json() or {}

        new_username = (data.get("username") or "").strip()
        new_email = (data.get("email") or "").strip().lower()

        update_doc = {}

        # Username / email validation & uniqueness
        if new_username:
            if len(new_username) < 3:
                return jsonify({"error": "Username must be at least 3 characters long"}), 400
            if new_username != user.get("username") and users_collection.find_one(
                {"username": new_username}
            ):
                return jsonify({"error": "Username already exists"}), 400
            update_doc["username"] = new_username

        if new_email:
            if "@" not in new_email:
                return jsonify({"error": "Invalid email format"}), 400
            if new_email != user.get("email") and users_collection.find_one(
                {"email": new_email}
            ):
                return jsonify({"error": "Email already registered"}), 400
            update_doc["email"] = new_email

        # Optional extended fields
        if "phone" in data:
            phone = (data.get("phone") or "").strip()
            update_doc["phone"] = phone

        if "location" in data:
            location = (data.get("location") or "").strip()
            update_doc["location"] = location

        if "about" in data:
            about = (data.get("about") or "").strip()
            update_doc["about"] = about

        if not update_doc:
            return jsonify({"message": "No changes to update"}), 200

        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_doc})

        # Return updated profile snapshot
        updated = users_collection.find_one({"_id": ObjectId(user_id)})
        prof = {
            "id": str(updated["_id"]),
            "username": updated.get("username", ""),
            "email": updated.get("email", ""),
            "created_at": updated.get("created_at").isoformat()
            if updated.get("created_at")
            else "",
            "is_active": updated.get("is_active", True),
            "avatar_url": updated.get("avatar_url", None),
            "phone": updated.get("phone", ""),
            "location": updated.get("location", ""),
            "about": updated.get("about", ""),
        }
        return jsonify({"message": "Profile updated", "user": prof}), 200
    except Exception as e:
        print(f"❌ Profile error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to get/update profile"}), 500

# Avatar static files (CORS enabled)
from flask import send_from_directory, make_response
@app.route("/uploads/avatars/<filename>")
def uploaded_avatar(filename):
    resp = make_response(send_from_directory(UPLOAD_FOLDER, filename))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

# ===============================
# MAIN ENTRY
# ===============================

if __name__ == "__main__":
    print("🚀 Flask running at http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
