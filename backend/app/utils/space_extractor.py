import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def extract_space_from_text(text: Optional[str]) -> Optional[str]:
    """
    Extract space name from text using the pattern #spacename:
    
    Args:
        text: The text to search for space pattern
        
    Returns:
        The extracted space name or None if no pattern found
        
    Examples:
        extract_space_from_text("This is about #books: machine learning") -> "books"
        extract_space_from_text("Regular text without pattern") -> None
        extract_space_from_text("#music: my favorite songs") -> "music"
    """
    if not text or not isinstance(text, str):
        return None
    
    # Pattern to match #spacename: where spacename can contain letters, numbers, underscores, hyphens
    pattern = r'#([a-zA-Z0-9_-]+):'
    
    try:
        match = re.search(pattern, text.strip())
        if match:
            space_name = match.group(1).lower().strip()
            # Validate space name (basic validation)
            if len(space_name) > 0 and len(space_name) <= 50:
                logger.info(f"Extracted space: '{space_name}' from text")
                return space_name
            else:
                logger.warning(f"Invalid space name length: '{space_name}'")
                return None
        return None
    except Exception as e:
        logger.error(f"Error extracting space from text: {str(e)}")
        return None

def remove_space_pattern_from_text(text: Optional[str]) -> Optional[str]:
    """
    Remove space pattern from text for clean searching
    
    Args:
        text: The text to clean
        
    Returns:
        Text with space pattern removed
        
    Examples:
        remove_space_pattern_from_text("This is about #books: machine learning") -> "This is about machine learning"
    """
    if not text or not isinstance(text, str):
        return text
    
    # Pattern to match #spacename: 
    pattern = r'#[a-zA-Z0-9_-]+:\s*'
    
    try:
        cleaned_text = re.sub(pattern, '', text).strip()
        return cleaned_text if cleaned_text else text
    except Exception as e:
        logger.error(f"Error removing space pattern from text: {str(e)}")
        return text 