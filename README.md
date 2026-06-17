# contextai

A local project-to-AI interface for codebases and file trees.

Convert a real directory into a structured, AI-readable JSON representation, let an AI propose changes, and safely apply those changes back to your project.

## Overview

contextai is designed to bridge the gap between local development projects and web-based AI tools that don't have direct filesystem access. Instead of granting an AI agent direct control of your machine, contextai acts as a safe, controlled interface.

### Key Features

✅ **Scan & Export**: Convert your project into a structured `project.json` snapshot  
✅ **Safe Isolation**: AI operates only on JSON, never directly on your filesystem  
✅ **Structured Format**: Predictable schema makes changes reliable and validatable  
✅ **Automatic Backups**: Keep the last 5 snapshots for easy rollback  
✅ **File Filtering**: Ignore build artifacts, dependencies, and sensitive files  
✅ **Portable**: Works with any AI tool that reads JSON (web-based, offline, CLI)  

## Installation

1. Clone or download the contextai repository
2. Ensure Python 3.7+ is installed
3. No external dependencies required (pure Python)

```bash
cd contextai
```

## Quick Start

### Step 1: Initialize a Project

```bash
python3 contextai.py init /path/to/your/project
```

This creates a `.contextai/` directory inside your project to store metadata and backups.

### Step 2: Export to JSON

```bash
python3 contextai.py get /path/to/your/project
```

This generates `.contextai/project.json` containing your project structure and file contents.

### Step 3: Share with AI

1. Copy the contents of `project.json`
2. Read `.contextai/AIcontext.md` for instructions
3. Paste both into your AI tool
4. Ask the AI to modify the JSON

### Step 4: Apply Changes

After the AI returns a modified `project.json`:

```bash
python3 contextai.py apply /path/to/your/project /path/to/modified.json
```

This safely applies the changes back to your actual project files.

### Step 5: Restore if Needed

If something goes wrong, restore from a backup:

```bash
python3 contextai.py restore /path/to/your/project --backup project_20240617_143022.json
```

## Usage Examples

### Export with options

```bash
# Ignore node_modules
python3 contextai.py get /project --node

# Ignore specific patterns
python3 contextai.py get /project -I __pycache__ -I ".pytest_cache"

# Limit to 100 files
python3 contextai.py get /project --changelimit 100
```

### Dry-run before applying

```bash
# See what would change without actually changing
python3 contextai.py apply /project modified.json --dry-run
```

## Project Structure

After initialization, your project contains:

```
project/
├── .contextai/
│   ├── source/           # contextai internal logic
│   ├── backups/          # Previous snapshots
│   ├── project.json      # Current snapshot
│   └── AIcontext.md      # AI instructions
└── ... (your actual project files)
```

## Configuration

Edit `settings.py` to customize:

- `MAX_FILE_COUNT`: Maximum files to export (default: 500)
- `MAX_FILE_SIZE_MB`: Maximum file size to include content (default: 10 MB)
- `BACKUP_RETENTION_COUNT`: How many backups to keep (default: 5)
- `TEXT_EXTENSIONS`: Which file types are considered text
- `DEFAULT_IGNORE_PATTERNS`: Patterns to ignore by default

## Understanding project.json

The snapshot contains:

```json
{
  "schema_version": "1.0",
  "project": {
    "id": "abc123def456",
    "name": "my_project",
    "root": "/path/to/project"
  },
  "meta": {
    "created_at": "2026-06-17T12:30:45Z",
    "last_updated": "2026-06-17T12:30:45Z"
  },
  "tree": [
    {
      "id": "file_001",
      "path": "src/main.py",
      "type": "file",
      "format": "text/python",
      "size": 1234,
      "hash": "abc123...",
      "content": "# Python code here"
    },
    {
      "id": "dir_001",
      "path": "src",
      "type": "directory",
      "format": null,
      "size": 0
    }
  ]
}
```

### What the AI can modify

- ✅ File `content` (text files only)
- ✅ Create new files/directories
- ✅ Delete files/directories
- ✅ Rename files by changing `path`
- ✅ Add new items to the `tree` array

### What the AI should NOT modify

- ❌ The `schema_version` (must stay "1.0")
- ❌ The project `id` (must be unique per project)
- ❌ The `hash` field (recalculated on apply)
- ❌ Paths outside the project root
- ❌ File `id` values (must stay consistent)

## Safety Features

### Path Restrictions

- Projects must be initialized under `/home`
- AI cannot escape the project root
- All paths are validated before filesystem writes

### Backup System

- Every export creates a backup
- Last 5 snapshots always kept
- Restore any previous state instantly
- Large backups (>100KB) are compressed

### Validation

- JSON schema is validated before and after edits
- File operations are checked for safety
- Failed changes don't corrupt the project
- Clear error messages on problems

## Workflow Example

### Scenario: Fix typos and add logging

**Step 1**: Export your project
```bash
python3 contextai.py get /my_project
```

**Step 2**: Copy `project.json` to your AI

**Step 3**: Ask the AI:
```
Please fix all typos in docstrings and add debug logging to critical functions.
Keep the structure exactly as-is. Return the modified project.json.
```

**Step 4**: AI returns modified JSON

**Step 5**: Save modified JSON locally as `updated.json`

**Step 6**: Apply changes
```bash
python3 contextai.py apply /my_project updated.json
```

**Step 7**: Review changes in your editor

**Step 8**: If something went wrong, restore:
```bash
python3 contextai.py restore /my_project --backup project_20260617_143022.json
```

## Limitations

- Maximum file count: 500 (configurable)
- Maximum file size for content: 10 MB (configurable)
- Binary files not included in snapshot (only metadata)
- Text encoding: UTF-8 (with fallback handling)

## Future Ideas

- Function/class-level exports
- Dependency-aware packaging
- Change previews and diff viewers
- Schema versioning and migrations
- Project summaries for large repos
- AI-specific ignore profiles

## Security Notes

contextai prioritizes safety:

- No direct terminal access for AI
- No unrestricted filesystem operations
- All changes validated before application
- Automatic rollback capability via backups
- Clear audit trail in backup history

It's not a replacement for agent-based AI tools, but for cases where you want to use free/simple web-based AI with full control over changes.

## Troubleshooting

### "Not initialized" error
```bash
python3 contextai.py init /path/to/project
```

### "File limit exceeded"
```bash
python3 contextai.py get /path/to/project --changelimit 1000
```

### "Failed to apply changes"
1. Check the error message (usually indicates which file failed)
2. Validate the modified JSON is syntactically correct
3. Ensure all items have `id`, `path`, and `type`

### "Restore from backup"
```bash
ls /path/to/project/.contextai/backups/
python3 contextai.py restore /path/to/project --backup <backup_name>
```

## License

contextai is open source. See LICENSE file for details.

## Contributing

Contributions welcome! Areas for improvement:

- Performance optimization for large projects
- Additional file format handlers
- Better diff/preview features
- Integration with popular AI platforms
- Test suite expansion

---

**Questions?** Check `.contextai/AIcontext.md` after initialization for AI-specific guidance.
