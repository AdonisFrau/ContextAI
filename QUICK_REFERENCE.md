# contextai Quick Reference

## Installation
```bash
# No dependencies - just Python 3.7+
cd contextai
```

## Basic Commands

### Initialize
```bash
python3 contextai.py init /path/to/project
```
Creates `.contextai/` workspace. Run once per project.

### Export
```bash
python3 contextai.py get /path/to/project
```
Creates `project.json` snapshot. Re-run after AI modifications.

### Apply
```bash
python3 contextai.py apply /path/to/project /path/to/modified.json
```
Applies changes from JSON to real files.

### Restore
```bash
python3 contextai.py restore /path/to/project --backup project_20260617_143022.json
```
Restore from a previous backup snapshot.

## Workflow

```
1. init     → Create .contextai workspace
   ↓
2. get      → Export project to project.json
   ↓
3. [Copy project.json to AI tool]
   ↓
4. [AI modifies JSON]
   ↓
5. apply    → Apply changes to real project
   ↓
6. Done!    (or restore if needed)
```

## Export Flags

```bash
--node                  # Ignore node_modules
-I PATTERN              # Ignore specific pattern (repeatable)
--changelimit N         # Max N files to export
```

Example:
```bash
python3 contextai.py get /project --node -I __pycache__ --changelimit 100
```

## Apply Flags

```bash
--dry-run              # Preview changes without applying
```

Example:
```bash
python3 contextai.py apply /project modified.json --dry-run
```

## Common Operations

### Step-by-step: Fix typos with AI

```bash
# 1. Export project
python3 contextai.py get /my_project

# 2. Copy .contextai/project.json to AI tool
# 3. Copy .contextai/AIcontext.md to AI tool

# Paste into AI tool:
# "Fix all typos in comments and docstrings.
#  Keep structure exactly the same.
#  Return the modified project.json"

# 4. Save AI's response as updated.json

# 5. Preview changes
python3 contextai.py apply /my_project updated.json --dry-run

# 6. Apply changes
python3 contextai.py apply /my_project updated.json

# 7. Review in your editor
# Done!
```

### Step-by-step: Add new feature

```bash
# 1. Export
python3 contextai.py get /my_project

# 2. Ask AI to add feature
# "Add a new 'logging' module with debug and error functions.
#  Create logs/ directory.
#  Update main.py to import it.
#  Include docstrings.
#  Return modified project.json"

# 3. Save response as updated.json

# 4. Preview
python3 contextai.py apply /my_project updated.json --dry-run

# 5. Apply
python3 contextai.py apply /my_project updated.json

# 6. Test the new code
```

## Understanding project.json

### Structure
```json
{
  "schema_version": "1.0",
  "project": {
    "id": "unique_id",
    "name": "project_name",
    "root": "/absolute/path"
  },
  "meta": {
    "created_at": "ISO_TIMESTAMP",
    "last_updated": "ISO_TIMESTAMP"
  },
  "tree": [
    {
      "id": "file_id",
      "path": "relative/path.py",
      "type": "file|directory",
      "format": "text/python|binary/png",
      "size": 1234,
      "hash": "sha256...",
      "content": "..."  // text files only
    }
  ]
}
```

### What to modify
- ✅ `content` - file content
- ✅ `path` - rename (keep same `id`)
- ✅ Add items to `tree` - create files/dirs
- ✅ Remove items from `tree` - delete files/dirs

### What NOT to modify
- ❌ `schema_version` - must stay "1.0"
- ❌ `project.id` - must be unique
- ❌ `id` fields - must stay consistent
- ❌ `hash` field - auto-recalculated

## Files & Directories

After `init`, your project contains:

```
project/
├── .contextai/
│   ├── project.json     ← Current snapshot
│   ├── AIcontext.md     ← AI instructions
│   └── backups/         ← Previous snapshots
└── ... your files ...
```

## Settings

Edit `settings.py`:

```python
MAX_FILE_COUNT = 500          # Max files to export
MAX_FILE_SIZE_MB = 10         # Max file size to include
BACKUP_RETENTION_COUNT = 5    # Backups to keep
TEXT_EXTENSIONS = {'.py', ...}  # Text file types
DEFAULT_IGNORE_PATTERNS = {'__pycache__', ...}
```

## Backups

Backups are automatically created. List them:

```bash
ls /project/.contextai/backups/
```

Restore one:

```bash
python3 contextai.py restore /project --backup project_20260617_143022.json
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Not initialized" | Run `init` first |
| "File limit exceeded" | Use `--changelimit N` |
| "Apply failed" | Check JSON is valid and paths exist |
| "Want to revert" | Use `restore --backup <name>` |
| "JSON too large" | Increase limits in `settings.py` or use `--changelimit` |

## Tips

1. **Always preview first**: Use `--dry-run` before apply
2. **Export often**: Run `get` frequently to keep snapshots current
3. **Keep backups**: They're automatic, but be aware they exist
4. **Read AIcontext.md**: Share it with AI for better results
5. **Start small**: Ask AI for targeted changes, not everything
6. **Copy the format**: When asking AI, include examples of current code structure

## Examples

### For web projects
```bash
python3 contextai.py get /project --node -I dist -I build
```

### For Python projects
```bash
python3 contextai.py get /project -I __pycache__ -I .pytest_cache -I ".egg-info"
```

### For documentation updates
```bash
python3 contextai.py get /project -I src -I node_modules --changelimit 50
```

## Getting Help

1. Check `.contextai/AIcontext.md` for AI-specific rules
2. Read `README.md` for detailed documentation
3. Review error messages - they explain what went wrong
4. Check `settings.py` for configuration options

---

**Happy AI-assisted editing!** 🚀
