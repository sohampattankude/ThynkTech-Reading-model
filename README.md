# 📚 Reading Evaluation Module

> **ThynkChat INDIA V2 - Internship Assignment**  
> AI-powered reading assessment system for evaluating student reading performance

## 📋 Project Overview

The **Reading Evaluation Module** is a FastAPI-based backend service that evaluates a student's reading performance by comparing spoken audio with reference textbook content.

### Key Features

- 🎤 **Speech-to-Text (ASR)**: Converts student audio recordings to text using OpenAI Whisper
- 📝 **Text Normalization**: Cleans and standardizes text for accurate comparison
- 🔍 **Fuzzy Matching**: Uses RapidFuzz for intelligent word comparison
- 📊 **Performance Metrics**: Calculates accuracy, completeness, and fluency (WPM)
- ⚠️ **Suspicious Reading Detection**: Flags unusually fast reading speeds

### System Pipeline

```
Audio Input → Speech Recognition → Text Comparison → Scoring → API Response
```

## 🏗️ Project Structure

```
reading-evaluation/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoint definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asr_service.py       # Whisper speech-to-text service
│   │   ├── text_service.py      # Text normalization & comparison
│   │   ├── evaluation_service.py # Metrics calculation
│   │   └── chapter_service.py   # Chapter data management
│   └── utils/
│       ├── __init__.py
│       └── audio_utils.py   # Audio processing utilities
│
├── data/
│   └── chapters.json        # Reference text storage
│
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Setup Instructions

### Prerequisites

- **Python 3.9+** installed
- **FFmpeg** installed (required for audio processing)
- **Git** (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd reading-evaluation
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install FFmpeg

FFmpeg is required for audio processing:

**Windows:**
1. Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract and add to system PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Step 5: Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## 📖 API Documentation

### Interactive Docs

Once the server is running, access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Endpoints

#### 1. Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Reading Evaluation Module is running",
  "version": "1.0.0"
}
```

#### 2. Assess Reading (Main Endpoint)

```http
POST /assess/audio
```

**Request:**
- `audio`: Audio file (`.wav` or `.mp3`)
- `chapter_id`: Chapter identifier (form field)

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/assess/audio" \
  -F "audio=@student_reading.wav" \
  -F "chapter_id=chapter_1"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/assess/audio"
files = {"audio": open("student_reading.wav", "rb")}
data = {"chapter_id": "chapter_1"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response:**
```json
{
  "accuracy": 82.5,
  "completeness": 75.0,
  "fluency_wpm": 110.0,
  "remarks": "Good reading performance. Most of the text was covered. Reading pace is appropriate.",
  "transcript": "reading is one of the most important skills that we learn in school...",
  "suspicious": false,
  "details": {
    "matched_words": 45,
    "total_student_words": 55,
    "total_reference_words": 60,
    "audio_duration_seconds": 30.5
  }
}
```

#### 3. List Available Chapters

```http
GET /chapters
```

**Response:**
```json
{
  "chapters": [
    {"id": "chapter_1", "title": "Introduction to Reading", "word_count": 55},
    {"id": "chapter_2", "title": "The Water Cycle", "word_count": 78},
    {"id": "chapter_3", "title": "Healthy Habits", "word_count": 65}
  ]
}
```

#### 4. Get Chapter Details

```http
GET /chapters/{chapter_id}
```

**Response:**
```json
{
  "id": "chapter_1",
  "title": "Introduction to Reading",
  "text": "Reading is one of the most important skills..."
}
```

## 📊 Evaluation Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| **Accuracy** | % of correctly matched words | `(Matched Words / Student Words) × 100` |
| **Completeness** | % of reference text covered | `(Matched Words / Reference Words) × 100` |
| **Fluency (WPM)** | Reading speed | `(Word Count / Duration in minutes)` |
| **Suspicious** | Flag for abnormal speed | `WPM > 250` |

### WPM Ranges

| Category | WPM Range |
|----------|-----------|
| Very Slow | 0 - 60 |
| Slow | 60 - 100 |
| Normal | 100 - 160 |
| Fast | 160 - 200 |
| Very Fast | 200 - 250 |
| Suspicious | > 250 |

## 🧪 Sample Output

### Successful Evaluation

```json
{
  "accuracy": 85.7,
  "completeness": 78.3,
  "fluency_wpm": 125.5,
  "remarks": "Good reading performance. Most of the text was covered. Reading pace is appropriate.",
  "transcript": "reading is one of the most important skills that we learn in school it helps us understand the world around us",
  "suspicious": false,
  "details": {
    "matched_words": 47,
    "total_student_words": 55,
    "total_reference_words": 60,
    "audio_duration_seconds": 26.3
  }
}
```

### Suspicious Reading Detection

```json
{
  "accuracy": 92.0,
  "completeness": 88.5,
  "fluency_wpm": 280.0,
  "remarks": "⚠️ Warning: Reading speed is unusually fast. This may indicate the audio was played back at increased speed. Excellent accuracy! Words are pronounced correctly. Good coverage of the reference text. Very fast reading. Ensure clarity isn't sacrificed for speed.",
  "suspicious": true
}
```

## 🔧 Configuration

### Whisper Model Size

Edit `app/services/asr_service.py` to change the Whisper model:

```python
# Options: "tiny", "base", "small", "medium", "large"
asr_service = ASRService(model_size="base")
```

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 39M | Fastest | Lower |
| base | 74M | Fast | Good |
| small | 244M | Medium | Better |
| medium | 769M | Slow | High |
| large | 1550M | Slowest | Best |

### Fuzzy Matching Threshold

Edit `app/services/text_service.py`:

```python
# Default: 80 (80% similarity required for match)
text_service = TextService(fuzzy_threshold=80)
```

## 📁 Adding New Chapters

Edit `data/chapters.json`:

```json
{
  "chapters": {
    "chapter_6": {
      "id": "chapter_6",
      "title": "Your Chapter Title",
      "text": "Your chapter content goes here..."
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure FFmpeg is installed and added to system PATH
   - Restart terminal/IDE after installation

2. **Whisper model download fails**
   - Check internet connection
   - Models are cached at `~/.cache/whisper/`

3. **Audio format not supported**
   - Ensure audio is `.wav` or `.mp3`
   - Check file is not corrupted

4. **Slow first request**
   - First request loads the Whisper model (normal behavior)
   - Subsequent requests are faster

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI |
| Language | Python 3.9+ |
| ASR | OpenAI Whisper |
| Text Matching | RapidFuzz |
| Audio Processing | Pydub, Soundfile |
| Data Storage | JSON |

## 📝 License

This project is developed as part of the ThynkChat Internship Program.

---

**Author:** Intern  
**Date:** January 2026  
**Module:** Reading Evaluation Module  
**Domain:** AI / Backend / NLP / Speech Processing
