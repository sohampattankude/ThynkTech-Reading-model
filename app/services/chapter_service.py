"""
Chapter Service
===============
Manages reference text storage and retrieval for chapters.

This service handles loading chapter data from JSON storage
and provides methods to query chapter content.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class ChapterService:
    """
    Service for managing chapter reference texts.
    
    Loads chapter data from a JSON file and provides
    methods to retrieve chapter content for evaluation.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize ChapterService.
        
        Args:
            data_path: Path to chapters.json file.
                      If None, uses default path in data/ directory.
        """
        if data_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            data_path = project_root / "data" / "chapters.json"
        
        self.data_path = Path(data_path)
        self._chapters_cache = None
    
    def _load_chapters(self) -> Dict:
        """
        Load chapters from JSON file.
        
        Returns:
            Dictionary of chapter data
            
        Raises:
            FileNotFoundError: If chapters.json doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if self._chapters_cache is not None:
            return self._chapters_cache
        
        if not self.data_path.exists():
            print(f"⚠️ Chapters file not found at {self.data_path}")
            print("Creating default chapters file...")
            self._create_default_chapters()
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._chapters_cache = data.get('chapters', {})
                return self._chapters_cache
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in chapters file: {e.msg}",
                e.doc,
                e.pos
            )
    
    def _create_default_chapters(self):
        """
        Create a default chapters.json file with sample content.
        """
        default_data = {
            "chapters": {
                "chapter_1": {
                    "id": "chapter_1",
                    "title": "Introduction to Reading",
                    "text": "Reading is one of the most important skills that we learn in school. It helps us understand the world around us and opens doors to new knowledge and experiences. When we read, our brain processes words and creates meaning from them. Good readers practice every day and enjoy exploring new books and stories."
                },
                "chapter_2": {
                    "id": "chapter_2",
                    "title": "The Water Cycle",
                    "text": "The water cycle is the continuous movement of water on, above, and below the surface of the Earth. Water evaporates from oceans, lakes, and rivers into the atmosphere. When the water vapor cools, it condenses into clouds. Eventually, the water falls back to Earth as precipitation, such as rain or snow. This cycle repeats endlessly, ensuring that water is constantly recycled on our planet."
                },
                "chapter_3": {
                    "id": "chapter_3",
                    "title": "Healthy Habits",
                    "text": "Maintaining healthy habits is essential for a happy and productive life. Eating nutritious foods gives our body the energy it needs. Regular exercise keeps our muscles and heart strong. Getting enough sleep helps our brain rest and recover. Drinking plenty of water keeps us hydrated throughout the day. These simple habits can make a big difference in how we feel."
                }
            }
        }
        
        # Ensure directory exists
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created default chapters file at {self.data_path}")
    
    def get_chapter_text(self, chapter_id: str) -> Optional[str]:
        """
        Get the text content of a specific chapter.
        
        Args:
            chapter_id: Unique identifier for the chapter
            
        Returns:
            Chapter text content, or None if not found
        """
        chapters = self._load_chapters()
        chapter = chapters.get(chapter_id)
        
        if chapter is None:
            return None
        
        return chapter.get('text', '')
    
    def get_chapter(self, chapter_id: str) -> Optional[Dict]:
        """
        Get full chapter details by ID.
        
        Args:
            chapter_id: Unique identifier for the chapter
            
        Returns:
            Chapter dictionary with id, title, and text
        """
        chapters = self._load_chapters()
        return chapters.get(chapter_id)
    
    def list_chapters(self) -> List[Dict]:
        """
        List all available chapters.
        
        Returns:
            List of dictionaries with chapter id and title
        """
        chapters = self._load_chapters()
        return [
            {
                "id": chapter_id,
                "title": chapter_data.get('title', 'Untitled'),
                "word_count": len(chapter_data.get('text', '').split())
            }
            for chapter_id, chapter_data in chapters.items()
        ]
    
    def add_chapter(
        self, 
        chapter_id: str, 
        title: str, 
        text: str
    ) -> bool:
        """
        Add a new chapter to the storage.
        
        Args:
            chapter_id: Unique identifier for the chapter
            title: Chapter title
            text: Chapter text content
            
        Returns:
            True if added successfully, False if ID already exists
        """
        chapters = self._load_chapters()
        
        if chapter_id in chapters:
            return False
        
        chapters[chapter_id] = {
            "id": chapter_id,
            "title": title,
            "text": text
        }
        
        # Save to file
        self._save_chapters(chapters)
        
        # Update cache
        self._chapters_cache = chapters
        
        return True
    
    def update_chapter(
        self, 
        chapter_id: str, 
        title: Optional[str] = None, 
        text: Optional[str] = None
    ) -> bool:
        """
        Update an existing chapter.
        
        Args:
            chapter_id: Chapter identifier
            title: New title (optional)
            text: New text content (optional)
            
        Returns:
            True if updated, False if chapter not found
        """
        chapters = self._load_chapters()
        
        if chapter_id not in chapters:
            return False
        
        if title is not None:
            chapters[chapter_id]['title'] = title
        
        if text is not None:
            chapters[chapter_id]['text'] = text
        
        self._save_chapters(chapters)
        self._chapters_cache = chapters
        
        return True
    
    def delete_chapter(self, chapter_id: str) -> bool:
        """
        Delete a chapter from storage.
        
        Args:
            chapter_id: Chapter identifier
            
        Returns:
            True if deleted, False if not found
        """
        chapters = self._load_chapters()
        
        if chapter_id not in chapters:
            return False
        
        del chapters[chapter_id]
        
        self._save_chapters(chapters)
        self._chapters_cache = chapters
        
        return True
    
    def _save_chapters(self, chapters: Dict):
        """
        Save chapters to JSON file.
        
        Args:
            chapters: Dictionary of chapter data
        """
        data = {"chapters": chapters}
        
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def reload_chapters(self):
        """
        Force reload chapters from file, clearing cache.
        """
        self._chapters_cache = None
        self._load_chapters()


# Singleton instance
_chapter_service_instance = None

def get_chapter_service(data_path: Optional[str] = None) -> ChapterService:
    """
    Get singleton instance of ChapterService.
    
    Args:
        data_path: Optional custom path to chapters.json
        
    Returns:
        ChapterService instance
    """
    global _chapter_service_instance
    if _chapter_service_instance is None:
        _chapter_service_instance = ChapterService(data_path)
    return _chapter_service_instance
