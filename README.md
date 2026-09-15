# 🚀 Git Helper

Automation of Git and SSH key management for student projects.

## Quick Start

### Main menu

```bash
git_helper.bat
```

### Quick code check (from any folder)

```bash
quick_lint
```

> Add the project path to PATH to use `quick_lint` from anywhere. [More details →](doc/QUICK_LINT.md)

## Project Structure

```text
git_helper.bat          # Main menu (run this!)
quick_lint.bat          # Quick check (from anywhere)
src/                    # Python scripts
  ├── ssh_manager.py
  ├── create_ssh_key.py
  ├── delete_ssh_key.py
  ├── clone_repository.py
  ├── sync_upstream.py
  ├── create_branch.py
  ├── git_docker_utils.py  # Docker utilities
  └── run_linter.py        # Super-linter launcher
doc/                    # Documentation
  ├── QUICKSTART.md     # Start with this file!
  ├── CHEATSHEET.md     # Quick reference
  ├── USAGE_GUIDE.md    # Detailed instructions
  ├── LINTER_GUIDE.md   # Linter guide
  ├── QUICK_LINT.md     # Quick code check
  ├── README.md         # Full documentation
  └── SUMMARY.md        # Change log
```

## Menu

1. **Create SSH key** - for a new client (first time)
2. **Delete SSH key** - remove a key from the system
3. **Clone repository** - after creating a key
4. **Update main** - sync with the teacher's repo
5. **Create branch** - for a new lab assignment
6. **Run super-linter** - code quality check (NEW!)
7. **Exit**

## Documentation

📖 Full documentation in the **doc/** folder

Start with `doc/QUICKSTART.md` for a quick start!

---

**Requirements:** Python 3.8+, Git, Git Bash, Docker Desktop (for the linter)
