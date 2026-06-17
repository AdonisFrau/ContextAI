# AI Context for contextai Project

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
  "content": "# Updated content here\nprint('hello')"
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
