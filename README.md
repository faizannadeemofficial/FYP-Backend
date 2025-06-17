# Content Moderation API

A comprehensive content moderation system that detects and filters inappropriate content across multiple media types including text, audio, images, and videos.

## 📋 Project Overview

This project provides a Flask-based API for content moderation with the following key features:

- **Text Moderation**: Detects and masks profane words using ML models and custom word lists
- **Audio Moderation**: Transcribes audio, detects profanity, and replaces offensive words with beep sounds
- **Image Moderation**: Uses CLIP model to detect harmful content and applies blur effects
- **Video Moderation**: Comprehensive video processing with frame-by-frame analysis and audio moderation
- **Machine Learning**: Pre-trained models for offensive text classification using TF-IDF and Logistic Regression

## 🚀 Installation Steps

### Prerequisites
- Python 3.8 or higher
- FFmpeg (for video processing)
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd 1.1.1
```

### Step 2: Create Virtual Environment
```bash
python -m venv env
```

### Step 3: Activate Virtual Environment
**Windows:**
```bash
env\Scripts\activate
```

**Linux/Mac:**
```bash
source env/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Install FFmpeg
**Windows:**
- Download from https://ffmpeg.org/download.html
- Add to system PATH

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### Step 6: Run the Application
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## 📁 Project Structure

```
1.1.1/
├── app.py                 # Main Flask application
├── text.py               # Text moderation module
├── audio.py              # Audio moderation module
├── image.py              # Image moderation module
├── video.py              # Video moderation module
├── predict.py            # ML prediction module
├── model/                # Machine learning models
│   ├── training.py       # Model training script
│   ├── offensive_classifier.joblib    # Trained classifier
│   ├── tfidf_vectorizer.joblib        # TF-IDF vectorizer
│   ├── clean_file.csv    # Training dataset
│   └── badwords.json     # Profanity word list
├── storage/              # File storage directories
│   ├── uploads/          # Uploaded files
│   ├── audio/            # Processed audio files
│   ├── imgs/             # Processed images
│   ├── output/           # Output videos
│   └── testing/          # Test files
└── requirements.txt      # Python dependencies
```

## 🔌 API Endpoints

### Base URL
```
http://localhost:5000
```

### 1. Health Check
**Endpoint:** `GET /`
**Description:** Check if the API is running
**Response:**
```html
<h1>Content Moderation APIs are live...</h1>
```

### 2. Text Moderation
**Endpoint:** `POST /textmoderation`
**Description:** Filter profane words from text input

**Request Body (JSON):**
```json
{
    "sentence": "Your text here",
    "mask_character": "🤬",
    "custom_words": ["custom", "profane", "words"]
}
```

**CURL Request**
```curl
curl -X POST http://localhost:5000/textmoderation \
  -H "Content-Type: application/json" \
  -d '{
    "sentence": "This is a damn bad example.",
    "mask_character": "🤬",
    "custom_words": ["damn", "bad"]
  }'

```

**Response:**
```json
[
    {
        "FilteredWord": "you",
        "IsProfane": false,
        "OriginalWord": "you"
    },
    {
        "FilteredWord": "have",
        "IsProfane": false,
        "OriginalWord": "have"
    },
    {
        "FilteredWord": "made",
        "IsProfane": false,
        "OriginalWord": "made"
    },
    {
        "FilteredWord": "your",
        "IsProfane": false,
        "OriginalWord": "your"
    },
    {
        "FilteredWord": "🤬🤬🤬🤬🤬🤬🤬",
        "IsProfane": true,
        "OriginalWord": "fucking"
    },
    {
        "FilteredWord": "turn",
        "IsProfane": false,
        "OriginalWord": "turn"
    },
    {
        "FilteredWord": "charlie",
        "IsProfane": false,
        "OriginalWord": "charlie"
    }
]
```

### 3. Audio Moderation
**Endpoint:** `POST /audiomoderation`
**Description:** Process audio file and replace profane words with beep sounds

**Request (Multipart Form):**
- `audio`: Audio file (mp3, wav, etc.)
- `mask_char`: Character for masking (default: "*")
- `words`: Custom profane words list

**CURL Request**
```curl
curl -X POST http://localhost:5000/audiomoderation \
  -F "audio=@/path/to/your/audiofile.mp3" \
  -F "mask_char=*" \
  -F "words=badword1" \
  -F "words=badword2"
```

