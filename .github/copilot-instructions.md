# Git Helper - AI Agent Instructions

## Project Overview

Git Helper is a tool for automating the Git/SSH workflow for student projects. The central entry point is `git_helper.bat` (Windows batch file with a menu), which launches Python scripts from the `src/` folder.

**Target audience:** Students with multiple GitHub accounts working on different course repositories.

## Core Architecture

### Entry Point Pattern

- **Main Menu:** [git_helper.bat](../git_helper.bat) - batch script that:
  - Creates/activates a Python venv
  - Shows an interactive menu (1-7)
  - Calls the corresponding Python modules from `src/`
- **Quick Lint:** [quick_lint.bat](../quick_lint.bat) - minimal linter launcher:
  - Runs from any directory (add to PATH)
  - Uses the current directory as the target
  - venv always from `%SCRIPT_DIR%` (where the bat is located)
  - Syntax: `quick_lint` (no arguments)
  
### Path Convention (CRITICAL!)

All scripts parse a specific path pattern:

```text
C:\Users\...\{DISCIPLINE} ({Surname})\students\{SurnameFirstName}\...
```

Examples:

- `WT-AC-2025 (Kozlovskaya)` - fork repository root
- `WT-AC-2025 (Kozlovskaya)\students\KozlovskayaAnna\task_05` - task folder

**Regex pattern:** `^(.+?)\s*\(([^)]+)\)$` parses `{repo_name} ({surname})`

### Module Organization

```text
src/
├── ssh_manager.py         # SSHManager class - core for all SSH operations
├── create_ssh_key.py      # CLI wrapper for SSHManager.generate_ssh_key()
├── delete_ssh_key.py      # CLI wrapper for SSHManager.remove_ssh_key()
├── clone_repository.py    # Parses path → finds SSH key → clones
├── sync_upstream.py       # Syncs main with upstream (brstu/{discipline})
├── create_branch.py       # Imports sync_upstream.py → creates branch
├── git_docker_utils.py    # GitDockerUtils class for the linter
└── run_linter.py          # CLI wrapper for the super-linter via Docker
```

## Key Design Patterns

### 1. SSHManager Class Pattern

`ssh_manager.py` is the only module that works with SSH. All others import it.

**Key convention:** SSH host = `github-{SurnameFirstName}`, key = `id_ed25519_{SurnameFirstName}`

```python
# Example usage in other modules:
from ssh_manager import SSHManager
ssh_mgr = SSHManager()
full_name = ssh_mgr.get_full_name_from_config(surname)  # Kozlovskaya → KozlovskayaAnna
```

### 2. Module Importation Pattern (cross-script calls)

`create_branch.py` IMPORTS `sync_upstream.py` dynamically via `importlib`:

```python
spec = importlib.util.spec_from_file_location("sync_upstream_module", sync_script)
sync_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_module)
exit_code = sync_module.sync_upstream(repo_path, silent=True)
```

**Why:** Avoids duplicating the upstream synchronization logic.

### 3. Path Resolution Pattern

All modules with path parsing use:

```python
def find_repo_folder(path) -> Optional[Tuple[Path, str]]:
    """Walks up the tree to the '{repo} ({surname})' pattern"""
    # Used in: clone_repository.py, sync_upstream.py
```

### 4. Git Root Discovery

`git_docker_utils.py` and others walk up to `.git`:

```python
def find_git_root(start_path) -> Optional[Path]:
    while current != current.parent:
        if (current / ".git").exists():
            return current
```

### 5. Encoding Handling (Windows-specific)

All subprocess calls use:

```python
import locale
console_encoding = locale.getpreferredencoding()
subprocess.run(..., encoding=console_encoding, errors='replace')
```

**Reason:** Cyrillic in paths/file names on Windows.

## Critical Workflows

### Super-Linter Integration

[run_linter.py](../src/run_linter.py) + [git_docker_utils.py](../src/git_docker_utils.py):

1. **Auto-detection:** Scans files → determines extensions → automatically selects linters
2. **Docker invocation:** Mounts the repository root to `/tmp/lint`, checks only the relative path
3. **Config:** Looks for `.markdownlint.yaml` in the repository root (not in the checked folder!)
4. **Dual Mode:** Interactive (default) + quiet mode (`--silent --path`)

**CLI arguments:**

```bash
python run_linter.py                    # Interactive mode
python run_linter.py --path "C:\..."   # Interactive with pre-filled path
python run_linter.py --path "C:\..." --silent  # Quiet mode (for quick_lint)
```

**Docker command:**

```python
docker run --rm -e RUN_LOCAL=true \
  -e FILTER_REGEX_INCLUDE="students/.*" \
  -e VALIDATE_MARKDOWN=true \
  -v /path/to/repo:/tmp/lint \
  ghcr.io/super-linter/super-linter:v6
```

### Upstream Sync Pattern

`sync_upstream.py` builds the URL: `git@github-{surname}:brstu/{discipline}.git`

- Surname from the path pattern → SSH host
- Discipline (e.g., `WT-AC-2025`) → original repository name

### Branch Creation Flow

1. Imports `sync_upstream.py`
2. Syncs main with upstream (brstu)
3. Creates a branch from the updated main
4. Publishes to origin (student's fork)

## Conventions & Best Practices

### Error Handling

- All functions return `Tuple[bool, str]` for (success, message)
- Output with emojis: ✅ success, ❌ error, ⚠️ warning, 🔹 info

### User Output Style

```python
def print_separator(char: str = "═", length: int = 60) -> None:
def print_header(text: str) -> None:
    print_separator()
    print(f"📦 {text}")
    print_separator()
```

**Used everywhere!** Keep it consistent.

### Validation Pattern

SSHManager contains regex validation for:

- GitHub username: `^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38})?$`
- First/surname: `^[a-zA-Zа-яА-ЯёЁ]{2,50}$`

### Config Management

SSH config is updated atomically:

```python
def update_ssh_config(full_name: str):
    # 1. Reads the entire config
    # 2. Looks for an existing entry for Host github-{full_name}
    # 3. Updates or adds a new one
    # 4. Writes it back
```

## External Dependencies

- **Python 3.8+** (checked in git_helper.bat)
- **Git** + **Git Bash** (for ssh-agent on Windows)
- **Docker Desktop** (only for the super-linter, menu option 6)

## Testing & Development

### Run Individual Scripts
Quick Lint Setup

```bash
# Add to the Windows PATH environment variable:
C:\Users\kseni\Documents\GitHub\git_helper

# Usage from anywhere:
cd C:\Projects\MyRepo\task_01
quick_lint  # Checks the current directory

# Internal behavior:
# 1. %SCRIPT_DIR% → C:\Users\kseni\Documents\GitHub\git_helper
# 2. %TARGET_DIR% → %CD% (current directory)
# 3. Activates venv from SCRIPT_DIR
# 4. Calls: python run_linter.py --path TARGET_DIR --silent
```

### 
```bash
# Activate venv
venv\Scripts\activate

# Run a module directly
python src\create_ssh_key.py
```

### Path Testing

Use test paths in the format:

```text
C:\Test\WT-AC-2025 (TestSurname)\students\TestSurnameFirst\task_01
```

## Important Notes

- **NEVER change the path pattern** `{repo} ({surname})` - the whole project depends on it
- **SSH keys WITHOUT passphrase** (for automation) - see `generate_ssh_key()` with `-N ""`
- **Git config is set automatically** during cloning via `clone_repository.py`
- **Documentation lives in `doc/`**, but the README.md in the root is the main entry point for users
