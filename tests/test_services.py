"""
Test Suite for Reading Evaluation Module
=========================================
Unit tests for verifying the functionality of services.

Run tests with: pytest tests/test_services.py -v
"""

import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.text_service import TextService
from app.services.evaluation_service import EvaluationService
from app.services.chapter_service import ChapterService


class TestTextService:
    """Test cases for TextService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.text_service = TextService(fuzzy_threshold=80)
    
    def test_normalize_basic(self):
        """Test basic text normalization."""
        input_text = "Hello, World! How are you?"
        expected = "hello world how are you"
        result = self.text_service.normalize(input_text)
        assert result == expected
    
    def test_normalize_extra_spaces(self):
        """Test removal of extra spaces."""
        input_text = "Hello    World   Test"
        expected = "hello world test"
        result = self.text_service.normalize(input_text)
        assert result == expected
    
    def test_normalize_punctuation(self):
        """Test punctuation removal."""
        input_text = "Hello! What's up? Let's go."
        # Apostrophes are kept for contractions
        expected = "hello what's up let's go"
        result = self.text_service.normalize(input_text)
        assert result == expected
    
    def test_normalize_empty(self):
        """Test empty string normalization."""
        assert self.text_service.normalize("") == ""
        assert self.text_service.normalize(None) == ""
    
    def test_tokenize(self):
        """Test text tokenization."""
        input_text = "hello world test"
        expected = ["hello", "world", "test"]
        result = self.text_service.tokenize(input_text)
        assert result == expected
    
    def test_tokenize_empty(self):
        """Test empty string tokenization."""
        assert self.text_service.tokenize("") == []
        assert self.text_service.tokenize(None) == []
    
    def test_compare_texts_exact_match(self):
        """Test comparison with exact matching text."""
        student = "hello world test"
        reference = "hello world test"
        
        result = self.text_service.compare_texts(student, reference)
        
        assert result['matched_words'] == 3
        assert result['total_student_words'] == 3
        assert result['total_reference_words'] == 3
        assert len(result['exact_matches']) == 3
    
    def test_compare_texts_partial_match(self):
        """Test comparison with partial matching text."""
        student = "hello world"
        reference = "hello world test example"
        
        result = self.text_service.compare_texts(student, reference)
        
        assert result['matched_words'] == 2
        assert result['total_student_words'] == 2
        assert result['total_reference_words'] == 4
    
    def test_compare_texts_fuzzy_match(self):
        """Test fuzzy matching for similar words."""
        student = "helo wrold"  # Typos
        reference = "hello world"
        
        result = self.text_service.compare_texts(student, reference, use_fuzzy=True)
        
        # Should match via fuzzy matching
        assert result['matched_words'] >= 1  # At least one fuzzy match


class TestEvaluationService:
    """Test cases for EvaluationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluation_service = EvaluationService()
    
    def test_calculate_accuracy_full(self):
        """Test accuracy calculation with full match."""
        accuracy = self.evaluation_service.calculate_accuracy(10, 10)
        assert accuracy == 100.0
    
    def test_calculate_accuracy_partial(self):
        """Test accuracy calculation with partial match."""
        accuracy = self.evaluation_service.calculate_accuracy(8, 10)
        assert accuracy == 80.0
    
    def test_calculate_accuracy_zero(self):
        """Test accuracy calculation with zero words."""
        accuracy = self.evaluation_service.calculate_accuracy(0, 0)
        assert accuracy == 0.0
    
    def test_calculate_completeness(self):
        """Test completeness calculation."""
        completeness = self.evaluation_service.calculate_completeness(15, 20)
        assert completeness == 75.0
    
    def test_calculate_fluency(self):
        """Test fluency (WPM) calculation."""
        # 120 words in 60 seconds = 120 WPM
        fluency = self.evaluation_service.calculate_fluency(120, 60)
        assert fluency == 120.0
    
    def test_calculate_fluency_zero_duration(self):
        """Test fluency with zero duration."""
        fluency = self.evaluation_service.calculate_fluency(100, 0)
        assert fluency == 0.0
    
    def test_detect_suspicious_normal(self):
        """Test suspicious detection for normal speed."""
        is_suspicious = self.evaluation_service.detect_suspicious_reading(150)
        assert is_suspicious is False
    
    def test_detect_suspicious_fast(self):
        """Test suspicious detection for very fast speed."""
        is_suspicious = self.evaluation_service.detect_suspicious_reading(300)
        assert is_suspicious is True
    
    def test_categorize_speed(self):
        """Test speed categorization."""
        assert self.evaluation_service.categorize_speed(50) == "very_slow"
        assert self.evaluation_service.categorize_speed(80) == "slow"
        assert self.evaluation_service.categorize_speed(130) == "normal"
        assert self.evaluation_service.categorize_speed(180) == "fast"
        assert self.evaluation_service.categorize_speed(220) == "very_fast"
        assert self.evaluation_service.categorize_speed(300) == "suspicious"
    
    def test_get_grade(self):
        """Test grade calculation."""
        assert self.evaluation_service.get_grade(95, 90) == "A"
        assert self.evaluation_service.get_grade(85, 80) == "B"
        assert self.evaluation_service.get_grade(75, 70) == "C"
        assert self.evaluation_service.get_grade(65, 60) == "D"
        assert self.evaluation_service.get_grade(40, 30) == "F"
    
    def test_evaluate_full(self):
        """Test full evaluation pipeline."""
        comparison_result = {
            'matched_words': 40,
            'total_student_words': 50,
            'total_reference_words': 60,
            'exact_matches': ['word'] * 35,
            'fuzzy_matches': [('wrold', 'world', 85)] * 5
        }
        
        result = self.evaluation_service.evaluate(
            comparison_result=comparison_result,
            audio_duration=30,  # 30 seconds
            word_count=50
        )
        
        assert 'accuracy' in result
        assert 'completeness' in result
        assert 'fluency_wpm' in result
        assert 'remarks' in result
        assert 'suspicious' in result
        
        # Verify calculations
        assert result['accuracy'] == 80.0  # 40/50 * 100
        assert abs(result['completeness'] - 66.67) < 1  # 40/60 * 100
        assert result['fluency_wpm'] == 100.0  # 50 words / 0.5 minutes