**Response:**
```json
{
    "output_path": "storage/audio/1750182719.mp3",
    "profanity_data": [
        {
            "End": 0.32,
            "FilteredWord": " You",
            "IsProfane": false,
            "OriginalWord": " You",
            "Start": 0.0
        },
        {
            "End": 0.48,
            "FilteredWord": " have",
            "IsProfane": false,
            "OriginalWord": " have",
            "Start": 0.32
        },
        {
            "End": 0.64,
            "FilteredWord": " made",
            "IsProfane": false,
            "OriginalWord": " made",
            "Start": 0.48
        },
        {
            "End": 0.84,
            "FilteredWord": " your",
            "IsProfane": false,
            "OriginalWord": " your",
            "Start": 0.64
        },
        {
            "End": 1.1,
            "FilteredWord": "🤬🤬🤬🤬🤬🤬🤬🤬",
            "IsProfane": true,
            "OriginalWord": " fucking",
            "Start": 0.84
        },
        {
            "End": 1.38,
            "FilteredWord": " turn",
            "IsProfane": false,
            "OriginalWord": " turn",
            "Start": 1.1
        }
    ]
}
```

### 4. Image Moderation
**Endpoint:** `POST /imgmoderation`
**Description:** Detect harmful content in images and apply blur if needed

**Request (Multipart Form):**
- `image`: Image file (png, jpg, jpeg, gif)
- `blur_radius`: Blur intensity (default: 10)

**CURL Request**
```curl
curl -X POST http://localhost:5000/imgmoderation \
  -F "image=@/path/to/your/image.jpg" \
  -F "blur_radius=15"
```

**Response:**
```json
{
    "isFlagged": true,
    "harmful_detected": [
        "harmful content involving violence"
    ],
    "blured_image_path": "storage/imgs/1234567890.jpg"
}
```

### 5. Video Moderation
**Endpoint:** `POST /videomoderation`
**Description:** Comprehensive video moderation with frame and audio analysis

**Request (Multipart Form):**
- `video`: Video file (mp4, mov, avi)
- `blur_radius`: Blur intensity (default: 10)
- `mask_char`: Audio masking character (default: "🤬")
- `custom_words`: Custom profane words list

**CURL Request**
```curl
curl -X POST http://localhost:5000/videomoderation \
  -F "video=@/path/to/your/video.mp4" \
  -F "blur_radius=15" \
  -F "mask_char=😈" \
  -F "custom_words=badword1" \
  -F "custom_words=badword2"
```

**Response:**
```json
{
    "image_detections": [
        {
            "harmful_detected": [],
            "isFlagged": false,
            "second": 0
        },
        {
            "harmful_detected": [
                "harmful content involving tobacco use or promotion"
            ],
            "isFlagged": true,
            "second": 1
        },
        {
            "harmful_detected": [
                "harmful content involving tobacco use or promotion"
            ],
            "isFlagged": true,
            "second": 3
        }
    ],
    "moderated_video_path": "storage/output/1750182903.mp4",
    "text_moderated_data": [
        {
            "End": 0.34,
            "FilteredWord": " You",
            "IsProfane": false,
            "OriginalWord": " You",
            "Start": 0.0
        },
        {
            "End": 0.5,
            "FilteredWord": " have",
            "IsProfane": false,
            "OriginalWord": " have",
            "Start": 0.34
        },
        {
            "End": 0.66,
            "FilteredWord": " made",
            "IsProfane": false,
            "OriginalWord": " made",
            "Start": 0.5
        },
        {
            "End": 0.86,
            "FilteredWord": " your",
            "IsProfane": false,
            "OriginalWord": " your",
            "Start": 0.66
        },
        {
            "End": 1.12,
            "FilteredWord": "😈😈😈😈😈😈😈😈",
            "IsProfane": true,
            "OriginalWord": " fucking",
            "Start": 0.86
        },
        {
            "End": 1.4,
            "FilteredWord": " turn",
            "IsProfane": false,
            "OriginalWord": " turn",
            "Start": 1.12
        },
        {
            "End": 1.82,
            "FilteredWord": " Charlie,",
            "IsProfane": false,
            "OriginalWord": " Charlie,",
            "Start": 1.4
        }
    ]
}
```

