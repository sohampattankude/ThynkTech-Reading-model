"""
API Routes Module
=================
Defines all API endpoints for the Reading Evaluation Module.

Endpoints:
- GET /health: Health check endpoint
- POST /assess/audio: Upload audio and evaluate reading performance
"""

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.asr_service import ASRService
from app.services.text_service import TextService
from app.services.evaluation_service import EvaluationService
from app.services.chapter_service import ChapterService
from app.utils.audio_utils import AudioProcessor

# Initialize router
router = APIRouter()

# Initialize services
asr_service = ASRService()
text_service = TextService()
evaluation_service = EvaluationService()
chapter_service = ChapterService()
audio_processor = AudioProcessor()


# ===================== Response Models =====================

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    message: str
    version: str


class TranscriptResponse(BaseModel):
    """Response model containing the transcribed text."""
    transcript: str


class EvaluationResponse(BaseModel):
    """Response model for reading evaluation results."""
    accuracy: float
    completeness: float
    fluency_wpm: float
    remarks: str
    transcript: Optional[str] = None
    suspicious: Optional[bool] = None
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Response model for error messages."""
    error: str
    detail: str


# ===================== API Endpoints =====================

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Check if the Reading Evaluation service is running."
)
async def health_check():
    """
    Health check endpoint to verify service availability.
    
    Returns:
        HealthResponse: Service status information
    """
    return HealthResponse(
        status="healthy",
        message="Reading Evaluation Module is running",
        version="1.0.0"
    )


@router.post(
    "/assess/audio",
    response_model=EvaluationResponse,
    tags=["Assessment"],
    summary="Assess Reading Performance",
    description="""
    Upload an audio file of a student reading a chapter and receive 
    evaluation metrics including accuracy, completeness, and fluency.
    
    Supported audio formats: .wav, .mp3
    """
)
async def assess_audio(
    audio: UploadFile = File(..., description="Audio file (.wav or .mp3) of student reading"),
    chapter_id: str = Form(..., description="ID of the chapter being read")
):
    """
    Evaluate student reading performance from uploaded audio.
    
    This endpoint performs the following pipeline:
    1. Validates and processes the uploaded audio file
    2. Converts speech to text using ASR (Whisper)
    3. Retrieves reference text for the specified chapter
    4. Normalizes and compares texts
    5. Calculates evaluation metrics
    
    Args:
        audio: Uploaded audio file (wav or mp3)
        chapter_id: Identifier for the chapter being read
        
    Returns:
        EvaluationResponse: Reading performance metrics
        
    Raises:
        HTTPException: If audio format is invalid or chapter not found
    """
    
    # Validate audio file format
    if audio.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided for audio file"
        )
    
    file_extension = os.path.splitext(audio.filename)[1].lower()
    if file_extension not in ['.wav', '.mp3']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio format: {file_extension}. Supported formats: .wav, .mp3"
        )
    
    # Retrieve reference text for the chapter
    reference_text = chapter_service.get_chapter_text(chapter_id)
    if reference_text is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID '{chapter_id}' not found"
        )
    
    # Create temporary file to store uploaded audio
    temp_file = None
    try:
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_extension
        ) as temp_file:
            content = await audio.read()
            
            # Check if audio file is empty
            if len(content) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded audio file is empty"
                )
            
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process audio (convert to required format if needed)
        processed_audio_path = audio_processor.process_audio(temp_file_path)
        
        # Get audio duration for fluency calculation
        audio_duration = audio_processor.get_duration(processed_audio_path)
        
        if audio_duration is None or audio_duration < 0.5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is too short or invalid"
            )
        
        # Convert speech to text using ASR
        transcript = asr_service.transcribe(processed_audio_path)
        
        if not transcript or transcript.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not transcribe any speech from the audio. Please ensure the audio contains clear speech."
            )
        
        # Normalize both texts for comparison
        normalized_transcript = text_service.normalize(transcript)
        normalized_reference = text_service.normalize(reference_text)
        
        # Perform text comparison and calculate metrics
        comparison_result = text_service.compare_texts(
            student_text=normalized_transcript,
            reference_text=normalized_reference
        )
        
        # Calculate evaluation metrics
        evaluation_result = evaluation_service.evaluate(
            comparison_result=comparison_result,
            audio_duration=audio_duration,
            word_count=len(normalized_transcript.split())
        )
        
        # Generate response
        return EvaluationResponse(
            accuracy=round(evaluation_result['accuracy'], 2),
            completeness=round(evaluation_result['completeness'], 2),
            fluency_wpm=round(evaluation_result['fluency_wpm'], 1),
            remarks=evaluation_result['remarks'],
            transcript=transcript,
            suspicious=evaluation_result.get('suspicious', False),
            details={
                "matched_words": comparison_result['matched_words'],
                "total_student_words": comparison_result['total_student_words'],
                "total_reference_words": comparison_result['total_reference_words'],
                "audio_duration_seconds": round(audio_duration, 2)
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the audio: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass  # Ignore cleanup errors
        
        # Cleanup processed audio if different from temp file
        if 'processed_audio_path' in locals() and processed_audio_path != temp_file_path:
            try:
                if os.path.exists(processed_audio_path):
                    os.unlink(processed_audio_path)
            except Exception:
                pass


@router.get(
    "/chapters",
    tags=["Chapters"],
    summary="List Available Chapters",
    description="Get a list of all available chapters for reading assessment."
)
async def list_chapters():
    """
    List all available chapters.
    
    Returns:
        List of chapter IDs and titles
    """
    chapters = chapter_service.list_chapters()
    return {"chapters": chapters}


@router.get(
    "/chapters/{chapter_id}",
    tags=["Chapters"],
    summary="Get Chapter Details",
    description="Get the details and text of a specific chapter."
)
async def get_chapter(chapter_id: str):
    """
    Get chapter details by ID.
    
    Args:
        chapter_id: The chapter identifier
        
    Returns:
        Chapter details including text
    """
    chapter = chapter_service.get_chapter(chapter_id)
    if chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID '{chapter_id}' not found"
        )
    return chapter
