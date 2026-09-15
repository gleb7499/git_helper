# Automatic Linter Selection - Change Summary

## What Changed

### 1. New methods in `git_docker_utils.py`

#### `get_extension_to_linter_mapping()`
Maps file extensions to super-linter linters:
- `.md` → Markdown
- `.js, .jsx` → JavaScript
- `.py` → Python (Pylint + Flake8)
- `.html` → HTML
- `.css` → CSS
- `.json` → JSON
- `.yml, .yaml` → YAML
- `.ts, .tsx` → TypeScript
- `.xml` → XML
- `.sql` → SQL
- And others...

#### `scan_directory_for_file_types(directory)`
Recursively scans a folder and counts files by extension:
- Walks all files in subdirectories
- Counts the number of files of each type
- Skips hidden files and files without extensions
- Returns `{extension: count}`

#### `detect_linters_from_files(directory)`
Main automatic detection function:
- Scans the directory
- Maps extensions to linters
- Returns a list of unique linters and file statistics

#### `get_linter_description(linter_code)`
Returns a human-readable linter description:
- `"MARKDOWN"` → `"Markdown"`
- `"JAVASCRIPT_ES"` → `"JavaScript/ES"`
- Etc.

### 2. Updated `run_linter.py`

#### Removed
- ❌ Manual linter selection via menu
- ❌ Entering comma-separated numbers

#### Added
- ✅ Automatic file scanning
- ✅ File type detection
- ✅ Automatic linter selection
- ✅ File statistics output
- ✅ List of automatically selected linters

#### New process (6 steps instead of 5)
1. Docker check
2. Enter folder path
3. Find Git repository root
4. Configuration check
5. **Automatic file analysis and linter selection** ← NEW
6. Confirmation and launch

### 3. Updated documentation

File `doc/LINTER_GUIDE.md`:
- Describes the new automatic process
- Lists supported extensions
- Includes a statistics output example
- Updated step numbering

## Example Output

```
🔹 Step 5/6: Analyzing files and selecting linters

⏳ Scanning files in folder...

📊 File statistics:
   .md             — 5 file(s)
   .html           — 3 file(s)
   .css            — 2 file(s)
   .js             — 1 file(s)

🔍 Automatically selected linters: 4
   ✓ Markdown
   ✓ HTML
   ✓ CSS/SCSS
   ✓ JavaScript/ES

────────────────────────────────────────────────────────────
📋 Launch parameters:
   Repository: C:\...\WT-AC-2025 (Kotkovets)
   Checked folder: students/KotkovetsKirill/task_05
   File types: 4
   Linters: 4
────────────────────────────────────────────────────────────

Run the check? (y/n):
```

## Design Decisions

### 🔒 Security
- Directory existence check before scanning
- Skipping hidden files (starting with `.`)
- Exception handling during scanning
- File extension validation

### 🏗️ Architecture
- **Separation of concerns**: scanning is separated from mapping
- **Extensibility**: easy to add new extensions to the mapping
- **Readability**: separate methods for each task
- **Reusability**: `git_docker_utils` as a utility module
- **Type hints**: for all functions and return values

### ⚡ Performance
- Single directory scan
- Using `set()` for unique linters
- Efficient traversal via `rglob("*")`

### 🎯 UX (User Experience)
- Fully automated selection
- Informative statistics output
- Transparency: the user sees what was found
- Confirmation before launch

## Advantages

1. **No manual work** - the system determines what to check on its own
2. **Smart scanning** - recursive analysis of all files
3. **Precision** - only the linters that are needed are run
4. **Speed** - unnecessary linters are not launched
5. **Clarity** - file statistics before launch