## 📄 File Documentation

### Core Application Files

#### `app.py`
Main Flask application that provides REST API endpoints for content moderation.

**Key Features:**
- Flask web server configuration
- File upload handling with security validation
- API endpoint routing for all moderation types
- Error handling and response formatting

#### `text.py`
Text profanity filtering module using machine learning and rule-based approaches.

**Key Classes:**
- `TextProfanityFilter`: Main class for text moderation

**Key Methods:**
- `textProfanityFilteration()`: Main filtering function
- `convert_leetspeak()`: Converts leetspeak to normal text
- `isBadWord()`: Checks if word is in profanity list
- `predict_text()`: ML-based text classification

#### `audio.py`
Audio processing and moderation using speech-to-text and audio manipulation.

**Key Classes:**
- `AudioProfanityFilter`: Audio moderation handler

**Key Methods:**
- `transcribeAndModerate()`: Transcribes and moderates audio
- `audioProfanityFilteration()`: Main audio processing function

**Dependencies:**
- `faster-whisper`: Speech-to-text transcription
- `pydub`: Audio file manipulation

#### `image.py`
Image content moderation using CLIP (Contrastive Language-Image Pre-training) model.

**Key Classes:**
- `ImageProfanityFilter`: Image moderation handler

**Key Methods:**
- `detect()`: Detects harmful content in images
- `blur_image()`: Applies blur effect to flagged images
- `pretty_print()`: Displays detection results

**Features:**
- Detects 13 categories of harmful content
- Configurable confidence threshold
- Automatic blur application

#### `video.py`
Comprehensive video moderation combining image and audio analysis.

**Key Classes:**
- `VideoProfanityDetection`: Video moderation handler

**Key Methods:**
- `extract_audio()`: Extracts audio from video
- `middle_frame()`: Extracts frames for analysis
- `blur_and_audio()`: Applies blur and audio moderation
- `video_moderation()`: Main video processing pipeline

#### `predict.py`
Machine learning prediction module for text classification.

**Key Classes:**
- `ProfanityDetectionModel`: ML model wrapper

**Key Methods:**
- `predict_text()`: Classifies text as offensive or not

### Model Directory

#### `model/training.py`
Script for training the offensive text classification model.

**Features:**
- Uses TF-IDF vectorization
- Logistic Regression classifier
- Class weight balancing
- Model persistence with joblib

#### `model/offensive_classifier.joblib`
Pre-trained Logistic Regression model for offensive text classification.

#### `model/tfidf_vectorizer.joblib`
TF-IDF vectorizer fitted on training data for text feature extraction.

#### `model/clean_file.csv`
Training dataset containing labeled text samples for model training.

#### `model/badwords.json`
Comprehensive list of profane words and phrases for rule-based filtering.



## 🔧 Configuration

### Environment Variables
- `UPLOAD_FOLDER`: Directory for uploaded files (default: "./storage/uploads")
- `ALLOWED_IMAGE_EXTENSIONS`: Supported image formats
- `ALLOWED_VIDEO_EXTENSIONS`: Supported video formats

### Model Configuration
- **CLIP Model**: ViT-B/32 (default)
- **Detection Threshold**: 0.3 (configurable)
- **Blur Radius**: 10 (configurable)
- **Mask Character**: "*" (configurable)

## 🧪 Testing

The project includes test files in `storage/testing/` directory:
- Audio files: `profane.mp3`
- Video files: `7sec.mp4`, `gmbtbc.mp4`, `profane_video_with_audio.mp4`
- Image files: Various test images

## 📊 Performance

- **Text Processing**: Nearly real-time processing
- **Audio Processing**: Depends on audio length and Whisper model size
- **Image Processing**: ~1-2 seconds per image
- **Video Processing**: Depends on video length and resolution

## 🔒 Security Features

- File type validation
- Secure filename handling
- Input sanitization
- Error handling and logging

## 🤝 Contributors

1. Muhammad Faizan Nadeem (Back End Development)
2. Tabish Ali (Front End Development)
3. Muhammad Kashan Ali (Database Designing and Documentation)

## 🆘 Support

For issues and questions, please create an issue in the repository or contact me on [LinkedIn](https://www.linkedin.com/in/mfaizan422).


