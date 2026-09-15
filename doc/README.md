# 🚀 Git Helper - Git Workflow Assistant

A set of scripts for automating Git repository workflows for students.

## 📋 What's Included

### 1. **git_helper.bat** - Main script (run this!)

- Automatically creates and activates a Python virtual environment
- Nice interactive menu for choosing actions
- Launches the required Python scripts

### 2. **ssh_manager.py** - SSH management module

- ed25519 SSH key generation
- SSH config management
- Adding keys to ssh-agent
- User data validation

### 3. **create_ssh_key.py** - SSH key creation

- Interactive creation of an SSH key for GitHub
- Automatic configuration of ~/.ssh/config
- Adding the key to ssh-agent
- Displaying the public key for GitHub

### 4. **clone_repository.py** - Repository cloning

- Cloning via SSH with automatic key selection
- Path parsing to determine the repository and user
- Automatic git config setup (user.name, user.email)
- Interactive mode with confirmation

### 5. **sync_upstream.py** - Upstream synchronization

- Updates the fork's `main` branch from the original repository
- Automatically parses the discipline and surname from the path
- Builds the upstream URL: `git@github-{Surname}:brstu/{Discipline}.git`

### 6. **create_branch.py** - Creating a new branch

- Automatically syncs main with upstream (uses sync_upstream.py)
- Creates a new branch from the up-to-date main
- Automatically publishes the branch to origin
- Checks if the branch exists and offers to switch to it

## 🎯 Usage

### Easy way (recommended)

1. Run **`git_helper.bat`**
2. Choose the desired action:
   - **1** - Create SSH key (first step for a new user)
   - **2** - Clone repository (after creating the SSH key)
   - **3** - Update main from upstream
   - **4** - Create a new branch
   - **5** - Exit

### Workflow for a new client

#### Step 1: Create an SSH key

```bash
# Run git_helper.bat and choose option 1
# You will be asked to enter:
# - GitHub username (e.g.: annkrq)
# - Surname + First name (e.g.: KozlovskayaAnna)
```

The script will automatically:

- Generate an SSH key `id_ed25519_KozlovskayaAnna`
- Add the key to ssh-agent
- Configure `~/.ssh/config` with host `github-KozlovskayaAnna`
- Display the public key for adding to GitHub

#### Step 2: Add the key to GitHub

1. Copy the public key from the script output
2. Go to GitHub: Settings → SSH and GPG keys
3. Click "New SSH key"
4. Paste the key and save

#### Step 3: Clone the repository

```bash
# Run git_helper.bat and choose option 2
# Enter the path in the format:
# C:\Users\kseni\Documents\Универ\4-курс\ВЕБ\others\WT-AC-2025 (Kozlovskaya)
```

The script will automatically:

- Determine the repository: `WT-AC-2025`
- Find the SSH key by surname: `Kozlovskaya`
- Clone the repository via SSH
- Configure git config (user.name and user.email)

### Running Python scripts directly

```bash
# Activate venv (if not already activated)
venv\Scripts\activate

# Create SSH key
python create_ssh_key.py

# Clone repository
python clone_repository.py

# Sync upstream
python sync_upstream.py

# Create a new branch
python create_branch.py
```

## 📂 Path Structure

The scripts work with folders in this format:

```text
C:\Users\...\WT-AC-2025 (Kozlovskaya)
C:\Users\...\WT-AC-2025 (Kozlovskaya)\students\KozlovskayaAnna
```

Pattern: `{Discipline} ({Surname})`

The scripts will automatically find the repository root even if you specify a nested folder!

## ✨ Features

- ✅ **Safety**: All operations with error checking
- ✅ **Cross-platform**: Python scripts work on Windows/Linux/macOS
- ✅ **Automation**: Minimal manual steps
- ✅ **Nice output**: Clear emojis and formatting
- ✅ **Smart parsing**: Automatically determines discipline and surname from the path

## 🔧 Requirements

- Python 3.8+ (check is built into git_helper.bat)
- Git installed and configured
- SSH keys configured for GitHub access (automated via menu option 1)
- Git Bash for Windows (for ssh-agent)

## 🛡️ Security

All scripts are designed with security in mind:

- Validation of all input data
- Checking file existence before overwriting
- Proper file permissions for SSH files (0600)
- Secure storage of SSH keys in `~/.ssh`
- No passwords or sensitive data stored in code

## 🐛 Troubleshooting

### "Python not found"

Install Python from [python.org](https://www.python.org/downloads/)

### "ssh-agent not running"

For Windows (Git Bash):

```bash
eval "$(ssh-agent -s)"
```

For Linux/Mac:

```bash
eval "$(ssh-agent -s)"
```

### "Error during fetch upstream"

Check:

- SSH keys are configured in `~/.ssh/config`
- Internet access is available
- The `github-{Surname}` alias is configured correctly

### "Branch main not found"

Make sure you are in a git repository with a `main` branch

## 📝 Usage Examples

### Creating an SSH key

```text
🔑 Creating SSH key for GitHub
════════════════════════════════════════════════════════════
📝 Enter data for SSH key creation:

GitHub username (e.g., annkrq): annkrq
Surname + First name (no spaces): KozlovskayaAnna

✓ Username: annkrq
✓ Full name: KozlovskayaAnna
✓ Key name: id_ed25519_KozlovskayaAnna

Continue creating the key? (y/n): y
✅ SSH key successfully created: id_ed25519_KozlovskayaAnna
✅ SSH config updated. Host: github-KozlovskayaAnna

📌 Public SSH key:
────────────────────────────────────────────────────────────
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxx... annkrq
────────────────────────────────────────────────────────────
```

### Cloning a repository

```text
📦 Cloning repository via SSH
════════════════════════════════════════════════════════════
📝 Enter cloning data:

Target path: C:\Users\kseni\Documents\WT-AC-2025 (Kozlovskaya)

✓ Repository: WT-AC-2025
✓ Surname: Kozlovskaya
✓ Found SSH host: github-KozlovskayaAnna

Name for git config (e.g., Anna Kozlovskaya): Anna Kozlovskaya
GitHub username (e.g., annkrq): annkrq

════════════════════════════════════════════════════════════
📋 Summary information:
════════════════════════════════════════════════════════════
  Repository:  WT-AC-2025
  SSH Host:     github-KozlovskayaAnna
  Username:     annkrq
  Git Name:     Anna Kozlovskaya
  Git Email:    annkrq@users.noreply.github.com
════════════════════════════════════════════════════════════

✅ Repository successfully cloned and configured
```

### Upstream synchronization

```text
Enter the full path to the repository: C:\Users\...\WT-AC-2025 (Kozlovskaya)
🔹 Repository name: WT-AC-2025 (Kozlovskaya)
🔹 Discipline: WT-AC-2025
🔹 Surname: Kozlovskaya
🔹 Upstream: git@github-Kozlovskaya:brstu/WT-AC-2025.git
🔹 Switching to main and updating...
✅ Synchronization complete!
```

## 🏗️ Architecture

The project is built modularly:

- **ssh_manager.py** - Base module with the SSHManager class for SSH operations
- **create_ssh_key.py** - CLI script, uses ssh_manager
- **clone_repository.py** - CLI script, uses ssh_manager
- **sync_upstream.py** - Standalone script for synchronization
- **create_branch.py** - Branch creation script, uses sync_upstream
- **git_helper.bat** - Entry point, manages all scripts

Advantages of this architecture:

- Code reuse (DRY principle)
- Easy testing of individual modules
- Ability to use scripts independently or via the BAT menu
- Easy to add new features

---

**Author:** GitHub Copilot  
**Updated:** December 9, 2025
