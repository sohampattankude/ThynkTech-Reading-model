"""
Test Script for Reading Evaluation API
======================================
This script helps you test the reading evaluation system.

Usage:
1. Make sure the server is running: uvicorn app.main:app --reload
2. Run this script with an audio file:
   python test_api.py --audio your_audio.wav --chapter chapter_1

Or use the interactive mode:
   python test_api.py
"""

import requests
import argparse
import os
import sys


API_BASE_URL = "http://localhost:8000"


def check_health():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload")
        return False


def list_chapters():
    """List all available chapters."""
    try:
        response = requests.get(f"{API_BASE_URL}/chapters")
        if response.status_code == 200:
            chapters = response.json()["chapters"]
            print("\n📚 Available Chapters:")
            print("-" * 50)
            for chapter in chapters:
                print(f"   ID: {chapter['id']}")
                print(f"   Title: {chapter['title']}")
                print(f"   Word Count: {chapter['word_count']} words")
                print("-" * 50)
            return chapters
        else:
            print(f"❌ Failed to get chapters: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def get_chapter_text(chapter_id):
    """Get the text of a specific chapter."""
    try:
        response = requests.get(f"{API_BASE_URL}/chapters/{chapter_id}")
        if response.status_code == 200:
            chapter = response.json()
            print(f"\n📖 Chapter: {chapter['title']}")
            print("-" * 50)
            print(f"Text to read:\n{chapter['text']}")
            print("-" * 50)
            return chapter
        else:
            print(f"❌ Chapter not found: {chapter_id}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def assess_audio(audio_path, chapter_id):
    """
    Send audio file for assessment.
    
    Args:
        audio_path: Path to audio file (.wav or .mp3)
        chapter_id: ID of the chapter being read
    """
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return None
    
    print(f"\n🎤 Assessing audio: {audio_path}")
    print(f"📖 Chapter: {chapter_id}")
    print("-" * 50)
    
    try:
        with open(audio_path, "rb") as audio_file:
            files = {"audio": (os.path.basename(audio_path), audio_file)}
            data = {"chapter_id": chapter_id}
            
            print("⏳ Processing... (This may take a moment for the first request)")
            response = requests.post(
                f"{API_BASE_URL}/assess/audio",
                files=files,
                data=data,
                timeout=300  # 5 minutes timeout for first load
            )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Assessment Complete!")
            print("=" * 50)
            print(f"📊 RESULTS:")
            print(f"   Accuracy:     {result['accuracy']}%")
            print(f"   Completeness: {result['completeness']}%")
            print(f"   Fluency:      {result['fluency_wpm']} WPM")
            print(f"   Suspicious:   {'⚠️ Yes' if result.get('suspicious') else '✅ No'}")
            print(f"\n💬 Remarks: {result['remarks']}")
            
            if result.get('transcript'):
                print(f"\n📝 Transcript:\n   \"{result['transcript']}\"")
            
            if result.get('details'):
                details = result['details']
                print(f"\n📈 Details:")
                print(f"   Matched words: {details.get('matched_words', 'N/A')}")
                print(f"   Student words: {details.get('total_student_words', 'N/A')}")
                print(f"   Reference words: {details.get('total_reference_words', 'N/A')}")
                print(f"   Audio duration: {details.get('audio_duration_seconds', 'N/A')}s")
            
            print("=" * 50)
            return result
        else:
            print(f"❌ Assessment failed: {response.status_code}")
            print(f"   Error: {response.json()}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The model might be loading for the first time.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def interactive_mode():
    """Run in interactive mode."""
    print("\n" + "=" * 60)
    print("🎓 READING EVALUATION MODULE - Interactive Test")
    print("=" * 60)
    
    # Check API health
    if not check_health():
        return
    
    # List chapters
    chapters = list_chapters()
    if not chapters:
        return
    
    # Get chapter selection
    print("\nEnter chapter ID to view its text (or press Enter to skip): ", end="")
    chapter_input = input().strip()
    if chapter_input:
        get_chapter_text(chapter_input)
    
    # Get audio file path
    print("\n🎤 Enter the path to your audio file (.wav or .mp3): ", end="")
    audio_path = input().strip().strip('"')  # Remove quotes if present
    
    if not audio_path:
        print("No audio file provided. Exiting.")
        return
    
    # Get chapter ID for assessment
    print("📖 Enter chapter ID for assessment: ", end="")
    chapter_id = input().strip()
    
    if not chapter_id:
        chapter_id = "chapter_1"
        print(f"   Using default: {chapter_id}")
    
    # Perform assessment
    assess_audio(audio_path, chapter_id)


def main():
    parser = argparse.ArgumentParser(
        description="Test the Reading Evaluation API"
    )
    parser.add_argument(
        "--audio", "-a",
        help="Path to audio file (.wav or .mp3)"
    )
    parser.add_argument(
        "--chapter", "-c",
        default="chapter_1",
        help="Chapter ID to compare against (default: chapter_1)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available chapters"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check API health status"
    )
    
    args = parser.parse_args()
    
    if args.health:
        check_health()
    elif args.list:
        check_health()
        list_chapters()
    elif args.audio:
        if check_health():
            assess_audio(args.audio, args.chapter)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
