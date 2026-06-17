# contextai — Project Goal and System Specification

## Overview

contextai is a local project-to-AI interface for codebases and file trees. Its purpose is to convert a real directory on disk into a structured, AI-readable representation, let an AI propose changes in a controlled format, and then safely apply those changes back to the original project.

The core idea is simple:

1. Scan a project directory.
2. Export the project into a structured JSON snapshot.
3. Give that snapshot to an AI.
4. Let the AI edit the snapshot or generate a structured change set.
5. Apply those changes back to the original project through contextai.

contextai is designed to work as a local tool, not as a cloud service. It is meant to reduce friction when using web-based AI tools that do not have direct access to your filesystem, terminal, or IDE. Instead of letting an AI touch your machine directly, contextai acts as the bridge.

## Main Goal

The main goal of contextai is to make AI-assisted project editing safer, more portable, and easier to use with any AI model, including free web-based models that do not support agent access.

contextai should:

* Represent a project in a structured format that an AI can understand.
* Keep project data organized and reproducible.
* Prevent direct filesystem access by the AI.
* Allow controlled application of AI-made modifications.
* Preserve backups so changes can be reverted.
* Support large enough projects while still being practical for copy-paste workflows.

## Design Philosophy

contextai is built around a few important ideas:

### 1. The AI should not directly control the machine

The AI should not be able to freely run commands, access the terminal, or directly modify files. contextai keeps the AI outside the filesystem and only lets it work through a strict data format.

### 2. The project should be portable

A project snapshot should be easy to copy, share, store, and feed into any AI tool, even a web interface.

### 3. The format should be structured, not loose

Free-form natural language is unreliable. contextai should use a predictable schema so changes can be validated before being applied.

### 4. Backups are mandatory

Every meaningful state should be recoverable. If something breaks, the previous project snapshot must be available.

### 5. Simplicity matters

The system should stay lightweight and usable from the command line.

## Core Workflow

The intended workflow is:

### Step 1: Initialize a project

The user runs an init command on a chosen directory.

Example:

```bash
bash contextai.sh init <dir>
```

or

```bash
python3 contextai.py init <dir>
```

The exact entrypoint can be decided later, but the behavior should remain the same.

### Step 2: Create the hidden contextai workspace

Inside the target directory, contextai creates a hidden folder named `.contextai`.

This folder stores all contextai metadata, snapshots, settings, backups, and support files.

### Step 3: Export the project

When the user runs the get/export command, contextai scans the project root and generates or updates `project.json`.

Example:

```bash
bash contextai.sh get <dir>
```

If `.contextai` does not exist, the command should fail with a clear error.
If `.contextai` exists but is corrupted, the command should also fail safely.

### Step 4: Send the snapshot to an AI

The user copies the generated JSON or uses it as the basis for AI context. The AI reads the project snapshot and returns changes.

### Step 5: Apply the changes

After the AI returns a valid modified JSON or change set, contextai uses its compiler/apply script to validate and apply the changes back to the actual project files.

### Step 6: Store a backup

Before or during application, contextai saves the previous snapshot into the backup system so the user can restore it later if necessary.

## Directory Layout

When a project is initialized, `.contextai` should contain the following structure:

```text
.contextai/
├── source/
│   ├── compile.py
│   └── settings.py
├── backups/
├── project.json
├── AIcontext.md
└── (optional future metadata files)
```

### `source/`

This folder contains the internal logic needed for parsing, validation, export, and application.

#### `compile.py`

This is the core processing script. It should:

* Read `project.json`
* Validate schema correctness
* Detect unsupported changes
* Apply edits to the real filesystem
* Reject malformed JSON or invalid operations
* Prevent dangerous or out-of-scope file actions

#### `settings.py`

This stores configuration values and flags, such as:

* File limits
* Backup retention count
* Ignore rules
* Export rules
* Size thresholds
* Safety restrictions
* Allowed formats

### `project.json`

This is the main snapshot file. It stores the current project representation used by contextai.

It should contain:

* A project ID or identifier
* Project metadata
* Folder structure
* File entries
* File format/type information
* Checksums or hashes if needed
* Optional content for text-based files
* Instructions or validation metadata

### `backups/`

This folder stores previous versions of `project.json`.

The backup policy is that the last 5 JSON snapshots should be kept.

### `AIcontext.md`

