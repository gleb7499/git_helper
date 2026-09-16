# 🧪 Test Scenario: Automatic Linter Selection

## Test Preparation

### Prerequisites

- ✅ Docker Desktop running
- ✅ A Git repository with different file types
- ✅ Python 3.8+ installed

## Test 1: Folder with Different File Types

### Input Data

The folder contains:

- 5 `.md` files
- 3 `.html` files
- 2 `.css` files
- 1 `.js` file

### Steps

1. Run `git_helper.bat`
2. Choose option `6`
3. Enter the folder path
4. Wait for the automatic analysis

### Expected Result

```text
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
```

## Test 2: Only Python Files

### Input Data

The folder contains only `.py` files

### Expected Result

```
📊 File statistics:
   .py             — 8 file(s)

🔍 Automatically selected linters: 2
   ✓ Python (Pylint)
   ✓ Python (Flake8)
```

## Test 3: Mixed Extensions

### Input Data

- `.md`, `.json`, `.yml`, `.sh`

### Expected Result

```
📊 File statistics:
   .md             — 3 file(s)
   .json           — 2 file(s)
   .yml            — 1 file(s)
   .sh             — 1 file(s)

🔍 Automatically selected linters: 4
   ✓ Markdown
   ✓ JSON
   ✓ YAML
   ✓ Bash
```

## Test 4: Folder Without Supported Files

### Input Data

The folder contains only `.txt`, `.pdf`, `.docx`

### Expected Result

```
⚠️  No files found to check
   Make sure the folder has files with supported extensions
```

## Test 5: Nested Folder Structure

### Input Data

```
task_05/
  ├── index.html
  ├── styles/
  │   ├── main.css
  │   └── theme.css
  ├── scripts/
  │   └── app.js
  └── README.md
```

### Expected Result

All files should be found recursively:

```
📊 File statistics:
   .css            — 2 file(s)
   .html           — 1 file(s)
   .js             — 1 file(s)
   .md             — 1 file(s)

🔍 Automatically selected linters: 4
   ✓ Markdown
   ✓ HTML
   ✓ CSS/SCSS
   ✓ JavaScript/ES
```

## Test 6: Paths with Cyrillic and Spaces

### Input Data

A path like:

```
C:\Users\username\Documents\projects\WT-AC-2025 (Example)\students\ExampleUser\task_05
```

### Expected Result

- Scanning works correctly
- Cyrillic characters and spaces are handled
- Statistics are displayed correctly

## Security Check

### Test: Non-existent folder

**Input:** Path to a non-existent directory  
**Expected:** `❌ Folder does not exist: ...`

### Test: File instead of folder

**Input:** Path to a file  
**Expected:** `❌ The specified path is not a folder: ...`

### Test: Empty string

**Input:** Empty path  
**Expected:** `❌ Path cannot be empty`

## Performance Check

### Large folder (1000+ files)

- Scan time < 5 seconds
- Correct count of all files
- No interface freezes

## Final Check

After all tests, verify:

- ✅ Automatic selection works for all supported types
- ✅ Recursive scanning finds all files
- ✅ Paths with Cyrillic and spaces are handled
- ✅ Errors are handled correctly
- ✅ Statistics are displayed readably
- ✅ Linters are selected correctly
- ✅ Docker launches with the correct parameters
