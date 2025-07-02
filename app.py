import os
import time
import bcrypt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

from text import TextProfanityFilter
from audio import AudioProfanityFilter
from image import ImageProfanityFilter
from video import VideoProfanityDetection
from database import DatabaseOPS
import utils

app = Flask(__name__)
CORS(app)
limiter = Limiter(
    get_remote_address, app=app, default_limits=["200 per day", "50 per hour"]
)  # Limiting the user request

# print(f"Flask expects static files in: {os.path.abspath(app.static_folder)}")

tpf = TextProfanityFilter()  # Instance of TextProfanityFilter
apf = AudioProfanityFilter(textpf=tpf)  # Instance of AudioProfanityFilter
ipd = ImageProfanityFilter()  # Instance of ImageProfanityFilter

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = "./storage/uploads"
STATIC_FOLDER = "./storage/files"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists("storage/imgs"):
    os.makedirs("storage/imgs")


def allowed_image_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def allowed_video_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    )


# Connection Status Endpoint
@app.route("/")
def Main():
    return "<h1>Content Moderation APIs are live...</h1>"


@app.route("/files/<path:filename>", methods=["POST"])
def serve_custom_static(filename):
    auth_token = request.headers.get(
        "Authorization"
    )  # Getting the auth token from the request header
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)  # Verifying the token
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    try:
        return send_from_directory(STATIC_FOLDER, filename)
    except FileNotFoundError:
        return 400  # Or handle the error as you see fit


# ----------------------------------------- Authentication Endpoints -----------------------------------------


# Register Endpoint
@app.route("/api/auth/register", methods=["POST"])
@limiter.limit("5 per minute")  # Limit to 5 login attempts per minute per IP
def register():
    data = request.get_json()
    username = data["username"]
    email_id = data["email_id"]
    password = data["password"]

    # Convert the password string to bytes and hash it
    salt = bcrypt.gensalt()  # Generates a random salt
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    DaOPS = DatabaseOPS()  # DatabaseOPS instance
    isInserted = DaOPS.inserting_data_in_users(
        username=username, email=email_id, password=hashed_password
    )

    if isInserted:
        return jsonify({"Response": "User registered successfully"}), 200
    else:
        return jsonify({"Response": "An error occured"}), 500


