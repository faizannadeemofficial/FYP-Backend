import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='f:/FYP/1.1.1/.env')

MAILTRAP_API_URL = "https://send.api.mailtrap.io/api/send"
MAILTRAP_TOKEN = os.getenv("smtp_pass")

def send_mailtrap_email(to_email, otp: str, subject="Your OTP Code", from_email="censorx@demomailtrap.co", from_name="CensorX", category="Integration Test"):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MAILTRAP_TOKEN}"
    }
    text = f"Here is your OTP: {otp}"
    payload = {
        "from": {
            "email": from_email,
            "name": from_name
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "text": text,
        "category": category
    }
    try:
        response = requests.post(MAILTRAP_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return {"success": True, "message": "Email sent!", "response": response.json()}
    except requests.exceptions.HTTPError as http_err:
        return {"success": False, "error": f"HTTP error: {http_err}", "details": response.text}
    except Exception as err:
        return {"success": False, "error": f"Other error: {err}"}