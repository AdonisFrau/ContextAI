"""
contextai Utility Functions

Helper functions for path handling, hashing, validation, and common operations.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import settings


def get_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(filepath)


def should_ignore_path(filepath: str, ignore_patterns: Optional[Set[str]] = None) -> bool:
    """Check if a path should be ignored based on patterns"""
    if ignore_patterns is None:
        ignore_patterns = settings.DEFAULT_IGNORE_PATTERNS
    
    path_parts = Path(filepath).parts
    for part in path_parts:
        if part in ignore_patterns:
            return True
    return False


def is_hidden_file(filepath: str) -> bool:
    """Check if a file is hidden (starts with dot on Unix)"""
    return Path(filepath).name.startswith('.')


def get_relative_path(filepath: str, root: str) -> str:
    """Get relative path from root"""
    return os.path.relpath(filepath, root)


def get_absolute_path(relative_path: str, root: str) -> str:
    """Get absolute path from relative path and root"""
    return os.path.join(root, relative_path)


def is_safe_path(path: str, root: str) -> bool:
    """Check if a path is within the allowed root and doesn't use path traversal"""
    try:
        real_path = os.path.realpath(path)
        real_root = os.path.realpath(root)
        return real_path.startswith(real_root)
    except (OSError, ValueError):
        return False


def validate_json_schema(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate project.json schema correctness"""
    errors = []
    
    # Check required top-level keys
    required_keys = {'schema_version', 'project', 'meta', 'tree'}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - set(data.keys())
        errors.append(f"Missing required keys: {missing}")
    
    # Validate schema_version
    if data.get('schema_version') != settings.SCHEMA_VERSION:
        errors.append(f"Schema version mismatch. Expected {settings.SCHEMA_VERSION}, got {data.get('schema_version')}")
    
    # Validate project object
    project = data.get('project', {})
    project_required = {'id', 'name'}
    if not project_required.issubset(project.keys()):
        errors.append(f"Missing project fields: {project_required - set(project.keys())}")
    
    # Validate meta object
    meta = data.get('meta', {})
    if 'created_at' not in meta or 'last_updated' not in meta:
        errors.append("Missing meta fields: created_at and/or last_updated")
    
    # Validate tree array
    if not isinstance(data.get('tree'), list):
        errors.append("Tree must be a list")
    else:
        for idx, item in enumerate(data.get('tree', [])):
            item_errors = validate_tree_item(item, idx)
            errors.extend(item_errors)
    
    if errors:
        return False, "; ".join(errors)
    return True, None


def validate_tree_item(item: Dict[str, Any], idx: int) -> List[str]:
    """Validate a single tree item in project.json"""
    errors = []
    required = {'id', 'path', 'type'}
    
    if not required.issubset(item.keys()):
        missing = required - set(item.keys())
        errors.append(f"Tree item {idx} missing fields: {missing}")
    
    if item.get('type') not in {'file', 'directory'}:
        errors.append(f"Tree item {idx} has invalid type: {item.get('type')}")
    
    return errors


def timestamp_now() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + "Z"


def ensure_dir_exists(dirpath: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        Path(dirpath).mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        return False


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load and parse JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return None


def save_json_file(filepath: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """Save data as formatted JSON file"""
    try:
        ensure_dir_exists(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except IOError as e:
        return False


def read_file_content(filepath: str, max_size_mb: Optional[int] = None) -> Optional[str]:
    """Read text file content safely"""
    try:
        if max_size_mb is None:
            max_size_mb = settings.MAX_FILE_SIZE_MB
        
        file_size_mb = get_file_size(filepath) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return None
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except (IOError, OSError):
        return None


def write_file_content(filepath: str, content: str) -> bool:
    """Write text content to file"""
    try:
        ensure_dir_exists(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except IOError:
        return False
