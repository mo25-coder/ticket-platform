from flask import request, jsonify
import jwt
from functools import wraps

SECRET_KEY = "super-secret-key"  # في الإنتاج: app.config['SECRET_KEY'] أو env var

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split()
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]
        
        if not token:
            return jsonify({"message": "Token مفقود"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token منتهي"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token غير صالح"}), 401

        return f(*args, **kwargs)
    return wrapper
