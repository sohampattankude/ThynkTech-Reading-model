"""
ASR (Automatic Speech Recognition) Service
==========================================
Handles speech-to-text conversion using OpenAI Whisper.

This service provides functionality to transcribe audio files
containing student speech into text for evaluation.
"""

import os
from typing import Optional
import whisper


class ASRService:
    """
    Automatic Speech Recognition service using OpenAI Whisper.
    
    Whisper is a general-purpose speech recognition model that
    supports multiple languages and can handle various audio qualities.
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize the ASR service with specified Whisper model.
        
        Args:
            model_size: Size of Whisper model to use.
                       Options: "tiny", "base", "small", "medium", "large"
                       Larger models are more accurate but slower.
                       Default is "base" for balance of speed and accuracy.
        """
        self.model_size = model_size
        self._model = None  # Lazy loading
        
    @property
    def model(self):
        """
        Lazy load the Whisper model to avoid loading on import.
        Model is loaded only when first transcription is requested.
        """
        if self._model is None:
            print(f"🎤 Loading Whisper model: {self.model_size}...")
            self._model = whisper.load_model(self.model_size)
            print("✅ Whisper model loaded successfully!")
        return self._model
    
    def transcribe(
        self, 
        audio_path: str,
        language: Optional[str] = "en"
    ) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file to transcribe
            language: Language code (e.g., "en" for English, "hi" for Hindi)
                     Set to None for automatic language detection.
                     
        Returns:
            Transcribed text from the audio
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If transcription fails
        """
        # Validate audio file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Perform transcription using Whisper
            # Options explained:
            # - fp16=False: Use FP32 for CPU compatibility
            # - language: Specify language to improve accuracy
            result = self.model.transcribe(
                audio_path,
                fp16=False,  # Set to True if using GPU
                language=language
            )
            
            # Extract transcribed text
            transcript = result.get("text", "").strip()
            
            return transcript
            
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def transcribe_with_timestamps(
        self, 
        audio_path: str,
        language: Optional[str] = "en"
    ) -> dict:
        """
        Transcribe audio file with word-level timestamps.
        
        Useful for advanced analysis like detecting pauses
        or word-by-word timing analysis.
        
        Args:
            audio_path: Path to the audio file
            language: Language code
            
        Returns:
            Dictionary containing full transcript and segments with timestamps
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            result = self.model.transcribe(
                audio_path,
                fp16=False,
                language=language,
                word_timestamps=True  # Enable word-level timestamps
            )
            
            return {
                "text": result.get("text", "").strip(),
                "segments": result.get("segments", []),
                "language": result.get("language", language)
            }
            
        except Exception as e:
            raise Exception(f"Failed to transcribe audio with timestamps: {str(e)}")
    
    def detect_language(self, audio_path: str) -> str:
        """
        Detect the spoken language in an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Detected language code (e.g., "en", "hi", "mr")
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Load audio and detect language
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            return detected_language
            
        except Exception as e:
            print(f"Language detection failed: {str(e)}")
            return "en"  # Default to English


# Singleton instance for reuse
_asr_service_instance = None

def get_asr_service(model_size: str = "base") -> ASRService:
    """
    Get singleton instance of ASR service.
    
    Args:
        model_size: Whisper model size
        
    Returns:
        ASRService instance
    """
    global _asr_service_instance
    if _asr_service_instance is None:
        _asr_service_instance = ASRService(model_size)
    return _asr_service_instance
