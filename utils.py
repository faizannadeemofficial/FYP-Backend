import jwt
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")  # Keep it safe (e.g., in .env file)
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Generate Auth token
def authentication_token(user_id: str, user_email: str, user_name: str):
    "Generate access token(JWT)"
    now = datetime.datetime.utcnow()

    # Create Access Token
    access_payload = {
        "user_id": user_id,
        "email": user_email,
        "user_name": user_name,
        "type": "access",
        "exp": now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm="HS256")

    return access_token

# Generate refresh token
def refresh_token(user_id: str, user_email: str, user_name: str):
    "Generate refresh token(JWT)"
    now = datetime.datetime.utcnow()

    # Create Refresh Token
    refresh_payload = {
        "user_id": user_id,
        "email": user_email,
        "user_name": user_name,
        "type": "access",
        "exp": now + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm="HS256")

    return refresh_token

# verify_tokens
def verify_token(token):
    "Validates JWT token"
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return "Token expired"
    except jwt.InvalidTokenError:
        return "Invalid token"
