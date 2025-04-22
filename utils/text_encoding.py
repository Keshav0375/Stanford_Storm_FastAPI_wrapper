import logging
from typing import Any, Dict, List, Union
import unicodedata
import re

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalize text by replacing problematic Unicode characters with their closest ASCII equivalents.
    This is more efficient than encoding/decoding and handles more edge cases.
    """
    if not isinstance(text, str):
        return text
    
    # First try to normalize the text using NFKC form
    normalized = unicodedata.normalize('NFKC', text)
    
    # Replace specific problematic characters
    replacements = {
        '\u20b9': 'Rs',  # Indian Rupee
        '\u20ac': 'EUR',  # Euro
        '\u00a3': 'GBP',  # British Pound
        '\u00a5': 'JPY',  # Japanese Yen
        '\u00a2': 'cents',  # Cent
        '\u00a9': '(c)',  # Copyright
        '\u00ae': '(R)',  # Registered
        '\u2122': '(TM)',  # Trademark
        '\u2022': '-',  # Bullet
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
        '\u00b0': ' degrees',  # Degree symbol
        '\u2026': '...',  # Ellipsis
        '\u2030': ' per mille',  # Per mille
        '\u2192': '->',  # Right arrow
        '\u2190': '<-',  # Left arrow
        '\u2191': '^',  # Up arrow
        '\u2193': 'v',  # Down arrow
        '\u25cf': '*',  # Black circle
        '\u2605': '*',  # Black star
        '\u2606': '*',  # White star
        '\u2713': 'check',  # Check mark
        '\u2717': 'x',  # Cross mark
    }

    for char, replacement in replacements.items():
        normalized = normalized.replace(char, replacement)

    normalized = re.sub(r'[\u0080-\uffff]', ' ', normalized)

    return normalized

def normalize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize all string values in a dictionary."""
    normalized = {}
    for key, value in data.items():
        if isinstance(value, str):
            normalized[key] = normalize_text(value)
        elif isinstance(value, dict):
            normalized[key] = normalize_dict(value)
        elif isinstance(value, list):
            normalized[key] = normalize_list(value)
        else:
            normalized[key] = value
    return normalized

def normalize_list(data: List[Any]) -> List[Any]:
    """Normalize all string values in a list."""
    normalized = []
    for item in data:
        if isinstance(item, str):
            normalized.append(normalize_text(item))
        elif isinstance(item, dict):
            normalized.append(normalize_dict(item))
        elif isinstance(item, list):
            normalized.append(normalize_list(item))
        else:
            normalized.append(item)
    return normalized

def safe_json_serialize(obj: Any) -> str:
    """Safely serialize an object to JSON with proper encoding handling."""
    import json
    try:
        return json.dumps(obj, ensure_ascii=False)
    except (UnicodeEncodeError, TypeError) as e:
        logger.warning(f"JSON serialization error: {str(e)}. Attempting to normalize data.")
        if isinstance(obj, dict):
            normalized = normalize_dict(obj)
        elif isinstance(obj, list):
            normalized = normalize_list(obj)
        elif isinstance(obj, str):
            normalized = normalize_text(obj)
        else:
            normalized = str(obj)
        return json.dumps(normalized, ensure_ascii=False) 