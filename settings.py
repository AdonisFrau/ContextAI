"""
contextai Settings and Configuration

Stores configuration values and flags such as:
- File limits
- Backup retention count
- Ignore rules
- Export rules
- Size thresholds
- Safety restrictions
- Allowed formats
"""

import os
from pathlib import Path

# Core Settings
MAX_FILE_COUNT = 500  # Default maximum number of files to export
MAX_FILE_SIZE_MB = 10  # Maximum size of a single file to include content
BACKUP_RETENTION_COUNT = 5  # Keep last 5 backups
BACKUP_COMPRESSION_THRESHOLD_KB = 100  # Compress backups over 100KB

# Directory Settings
CONTEXTAI_DIRNAME = ".contextai"
CONTEXTAI_SOURCE_DIR = "source"
CONTEXTAI_BACKUPS_DIR = "backups"
CONTEXTAI_PROJECT_JSON = "project.json"
CONTEXTAI_AICONTEXT_MD = "AIcontext.md"

# Path Restrictions
ALLOWED_ROOT_PREFIX = "/home"  # contextai should not initialize above /home

# File Type Rules
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.json', '.md', '.txt', '.html', '.css',
    '.java', '.xml', '.yaml', '.yml', '.c', '.cpp', '.sh', '.bat',
    '.go', '.rb', '.php', '.rs', '.swift', '.kt', '.scala', '.groovy',
    '.clj', '.cljs', '.vim', '.lua', '.pl', '.r', '.m', '.mm',
    '.h', '.hpp', '.hxx', '.h++', '.c++', '.cxx', '.cc', '.cs',
    '.vb', '.f90', '.f95', '.f03', '.f08', '.for', '.ftn',
    '.sql', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.py3',
    '.gitignore', '.gitattributes', '.dockerignore', '.env',
    '.env.example', '.eslintrc', '.prettierrc', '.babelrc',
    '.editorconfig', '.htaccess', '.htpasswd', '.nginx',
    '.dockerfile', '.makefile', '.cmake', '.gradle',
    '.properties', '.config', '.ini', '.conf', '.cfg',
    '.vue', '.jsx', '.tsx', '.elm', '.hx', '.ex', '.exs'
}

# Text-like formats that are technically graphical but still text
TEXT_LIKE_FORMATS = {'.svg', '.ppm'}

TEXT_FORMATS = TEXT_EXTENSIONS | TEXT_LIKE_FORMATS

# Binary formats (exclude from content)
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.tiff',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz', '.iso',
    '.exe', '.dll', '.so', '.dylib', '.o', '.a', '.lib',
    '.pyc', '.pyo', '.class', '.jar', '.war', '.ear', '.aar',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.odt', '.ods', '.odp', '.rtf', '.woff', '.woff2', '.ttf', '.otf',
    '.eot', '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv',
    '.wav', '.flac', '.aac', '.m4a', '.opus', '.weba'
}

# Directories to ignore by default
DEFAULT_IGNORE_PATTERNS = {
    '__pycache__',
    '.git',
    '.gitignore',
    'node_modules',
    '.venv',
    'venv',
    'env',
    '.env',
    '.pytest_cache',
    '.coverage',
    'dist',
    'build',
    '.egg-info',
    '.tox',
    '.mypy_cache',
    '.vscode',
    '.idea',
    '.DS_Store',
    'Thumbs.db',
    '.next',
    '.nuxt',
    '.cache',
    'target',
    '.gradle',
    '.m2'
}

# Schema Version
SCHEMA_VERSION = "1.0"

# Validation Rules
MAX_JSON_SIZE_MB = 50  # Maximum size of project.json to prevent bloat
MIN_BACKUP_INTERVAL_SECONDS = 1  # Minimum time between backups to prevent spam
ALLOWED_CHANGE_TYPES = {'create', 'edit', 'delete', 'rename', 'mkdir'}

# Safety Restrictions
FORBIDDEN_OPERATIONS = {
    '/etc',
    '/sys',
    '/proc',
    '/dev',
    '/root',
    '/var/log'
}

# Debug Mode
DEBUG = os.getenv('CONTEXTAI_DEBUG', 'false').lower() == 'true'


def get_default_ignore_list():
    """Get the default list of patterns to ignore"""
    return list(DEFAULT_IGNORE_PATTERNS)


def is_text_file(filename: str) -> bool:
    """Check if a file should be treated as text"""
    ext = Path(filename).suffix.lower()
    return ext in TEXT_FORMATS


def is_binary_file(filename: str) -> bool:
    """Check if a file should be treated as binary"""
    ext = Path(filename).suffix.lower()
    return ext in BINARY_EXTENSIONS


def is_allowed_root(path: str) -> bool:
    """Check if a path is within allowed root directories"""
    return path.startswith(ALLOWED_ROOT_PREFIX)
