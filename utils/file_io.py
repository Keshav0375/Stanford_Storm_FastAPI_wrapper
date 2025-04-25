import json
import os
from typing import Dict, Any, Optional


def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read JSON file and handle serialization errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Handle case where file might have JSON objects on separate lines
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [json.loads(line) for line in f if line.strip()]
        except:
            pass
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")

    return {}


def read_text_file(file_path: str) -> str:
    """Read text file safely with multiple encoding fallbacks."""
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return ""

    # If all encodings fail, try binary mode and decode with errors='replace'
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            return content.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Failed to read file {file_path} with all encodings: {e}")
        return ""


def write_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Write data to JSON file safely."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing to JSON file {file_path}: {e}")


def write_text_file(text: str, file_path: str) -> None:
    """Write text to file safely."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"Error writing to text file {file_path}: {e}")


def write_str(s: str, file_path: str) -> None:
    """
    Enhanced version of write_str that creates directories and uses UTF-8 encoding.
    This replaces the STORM version of the same function.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(s)
    except Exception as e:
        print(f"Error writing string to file {file_path}: {e}")