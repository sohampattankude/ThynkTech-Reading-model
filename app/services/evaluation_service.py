"""
Evaluation Service
==================
Calculates reading performance metrics based on text comparison results.

Metrics calculated:
- Accuracy: Percentage of correctly matched words
- Completeness: Percentage of reference text covered
- Fluency (WPM): Words per minute based on audio duration
- Suspicious flag: Detection of unusually fast reading
"""

from typing import Dict, Optional


class EvaluationService:
    """
    Service for calculating reading evaluation metrics.
    
    Evaluates student reading performance based on comparison
    results and audio characteristics.
    """
    
    # Standard WPM ranges for different reading levels
    WPM_RANGES = {
        "very_slow": (0, 60),
        "slow": (60, 100),
        "normal": (100, 160),
        "fast": (160, 200),
        "very_fast": (200, 250),
        "suspicious": (250, float('inf'))
    }
    
    # Thresholds for performance remarks
    ACCURACY_THRESHOLDS = {
        "excellent": 90,
        "good": 75,
        "average": 60,
        "needs_improvement": 40
    }
    
    def __init__(
        self, 
        suspicious_wpm_threshold: float = 250,
        min_completeness_for_valid: float = 20
    ):
        """
        Initialize EvaluationService.
        
        Args:
            suspicious_wpm_threshold: WPM above this is flagged as suspicious.
                                    Normal adult reading is 150-250 WPM.
                                    Speaking while reading is typically 100-160 WPM.
            min_completeness_for_valid: Minimum completeness % for valid evaluation
        """
        self.suspicious_wpm_threshold = suspicious_wpm_threshold
        self.min_completeness_for_valid = min_completeness_for_valid
    
    def evaluate(
        self, 
        comparison_result: Dict,
        audio_duration: float,
        word_count: int
    ) -> Dict:
        """
        Calculate all evaluation metrics.
        
        Args:
            comparison_result: Result dictionary from TextService.compare_texts()
            audio_duration: Duration of audio in seconds
            word_count: Number of words spoken by student
            
        Returns:
            Dictionary containing:
            - accuracy: Percentage of correctly matched words
            - completeness: Percentage of reference text covered
            - fluency_wpm: Words per minute
            - remarks: Performance feedback message
            - suspicious: Boolean flag for unusual reading speed
            - breakdown: Detailed metric breakdown
        """
        # Extract comparison data
        matched_words = comparison_result.get('matched_words', 0)
        total_student_words = comparison_result.get('total_student_words', 0)
        total_reference_words = comparison_result.get('total_reference_words', 1)
        
        # Calculate core metrics
        accuracy = self.calculate_accuracy(matched_words, total_student_words)
        completeness = self.calculate_completeness(matched_words, total_reference_words)
        fluency_wpm = self.calculate_fluency(word_count, audio_duration)
        
        # Check for suspicious reading speed
        is_suspicious = self.detect_suspicious_reading(fluency_wpm)
        
        # Generate performance remarks
        remarks = self.generate_remarks(
            accuracy=accuracy,
            completeness=completeness,
            fluency_wpm=fluency_wpm,
            is_suspicious=is_suspicious
        )
        
        return {
            "accuracy": accuracy,
            "completeness": completeness,
            "fluency_wpm": fluency_wpm,
            "remarks": remarks,
            "suspicious": is_suspicious,
            "breakdown": {
                "matched_words": matched_words,
                "total_student_words": total_student_words,
                "total_reference_words": total_reference_words,
                "exact_match_count": len(comparison_result.get('exact_matches', [])),
                "fuzzy_match_count": len(comparison_result.get('fuzzy_matches', [])),
                "reading_speed_category": self.categorize_speed(fluency_wpm)
            }
        }
    
    def calculate_accuracy(
        self, 
        matched_words: int, 
        total_student_words: int
    ) -> float:
        """
        Calculate accuracy percentage.
        
        Accuracy = (Matched Words / Total Student Words) * 100
        
        This measures how many of the words spoken by the student
        correctly match the reference text.
        
        Args:
            matched_words: Number of correctly matched words
            total_student_words: Total words spoken by student
            
        Returns:
            Accuracy percentage (0-100)
        """
        if total_student_words == 0:
            return 0.0
        
        accuracy = (matched_words / total_student_words) * 100
        return min(100.0, accuracy)  # Cap at 100%
    
    def calculate_completeness(
        self, 
        matched_words: int, 
        total_reference_words: int
    ) -> float:
        """
        Calculate completeness percentage.
        
        Completeness = (Matched Words / Total Reference Words) * 100
        
        This measures how much of the reference text the student covered.
        
        Args:
            matched_words: Number of correctly matched words
            total_reference_words: Total words in reference text
            
        Returns:
            Completeness percentage (0-100)
        """
        if total_reference_words == 0:
            return 0.0
        
        completeness = (matched_words / total_reference_words) * 100
        return min(100.0, completeness)  # Cap at 100%
    
    def calculate_fluency(
        self, 
        word_count: int, 
        audio_duration: float
    ) -> float:
        """
        Calculate fluency in words per minute (WPM).
        
        Fluency = (Word Count / Audio Duration in seconds) * 60
        
        Args:
            word_count: Number of words spoken
            audio_duration: Audio duration in seconds
            
        Returns:
            Words per minute
        """
        if audio_duration <= 0:
            return 0.0
        
        # Convert to words per minute
        wpm = (word_count / audio_duration) * 60
        return wpm
    
    def detect_suspicious_reading(self, fluency_wpm: float) -> bool:
        """
        Detect if reading speed is suspiciously fast.
        
        Very high WPM might indicate:
        - Pre-recorded audio
        - Text-to-speech
        - Playback at increased speed
        
        Args:
            fluency_wpm: Words per minute
            
        Returns:
            True if reading speed is suspicious
        """
        return fluency_wpm > self.suspicious_wpm_threshold
    
    def categorize_speed(self, fluency_wpm: float) -> str:
        """
        Categorize reading speed into descriptive category.
        
        Args:
            fluency_wpm: Words per minute
            
        Returns:
            Speed category string
        """
        for category, (low, high) in self.WPM_RANGES.items():
            if low <= fluency_wpm < high:
                return category
        return "unknown"
    
    def generate_remarks(
        self,
        accuracy: float,
        completeness: float,
        fluency_wpm: float,
        is_suspicious: bool
    ) -> str:
        """
        Generate human-readable performance feedback.
        
        Args:
            accuracy: Accuracy percentage
            completeness: Completeness percentage
            fluency_wpm: Words per minute
            is_suspicious: Whether reading speed is suspicious
            
        Returns:
            Performance remarks string
        """
        remarks_parts = []
        
        # Suspicious reading warning (highest priority)
        if is_suspicious:
            remarks_parts.append(
                "⚠️ Warning: Reading speed is unusually fast. "
                "This may indicate the audio was played back at increased speed."
            )
        
        # Accuracy feedback
        if accuracy >= self.ACCURACY_THRESHOLDS["excellent"]:
            remarks_parts.append("Excellent accuracy! Words are pronounced correctly.")
        elif accuracy >= self.ACCURACY_THRESHOLDS["good"]:
            remarks_parts.append("Good reading performance.")
        elif accuracy >= self.ACCURACY_THRESHOLDS["average"]:
            remarks_parts.append("Average performance. Practice pronunciation.")
        elif accuracy >= self.ACCURACY_THRESHOLDS["needs_improvement"]:
            remarks_parts.append("Needs improvement. Focus on reading clearly.")
        else:
            remarks_parts.append("Significant improvement needed. Practice reading aloud.")
        
        # Completeness feedback
        if completeness < 50:
            remarks_parts.append("Only partial text was read.")
        elif completeness < 80:
            remarks_parts.append("Most of the text was covered.")
        else:
            remarks_parts.append("Good coverage of the reference text.")
        
        # Fluency feedback
        speed_category = self.categorize_speed(fluency_wpm)
        if speed_category == "very_slow":
            remarks_parts.append("Reading pace is slow. Try to read more fluently.")
        elif speed_category == "slow":
            remarks_parts.append("Reading pace is slightly slow.")
        elif speed_category == "normal":
            remarks_parts.append("Reading pace is appropriate.")
        elif speed_category == "fast":
            remarks_parts.append("Good fluent reading pace!")
        elif speed_category == "very_fast":
            remarks_parts.append("Very fast reading. Ensure clarity isn't sacrificed for speed.")
        
        return " ".join(remarks_parts)
    
    def get_grade(self, accuracy: float, completeness: float) -> str:
        """
        Calculate overall grade based on metrics.
        
        Args:
            accuracy: Accuracy percentage
            completeness: Completeness percentage
            
        Returns:
            Grade string (A, B, C, D, F)
        """
        # Weighted average: 60% accuracy, 40% completeness
        overall_score = (accuracy * 0.6) + (completeness * 0.4)
        
        if overall_score >= 90:
            return "A"
        elif overall_score >= 80:
            return "B"
        elif overall_score >= 70:
            return "C"
        elif overall_score >= 60:
            return "D"
        else:
            return "F"


# Singleton instance
_evaluation_service_instance = None

def get_evaluation_service() -> EvaluationService:
    """
    Get singleton instance of EvaluationService.
    
    Returns:
        EvaluationService instance
    """
    global _evaluation_service_instance
    if _evaluation_service_instance is None:
        _evaluation_service_instance = EvaluationService()
    return _evaluation_service_instance
