# 🚀 Git Helper - Git Workflow Assistant

A set of scripts for creating GitHub SSH keys and cloning repositories.

## 📋 What's Included

- **git_helper.bat** - main script (run this!): creates and activates a Python virtual environment, shows the menu, launches the selected script
- **src/ssh_manager.py** - SSH management module: ed25519 key generation, `~/.ssh/config` management, input validation
- **src/create_ssh_key.py** - SSH key creation for GitHub
- **src/delete_ssh_key.py** - SSH key removal together with its config entry
- **src/clone_repository.py** - repository cloning over SSH

## 🎯 Usage

Run **`git_helper.bat`** and choose an action:

1. **Create SSH key** (first step for a new user)
2. **Delete SSH key**
3. **Clone repository**
4. **Exit**

### Creating an SSH key

The script asks for the GitHub username (e.g. `annkrq`) and the surname plus first name written together (e.g. `KozlovskayaAnna`), then:

- generates the key `id_ed25519_KozlovskayaAnna` without a passphrase;
- adds the host `github-Kozlovskaya` to `~/.ssh/config`;
- copies the public key to the clipboard and opens <https://github.com/settings/keys>.

All that is left is to click **New SSH key** and paste the key.

```text
Ключ создан: id_ed25519_KozlovskayaAnna (host: github-Kozlovskaya)

ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... annkrq

Ключ скопирован в буфер обмена. Вставьте его на сайте: https://github.com/settings/keys
```

### Cloning a repository

The script asks for the target folder and the repository link (e.g. `https://github.com/annkrq/repo-name`). The repository is cloned into a subfolder named after it.

The SSH key is picked automatically: the owner from the link is compared with the GitHub username of each key (it is stored in the public key comment). If there is only one key, it is used. The script asks for a choice only when the key cannot be determined unambiguously.

In the cloned repository, `user.name` (the key's username) and `user.email` (`username@users.noreply.github.com`) are configured.

### Running Python scripts directly

```bash
venv\Scripts\activate
python src\create_ssh_key.py
python src\clone_repository.py
```

## 🔧 Requirements

- Python 3.8+ (check is built into git_helper.bat)
- Git installed and configured
- OpenSSH (`ssh-keygen`), included with Windows 10/11 and Git for Windows

## 🛡️ Security

- Validation of all input data
- Checking file existence before overwriting
- Proper file permissions for SSH files (0600)
- SSH keys are stored in `~/.ssh`; no passwords or secrets in code

## 🏗️ Architecture

- **ssh_manager.py** - base module with the `SSHManager` class
- **create_ssh_key.py**, **delete_ssh_key.py**, **clone_repository.py** - scripts that use `ssh_manager`
- **git_helper.bat** - entry point
