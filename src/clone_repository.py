"""
Clone Repository Script

Script for cloning repositories over SSH. Takes a target path and a GitHub
repository link, picks the SSH key by the repository owner, and configures
git config in the cloned repository.
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from ssh_manager import SSHManager


def print_separator(char: str = "═", length: int = 60) -> None:
    """Prints a separator."""
    print(char * length)


def print_header(text: str) -> None:
    """Prints a section header."""
    print()
    print_separator()
    print(f"📦 {text}")
    print_separator()
    print()


def parse_repo_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Extract the owner and repository name from a GitHub link.

    Supported formats:
        https://github.com/owner/repo(.git)(/...)
        git@github.com:owner/repo.git
        git@github-Alias:owner/repo.git
        ssh://git@github.com/owner/repo.git

    Args:
        url: Repository link

    Returns:
        Tuple (owner, repo) or None if the link is not recognized
    """
    url = url.strip()
    pattern = (
        r'^(?:https?://(?:www\.)?github\.com/|'
        r'ssh://git@[^/]+/|'
        r'git@[^:]+:)'
        r'([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+?)(?:\.git)?(?:/.*)?$'
    )
    match = re.match(pattern, url)

    if not match:
        return None

    return match.group(1), match.group(2)


def get_key_username(ssh_manager: SSHManager, full_name: str) -> Optional[str]:
    """
    Read the GitHub username from the public key comment
    (it is written there by ssh-keygen -C when the key is created).

    Args:
        ssh_manager: SSHManager instance
        full_name: Full name from the key file name

    Returns:
        Username or None
    """
    pub_key = ssh_manager.get_public_key(full_name)

    if not pub_key:
        return None

    parts = pub_key.split(maxsplit=2)

    if len(parts) == 3 and ssh_manager.validate_username(parts[2].strip()):
        return parts[2].strip()

    return None