# Login Endpoint
@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")  # Limit to 5 login attempts per minute per IP
def login():
    data = request.get_json()
    email = data["email_id"]
    password = data["password"]  # Plain password from user input

    DaOPS = DatabaseOPS()  # DatabaseOPS instance
    stored_pwd_hash = DaOPS.get_password(email_id=email)

    if stored_pwd_hash is None:
        return jsonify({"error": "User not found"}), 404

    # If stored_hash is a string, convert to bytes
    if isinstance(stored_pwd_hash, str):
        stored_pwd_hash = stored_pwd_hash.encode("utf-8")

    isValidUser = bcrypt.checkpw(password.encode("utf-8"), stored_pwd_hash)

    if isValidUser:
        user_id, user_name = DaOPS.get_user_data(email_id=email)
        auth_token = utils.authentication_token(
            user_id=user_id, user_email=email, user_name=user_name
        )  # Authentication JWT Token
        refresh_token = utils.refresh_token(
            user_id=user_id, user_email=email, user_name=user_name
        )  # Refresh JWT Token

        if (
            DaOPS.set_tokens(
                email=email, auth_token=auth_token, refresh_token=refresh_token
            )
            == 1
        ):
            return (
                jsonify(
                    {
                        "auth_token": auth_token,
                        "refresh_token": refresh_token,
                        "user": {
                            "user_id": user_id,
                            "user_name": user_name,
                            "email_id": email,
                        },
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/auth/refresh_tokens", methods=["POST"])
@limiter.limit("5 per minute")  # Limit to 5 attempts per minute per IP
def refresh_tokens():
    data = request.get_json()
    refresh_token = data["refresh_token"]

    decoded_token = utils.verify_token(refresh_token)
    user_id = decoded_token["user_id"]
    email = decoded_token["email"]
    user_name = decoded_token["user_name"]

    new_auth_token = utils.authentication_token(
        user_id=user_id, user_email=email, user_name=user_name
    )

    new_refresh_token = utils.refresh_token(
        user_id=user_id, user_email=email, user_name=user_name
    )

    DaOPS = DatabaseOPS()

    if (
        DaOPS.set_tokens(
            email=email, auth_token=new_auth_token, refresh_token=new_refresh_token
        )
        == 1
    ):
        return (
            jsonify({"auth_token": new_auth_token, "refresh_token": new_refresh_token}),
            200,
        )
    else:
        return jsonify({"error": "Error while generating tokens."}), 500


@app.route("/api/auth/logout", methods=["POST"])
@limiter.limit("5 per minute")  # Limit to 5 attempts per minute per IP
def logout():
    data = request.get_json()
    refresh_token = data["refresh_token"]

    DaOPS = DatabaseOPS()
    if DaOPS.logout(refresh_token=refresh_token) == 1:
        return jsonify({"message": "Logged out successfully."}), 200
    else:
        return jsonify({"error": "Error occured while logging out."})


# ----------------------------------------- System Endpoints -----------------------------------------


# Text Moderation Endpoint
@app.route("/textmoderation", methods=["POST"])
def TextModeration():

    auth_token = request.headers.get(
        "Authorization"
    )  # Getting the auth token from the request header
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)  # Verifying the token
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    user_id = decoded_token["user_id"]  # Getting the user id from the token

    # Getting data from the request
    data = request.get_json()
    profane_sentence = data["sentence"]
    mask_character = data["mask_character"]
    custom_words = data["custom_words"]

    r = tpf.textProfanityFilteration(
        profane_sentence=profane_sentence,
        mask_char=mask_character,
        custom_words=custom_words,
    )

    output_content = ""
    for x in r:
        output_content += x["FilteredWord"] + " "

    DaOPS = DatabaseOPS()
    input_content_id = DaOPS.insert_input_content(
        user_id=user_id,
        content_type="TEXT",
        input_content=profane_sentence,
        mask_character=mask_character,
        output_content=output_content,
    )

    if input_content_id is not None:
        print(f"Input content id is: {input_content_id}")
        for x in custom_words:  # Inserting custom words into the database
            DaOPS.insert_custom_words(input_content_id=input_content_id, custom_word=x)
        for x in r:  # Inserting processed text into the database
            DaOPS.insert_processed_text(
                input_content_id=input_content_id,
                original_word=x["OriginalWord"],
                is_flagged=x["IsProfane"],
                filtered_word=x["FilteredWord"],
            )
        return jsonify(r), 200
    else:
        return jsonify({"error": "Internal server error"}), 500


# Audio Moderation Endpoint
@app.route("/audiomoderation", methods=["POST"])
def AudioModeration():
    auth_token = request.headers.get(
        "Authorization"
    )  # Getting the auth token from the request header
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)  # Verifying the token
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    user_id = decoded_token["user_id"]  # Getting the user id from the token

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    mask_char = request.form.get(
        "mask_char", "*"
    )  # Getting the mask character from the request form
    custom_bad_words = request.form.getlist(
        "words"
    )  # Getting the custom words from the request form

    audio_file = request.files["audio"]  # Getting the audio file from the request files
    filename = secure_filename(
        audio_file.filename
    )  # Getting the filename from the audio file
    filepath = os.path.join(
        STATIC_FOLDER, filename
    )  # Save the audio file to ./storage/files
    audio_file.save(filepath)  # Saving the audio file to the upload folder
    print(f"Audio file saved to: {filepath}")

    output_path, profanity_data = apf.audioProfanityFilteration(
        audio_path=filepath,
        output_file_name=f"{str(int(time.time()))}.mp3",
        mask_char=mask_char,
        custom_words=custom_bad_words,
    )

    DaOPS = DatabaseOPS()
    input_content_id = DaOPS.insert_input_content(
        user_id=user_id,
        content_type="AUDIO",
        input_content=filepath,
        mask_character=mask_char,
        output_content=output_path,
    )

    if input_content_id is not None:
        for x in custom_bad_words:
            DaOPS.insert_custom_words(input_content_id=input_content_id, custom_word=x)
        for x in profanity_data:
            DaOPS.insert_processed_audio(
                input_content_id=input_content_id,
                start_time=x["Start"],
                end_time=x["End"],
                is_flagged=x["IsProfane"],
                original_word=x["OriginalWord"],
                filtered_word=x["FilteredWord"],
            )
        return (
            jsonify(
                {
                    "output_path": output_path,
                    "profanity_data": profanity_data,
                }
            ),
            200,
        )
    else:
        return jsonify({"error": "Internal server error"}), 500


# Image Moderation Endpoint
@app.route("/imgmoderation", methods=["POST"])
def ImageModeration():
    try:
        # Check if image file is provided
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image_file = request.files["image"]
        filename = secure_filename(image_file.filename)

        # Validate file extension
        if not allowed_image_file(filename):
            return (
                jsonify(
                    {"error": "Invalid file extension. Allowed: png, jpg, jpeg, gif"}
                ),
                400,
            )

        # Get blur radius from form data, default to 10
        try:
            blur_radius = int(request.form.get("blur_radius", 10))
            if blur_radius < 0:
                raise ValueError
        except ValueError:
            return (
                jsonify(
                    {"error": "Invalid blur_radius. Must be a non-negative number"}
                ),
                400,
            )

        # Save uploaded image
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(filepath)

        r = ipd.detect(image_path=filepath)  # Detecting profanity in image

        blured_image_path = ipd.blur_image(
            input_path=filepath, blur_radius=blur_radius
        )  # Applying blur if it is flagged
        r["blured_image_path"] = (
            blured_image_path  # Adding new key value pair in response
        )

        return jsonify(r)

    except Exception as e:
        print("error: Processing error", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# Video Moderation Endpoint
@app.route("/videomoderation", methods=["POST"])
def VideoModeration():
    try:
        start_time = time.time()
        # Check if image file is provided
        if "video" not in request.files:
            return jsonify({"error": "No video file provided"}), 400

        video_file = request.files["video"]
        filename = secure_filename(video_file.filename)

        # Validate file extension
        if not allowed_video_file(filename):
            return (
                jsonify({"error": "Invalid file extension. Allowed: mp4, mov, avi"}),
                400,
            )

        # Get blur radius from form data, default to 10
        try:
            blur_radius = int(request.form.get("blur_radius", 10))
            if blur_radius < 1:
                blur_radius = 1  # Ensure it's at least 1
        except (ValueError, TypeError):
            return (
                jsonify({"error": "Invalid blur_radius. Must be a positive integer"}),
                400,
            )

        # Get mask character from form data, default to 10
        try:
            mask_char = request.form.get("mask_char", "🤬")
        except ValueError:
            return (
                jsonify({"error": "Invalid mask_char. Must be a string or emoji"}),
                400,
            )

        # Getting custom profane words
        words = request.form.getlist("custom_words")

        # Save uploaded video
        input_file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        video_file.save(input_file_path)

        # Using VideoProfanityDetection class for detection
        vpf = VideoProfanityDetection(
            input_video=input_file_path, custom_words=words, mask_char=mask_char
        )

        return jsonify(vpf.video_moderation(blur_video=True))

    except Exception as e:
        print(f"Internal error occured. Error is:\n {e}")
        return 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
