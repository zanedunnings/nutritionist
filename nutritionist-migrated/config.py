import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project name - used in various places
PROJECT_NAME = os.getenv("PROJECT_NAME", "nutritionist")

# Database configurations
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///./data/{PROJECT_NAME}.db")

# Secret key for JWT token
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Server configurations
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Email configurations (for future use)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "no-reply@example.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_SERVER = os.getenv("EMAIL_SERVER", "smtp.example.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))

# Nutritionist-specific configurations
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MEAL_PLAN_DB = os.getenv("MEAL_PLAN_DB", "meal_plans.db")
OTP_EXPIRATION_MINUTES = int(os.getenv("OTP_EXPIRATION_MINUTES", "5")) 