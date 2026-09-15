#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
New branch creation script
Creates a new branch in the repository after syncing with upstream
"""

import os
import sys
import subprocess
import re
from pathlib import Path


def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    try:
        # Determine the Windows console encoding
        import locale
        console_encoding = locale.getpreferredencoding()
        
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            encoding=console_encoding,
            errors='replace',  # Replace problematic characters
            shell=True
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout.strip(), e.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def find_git_repo(path):
    """
    Find the git repository root folder
    Walks up the folder tree until it finds .git
    """
    current = Path(path).resolve()
    
    # Check the current folder
    if (current / ".git").exists():
        return current
    
    print(f"🔹 .git не найден в \"{current}\", проверяем родительские папки...")
    
    # Go up
    while current.parent != current:  # Until the drive root is reached
        current = current.parent
        if (current / ".git").exists():
            print(f"🔹 Найден git-репозиторий: {current}")
            return current
    
    print("❌ Git-репозиторий не найден! Завершение.")
    input("Нажмите Enter для выхода...")
    sys.exit(1)


def validate_branch_name(branch_name):
    """Check that the branch name is valid"""
    if not branch_name:
        print("❌ Имя ветки не может быть пустым! Завершение.")
        return False
    
    # Check for invalid characters
    invalid_chars = r'[\\/:*?"<>|]'
    if re.search(invalid_chars, branch_name):
        print("❌ Имя ветки содержит недопустимые символы! Завершение.")
        return False
    
    return True


def sync_with_upstream(repo_path):
    """Call sync_upstream for synchronization"""
    print()
    print("=" * 40)
    print("🔹 Синхронизация с upstream")
    print("=" * 40)
    print()
    
    # Import the sync_upstream module
    script_dir = Path(__file__).parent
    sync_script = script_dir / "sync_upstream.py"
    
    if not sync_script.exists():
        print(f"❌ Файл sync_upstream.py не найден в папке скриптов! Завершение.")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    print("🔹 Вызов sync_upstream.py для обновления main...")
    
    # Import the synchronization function directly
    import importlib.util
    spec = importlib.util.spec_from_file_location("sync_upstream_module", sync_script)
    
    if spec is None or spec.loader is None:
        print("❌ Не удалось загрузить модуль sync_upstream.py")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    sync_module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(sync_module)
        exit_code = sync_module.sync_upstream(repo_path, silent=True)
        
        if exit_code != 0:
            print()
            print("❌ Ошибка при синхронизации upstream! Создание ветки прервано.")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Ошибка при вызове sync_upstream: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    return True


def create_branch(repo_path, branch_name):
    """Create and publish a new branch"""
    print()
    print("=" * 40)
    print("🔹 Создание новой ветки")
    print("=" * 40)
    print()
    
    # Check the current branch
    success, current_branch, _ = run_command("git branch --show-current", cwd=repo_path)
    
    if not success or current_branch != "main":
        print(f"⚠️ Текущая ветка: {current_branch}")
        print("🔹 Переключаемся на main...")
        success, _, _ = run_command("git checkout main", cwd=repo_path)
        if not success:
            print("❌ Не удалось переключиться на main! Завершение.")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
    
    # Check that such a branch does not already exist
    success, _, _ = run_command(f"git rev-parse --verify {branch_name}", cwd=repo_path, check=False)
    
    if success:
        print(f"⚠️ Ветка \"{branch_name}\" уже существует локально!")
        print(f"🔄 Автоматическое переключение на существующую ветку...")
        
        success, _, _ = run_command(f"git checkout {branch_name}", cwd=repo_path)
        if not success:
            print(f"❌ Не удалось переключиться на ветку \"{branch_name}\"! Завершение.")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
        print(f"✅ Переключено на существующую ветку \"{branch_name}\"")
        return True
    
    # Create the new branch
    print(f"🔹 Создание и переключение на ветку: {branch_name}")
    success, _, _ = run_command(f"git checkout -b {branch_name}", cwd=repo_path)
    
    if not success:
        print(f"❌ Не удалось создать ветку \"{branch_name}\"! Завершение.")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    print()
    print("=" * 40)
    print(f"✅ Ветка \"{branch_name}\" успешно создана!")
    print(f"✅ Вы находитесь в ветке: {branch_name}")
    print("=" * 40)
    
    return True


def sanitize_folder_name(name):
    """
    Clean the folder name of characters invalid on Windows.
    
    Args:
        name: Original name
        
    Returns:
        Safe folder name
    """
    # Remove characters invalid on Windows: \ / : * ? " < > |
    invalid_chars = r'[\\/:*?"<>|]'
    sanitized = re.sub(invalid_chars, '_', name)
    
    # Remove trailing dots (not allowed on Windows)
    sanitized = sanitized.rstrip('.')
    
    # Trim leading and trailing spaces
    sanitized = sanitized.strip()
    
    return sanitized


def create_branch_folder(initial_path, branch_name):
    """
    Create a folder named after the branch at the originally specified path.
    
    Args:
        initial_path: The path the user originally specified
        branch_name: Name of the created branch
        
    Returns:
        Path object of the created folder or None if declined
    """
    print()
    print("=" * 40)
    print("🔹 Создание рабочей папки")
    print("=" * 40)
    print()
    
    # Clean up the folder name
    folder_name = sanitize_folder_name(branch_name)
    
    if not folder_name:
        print("⚠️  После очистки имя папки пустое, пропускаем создание")
        return None
    
    # Build the full path to the new folder
    target_folder = Path(initial_path) / folder_name
    
    print(f"📁 Планируется создать папку:")
    print(f"   {target_folder}")
    print()
    
    # Check existence
    if target_folder.exists():
        print(f"⚠️  Папка \"{folder_name}\" уже существует по этому пути")
        
        if target_folder.is_dir():
            print("💡 Папка будет использована для работы")
            return target_folder
        else:
            print("❌ Путь существует, но это файл, а не папка")
            return None
    
    # Create the folder automatically
    try:
        target_folder.mkdir(parents=True, exist_ok=True)
        print()
        print(f"✅ Папка успешно создана: {target_folder}")
        return target_folder
        
    except PermissionError:
        print()
        print("❌ Ошибка: Недостаточно прав для создания папки")
        return None
    except OSError as e:
        print()
        print(f"❌ Ошибка при создании папки: {e}")
        return None
    except Exception as e:
        print()
        print(f"❌ Неожиданная ошибка: {e}")
        return None


def publish_branch(repo_path, branch_name):
    """Publish the branch to the remote repository"""
    print()
    print("=" * 40)
    print("🔹 Публикация ветки в удалённый репозиторий")
    print("=" * 40)
    print()
    
    print(f"🔹 Отправка ветки \"{branch_name}\" в origin...")
    success, _, stderr = run_command(f"git push -u origin {branch_name}", cwd=repo_path, check=False)
    
    if not success:
        print()
        print("⚠️ Не удалось опубликовать ветку в удалённый репозиторий!")
        print("💡 Проверьте:")
        print("   - Интернет-соединение")
        print("   - Права доступа к репозиторию")
        print("   - Настройки SSH-ключей")
        print()
        print(f"📌 Вы можете опубликовать ветку позже командой:")
        print(f"   git push -u origin {branch_name}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    print()
    print("=" * 40)
    print(f"✅ Ветка \"{branch_name}\" успешно опубликована!")
    print("=" * 40)
    print()
    print("💡 Подсказка: Теперь вы можете работать с веткой:")
    print("   - git add . (добавить изменения)")
    print("   - git commit -m \"описание\" (зафиксировать изменения)")
    print("   - git push (отправить изменения в удалённый репозиторий)")
    print()


def main():
    """Main function"""
    try:
        print()
        print("=" * 40)
        print("🔹 Скрипт создания новой ветки")
        print("=" * 40)
        print()
        
        # Ask for the repository path
        repo_path_str = input("Введите полный путь к репозиторию: ").strip()
        
        if not repo_path_str:
            print("❌ Путь не может быть пустым!")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
        
        # Save the original path for folder creation
        initial_path = Path(repo_path_str).resolve()
        
        # Check the folder
        if not initial_path.exists():
            print(f"❌ Папка \"{initial_path}\" не найдена! Завершение.")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
        
        # Find the git repository
        repo_path = find_git_repo(initial_path)
        print(f"🔹 Путь к репозиторию: {repo_path}")
        
        # Ask for the branch name
        print()
        branch_name = input("Введите название новой ветки: ").strip()
        
        # Branch name validation
        if not validate_branch_name(branch_name):
            input("Нажмите Enter для выхода...")
            sys.exit(1)
        
        # Sync with upstream
        sync_with_upstream(repo_path)
        
        # Creating the branch
        create_branch(repo_path, branch_name)
        
        # Publish the branch
        publish_branch(repo_path, branch_name)
        
        # Creating a working folder named after the branch
        created_folder = create_branch_folder(initial_path, branch_name)
        
        # Final message
        print()
        print("=" * 40)
        print("✅ ГОТОВО!")
        print("=" * 40)
        if created_folder:
            print(f"📁 Рабочая папка: {created_folder}")
        print(f"🌿 Текущая ветка: {branch_name}")
        print("=" * 40)
        
        input("\nНажмите Enter для выхода...")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()
