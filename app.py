import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from text import TextProfanityFilter
from audio import AudioProfanityFilter
from image import ImageProfanityFilter
from video import VideoProfanityDetection

app = Flask(__name__)
CORS(app)

tpf = TextProfanityFilter()  # Instance of TextProfanityFilter
apf = AudioProfanityFilter(textpf=tpf)  # Instance of AudioProfanityFilter
ipd = ImageProfanityFilter()  # Instance of ImageProfanityFilter

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = "./storage/uploads"
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


# Text Moderation Endpoint
@app.route("/textmoderation", methods=["POST"])
def TextModeration():
    data = request.get_json()
    profane_sentence = data["sentence"]
    mask_character = data["mask_character"]
    custom_words = data["custom_words"]

    r = tpf.textProfanityFilteration(
        profane_sentence=profane_sentence,
        mask_char=mask_character,
        custom_words=custom_words,
    )

    return jsonify(r), 200


# Audio Moderation Endpoint
@app.route("/audiomoderation", methods=["POST"])
def AudioModeration():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    mask_char = request.form.get("mask_char", "*")
    words = request.form.getlist("words")

    audio_file = request.files["audio"]
    filename = secure_filename(audio_file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    audio_file.save(filepath)

    output_path, profanity_data = apf.audioProfanityFilteration(
        audio_path=filepath,
        output_path=f"storage/audio/{int(time.time())}.mp3",
        mask_char=mask_char,
        custom_words=words,
    )

    return jsonify({"output_path": output_path, "profanity_data": profanity_data})


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
            input_video=input_file_path,
            custom_words=words,
            mask_char=mask_char
        )

        return jsonify(
            vpf.video_moderation(blur_video = True)
            )

    except Exception as e:
        print(f"Internal error occured. Error is:\n {e}")
        return 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
