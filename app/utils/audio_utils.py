"""
Audio Processing Utilities
==========================
Handles audio file processing, format conversion, and duration calculation.

Supports:
- WAV and MP3 formats
- Audio format conversion
- Duration extraction
- Audio validation
"""

import os
import tempfile
from typing import Optional
from pathlib import Path

from pydub import AudioSegment
import soundfile as sf


class AudioProcessor:
    """
    Utility class for processing audio files.
    
    Handles audio format conversion and validation for
    speech recognition compatibility.
    """
    
    # Supported input formats
    SUPPORTED_FORMATS = ['.wav', '.mp3']
    
    # Target format for Whisper (WAV with specific parameters)
    TARGET_FORMAT = 'wav'
    TARGET_SAMPLE_RATE = 16000  # 16kHz recommended for Whisper
    TARGET_CHANNELS = 1  # Mono audio
    
    def __init__(self):
        """Initialize AudioProcessor."""
        pass
    
    def process_audio(self, audio_path: str) -> str:
        """
        Process audio file for speech recognition.
        
        Converts audio to WAV format with:
        - 16kHz sample rate
        - Mono channel
        - 16-bit PCM encoding
        
        Args:
            audio_path: Path to input audio file
            
        Returns:
            Path to processed audio file (may be same as input if already compatible)
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio format is not supported
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Get file extension
        file_ext = Path(audio_path).suffix.lower()
        
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {file_ext}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )
        
        # Load audio using pydub
        try:
            if file_ext == '.mp3':
                audio = AudioSegment.from_mp3(audio_path)
            elif file_ext == '.wav':
                audio = AudioSegment.from_wav(audio_path)
            else:
                audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            raise ValueError(f"Failed to load audio file: {str(e)}")
        
        # Check if conversion is needed
        needs_conversion = (
            audio.frame_rate != self.TARGET_SAMPLE_RATE or
            audio.channels != self.TARGET_CHANNELS or
            file_ext != '.wav'
        )
        
        if not needs_conversion:
            return audio_path
        
        # Convert audio
        processed_audio = self._convert_audio(audio)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.wav'
        )
        temp_path = temp_file.name
        temp_file.close()
        
        processed_audio.export(
            temp_path,
            format='wav',
            parameters=[
                '-ar', str(self.TARGET_SAMPLE_RATE),
                '-ac', str(self.TARGET_CHANNELS)
            ]
        )
        
        return temp_path
    
    def _convert_audio(self, audio: AudioSegment) -> AudioSegment:
        """
        Convert audio to target specifications.
        
        Args:
            audio: Pydub AudioSegment
            
        Returns:
            Converted AudioSegment
        """
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(self.TARGET_CHANNELS)
        
        # Resample to target sample rate
        if audio.frame_rate != self.TARGET_SAMPLE_RATE:
            audio = audio.set_frame_rate(self.TARGET_SAMPLE_RATE)
        
        return audio
    
    def get_duration(self, audio_path: str) -> Optional[float]:
        """
        Get duration of audio file in seconds.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or None if cannot be determined
        """
        if not os.path.exists(audio_path):
            return None
        
        try:
            # Try using soundfile first (faster for WAV)
            file_ext = Path(audio_path).suffix.lower()
            
            if file_ext == '.wav':
                info = sf.info(audio_path)
                return info.duration
            else:
                # Use pydub for other formats
                audio = AudioSegment.from_file(audio_path)
                return len(audio) / 1000.0  # Convert milliseconds to seconds
                
        except Exception as e:
            print(f"Warning: Could not determine audio duration: {str(e)}")
            return None
    
    def validate_audio(self, audio_path: str) -> dict:
        """
        Validate audio file and return its properties.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with validation results:
            - valid: Boolean indicating if file is valid
            - format: File format
            - duration: Duration in seconds
            - sample_rate: Sample rate in Hz
            - channels: Number of audio channels
            - error: Error message if invalid
        """
        result = {
            "valid": False,
            "format": None,
            "duration": None,
            "sample_rate": None,
            "channels": None,
            "error": None
        }
        
        if not os.path.exists(audio_path):
            result["error"] = "File does not exist"
            return result
        
        file_ext = Path(audio_path).suffix.lower()
        result["format"] = file_ext
        
        if file_ext not in self.SUPPORTED_FORMATS:
            result["error"] = f"Unsupported format: {file_ext}"
            return result
        
        try:
            audio = AudioSegment.from_file(audio_path)
            
            result["valid"] = True
            result["duration"] = len(audio) / 1000.0
            result["sample_rate"] = audio.frame_rate
            result["channels"] = audio.channels
            
            # Additional validation
            if result["duration"] < 0.5:
                result["valid"] = False
                result["error"] = "Audio is too short (less than 0.5 seconds)"
            
        except Exception as e:
            result["error"] = f"Failed to process audio: {str(e)}"
        
        return result
    
    def get_audio_info(self, audio_path: str) -> dict:
        """
        Get detailed information about an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        info = {
            "path": audio_path,
            "exists": os.path.exists(audio_path),
            "format": Path(audio_path).suffix.lower() if audio_path else None,
            "size_bytes": None,
            "duration_seconds": None,
            "sample_rate_hz": None,
            "channels": None,
            "bit_depth": None
        }
        
        if not info["exists"]:
            return info
        
        info["size_bytes"] = os.path.getsize(audio_path)
        
        try:
            audio = AudioSegment.from_file(audio_path)
            info["duration_seconds"] = len(audio) / 1000.0
            info["sample_rate_hz"] = audio.frame_rate
            info["channels"] = audio.channels
            info["bit_depth"] = audio.sample_width * 8
        except Exception:
            pass
        
        return info


# Singleton instance
_audio_processor_instance = None

def get_audio_processor() -> AudioProcessor:
    """
    Get singleton instance of AudioProcessor.
    
    Returns:
        AudioProcessor instance
    """
    global _audio_processor_instance
    if _audio_processor_instance is None:
        _audio_processor_instance = AudioProcessor()
    return _audio_processor_instance
