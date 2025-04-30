from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_mail import Mail

from routes import main  # Blueprint الخاص بالواجهات
from auth import auth    # Blueprint الخاص بالتوثيق

# إعداد التطبيق
app = Flask(__name__)
CORS(app, supports_credentials=True)

# إعدادات السيشن
app.secret_key = "your-secret"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# إعداد قاعدة البيانات
DB_PATH = "database.db"  # تأكد أن هذا المتغير يُستخدم في باقي الملفات

# إعدادات البريد الإلكتروني
app.config.update(
    MAIL_SERVER='smtp.example.com',
    MAIL_PORT=587,
    MAIL_USERNAME='your@email.com',
    MAIL_PASSWORD='yourpassword',
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False
)
mail = Mail(app)

# تسجيل الـ Blueprints
app.register_blueprint(main)
app.register_blueprint(auth)

# تشغيل التطبيق
if __name__ == "__main__":
    app.run(debug=True)