def choose_key(ssh_manager: SSHManager, owner: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """
    Pick an SSH key by the repository owner: the key whose GitHub username
    matches the owner, or the only key available. The user is asked to choose
    only when the key cannot be determined unambiguously.

    Args:
        ssh_manager: SSHManager instance
        owner: Repository owner from the link

    Returns:
        Tuple (full_name, host_name, username) or None if no key can be chosen
    """
    keys = ssh_manager.list_ssh_keys()

    if not keys:
        print("❌ SSH ключи не найдены. Сначала создайте ключ (пункт 1 меню).")
        return None

    config_text = ""
    if ssh_manager.config_path.exists():
        config_text = ssh_manager.config_path.read_text(encoding='utf-8')

    entries: List[Tuple[str, str, Optional[str]]] = [
        (full_name, host_name, get_key_username(ssh_manager, full_name))
        for full_name, host_name in keys
    ]

    def describe(entry: Tuple[str, str, Optional[str]]) -> str:
        full_name, host_name, username = entry
        in_config = re.search(rf'^\s*Host\s+{re.escape(host_name)}\s*$', config_text, re.MULTILINE)
        note = "" if in_config else "  ⚠️  нет записи в SSH config"
        return f"{full_name}  (GitHub: {username or '?'}, host: {host_name}){note}"

    matches = [e for e in entries if e[2] and e[2].lower() == owner.lower()]

    if len(matches) == 1 or len(entries) == 1:
        chosen = matches[0] if matches else entries[0]
        print(f"🔑 Ключ: {describe(chosen)}")
        return chosen

    candidates = matches or entries

    print("🔑 От имени какого человека клонировать?\n")

    for index, entry in enumerate(candidates, start=1):
        print(f"  {index}. {describe(entry)}")

    print()

    while True:
        choice = input(f"Номер (1-{len(candidates)}): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            return candidates[int(choice) - 1]

        print("❌ Неверный номер. Попробуйте снова.")


def clone_repository(
    clone_url: str,
    target_path: str,
    git_user_name: str,
    git_email: str
) -> Tuple[bool, str]:
    """
    Clone a repository and configure git config.

    Args:
        clone_url: SSH URL like git@github-Host:owner/repo.git
        target_path: Path to clone into
        git_user_name: Name for git config user.name
        git_email: Email for git config user.email

    Returns:
        Tuple (success, message)
    """
    try:
        print(f"🔹 Клонирование: {clone_url}")
        print(f"🔹 В директорию: {target_path}")
        print()

        cmd = [
            "git", "clone", clone_url, target_path
        ]

        # accept-new: do not ask to confirm the host fingerprint on first connection
        env = dict(os.environ, GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env=env
        )

        if result.returncode != 0:
            return False, f"❌ Ошибка клонирования:\n{result.stderr}"

        print("✅ Репозиторий успешно склонирован")
        print()

        repo_path = Path(target_path)

        if not repo_path.exists():
            return False, "❌ Директория репозитория не найдена после клонирования"

        for key, value in (("user.name", git_user_name), ("user.email", git_email)):
            result = subprocess.run(
                ["git", "-C", str(repo_path), "config", key, value],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return False, f"❌ Ошибка настройки {key}:\n{result.stderr}"

        print("✅ Git config настроен:")
        print(f"   user.name  = {git_user_name}")
        print(f"   user.email = {git_email}")

        return True, "✅ Репозиторий успешно склонирован и настроен"

    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"


def main() -> int:
    """
    Main repository cloning function.

    Returns:
        Exit code (0 - success, 1 - error)
    """
    try:
        print_header("Клонирование репозитория через SSH")

        ssh_manager = SSHManager()

        # Step 1: target path and link
        print("📝 Введите данные для клонирования:\n")

        target_path = input("Целевой путь (папка, внутри которой будет создана папка репозитория): ").strip().strip('"')

        if not target_path:
            print("❌ Путь не может быть пустым")
            return 1

        target_path = os.path.normpath(target_path)

        repo_url = input("Ссылка на репозиторий GitHub: ").strip()
        parsed = parse_repo_url(repo_url)

        if not parsed:
            print("❌ Не удалось разобрать ссылку!")
            print("   Пример: https://github.com/Owner/repo-name")
            return 1

        owner, repo_name = parsed

        # The repository is cloned into a subfolder named after it inside the given path
        target_path = os.path.join(target_path, repo_name)

        print()
        print(f"✓ Владелец:    {owner}")
        print(f"✓ Репозиторий: {repo_name}")
        print(f"✓ Папка:       {target_path}")
        print()

        # Step 2: pick the key by the repository owner
        chosen = choose_key(ssh_manager, owner)

        if not chosen:
            return 1

        full_name, host_name, username = chosen

        print()

        # Step 3: git config data
        if not username:
            username = input("GitHub username этого человека: ").strip()

            if not username:
                print("❌ Username не может быть пустым")
                return 1

        git_user_name = username
        git_email = f"{username}@users.noreply.github.com"

        clone_url = f"git@{host_name}:{owner}/{repo_name}.git"

        print()
        print("═" * 60)
        print("📋 Итоговая информация:")
        print("═" * 60)
        print(f"  Ссылка:       {clone_url}")
        print(f"  Ключ:         id_ed25519_{full_name}")
        print(f"  Git Name:     {git_user_name}")
        print(f"  Git Email:    {git_email}")
        print(f"  Целевой путь: {target_path}")
        print("═" * 60)
        print()

        if os.path.exists(target_path) and os.listdir(target_path):
            print(f"❌ Директория {target_path} уже существует и не пуста!")
            return 1

        os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)

        # Step 4: cloning
        print_header("Клонирование репозитория")

        success, message = clone_repository(
            clone_url=clone_url,
            target_path=target_path,
            git_user_name=git_user_name,
            git_email=git_email
        )

        print()
        print(message)

        if not success:
            return 1

        print()
        print_separator("═")
        print("✅ Репозиторий успешно настроен и готов к работе!")
        print_separator("═")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n\n❌ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
