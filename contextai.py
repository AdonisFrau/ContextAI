#!/usr/bin/env python3
"""
contextai - Local project-to-AI interface for codebases

A tool that converts a real directory into a structured, AI-readable representation,
lets an AI propose changes, and safely applies those changes back to the project.

Usage:
  python3 contextai.py init <dir>
  python3 contextai.py get <dir>
  python3 contextai.py apply <dir> <modified_json>
  python3 contextai.py restore <dir> --backup <backup_name>
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
from datetime import datetime
import settings
import utils
from compile import Compiler, CompileError


class ContextAI:
    """Main contextai application"""
    
    def __init__(self, project_root: str):
        """Initialize contextai with a project root"""
        self.project_root = os.path.abspath(project_root)
        self.contextai_dir = os.path.join(self.project_root, settings.CONTEXTAI_DIRNAME)
        self.source_dir = os.path.join(self.contextai_dir, settings.CONTEXTAI_SOURCE_DIR)
        self.backups_dir = os.path.join(self.contextai_dir, settings.CONTEXTAI_BACKUPS_DIR)
        self.project_json_path = os.path.join(self.contextai_dir, settings.CONTEXTAI_PROJECT_JSON)
        self.aicontext_md_path = os.path.join(self.contextai_dir, settings.CONTEXTAI_AICONTEXT_MD)
    
    def validate_root_directory(self) -> bool:
        """Check if project root is within allowed paths"""
        if not settings.is_allowed_root(self.project_root):
            print(f"❌ Error: Project must be initialized under {settings.ALLOWED_ROOT_PREFIX}")
            print(f"   Attempted: {self.project_root}")
            return False
        return True
    
    def init(self) -> bool:
        """Initialize a project for contextai"""
        print(f"📁 Initializing contextai for: {self.project_root}")
        
        # Validate directory exists
        if not os.path.isdir(self.project_root):
            print(f"❌ Error: Directory does not exist: {self.project_root}")
            return False
        
        # Check if already initialized
        if os.path.exists(self.contextai_dir):
            print(f"⚠️  Already initialized at {self.contextai_dir}")
            return True
        
        # Validate root path restriction
        if not self.validate_root_directory():
            return False
        
        try:
            # Create .contextai structure
            utils.ensure_dir_exists(self.source_dir)
            utils.ensure_dir_exists(self.backups_dir)
            
            # Copy settings and compile module to source
            self._setup_source_files()
            
            print(f"✅ Initialized contextai workspace at {self.contextai_dir}")
            return True
        except Exception as e:
            print(f"❌ Error during initialization: {str(e)}")
            return False
    
    def _setup_source_files(self):
        """Copy source files to .contextai/source/"""
        # For now, we'll create stub references
        # In production, these would be symlinks or copies of the actual modules
        pass
    
    def get(self, ignore_node_modules: bool = False, ignore_patterns: Optional[Set[str]] = None, 
            file_limit: Optional[int] = None) -> bool:
        """Export project to project.json"""
        print(f"📤 Exporting project: {self.project_root}")
        
        # Check if initialized
        if not os.path.exists(self.contextai_dir):
            print(f"❌ Error: Not initialized. Run 'init' first.")
            return False
        
        if file_limit is None:
            file_limit = settings.MAX_FILE_COUNT
        
        # Build ignore set
        ignore_set = set(settings.DEFAULT_IGNORE_PATTERNS)
        if ignore_node_modules:
            ignore_set.add('node_modules')
        if ignore_patterns:
            ignore_set.update(ignore_patterns)
        
        try:
            # Save backup of old project.json if it exists
            if os.path.exists(self.project_json_path):
                self._save_backup()
            
            # Scan project tree
            tree = self._scan_directory(self.project_root, ignore_set, file_limit)
            
            if tree is None:
                print(f"❌ Error: Failed to scan directory")
                return False
            
            # Create project.json structure
            project_data = {
                'schema_version': settings.SCHEMA_VERSION,
                'project': {
                    'id': self._generate_project_id(),
                    'name': os.path.basename(self.project_root),
                    'root': self.project_root
                },
                'meta': {
                    'created_at': utils.timestamp_now(),
                    'last_updated': utils.timestamp_now()
                },
                'tree': tree
            }
            
            # Validate before saving
            is_valid, error_msg = utils.validate_json_schema(project_data)
            if not is_valid:
                print(f"❌ Error: Generated invalid schema: {error_msg}")
                return False
            
            # Save project.json
            if utils.save_json_file(self.project_json_path, project_data):
                print(f"✅ Exported {len(tree)} items to {self.project_json_path}")
                
                # Generate AIcontext.md
                self._generate_aicontext()
                return True
            else:
                print(f"❌ Error: Failed to save project.json")
                return False
        
        except Exception as e:
            print(f"❌ Error during export: {str(e)}")
            return False
    
    def _scan_directory(self, root: str, ignore_patterns: Set[str], file_limit: int) -> Optional[List[Dict]]:
        """Recursively scan directory and build tree"""
        tree = []
        file_count = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=True):
                # Filter out ignored directories
                dirnames[:] = [d for d in dirnames if d not in ignore_patterns and not utils.is_hidden_file(d)]
                
                # Process directories
                for dirname in dirnames:
                    if file_count >= file_limit:
                        print(f"⚠️  File limit ({file_limit}) reached")
                        return tree
                    
                    dir_path = os.path.join(dirpath, dirname)
                    rel_path = utils.get_relative_path(dir_path, root)
                    
                    tree.append({
                        'id': self._generate_file_id(rel_path),
                        'path': rel_path.replace('\\', '/'),
                        'type': 'directory',
                        'format': None,
                        'size': 0
                    })
                    file_count += 1
                
                # Process files
                for filename in filenames:
                    if file_count >= file_limit:
                        print(f"⚠️  File limit ({file_limit}) reached")
                        return tree
                    
                    if utils.is_hidden_file(filename):
                        continue
                    
                    file_path = os.path.join(dirpath, filename)
                    rel_path = utils.get_relative_path(file_path, root)
                    
                    # Get file metadata
                    try:
                        file_size = utils.get_file_size(file_path)
                        file_hash = utils.get_file_hash(file_path)
                        is_text = settings.is_text_file(filename)
                        
                        item = {
                            'id': self._generate_file_id(rel_path),
                            'path': rel_path.replace('\\', '/'),
                            'type': 'file',
                            'format': self._get_file_format(filename),
                            'size': file_size,
                            'hash': file_hash
                        }
                        
                        # Include content for text files
                        if is_text:
                            content = utils.read_file_content(file_path)
                            if content is not None:
                                item['content'] = content
                        
                        tree.append(item)
                        file_count += 1
                    except Exception as e:
                        print(f"⚠️  Skipped {rel_path}: {str(e)}")
            
            return tree
        except Exception as e:
            print(f"❌ Scan error: {str(e)}")
            return None
    
    def apply(self, modified_json_path: str, dry_run: bool = False) -> bool:
        """Apply changes from modified JSON"""
        print(f"📥 Applying changes to: {self.project_root}")
        
        # Check if initialized
        if not os.path.exists(self.project_json_path):
            print(f"❌ Error: Project not initialized. Run 'init' and 'get' first.")
            return False
        
        try:
            # Load modified JSON
            if not os.path.exists(modified_json_path):
                print(f"❌ Error: Modified JSON not found: {modified_json_path}")
                return False
            
            modified_data = utils.load_json_file(modified_json_path)
            if modified_data is None:
                print(f"❌ Error: Failed to parse modified JSON")
                return False
            
            # Load original JSON
            original_data = utils.load_json_file(self.project_json_path)
            
            # Create compiler and apply
            compiler = Compiler(self.project_root)
            success, error_msg, changes = compiler.apply_changes(modified_data, original_data, dry_run=dry_run)
            
            if dry_run:
                print(f"🔍 Dry run results:")
                print(f"  Created: {len(changes.get('created', []))}")
                print(f"  Modified: {len(changes.get('modified', []))}")
                print(f"  Deleted: {len(changes.get('deleted', []))}")
                print(f"  Renamed: {len(changes.get('renamed', []))}")
                return True
            
            if success:
                # Save new project.json
                if utils.save_json_file(self.project_json_path, modified_data):
                    print(f"✅ Changes applied successfully")
                    print(f"  Created: {changes.get('created', 0)}")
                    print(f"  Modified: {changes.get('modified', 0)}")
                    print(f"  Deleted: {changes.get('deleted', 0)}")
                    print(f"  Renamed: {changes.get('renamed', 0)}")
                    return True
            else:
                print(f"❌ Error applying changes: {error_msg}")
                return False
        
        except Exception as e:
            print(f"❌ Error during apply: {str(e)}")
            return False
    
    def restore(self, backup_name: str) -> bool:
        """Restore from a backup"""
        print(f"🔄 Restoring backup: {backup_name}")
        
        backup_path = os.path.join(self.backups_dir, backup_name)
        if not os.path.exists(backup_path):
            print(f"❌ Error: Backup not found: {backup_name}")
            return False
        
        try:
            # For now, just restore the backup to project.json
            shutil.copy(backup_path, self.project_json_path)
            print(f"✅ Restored from backup: {backup_name}")
            return True
        except Exception as e:
            print(f"❌ Error restoring backup: {str(e)}")
            return False
    
    def _save_backup(self) -> bool:
        """Save current project.json as a backup"""
        try:
            # Generate backup name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"project_{timestamp}.json"
            backup_path = os.path.join(self.backups_dir, backup_name)
            
            utils.ensure_dir_exists(self.backups_dir)
            shutil.copy(self.project_json_path, backup_path)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            return True
        except Exception as e:
            print(f"⚠️  Failed to save backup: {str(e)}")
            return False
    
    def _cleanup_old_backups(self):
        """Keep only the last N backups"""
        try:
            backups = sorted(os.listdir(self.backups_dir))
            if len(backups) > settings.BACKUP_RETENTION_COUNT:
                for old_backup in backups[:-settings.BACKUP_RETENTION_COUNT]:
                    os.remove(os.path.join(self.backups_dir, old_backup))
        except Exception as e:
            print(f"⚠️  Failed to cleanup backups: {str(e)}")
    
    def _generate_project_id(self) -> str:
        """Generate a unique project ID"""
        import hashlib
        hash_input = f"{self.project_root}{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _generate_file_id(self, filepath: str) -> str:
        """Generate a consistent file ID"""
        import hashlib
        return hashlib.md5(filepath.encode()).hexdigest()[:12]
    
    def _get_file_format(self, filename: str) -> str:
        """Determine file format/mimetype"""
        ext = Path(filename).suffix.lower()
        
        if ext in settings.TEXT_FORMATS:
            return f"text/{ext[1:]}"
        elif ext in settings.BINARY_EXTENSIONS:
            return f"binary/{ext[1:]}"
        else:
            return "application/octet-stream"
    
    def _generate_aicontext(self) -> bool:
        """Generate AIcontext.md file"""
        try:
            content = """# AI Context for contextai Project