This file explains what contextai is, what the project is, how the AI should interpret the snapshot, and how the AI should format modifications safely.

This file is meant to help any AI understand the rules of the system without needing extra explanation every time.

## `project.json` Purpose

The purpose of `project.json` is to be a structured, machine-readable snapshot of the project.

It should not merely be a dump of file contents. It should act more like an organized model of the repository.

It should include:

* The project root name
* A unique project identifier
* A version number for the schema
* A list of files and folders
* File IDs
* Relative paths
* File type metadata
* Whether a file is text or binary
* Content only for text files
* Optional size and checksum metadata
* Flags for ignored or excluded files

## Suggested JSON Structure

A simple conceptual example:

```json
{
  "schema_version": "1.0",
  "project": {
    "id": "project_001",
    "name": "my_project",
    "root": "/home/user/my_project"
  },
  "meta": {
    "created_at": "2026-06-17T00:00:00Z",
    "last_updated": "2026-06-17T00:00:00Z"
  },
  "tree": [
    {
      "id": "file_001",
      "path": "src/main.py",
      "type": "file",
      "format": "text/python",
      "size": 1234,
      "hash": "...",
      "content": "print('hello')"
    }
  ]
}
```

This is only a conceptual starting point. The final schema can be expanded or simplified later.

## File Type Rules

contextai should distinguish between file types so it knows what can safely be exported as content.

### Text files

Text files should be included with their readable content.

Examples:

* `.py`
* `.js`
* `.ts`
* `.json`
* `.md`
* `.txt`
* `.html`
* `.css`
* `.java`
* `.xml`
* `.yaml`
* `.yml`
* `.c`
* `.cpp`
* `.sh`
* `.bat` where relevant

### Allowed image-like text formats

Some formats are technically graphics-related but still text-readable and may be included as content.

Examples:

* `.svg`
* `.ppm`

These should be treated as text if they are plain text files.

### Binary files

Binary files should generally not be copied into the AI context as raw text.

Examples:

* `.png`
* `.jpg`
* `.jpeg`
* `.gif`
* `.webp`
* compiled executables
* object files
* archives unless explicitly handled

Instead, binary files should be represented as metadata entries only, such as:

* file name
* file type
* size
* checksum
* path

This helps keep the snapshot clean and readable.

## File Limit

The scan command should enforce a maximum file limit, defaulting to 500 files.

This limit is important because:

* huge projects become too large for AI context anyway
* scanning everything can become slow
* it prevents accidental export of massive directories
* it keeps contextai practical for copy-paste workflows

The limit should be adjustable through configuration or flags, but the default must stay safe.

## Root Directory Restriction

contextai should not allow initialization above `/home`.

This is a safety restriction that keeps the tool from operating in dangerous or too-broad filesystem areas.

The intent is to make sure the tool stays inside a user-safe working area and does not accidentally target system-level or unrestricted paths.

If the user attempts to initialize outside the allowed region, the command should fail with a clear error.

## Backup System

Backups are one of the most important parts of contextai.

### Backup policy

* Keep the last 5 backup snapshots.
* Every successful export or apply may update the backup trail.
* Backups should be named in a numbered format.

Example naming:

```text
1_backup_project.json
2_backup_project.json
3_backup_project.json
```

or another consistent numbering scheme.

### Backup compression threshold

If a JSON backup exceeds 100 KB, it should be compressed into a zip container.

This helps keep storage efficient and avoids unnecessary bloat.

### Backup selection

The user should be able to restore or reference a specific backup by name.

Example:

```bash
python3 contextai.py --backup <nameOfBackup>
```

This should allow the user to choose a specific historical snapshot instead of only using the latest one.

## `AIcontext.md` Purpose

`AIcontext.md` is a human-readable guidance file intended for the AI.

It should explain:

* What contextai is
* What the project represents
* How the JSON should be interpreted
* Which actions are allowed
* Which actions are forbidden
* How to modify files safely
* How to avoid breaking the schema
* How to return valid structured changes

This file acts like a built-in instruction pack for any AI model consuming the snapshot.

It should also mention:

* only modify what is requested
* do not invent paths that do not exist
* preserve the schema
* do not introduce unsupported formats
* keep changes minimal unless asked otherwise

## Export Behavior (`get`)

The `get` command should:

