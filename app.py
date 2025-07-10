import os
import time
import bcrypt
from flask import Flask, Response, abort, request, jsonify, send_file, send_from_directory
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
            DaOPS.close()  # Close the database connection
            # Return the auth token, refresh token, user id, user name and email
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




# Stream Media File
@app.route('/stream/<path:filename>')
def stream_file(filename):
    file_path = os.path.join("storage/files", filename)
    if not os.path.exists(file_path):
        return abort(404)

    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(file_path)

    # Handle partial content (video/audio seeking)
    try:
        size = os.path.getsize(file_path)
        byte1, byte2 = 0, None

        match = range_header.replace('bytes=', '').split('-')
        if match[0]:
            byte1 = int(match[0])
        if len(match) == 2 and match[1]:
            byte2 = int(match[1])

        length = size - byte1 if byte2 is None else byte2 - byte1 + 1
        with open(file_path, 'rb') as f:
            f.seek(byte1)
            data = f.read(length)

        response = Response(data, 206, mimetype='application/octet-stream',
                            content_type='application/octet-stream')
        response.headers.add('Content-Range', f'bytes {byte1}-{byte1+length-1}/{size}')
        response.headers.add('Accept-Ranges', 'bytes')
        return response
    except Exception as e:
        return abort(500, str(e))


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
    project_name = data["project_name"]

    r = tpf.textProfanityFilteration(
        profane_sentence=profane_sentence,
        mask_char=mask_character,
        custom_words=custom_words,
    )

    output_content = ""
    if len(r) == 0:
        return jsonify({"message": "No Profanity Detected"}), 200
    else:
        for x in r:
            output_content += x["FilteredWord"] + " "

    DaOPS = DatabaseOPS()
    input_content_id = DaOPS.insert_input_content(
        user_id=user_id,
        content_type="TEXT",
        input_content=profane_sentence,
        mask_character=mask_character,
        output_content=output_content,
        project_name=project_name,
    )

    if input_content_id is not None:

        for x in custom_words:  # Inserting custom words into the database
            try:
                DaOPS.insert_custom_words(input_content_id=input_content_id, custom_word=x)
            except Exception as e:
                print(f"Error from app.py in inserting custom words is: {e}")
        for x in r:  # Inserting processed text into the database
            try:
                DaOPS.insert_processed_text(
                    input_content_id=input_content_id,
                    original_word=x["OriginalWord"],
                    is_flagged=x["IsProfane"],
                    filtered_word=x["FilteredWord"],
                )
            except Exception as e:
                print(f"Error from app.py in inserting_processed_text is: {e}")
                return (
                    jsonify(
                        {
                            "error": "Internal server error while inserting data in processed text table"
                        }
                    ),
                    500,
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
    project_name = request.form.get(
        "project_name", str(int(time.time()))
    )
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
        project_name=project_name,
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

    project_name = request.form.get(
        "project_name", str(int(time.time()))
    )

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
        filepath = os.path.join("storage/files/", filename)
        image_file.save(filepath)

        r = ipd.detect(image_path=filepath)  # Detecting profanity in image

        blured_image_path = ipd.blur_image(
            input_path=filepath, blur_radius=blur_radius
        )  # Applying blur if it is flagged
        r["blured_image_path"] = (
            blured_image_path  # Adding new key value pair in response
        )

        DaOPS = DatabaseOPS()
        input_content_id = DaOPS.insert_input_content(
            user_id=user_id,
            content_type="IMAGE",
            input_content=filepath,
            mask_character="",
            output_content=blured_image_path,
            project_name=project_name,
        )

        if input_content_id is not None:
            for x in r["harmful_detected"]:
                if (
                    DaOPS.insert_processed_image(
                        input_content_id=input_content_id,
                        detected_content=x,
                        is_flagged=r["isFlagged"],
                    )
                    != 1
                ):
                    return (
                        jsonify(
                            {
                                "error": "Internal server error while inserting data in processed image table"
                            }
                        ),
                        500,
                    )

            if (
                DaOPS.insert_visual_content_features(
                    input_content_id=input_content_id,
                    blur_radius=str(blur_radius),
                    fps=0,
                )
                != 1
            ):
                return (
                    jsonify(
                        {
                            "error": "Internal server error while inseting data in insert_visual_content_features table"
                        }
                    ),
                    500,
                )
            return jsonify(r), 200
        else:
            return jsonify({"error": "Internal server error"}), 500

    except Exception as e:
        print("error: Processing error", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# Video Moderation Endpoint
@app.route("/videomoderation", methods=["POST"])
def VideoModeration():
    try:
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

        # Check if image file is provided
        if "video" not in request.files:
            return jsonify({"error": "No video file provided"}), 400

        video_file = request.files["video"]
        filename = secure_filename(video_file.filename)

        project_name = request.form.get(
        "project_name", str(int(time.time()))
    )

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
        input_file_path = os.path.join("storage/files", filename)
        video_file.save(input_file_path)

        # Using VideoProfanityDetection class for detection
        vpf = VideoProfanityDetection(
            input_video=input_file_path, custom_words=words, mask_char=mask_char
        )

        r = vpf.video_moderation(blur_video=True)

        DaOPS = DatabaseOPS()
        input_content_id = DaOPS.insert_input_content(
            user_id=user_id,
            content_type="VIDEO",
            input_content=input_file_path,
            mask_character=mask_char,
            output_content=r["moderated_video_path"],
            project_name=project_name,
        )

        for x in r["text_moderated_data"]:
            DaOPS.insert_processed_audio(
                input_content_id=input_content_id,
                start_time=x["Start"],
                end_time=x["End"],
                is_flagged=x["IsProfane"],
                original_word=x["OriginalWord"],
                filtered_word=x["FilteredWord"],
            )

        for x in r["image_detections"]:
            primary_key = DaOPS.insert_processed_video(
                input_content_id=input_content_id,
                start_second=x["second"],
                end_second=x["second"] + 1,
            )
            if len(x["harmful_detected"]) > 0:
                for detected_content in x["harmful_detected"]:
                    DaOPS.insert_video_content_detections(
                        processed_video_id=str(primary_key),
                        detected_content=detected_content,
                    )
        return jsonify(r), 200

    except Exception as e:
        print(f"Internal error occured. Error is:\n {e}")
        return jsonify(f"Internal error occured. Error is:\n {e}"), 200


# ================================================================== Retrieval APIs ====================================================================

# Retrieve all input content for a user
@app.route("/api/retrieve/", methods=["POST"])
def retrieve_input_content():
    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    user_id = decoded_token["user_id"]
    DaOPS = DatabaseOPS()
    data = DaOPS.get_input_content(user_id=[user_id])

    if data is not None:
        return jsonify(data), 200
    else:
        return jsonify({"error": "Internal server error"}), 500
    
# This endpoint retrieves processed audio data based on input content ID.
@app.route("/api/retrieve/processed_text", methods=["POST"])
def retrieve_processed_text():
    """ Retrieves processed text data based on input content ID.
    Expects a JSON body with "input_content_id" as a list.
    Returns processed text data or an error message.
    """

    print("debug 0")
    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    user_id = decoded_token["user_id"]
    data = request.get_json()
    input_content_id = data.get("input_content_id", [])
    print(f"Input Content ID: {input_content_id} and its type is {type(input_content_id)}")

    print("debug 1")

    DaOPS = DatabaseOPS()
    processed_text_data = DaOPS.get_processed_text(
        input_content_id=input_content_id,
    )
    print(f"Processed Text Data: {processed_text_data}")

    if processed_text_data is not None:
        print("debug 2")
        return jsonify(processed_text_data), 200
    else:
        return jsonify({"error": "Internal server error"}), 500

# This endpoint retrieves processed audio data based on input content ID.
@app.route("/api/retrieve/processed_audio", methods=["POST"])
def retrieve_processed_audio():
    """ Retrieves processed audio data based on input content ID.
    Expects a JSON body with "input_content_id" as a list.
    Returns processed audio data or an error message.
    """

    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    user_id = decoded_token["user_id"]
    data = request.get_json()
    input_content_id = data.get("input_content_id")

    DaOPS = DatabaseOPS()
    processed_audio_data = DaOPS.get_processed_audio(
        input_content_id=input_content_id,
    )

    if processed_audio_data is not None:
        return jsonify(processed_audio_data), 200
    else:
        return jsonify({"error": "Internal server error"}), 500

# This endpoint retrieves processed image data based on input content ID.
@app.route("/api/retrieve/processed_image", methods=["POST"])
def retrieve_processed_image():
    """ Retrieves processed image data based on input content ID.
    Expects a JSON body with "input_content_id" as a list.
    Returns processed image data or an error message.
    """

    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    user_id = decoded_token["user_id"]
    data = request.get_json()
    input_content_id = data.get("input_content_id")

    DaOPS = DatabaseOPS()
    processed_image_data = DaOPS.get_processed_image(
        input_content_id=input_content_id,
    )

    if processed_image_data is not None:
        return jsonify(processed_image_data), 200
    else:
        return jsonify({"error": "Internal server error"}), 500
    
# This endpoint retrieves processed video data based on input content ID.
@app.route("/api/retrieve/processed_video", methods=["POST"])
def retrieve_processed_video():
    """ Retrieves processed video data based on input content ID.
    Expects a JSON body with "input_content_id" as a list.
    Returns processed video data or an error message.
    """

    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded_token = utils.verify_token(auth_token)
    if decoded_token == "Token expired":
        return jsonify({"error": "Token expired"}), 401
    elif decoded_token == "Invalid token":
        return jsonify({"error": "Invalid token"}), 401

    user_id = decoded_token["user_id"]
    data = request.get_json()
    input_content_id = data.get("input_content_id")

    DaOPS = DatabaseOPS()
    processed_video_data = DaOPS.get_processed_video(
        input_content_id=input_content_id,
    )

    if processed_video_data is not None:
        return jsonify(processed_video_data), 200
    else:
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
