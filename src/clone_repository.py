"""
Clone Repository Script

Script for cloning repositories via SSH with automatic
detection of the required SSH key from the path and git config setup.
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple
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


def parse_target_path(target_path: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse the target path to extract information.
    
    Args:
        target_path: Path like C:\\...\\WT-AC-2025 (Kozlovskaya)
        
    Returns:
        Tuple (parent_dir, repo_name, surname) or None on error
        
    Example:
        "C:\\Users\\...\\WT-AC-2025 (Kozlovskaya)" →
        ("C:\\Users\\...", "WT-AC-2025", "Kozlovskaya")
    """
    try:
        # Normalize the path
        target_path = os.path.normpath(target_path.strip())
        
        # Extract the last part of the path (folder name)
        folder_name = os.path.basename(target_path)
        parent_dir = os.path.dirname(target_path)
        
        # Parse the "RepoName (Surname)" format
        pattern = r'^(.+?)\s*\(([^)]+)\)$'
        match = re.match(pattern, folder_name)
        
        if not match:
            return None
        
        repo_name = match.group(1).strip()
        surname = match.group(2).strip()
        
        return parent_dir, repo_name, surname
        
    except Exception:
        return None


def get_full_name_from_config(surname: str, ssh_manager: SSHManager) -> Optional[str]:
    """
    Try to find the full name based on the surname from SSH config.
    
    Args:
        surname: User surname
        ssh_manager: SSHManager instance
        
    Returns:
        Full name or None if not found
    """
    try:
        config_path = ssh_manager.config_path
        
        if not config_path.exists():
            return None
        
        config_content = config_path.read_text(encoding='utf-8')
        
        # Look for a Host with the surname
        pattern = rf'Host github-(\w*{re.escape(surname)}\w*)'
        matches = re.findall(pattern, config_content, re.IGNORECASE)
        
        if matches:
            return matches[0]
        
        return None
        
    except Exception:
        return None


def clone_repository(
    repo_name: str,
    username: str,
    host_name: str,
    target_path: str,
    git_user_name: str,
    git_email: str
) -> Tuple[bool, str]:
    """
    Clone the repository and configure git config.
    
    Args:
        repo_name: Repository name
        username: GitHub username
        host_name: SSH host from config (e.g., github-Kozlovskaya)
        target_path: Where to clone
        git_user_name: Name for git config user.name
        git_email: Email for git config user.email
        
    Returns:
        Tuple (success, message)
    """
    try:
        # Build the clone command
        clone_url = f"git@{host_name}:{username}/{repo_name}.git"
        
        print(f"🔹 Клонирование: {clone_url}")
        print(f"🔹 В директорию: {target_path}")
        print()
        
        # Clone the repository
        cmd = ["git", "clone", clone_url, target_path]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return False, f"❌ Ошибка клонирования:\n{result.stderr}"
        
        print("✅ Репозиторий успешно склонирован")
        print()
        
        # Configure git config in the cloned repository
        repo_path = Path(target_path)
        
        if not repo_path.exists():
            return False, "❌ Директория репозитория не найдена после клонирования"
        
        # Set user.name
        cmd_name = ["git", "-C", str(repo_path), "config", "user.name", git_user_name]
        result = subprocess.run(cmd_name, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            return False, f"❌ Ошибка настройки user.name:\n{result.stderr}"
        
        # Set user.email
        cmd_email = ["git", "-C", str(repo_path), "config", "user.email", git_email]
        result = subprocess.run(cmd_email, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            return False, f"❌ Ошибка настройки user.email:\n{result.stderr}"
        
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
        
        # Initialize the manager
        ssh_manager = SSHManager()
        
        # Step 1: Get the target path
        print("📝 Введите данные для клонирования:\n")
        print("ℹ️  Формат пути: C:\\...\\RepoName (Surname)")
        print("   Например: C:\\Users\\kseni\\Documents\\WT-AC-2025 (Kozlovskaya)\n")
        
        target_path = input("Целевой путь: ").strip()
        
        if not target_path:
            print("❌ Путь не может быть пустым")
            return 1
        
        # Parse the path
        parsed = parse_target_path(target_path)
        
        if not parsed:
            print("❌ Неверный формат пути!")
            print("   Ожидается: C:\\...\\RepoName (Surname)")
            return 1
        
        parent_dir, repo_name, surname = parsed
        
        print()
        print(f"✓ Репозиторий: {repo_name}")
        print(f"✓ Фамилия: {surname}")
        print()
        
        # Try to find the full name from SSH config
        full_name = get_full_name_from_config(surname, ssh_manager)
        
        if full_name:
            print(f"✓ Найден SSH host: github-{full_name}")
            host_name = f"github-{full_name}"
        else:
            print(f"⚠️  SSH host для {surname} не найден в config")
            print("   Введите полное имя (ФамилияИмя) вручную:")
            full_name = input("   Полное имя: ").strip()
            
            if not full_name:
                print("❌ Полное имя не может быть пустым")
                return 1
            
            host_name = f"github-{full_name}"
        
        print()
        
        # Step 2: Get user data
        print("📝 Введите данные GitHub пользователя:\n")
        
        git_user_name = input("Имя для git config (например, Anna Kozlovskaya): ").strip()
        
        if not git_user_name:
            print("❌ Имя не может быть пустым")
            return 1
        
        username = input("GitHub username (например, annkrq): ").strip()
        
        if not username:
            print("❌ Username не может быть пустым")
            return 1
        
        # Build the email
        git_email = f"{username}@users.noreply.github.com"
        
        print()
        print("═" * 60)
        print("📋 Итоговая информация:")
        print("═" * 60)
        print(f"  Репозиторий:  {repo_name}")
        print(f"  SSH Host:     {host_name}")
        print(f"  Username:     {username}")
        print(f"  Git Name:     {git_user_name}")
        print(f"  Git Email:    {git_email}")
        print(f"  Целевой путь: {target_path}")
        print("═" * 60)
        print()
        
        # Check the target directory
        if os.path.exists(target_path):
            print(f"\n⚠️  Директория {target_path} уже существует!")
            print("🔄 Продолжаем клонирование (возможны ошибки)...")
            print()
        
        # Create the parent directory if it does not exist
        os.makedirs(parent_dir, exist_ok=True)
        
        # Step 3: Cloning
        print_header("Клонирование репозитория")
        
        success, message = clone_repository(
            repo_name=repo_name,
            username=username,
            host_name=host_name,
            target_path=target_path,
            git_user_name=git_user_name,
            git_email=git_email
        )
        
        print()
        print(message)
        
        if not success:
            return 1
        
        # Final information
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