## What is contextai?

contextai is a local project-to-AI interface. It converts a real directory on disk into a structured, AI-readable JSON snapshot, lets an AI propose changes to that snapshot, and then safely applies those changes back to the original project.

## How to interpret project.json

The `project.json` file contains:

- **schema_version**: The version of the contextai schema (currently "1.0")
- **project**: Metadata about the project (id, name, root path)
- **meta**: Timestamps for when the snapshot was created and last updated
- **tree**: An array of all files and directories in the project

### Tree items

Each item in the tree has:
- **id**: A unique identifier for this item
- **path**: Relative path from project root (using forward slashes)
- **type**: Either "file" or "directory"
- **format**: The file type or MIME type (e.g., "text/python", "binary/png")
- **size**: File size in bytes
- **hash**: SHA256 hash of the file content (for verification)
- **content**: (Text files only) The full file content as a string

## How to propose changes

You can modify `project.json` by:

1. **Editing file content**: Change the `content` field of text files
2. **Creating new files**: Add new items to the `tree` array with `type: "file"`
3. **Creating directories**: Add items with `type: "directory"`
4. **Deleting files/folders**: Remove items from the `tree` array
5. **Renaming**: Change the `path` of an item (keep the `id` the same)

## Important rules

⚠️  **DO NOT**:
- Invent new paths that don't make sense in the project structure
- Change the project `id` or `schema_version`
- Introduce unsupported file formats
- Use absolute paths; always use relative paths from the project root
- Add or modify items outside the allowed project tree

