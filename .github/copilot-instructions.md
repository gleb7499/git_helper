# Git Helper - AI Agent Instructions

## Project Overview

Git Helper is a tool for automating the SSH/Git workflow for people with several GitHub accounts. The entry point is `git_helper.bat` (Windows batch file with a menu), which launches Python scripts from the `src/` folder.

## Core Architecture

### Entry Point

[git_helper.bat](../git_helper.bat):

- Creates/activates a Python venv
- Shows the menu (1-4): create key, delete key, clone repository, exit
- Calls the corresponding scripts from `src/`

### Module Organization

```text
src/
├── ssh_manager.py         # SSHManager class - core for all SSH operations
├── create_ssh_key.py      # Generates key → SSH config → clipboard → browser
├── delete_ssh_key.py      # CLI wrapper for SSHManager.remove_ssh_key()
└── clone_repository.py    # Parses the link → picks the key by owner → clones
```

## Key Design Patterns

### SSHManager

`ssh_manager.py` is the only module that works with SSH. All others import it.

**Convention:** SSH host = `github-{Surname}`, key = `id_ed25519_{SurnameFirstName}`. The GitHub username is stored in the key comment (`ssh-keygen -C`).

### Key selection when cloning

`choose_key()` in `clone_repository.py` compares the owner from the link with the username stored in each public key comment. A single matching key, or the only key available, is used without questions; the selection menu is only a fallback.

### Encoding (Windows)

Cyrillic in paths: when needed, pass `encoding=locale.getpreferredencoding(), errors='replace'` to `subprocess.run`.

## Conventions

- Manager methods return `Tuple[bool, str]` (success, message)
- Output with emojis: ✅ success, ❌ error, ⚠️ warning, 🔹 info
- Keep script output minimal: only what the user needs
- Validation: GitHub username `^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38})?$`

## External Dependencies

- **Python 3.8+** (checked in git_helper.bat)
- **Git** and OpenSSH (`ssh-keygen`)

## Testing & Development

```bash
venv\Scripts\activate
python src\create_ssh_key.py
```

## Important Notes

- **SSH keys WITHOUT passphrase** - see `generate_ssh_key()` with `-N ""`
- **ssh-agent is not used**: keys are picked up through `IdentityFile` in the SSH config
- **Git config is set automatically** during cloning
- **Documentation** - `README.md` in the root and `doc/README.md`