class TestChapterService:
    """Test cases for ChapterService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use the default data path
        self.chapter_service = ChapterService()
    
    def test_list_chapters(self):
        """Test listing chapters."""
        chapters = self.chapter_service.list_chapters()
        
        assert isinstance(chapters, list)
        assert len(chapters) >= 1
        
        # Check structure of returned chapters
        for chapter in chapters:
            assert 'id' in chapter
            assert 'title' in chapter
            assert 'word_count' in chapter
    
    def test_get_chapter_text_exists(self):
        """Test getting text for existing chapter."""
        text = self.chapter_service.get_chapter_text('chapter_1')
        
        assert text is not None
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_get_chapter_text_not_exists(self):
        """Test getting text for non-existent chapter."""
        text = self.chapter_service.get_chapter_text('non_existent_chapter')
        assert text is None
    
    def test_get_chapter_details(self):
        """Test getting full chapter details."""
        chapter = self.chapter_service.get_chapter('chapter_1')
        
        assert chapter is not None
        assert 'id' in chapter
        assert 'title' in chapter
        assert 'text' in chapter


# Integration test example
class TestIntegration:
    """Integration tests for the evaluation pipeline."""
    
    def test_full_evaluation_pipeline(self):
        """Test the complete evaluation pipeline with sample data."""
        # Initialize services
        text_service = TextService()
        evaluation_service = EvaluationService()
        chapter_service = ChapterService()
        
        # Get reference text
        reference_text = chapter_service.get_chapter_text('chapter_1')
        assert reference_text is not None
        
        # Simulate student text (partial reading with some errors)
        student_text = "Reading is one of the most important skills that we learn in school"
        
        # Normalize texts
        normalized_student = text_service.normalize(student_text)
        normalized_reference = text_service.normalize(reference_text)
        
        # Compare texts
        comparison_result = text_service.compare_texts(
            student_text=normalized_student,
            reference_text=normalized_reference
        )
        
        # Evaluate
        result = evaluation_service.evaluate(
            comparison_result=comparison_result,
            audio_duration=10,  # Simulated 10 seconds
            word_count=len(normalized_student.split())
        )
        
        # Verify result structure
        assert 'accuracy' in result
        assert 'completeness' in result
        assert 'fluency_wpm' in result
        assert 'remarks' in result
        
        # Verify reasonable values
        assert 0 <= result['accuracy'] <= 100
        assert 0 <= result['completeness'] <= 100
        assert result['fluency_wpm'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