✅ **DO**:
- Keep changes minimal unless asked to do major refactoring
- Preserve the schema structure exactly
- Use consistent indentation and formatting
- Include `id`, `path`, and `type` for every tree item
- Maintain the logical structure of the project

## Example change

To modify a Python file:

```json
{
  "id": "file_123abc",
  "path": "src/main.py",
  "type": "file",
  "format": "text/python",
  "size": 2048,
  "hash": "...",
  "content": "# Updated content here\\nprint('hello')"
}
```

To create a new file:

```json
{
  "id": "file_new456",
  "path": "docs/readme.md",
  "type": "file",
  "format": "text/markdown",
  "size": 0,
  "hash": "",
  "content": "# New documentation"
}
```

## Validation

After you modify the snapshot:
1. Ensure all required fields are present
2. Check that the JSON is valid
3. Don't leave any items with missing `id`, `path`, or `type`
4. Make sure all paths use forward slashes

If the JSON is invalid, the apply step will fail and the original project is unchanged.

## Backups

Every time a snapshot is exported or changes are applied, contextai keeps automatic backups.
The last 5 backups are always kept, so if something goes wrong, you can restore from a previous state.

---

Good luck editing!
"""
            return utils.write_file_content(self.aicontext_md_path, content)
        except Exception as e:
            print(f"⚠️  Failed to generate AIcontext.md: {str(e)}")
            return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='contextai - Local project-to-AI interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 contextai.py init /path/to/project
  python3 contextai.py get /path/to/project
  python3 contextai.py apply /path/to/project modified.json
  python3 contextai.py restore /path/to/project --backup project_backup.json
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize a project')
    init_parser.add_argument('directory', help='Project directory')
    
    # get command
    get_parser = subparsers.add_parser('get', help='Export project to JSON')
    get_parser.add_argument('directory', help='Project directory')
    get_parser.add_argument('--node', action='store_true', help='Ignore node_modules')
    get_parser.add_argument('-I', '--ignore', action='append', help='Ignore patterns (can be used multiple times)')
    get_parser.add_argument('--changelimit', type=int, help='Max files to export')
    
    # apply command
    apply_parser = subparsers.add_parser('apply', help='Apply changes from modified JSON')
    apply_parser.add_argument('directory', help='Project directory')
    apply_parser.add_argument('json', help='Path to modified project.json')
    apply_parser.add_argument('--dry-run', action='store_true', help='Show what would change without applying')
    
    # restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('directory', help='Project directory')
    restore_parser.add_argument('--backup', required=True, help='Backup filename to restore')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'init':
            app = ContextAI(args.directory)
            return 0 if app.init() else 1
        
        elif args.command == 'get':
            app = ContextAI(args.directory)
            ignore_patterns = set(args.ignore) if args.ignore else None
            return 0 if app.get(
                ignore_node_modules=args.node,
                ignore_patterns=ignore_patterns,
                file_limit=args.changelimit
            ) else 1
        
        elif args.command == 'apply':
            app = ContextAI(args.directory)
            return 0 if app.apply(args.json, dry_run=args.dry_run) else 1
        
        elif args.command == 'restore':
            app = ContextAI(args.directory)
            return 0 if app.restore(args.backup) else 1
    
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
