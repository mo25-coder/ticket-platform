from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import add_user, get_user_by_username
import jwt
import datetime
from functools import wraps

SECRET_KEY = "super-secret-key"  # في الإنتاج حطها في config أو .env

auth = Blueprint("auth", __name__)
# create_user_table()

@auth.route("/", methods=["GET"])
def home():
    return jsonify({"message": "مرحبا بك في واجهة المصادقة"}), 200

@auth.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "الرجاء إدخال اسم المستخدم وكلمة المرور"}), 400

    password_hash = generate_password_hash(password)
    success = add_user(username, password_hash)
    if success:
        return jsonify({"message": "تم التسجيل بنجاح"})
    else:
        return jsonify({"message": "اسم المستخدم موجود بالفعل"}), 409

@auth.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    user = get_user_by_username(username)
    if user and check_password_hash(user[2], password):
        token = jwt.encode({
            "user_id": user[0],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token})
    else:
        return jsonify({"message": "اسم المستخدم أو كلمة المرور غير صحيحة"}), 401

@auth.route("/login-session", methods=["POST"])
def login_session():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    user = get_user_by_username(username)
    if user and check_password_hash(user[2], password):
        session["user_id"] = user[0]
        return jsonify({"message": "تم تسجيل الدخول (جلسة)"})
    else:
        return jsonify({"message": "اسم المستخدم أو كلمة المرور غير صحيحة"}), 401

@auth.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "تم تسجيل الخروج"})

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"message": "غير مصرح"}), 401
        return f(*args, **kwargs)
    return wrapper

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return jsonify({"message": "توكن غير موجود"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data["user_id"]
        except:
            return jsonify({"message": "توكن غير صالح أو منتهي"}), 401
        return f(*args, **kwargs)
    return decorated
