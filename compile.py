"""
contextai Compiler

Core processing script that:
- Reads project.json
- Validates schema correctness
- Detects unsupported changes
- Applies edits to the real filesystem
- Rejects malformed JSON or invalid operations
- Prevents dangerous or out-of-scope file actions
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import settings
import utils


class CompileError(Exception):
    """Custom exception for compilation/application errors"""
    pass


class Compiler:
    """Handles validation and application of changes to the project"""
    
    def __init__(self, project_root: str):
        """
        Initialize the compiler with a project root
        
        Args:
            project_root: The root directory of the actual project
        """
        self.project_root = project_root
        self.contextai_dir = os.path.join(project_root, settings.CONTEXTAI_DIRNAME)
    
    def load_project_json(self, filepath: str) -> Dict[str, Any]:
        """Load and validate project.json"""
        if not os.path.exists(filepath):
            raise CompileError(f"project.json not found at {filepath}")
        
        data = utils.load_json_file(filepath)
        if data is None:
            raise CompileError(f"Failed to parse project.json: Invalid JSON")
        
        is_valid, error_msg = utils.validate_json_schema(data)
        if not is_valid:
            raise CompileError(f"Schema validation failed: {error_msg}")
        
        return data
    
    def validate_changes(self, modified_project: Dict[str, Any], original_project: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that changes are safe and supported
        
        Returns:
            (is_valid, error_message)
        """
        # Check schema is still valid
        is_valid, error_msg = utils.validate_json_schema(modified_project)
        if not is_valid:
            return False, error_msg
        
        # Check that project ID hasn't changed
        if modified_project['project']['id'] != original_project['project']['id']:
            return False, "Project ID cannot be changed"
        
        # Validate each tree item
        for idx, item in enumerate(modified_project.get('tree', [])):
            # Check for dangerous paths
            abs_path = utils.get_absolute_path(item['path'], self.project_root)
            if not utils.is_safe_path(abs_path, self.project_root):
                return False, f"Unsafe path detected: {item['path']}"
        
        return True, None
    
    def detect_changes(self, original_tree: List[Dict], modified_tree: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Detect what changed between original and modified trees
        
        Returns:
            Dict with keys 'created', 'modified', 'deleted'
        """
        original_by_id = {item['id']: item for item in original_tree}
        modified_by_id = {item['id']: item for item in modified_tree}
        original_by_path = {item['path']: item for item in original_tree}
        modified_by_path = {item['path']: item for item in modified_tree}
        
        changes = {
            'created': [],
            'modified': [],
            'deleted': [],
            'renamed': []
        }
        
        # Find created and modified items
        for item_id, modified_item in modified_by_id.items():
            if item_id not in original_by_id:
                changes['created'].append(modified_item)
            else:
                original_item = original_by_id[item_id]
                # Check if content changed
                if modified_item.get('content') != original_item.get('content'):
                    changes['modified'].append(modified_item)
                # Check if path changed (rename)
                if modified_item['path'] != original_item['path']:
                    changes['renamed'].append({
                        'old_path': original_item['path'],
                        'new_path': modified_item['path'],
                        'item': modified_item
                    })
        
        # Find deleted items
        for item_id, original_item in original_by_id.items():
            if item_id not in modified_by_id:
                changes['deleted'].append(original_item)
        
        return changes
    
    def apply_changes(self, project_json: Dict[str, Any], original_json: Dict[str, Any], dry_run: bool = False) -> Tuple[bool, Optional[str], Dict]:
        """
        Apply changes from modified project.json to the real filesystem
        
        Args:
            project_json: The modified project.json data
            original_json: The original project.json data
            dry_run: If True, only show what would change without applying
        
        Returns:
            (success, error_message, applied_changes)
        """
        try:
            # Validate changes first
            is_valid, error_msg = self.validate_changes(project_json, original_json)
            if not is_valid:
                return False, error_msg, {}
            
            # Detect what changed
            changes = self.detect_changes(original_json.get('tree', []), project_json.get('tree', []))
            
            if dry_run:
                return True, None, changes
            
            applied_changes = {
                'created': 0,
                'modified': 0,
                'deleted': 0,
                'renamed': 0,
                'errors': []
            }
            
            # Apply deletions first
            for item in changes['deleted']:
                try:
                    abs_path = utils.get_absolute_path(item['path'], self.project_root)
                    if os.path.exists(abs_path):
                        if os.path.isdir(abs_path):
                            shutil.rmtree(abs_path)
                        else:
                            os.remove(abs_path)
                        applied_changes['deleted'] += 1
                except Exception as e:
                    applied_changes['errors'].append(f"Failed to delete {item['path']}: {str(e)}")
            
            # Apply renames
            for rename in changes['renamed']:
                try:
                    old_abs_path = utils.get_absolute_path(rename['old_path'], self.project_root)
                    new_abs_path = utils.get_absolute_path(rename['new_path'], self.project_root)
                    if os.path.exists(old_abs_path):
                        utils.ensure_dir_exists(os.path.dirname(new_abs_path))
                        shutil.move(old_abs_path, new_abs_path)
                        applied_changes['renamed'] += 1
                except Exception as e:
                    applied_changes['errors'].append(f"Failed to rename {rename['old_path']}: {str(e)}")
            
            # Apply creations and modifications
            for item in changes['created'] + changes['modified']:
                try:
                    abs_path = utils.get_absolute_path(item['path'], self.project_root)
                    
                    if item['type'] == 'directory':
                        utils.ensure_dir_exists(abs_path)
                        if item in changes['created']:
                            applied_changes['created'] += 1
                        else:
                            applied_changes['modified'] += 1
                    
                    elif item['type'] == 'file':
                        utils.ensure_dir_exists(os.path.dirname(abs_path))
                        content = item.get('content', '')
                        utils.write_file_content(abs_path, content)
                        if item in changes['created']:
                            applied_changes['created'] += 1
                        else:
                            applied_changes['modified'] += 1
                except Exception as e:
                    applied_changes['errors'].append(f"Failed to write {item['path']}: {str(e)}")
            
            success = len(applied_changes['errors']) == 0
            error_msg = None
            if not success:
                error_msg = "; ".join(applied_changes['errors'])
            
            return success, error_msg, applied_changes
        
        except Exception as e:
            return False, f"Error during apply: {str(e)}", {}
