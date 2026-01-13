"""
Text Processing Service
=======================
Handles text normalization and comparison between student 
transcription and reference text.

This service provides:
- Text normalization (lowercase, punctuation removal, etc.)
- Text comparison using exact and fuzzy matching
- Word tokenization
"""

import re
import string
from typing import List, Dict, Tuple

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein


class TextService:
    """
    Service for text normalization and comparison.
    
    Provides methods to clean and compare student transcriptions
    against reference text for reading evaluation.
    """
    
    def __init__(self, fuzzy_threshold: int = 80):
        """
        Initialize TextService.
        
        Args:
            fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching.
                           Words with similarity >= threshold are considered matches.
                           Default is 80 (80% similar).
        """
        self.fuzzy_threshold = fuzzy_threshold
        
        # Punctuation to remove (keeping apostrophes for contractions)
        self.punctuation_pattern = re.compile(
            f"[{re.escape(string.punctuation.replace(chr(39), ''))}]"
        )
        
        # Pattern for multiple whitespaces
        self.whitespace_pattern = re.compile(r'\s+')
        
    def normalize(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Normalization steps:
        1. Convert to lowercase
        2. Remove punctuation (except apostrophes)
        3. Replace multiple whitespaces with single space
        4. Strip leading/trailing whitespace
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove punctuation (keep apostrophes for words like "don't")
        normalized = self.punctuation_pattern.sub(' ', normalized)
        
        # Replace multiple whitespaces with single space
        normalized = self.whitespace_pattern.sub(' ', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    def tokenize(self, text: str) -> List[str]:
        """
        Split text into word tokens.
        
        Args:
            text: Text to tokenize (should be normalized first)
            
        Returns:
            List of word tokens
        """
        if not text:
            return []
        
        # Split by whitespace and filter empty strings
        tokens = [word for word in text.split() if word]
        
        return tokens
    
    def compare_texts(
        self, 
        student_text: str, 
        reference_text: str,
        use_fuzzy: bool = True
    ) -> Dict:
        """
        Compare student text with reference text.
        
        Performs word-by-word comparison using exact matching
        and optionally fuzzy matching for words that don't match exactly.
        
        Args:
            student_text: Normalized student transcription
            reference_text: Normalized reference text
            use_fuzzy: Whether to use fuzzy matching for non-exact matches
            
        Returns:
            Dictionary containing comparison results:
            - matched_words: Number of correctly matched words
            - total_student_words: Total words spoken by student
            - total_reference_words: Total words in reference
            - exact_matches: Words that matched exactly
            - fuzzy_matches: Words that matched via fuzzy matching
            - unmatched_student: Words spoken but not in reference
            - unmatched_reference: Reference words not spoken
            - match_details: Detailed per-word match information
        """
        # Tokenize both texts
        student_tokens = self.tokenize(student_text)
        reference_tokens = self.tokenize(reference_text)
        
        # Track results
        matched_words = 0
        exact_matches = []
        fuzzy_matches = []
        unmatched_student = []
        match_details = []
        
        # Create a copy of reference tokens to track coverage
        reference_remaining = reference_tokens.copy()
        
        # Process each student word
        for student_word in student_tokens:
            match_found = False
            match_type = None
            matched_ref_word = None
            match_score = 0
            
            # Try exact matching first
            if student_word in reference_remaining:
                match_found = True
                match_type = "exact"
                matched_ref_word = student_word
                match_score = 100
                reference_remaining.remove(student_word)
                exact_matches.append(student_word)
                matched_words += 1
                
            # Try fuzzy matching if exact match not found
            elif use_fuzzy:
                best_match = None
                best_score = 0
                best_idx = -1
                
                # Find best fuzzy match in remaining reference words
                for idx, ref_word in enumerate(reference_remaining):
                    score = fuzz.ratio(student_word, ref_word)
                    if score > best_score:
                        best_score = score
                        best_match = ref_word
                        best_idx = idx
                
                # Accept match if above threshold
                if best_score >= self.fuzzy_threshold:
                    match_found = True
                    match_type = "fuzzy"
                    matched_ref_word = best_match
                    match_score = best_score
                    reference_remaining.pop(best_idx)
                    fuzzy_matches.append((student_word, best_match, best_score))
                    matched_words += 1
            
            # Track unmatched words
            if not match_found:
                unmatched_student.append(student_word)
            
            # Record match details
            match_details.append({
                "student_word": student_word,
                "matched": match_found,
                "match_type": match_type,
                "reference_word": matched_ref_word,
                "score": match_score
            })
        
        return {
            "matched_words": matched_words,
            "total_student_words": len(student_tokens),
            "total_reference_words": len(reference_tokens),
            "exact_matches": exact_matches,
            "fuzzy_matches": fuzzy_matches,
            "unmatched_student": unmatched_student,
            "unmatched_reference": reference_remaining,
            "match_details": match_details
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate overall similarity between two texts.
        
        Uses RapidFuzz's ratio for calculating similarity percentage.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-100)
        """
        if not text1 or not text2:
            return 0.0
        
        return fuzz.ratio(text1, text2)
    
    def get_levenshtein_distance(self, word1: str, word2: str) -> int:
        """
        Calculate Levenshtein edit distance between two words.
        
        Useful for detailed analysis of mispronunciations.
        
        Args:
            word1: First word
            word2: Second word
            
        Returns:
            Number of edits (insertions, deletions, substitutions)
            required to transform word1 into word2
        """
        return Levenshtein.distance(word1, word2)
    
    def get_word_order_accuracy(
        self, 
        student_tokens: List[str], 
        reference_tokens: List[str]
    ) -> float:
        """
        Calculate how well the student maintained word order.
        
        Uses longest common subsequence to measure order preservation.
        
        Args:
            student_tokens: List of student word tokens
            reference_tokens: List of reference word tokens
            
        Returns:
            Order accuracy percentage (0-100)
        """
        if not student_tokens or not reference_tokens:
            return 0.0
        
        # Calculate LCS length
        lcs_length = self._longest_common_subsequence(
            student_tokens, 
            reference_tokens
        )
        
        # Calculate order accuracy based on LCS
        max_possible = min(len(student_tokens), len(reference_tokens))
        if max_possible == 0:
            return 0.0
        
        return (lcs_length / max_possible) * 100
    
    def _longest_common_subsequence(
        self, 
        seq1: List[str], 
        seq2: List[str]
    ) -> int:
        """
        Calculate length of longest common subsequence.
        
        Dynamic programming approach for finding LCS.
        
        Args:
            seq1: First sequence
            seq2: Second sequence
            
        Returns:
            Length of LCS
        """
        m, n = len(seq1), len(seq2)
        
        # Create DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Fill the table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        
        return dp[m][n]


# Singleton instance
_text_service_instance = None

def get_text_service(fuzzy_threshold: int = 80) -> TextService:
    """
    Get singleton instance of TextService.
    
    Args:
        fuzzy_threshold: Minimum similarity for fuzzy matching
        
    Returns:
        TextService instance
    """
    global _text_service_instance
    if _text_service_instance is None:
        _text_service_instance = TextService(fuzzy_threshold)
    return _text_service_instance