* verify `.contextai` exists
* verify the workspace is not corrupted
* scan the directory tree up to the file limit
* generate a fresh `project.json`
* update metadata
* optionally refresh backup state
* ignore unsupported or excluded paths

The export should overwrite the previous snapshot or replace it in a controlled way.

## Apply Behavior

The apply command is where contextai turns the AI’s output into actual filesystem changes.

The apply process should:

1. Load the modified JSON or patch description.
2. Validate the format strictly.
3. Reject malformed or unexpected structures.
4. Compare the requested changes with the real project structure.
5. Apply file additions, removals, and edits.
6. Save or rotate backups.
7. Confirm success or produce a clear error.

If the JSON format is incorrect, application must fail safely.

## Change Rules

contextai should allow only controlled changes.

The system should support:

* file content changes
* file creation
* file deletion
* path changes or renames
* folder structure edits

The system should be careful about what it accepts.

### Important limitation

The AI should not be able to freely invent arbitrary filesystem operations outside the allowed model. The tool should only accept changes that match the schema.

## Suggested Flags

The tool already has a few planned flags. These can be refined later.

### `--node`

Ignore `node_modules` and similar dependency directories.

This is important because those folders are usually huge and not useful for AI context.

### `-I`

Ignore one or more files or file patterns.

This could be used to exclude:

* specific files
* sensitive files
* build outputs
* generated files
* folders the user does not want included

### `--changelimit`

Change or cap the maximum file count that can be exported.

This should let users adjust the scan size when needed.

### Additional useful flags

Some extra flags may be useful later:

* `--dry-run` — show what would change without applying
* `--force` — bypass harmless prompts if safe
* `--restore <backup>` — restore from a chosen backup
* `--zip` — force compression for large snapshots
* `--text-only` — only include readable text files
* `--json-only` — export only JSON without extra docs

These are optional future ideas.

## Error Handling Requirements

contextai should fail clearly and safely in the following situations:

* `.contextai` is missing
* workspace files are corrupted
* `project.json` is invalid
* schema version is unsupported
* file limit is exceeded
* forbidden directory is targeted
* file type is unsupported
* backup storage fails
* apply conflicts with actual filesystem state

Every error should be understandable to the user.

## Security Considerations

Even though contextai is not a network service, it still needs careful handling.

The tool should protect against:

* accidental system-wide scans
* corrupted snapshots
* destructive apply operations
* malformed AI output
* dangerous path traversal
* unsupported binary injection into text context

contextai should always prefer safety over convenience.

## Why This Project Exists

The point of contextai is to make AI-assisted development more accessible to people who are using web-based or free-tier AI tools that cannot directly interact with a machine.

It is useful for:

* small and medium codebases
* local development
* privacy-conscious workflows
* offline or semi-manual AI editing
* copy-paste based AI assistance

It gives the user a way to let an AI help without turning that AI into a full agent with direct access to the system.

## What Makes contextai Different

contextai is not just another coding assistant.

It is trying to become a portable editing layer between a project and an AI model.

That makes it different from tools that:

* directly control terminals
* directly patch files
* require paid agent access
* depend on one specific AI provider
* assume direct IDE integration

contextai should work with any model that can read and produce structured text.

## Future Ideas

These are not required for the first version, but they are strong future directions:

* symbolic context extraction instead of full-file dumping
* function/class-level export
* dependency-aware export packages
* change preview / diff viewer
* rename detection
* partial apply mode
* restore-from-backup mode
* schema versioning and migration tools
* checksum validation on apply
* project summaries for large repos
* ignore profiles for common ecosystems
* one-click packaging for AI prompts

## Version 0 Focus

For the first version, the project should focus on only the essentials:

* initialize workspace
* create `.contextai`
* export to `project.json`
* store backups
* generate `AIcontext.md`
* validate incoming JSON
* apply edits safely
* support basic ignore rules
* enforce file limit and path restrictions

The first version does not need to be perfect. It only needs to be stable enough to prove the workflow.

## Final Vision

The final vision of contextai is a simple but powerful local tool that lets any AI assist with project editing without needing direct access to the machine.

It should feel like a bridge between:

* your project on disk
* a structured snapshot of that project
* an AI model that can reason about the snapshot
* a safe application layer that turns AI decisions into real changes

If it works well, contextai becomes a lightweight universal workflow for AI-assisted development.
