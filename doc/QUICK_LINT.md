# Quick Lint - Quick Code Check

## What is it?

`quick_lint` - a minimal command to run the super-linter from any directory.

## Installation

### 1. Add to PATH

**Windows 10/11:**

1. Press `Win + X` → **System**
2. **Advanced system settings** → **Environment Variables**
3. Under **User variables** find `Path` → **Edit**
4. **New** → add the path:
   ```
   C:\Users\kseni\Documents\GitHub\git_helper
   ```
5. **OK** → **OK** → **OK**

### 2. Verify

Open a **NEW** command prompt window (the old one won't see the PATH changes):

```bash
quick_lint --help
```

The usage help should appear.

## Usage

### Basic usage

```bash
# Go to the folder you want to check
cd C:\Projects\WT-AC-2025 (Kozlovskaya)\students\KozlovskayaAnna\task_05

# Run the check
quick_lint
```

### Output

**Successful check:**
```
🔍 Checking: task_05 (3 file types, 2 linters)
✅ Check passed successfully
```

**Errors found:**
```
🔍 Checking: task_05 (3 file types, 2 linters)

❌ Found problems: 5 errors, 2 warnings

🔴 CRITICAL ERRORS:
   [MARKDOWN] MD013: Line length exceeds 80 characters

❌ ERRORS:
   [HTML] Missing DOCTYPE declaration
   ...
```

## Requirements

- ✅ Docker Desktop running
- ✅ The folder is inside a Git repository
- ✅ Virtual environment created (run `git_helper.bat` at least once)

## Features

### Automatic file type detection

The script scans the folder and automatically selects linters for the found extensions:

- `.md` → Markdown
- `.html` → HTML
- `.css` → CSS
- `.js` → JavaScript
- `.py` → Python
- `.json` → JSON
- `.yml`/`.yaml` → YAML
- and others...

### Smart repository lookup

Even if you run `quick_lint` from a nested folder, the script will automatically find the Git repository root (the folder with `.git`).

### Quiet mode

Outputs only important information:
- Brief check statistics
- Only errors (no warnings)
- Minimal technical details

## Troubleshooting

### "Error: Virtual environment not found"

**Solution:** Run `git_helper.bat` once to create the virtual environment:

```bash
cd C:\Users\kseni\Documents\GitHub\git_helper
git_helper.bat
# Choose any menu option, then exit
```

### "Docker not running"

**Solution:** Start Docker Desktop and wait for it to fully start (the tray icon turns green).

### "Git repository not found"

**Solution:** Make sure you are inside a cloned Git repository:

```bash
# Check
git status

# If you get "not a git repository" - you are outside a repository
```

### "No files to check"

**Possible causes:**
- The folder has no files with supported extensions
- Files are in excluded folders (`node_modules`, `tools`)

## Alternative: Interactive Mode

If you need detailed output with step-by-step progress:

```bash
cd C:\Users\kseni\Documents\GitHub\git_helper
git_helper.bat
# Choose option 6 - Run super-linter
```

## See Also

- [LINTER_GUIDE.md](../doc/LINTER_GUIDE.md) - detailed linter guide
- [AUTO_LINTER_SELECTION.md](../doc/AUTO_LINTER_SELECTION.md) - how automatic linter detection works
