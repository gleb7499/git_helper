#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт синхронизации upstream
Обновляет ветку main форка из оригинального репозитория
"""

import os
import sys
import subprocess
import re
from pathlib import Path


def run_command(command, cwd=None, check=True):
    """Выполнить команду и вернуть результат"""
    try:
        # Определяем кодировку консоли Windows
        import locale
        console_encoding = locale.getpreferredencoding()
        
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            encoding=console_encoding,
            errors='replace',  # Заменяем проблемные символы
            shell=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except Exception as e:
        return False, "", str(e)


def find_repo_folder(path):
    """
    Найти папку репозитория с паттерном "DISCIPLINE (Surname)"
    Если текущая папка не подходит, ищет в родительской
    """
    path = Path(path).resolve()
    folder_name = path.name
    
    # Паттерн: "WT-AC-2025 (Kozlovskaya)"
    pattern = re.compile(r'^.+ \(.+\)$')
    
    if pattern.match(folder_name):
        return path, folder_name
    
    # Проверяем родительскую папку
    parent_path = path.parent
    parent_name = parent_path.name
    
    if pattern.match(parent_name):
        print(f"🔹 Папка \"{folder_name}\" не соответствует паттерну, найден репозиторий выше...")
        print(f"🔹 Найден репозиторий: {parent_name}")
        return parent_path, parent_name
    
    # Поднимаемся выше по дереву, пока не найдем паттерн или не достигнем корня
    current = path.parent.parent
    while current.parent != current:  # Пока не достигли корня диска
        current_name = current.name
        if pattern.match(current_name):
            print(f"🔹 Папка \"{folder_name}\" не соответствует паттерну, найден репозиторий выше...")
            print(f"🔹 Найден репозиторий: {current_name}")
            return current, current_name
        current = current.parent
    
    print(f"❌ Не удалось найти репозиторий с паттерном \"DISCIPLINE (Surname)\"!")
    return None, None


def parse_repo_name(repo_name):
    """
    Парсит имя репозитория для извлечения дисциплины и фамилии
    Формат: "WT-AC-2025 (Kozlovskaya)" -> discipline="WT-AC-2025", surname="Kozlovskaya"
    """
    match = re.match(r'^(.+) \((.+)\)$', repo_name)
    if not match:
        print(f"❌ Не удалось распарсить имя репозитория: {repo_name}")
        sys.exit(1)
    
    discipline = match.group(1).strip()
    surname = match.group(2).strip()
    
    return discipline, surname


def sync_upstream(repo_path, silent=False):
    """
    Синхронизировать ветку main с upstream
    
    Args:
        repo_path: Path объект или строка с путем к репозиторию
        silent: Если True, не выводить заголовки и не ждать нажатия Enter
    
    Returns:
        0 при успехе, 1 при ошибке
    """
    # Преобразуем в Path, если передана строка
    if isinstance(repo_path, str):
        repo_path = Path(repo_path)
    
    if not silent:
        print()
        print("=" * 40)
        print("🔹 Скрипт синхронизации upstream")
        print("=" * 40)
        print()
    
    # Проверяем существование папки
    if not repo_path.exists():
        print(f"❌ Папка \"{repo_path}\" не найдена! Завершение.")
        return 1
    
    # Находим папку репозитория
    repo_path, repo_name = find_repo_folder(repo_path)
    
    if repo_path is None or repo_name is None:
        return 1
    
    print(f"🔹 Имя репозитория: {repo_name}")
    
    # Парсим имя репозитория
    discipline, surname = parse_repo_name(repo_name)
    print(f"🔹 Дисциплина: {discipline}")
    print(f"🔹 Фамилия: {surname}")
    
    # Формируем UPSTREAM
    upstream = f"git@github-{surname}:brstu/{discipline}.git"
    print(f"🔹 Upstream: {upstream}")
    
    print()
    print("=" * 40)
    print(f"🔹 Синхронизация репозитория: {repo_name}")
    print("=" * 40)
    print()
    
    # Настройка upstream
    print("🔹 Добавляем/обновляем upstream...")
    run_command(f"git remote add upstream {upstream}", cwd=repo_path, check=False)
    success, _, _ = run_command(f"git remote set-url upstream {upstream}", cwd=repo_path, check=False)
    
    if not success:
        print("⚠️ Ошибка при настройке upstream, продолжаем...")
    
    # Проверка ветки main
    success, _, _ = run_command("git rev-parse --verify main", cwd=repo_path, check=False)
    if not success:
        print("❌ Ветка main не найдена! Завершение.")
        return 1
    
    # Обновление main
    print("🔹 Переключаемся на main и обновляем...")
    success, _, _ = run_command("git checkout main", cwd=repo_path)
    if not success:
        print("❌ Не удалось переключиться на main. Завершение.")
        return 1
    
    success, _, _ = run_command("git fetch upstream", cwd=repo_path)
    if not success:
        print("❌ Ошибка при fetch upstream. Проверьте SSH и интернет.")
        return 1
    
    success, _, _ = run_command("git reset --hard upstream/main", cwd=repo_path)
    if not success:
        print("❌ Ошибка при reset. Завершение.")
        return 1
    
    success, _, _ = run_command("git push origin main --force", cwd=repo_path, check=False)
    if not success:
        print("⚠️ Ошибка при пуше main в форк. Возможно, нет доступа или защита ветки.")
    
    # Пушим остальные изменения
    print("🔹 Пушим остальные изменения в форк клиента...")
    success, _, _ = run_command("git push origin", cwd=repo_path, check=False)
    if not success:
        print("⚠️ Ошибка при пуше изменений. Проверьте права и SSH.")
    
    if not silent:
        print()
        print("=" * 40)
        print("✅ Синхронизация завершена!")
        print("=" * 40)
    
    return 0


def main():
    """Главная функция"""
    try:
        # Запрос пути к репозиторию
        repo_path_str = input("Введите полный путь к репозиторию: ").strip()
        
        if not repo_path_str:
            print("❌ Путь не может быть пустым!")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
        
        repo_path = Path(repo_path_str)
        
        # Синхронизация
        exit_code = sync_upstream(repo_path)
        
        input("Нажмите Enter для выхода...")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()
