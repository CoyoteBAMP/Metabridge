import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Metabridge")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion-con-una-clave-segura")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_DATABASE = os.getenv("DB_DATABASE", "metabridge")
DB_USERNAME = os.getenv("DB_USERNAME", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "metabridge_webhook_secret")
