# 🔍 Super-Linter Usage Guide

## What is it?

Super-linter is a tool for automatic code quality checking. It runs via Docker and supports many programming languages.

## Requirements

- ✅ Docker Desktop installed and running
- ✅ The checked folder is inside a Git repository
- ✅ (Optional) `.markdownlint.yaml` in the repository root for rule configuration

## How to Use

### Step 1: Launch

```bash
git_helper.bat → Choose option 6
```

### Step 2: Specify the folder path

Example:
```
C:\Users\username\Documents\projects\WT-AC-2025 (Example)\students\ExampleUser\task_05
```

**Important:**
- The path must be INSIDE a Git repository
- The script will automatically find the repository root (the folder with .git)
- The check runs from the root, but only the specified folder is analyzed

### Step 3: Automatic linter selection

**Linters are selected automatically** based on the found file types!

The script:
1. Scans all files in the specified folder (recursively)
2. Determines file extensions
3. Automatically selects the corresponding linters

Supported extensions:
- **.md, .markdown** → Markdown
- **.js, .jsx** → JavaScript/ES
- **.ts, .tsx** → TypeScript
- **.py** → Python (Pylint + Flake8)
- **.html, .htm** → HTML
- **.css, .scss** → CSS
- **.json** → JSON
- **.yml, .yaml** → YAML
- **.sh, .bash** → Bash
- **.xml** → XML
- **.sql** → SQL
- **.dockerfile** → Dockerfile

**Example output:**
```
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

### Step 4: Confirmation and launch

The system shows the launch parameters:
- Repository root
- Checked folder (relative path)
- Number of file types
- Number of selected linters

After confirmation, a Docker container with the check is launched.

### Step 5: Results

Output is grouped by type:
- 🔴 **FATAL** - critical errors
- ❌ **ERROR** - errors
- ⚠️ **WARNING** - warnings

## Linter Configuration

### For Markdown

Create a `.markdownlint.yaml` file in the **repository root**:

```yaml
# Example configuration
MD013: false  # Disable line length check
MD033: false  # Allow HTML tags
MD041: false  # Do not require H1 at the start
```

### For other languages

Super-linter supports many configs:
- `.eslintrc.json` - for JavaScript
- `.flake8` - for Python Flake8
- `.pylintrc` - for Python Pylint
- Etc.

All configs must be in the **repository root**.

## How It Works

1. **Finding the repository root**
   - The script walks up the directory tree
   - Looks for a `.git` folder
   - This is the repository root

2. **Computing the relative path**
   - Root: `C:\...\WT-AC-2025 (Kotkovets)`
   - Checked folder: `C:\...\WT-AC-2025 (Kotkovets)\students\KotkovetsKirill\task_05`
   - Relative path: `students/KotkovetsKirill/task_05`

3. **Docker launch**
   - The repository root is mounted to `/tmp/lint`
   - The `FILTER_REGEX_INCLUDE` filter is used
   - Only files in the specified folder are checked

4. **Result processing**
   - Only WARNING, ERROR, FATAL are filtered
   - Grouping by type
   - Statistics counting

## Usage Examples

### Check only Markdown

```
Path: C:\...\task_05
Linters: [Enter] (Markdown by default)
```

### Check Markdown + Python

```
Path: C:\...\task_05
Linters: 1,3 (Markdown + Python Pylint)
```

### Full check

```
Path: C:\...\task_05
Linters: 1,2,3,6,7,8 (Markdown, JS, Python, HTML, CSS, JSON)
```

## Troubleshooting

### Docker not running

```
❌ Docker is not responding. Make sure Docker Desktop is running.
```

**Solution:** Start Docker Desktop and wait for it to fully load.

### Git repository not found

```
❌ Could not find the Git repository root
```

**Solution:** Make sure the folder is inside a cloned Git repository.

### Config not found

```
⚠️ Configuration .markdownlint.yaml not found in the root
```

**This is normal!** Super-linter will use default settings.

If you want your own rules - create a config in the repository root.

## Technical Details

### Docker command

```bash
docker run --rm \
  -e RUN_LOCAL=true \
  -e DEFAULT_BRANCH=main \
  -e VALIDATE_ALL_CODEBASE=false \
  -e VALIDATE_MARKDOWN=true \
  -e FILTER_REGEX_INCLUDE="students/KotkovetsKirill/task_05/.*" \
  -v "C:/path/to/repo:/tmp/lint" \
  ghcr.io/super-linter/super-linter:v6
```

### Why run from the root?

- Super-linter requires the repository root as the reference point
- Configuration files are located in the root
- Git metadata (.git) is needed to determine changed files

### Relative paths

All paths in the Docker container are relative to `/tmp/lint` (repository root).

## Useful Links

- [Super Linter GitHub](https://github.com/super-linter/super-linter)
- [Configuration documentation](https://github.com/super-linter/super-linter#configuration)
- [List of supported languages](https://github.com/super-linter/super-linter#supported-linters)

---

**Date:** December 14, 2025
