"""
Clone Repository Script

Скрипт для клонирования репозиториев через SSH с автоматическим
определением нужного SSH ключа на основе пути и настройкой git config.
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from ssh_manager import SSHManager


def print_separator(char: str = "═", length: int = 60) -> None:
    """Печатает разделитель."""
    print(char * length)


def print_header(text: str) -> None:
    """Печатает заголовок раздела."""
    print()
    print_separator()
    print(f"📦 {text}")
    print_separator()
    print()


def parse_target_path(target_path: str) -> Optional[Tuple[str, str, str]]:
    """
    Парсит целевой путь для извлечения информации.
    
    Args:
        target_path: Путь вида C:\\...\\WT-AC-2025 (Kozlovskaya)
        
    Returns:
        Tuple (parent_dir, repo_name, surname) или None при ошибке
        
    Example:
        "C:\\Users\\...\\WT-AC-2025 (Kozlovskaya)" →
        ("C:\\Users\\...", "WT-AC-2025", "Kozlovskaya")
    """
    try:
        # Нормализуем путь
        target_path = os.path.normpath(target_path.strip())
        
        # Извлекаем последнюю часть пути (имя папки)
        folder_name = os.path.basename(target_path)
        parent_dir = os.path.dirname(target_path)
        
        # Парсим формат "RepoName (Surname)"
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
    Пытается найти полное имя на основе фамилии из SSH config.
    
    Args:
        surname: Фамилия пользователя
        ssh_manager: Экземпляр SSHManager
        
    Returns:
        Полное имя или None, если не найдено
    """
    try:
        config_path = ssh_manager.config_path
        
        if not config_path.exists():
            return None
        
        config_content = config_path.read_text(encoding='utf-8')
        
        # Ищем Host с фамилией
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
    Клонирует репозиторий и настраивает git config.
    
    Args:
        repo_name: Имя репозитория
        username: GitHub username
        host_name: SSH host из config (например, github-Kozlovskaya)
        target_path: Путь куда клонировать
        git_user_name: Имя для git config user.name
        git_email: Email для git config user.email
        
    Returns:
        Tuple (успех, сообщение)
    """
    try:
        # Формируем команду клонирования
        clone_url = f"git@{host_name}:{username}/{repo_name}.git"
        
        print(f"🔹 Клонирование: {clone_url}")
        print(f"🔹 В директорию: {target_path}")
        print()
        
        # Клонируем репозиторий
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
        
        # Настраиваем git config в склонированном репозитории
        repo_path = Path(target_path)
        
        if not repo_path.exists():
            return False, "❌ Директория репозитория не найдена после клонирования"
        
        # Устанавливаем user.name
        cmd_name = ["git", "-C", str(repo_path), "config", "user.name", git_user_name]
        result = subprocess.run(cmd_name, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            return False, f"❌ Ошибка настройки user.name:\n{result.stderr}"
        
        # Устанавливаем user.email
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
    Основная функция клонирования репозитория.
    
    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        print_header("Клонирование репозитория через SSH")
        
        # Инициализация менеджера
        ssh_manager = SSHManager()
        
        # Шаг 1: Получение целевого пути
        print("📝 Введите данные для клонирования:\n")
        print("ℹ️  Формат пути: C:\\...\\RepoName (Surname)")
        print("   Например: C:\\Users\\kseni\\Documents\\WT-AC-2025 (Kozlovskaya)\n")
        
        target_path = input("Целевой путь: ").strip()
        
        if not target_path:
            print("❌ Путь не может быть пустым")
            return 1
        
        # Парсим путь
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
        
        # Пытаемся найти полное имя из SSH config
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
        
        # Шаг 2: Получение данных пользователя
        print("📝 Введите данные GitHub пользователя:\n")
        
        git_user_name = input("Имя для git config (например, Anna Kozlovskaya): ").strip()
        
        if not git_user_name:
            print("❌ Имя не может быть пустым")
            return 1
        
        username = input("GitHub username (например, annkrq): ").strip()
        
        if not username:
            print("❌ Username не может быть пустым")
            return 1
        
        # Формируем email
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
        
        # Проверяем существование целевой директории
        if os.path.exists(target_path):
            print(f"\n⚠️  Директория {target_path} уже существует!")
            print("🔄 Продолжаем клонирование (возможны ошибки)...")
            print()
        
        # Создаем родительскую директорию если её нет
        os.makedirs(parent_dir, exist_ok=True)
        
        # Шаг 3: Клонирование
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
        
        # Финальная информация
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
