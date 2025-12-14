"""
Run Super Linter Script

Интерактивный скрипт для запуска супер-линтера через Docker.
Проверяет код в указанной папке репозитория.
"""

import sys
from pathlib import Path
from git_docker_utils import GitDockerUtils


def print_separator(char: str = "═", length: int = 60) -> None:
    """Печатает разделитель."""
    print(char * length)


def print_header(text: str) -> None:
    """Печатает заголовок раздела."""
    print()
    print_separator()
    print(f"🔍 {text}")
    print_separator()
    print()


def main() -> int:
    """
    Основная функция запуска супер-линтера.
    
    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        print_header("Запуск супер-линтера")
        
        # Инициализация утилит
        utils = GitDockerUtils()
        
        # Шаг 1: Проверка Docker
        print("🔹 Шаг 1/6: Проверка Docker")
        docker_ok, docker_msg = utils.check_docker_running()
        print(docker_msg)
        
        if not docker_ok:
            print("\n💡 Запустите Docker Desktop и попробуйте снова")
            return 1
        
        print()
        
        # Шаг 2: Получение пути к папке
        print("🔹 Шаг 2/6: Укажите путь к папке для проверки")
        print()
        print("Пример:")
        print("  C:\\Users\\...\\WT-AC-2025 (Kotkovets)\\students\\KotkovetsKirill\\task_05")
        print()
        
        folder_path = input("Путь к папке: ").strip().strip('"').strip("'")
        
        if not folder_path:
            print("\n❌ Путь не может быть пустым")
            return 1
        
        folder = Path(folder_path)
        if not folder.exists():
            print(f"\n❌ Папка не существует: {folder_path}")
            return 1
        
        if not folder.is_dir():
            print(f"\n❌ Указанный путь не является папкой: {folder_path}")
            return 1
        
        print(f"\n✅ Папка найдена: {folder.name}")
        print()
        
        # Шаг 3: Поиск корня репозитория
        print("🔹 Шаг 3/6: Поиск корня Git репозитория")
        
        repo_root = utils.find_git_root(str(folder))
        
        if not repo_root:
            print(f"\n❌ Не удалось найти корень Git репозитория")
            print(f"   Убедитесь, что папка находится внутри Git репозитория")
            return 1
        
        print(f"✅ Корень репозитория: {repo_root}")
        
        # Вычисляем относительный путь
        relative_path = utils.get_relative_path(str(folder), repo_root)
        print(f"✅ Относительный путь: {relative_path}")
        print()
        
        # Шаг 4: Проверка конфигурации
        print("🔹 Шаг 4/6: Проверка конфигурации")
        
        has_config = utils.check_config_exists(repo_root, ".markdownlint.yaml")
        if has_config:
            print("✅ Конфигурация .markdownlint.yaml найдена в корне репозитория")
        else:
            print("⚠️  Конфигурация .markdownlint.yaml не найдена в корне")
            print("   Супер-линтер будет использовать настройки по умолчанию")
        
        print()
        
        # Шаг 5: Автоматическое определение линтеров
        print("🔹 Шаг 5/6: Анализ файлов и выбор линтеров")
        print()
        print("⏳ Сканирование файлов в папке...")
        
        selected_linters, file_stats = utils.detect_linters_from_files(folder)
        
        if not selected_linters:
            print("\n⚠️  Не найдено файлов для проверки")
            print("   Убедитесь, что в папке есть файлы с поддерживаемыми расширениями")
            return 1
        
        # Показываем статистику найденных файлов
        print()
        print("📊 Статистика файлов:")
        for ext, count in sorted(file_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ext:15s} — {count} файл(ов)")
        
        # Показываем автоматически выбранные линтеры
        print()
        print(f"🔍 Автоматически выбрано линтеров: {len(selected_linters)}")
        for linter in selected_linters:
            desc = utils.get_linter_description(linter)
            print(f"   ✓ {desc}")
        
        print()
        
        # Показываем параметры запуска
        print_separator("─")
        print("📋 Параметры запуска:")
        print(f"   Репозиторий: {repo_root}")
        print(f"   Проверяемая папка: {relative_path}")
        print(f"   Типов файлов: {len(file_stats)}")
        print(f"   Линтеров: {len(selected_linters)}")
        print_separator("─")
        print()
        
        # Шаг 6: Запуск линтера
        print_header("Шаг 6/6: Запуск супер-линтера")
        
        print("⏳ Выполняется проверка...")
        print("   (это может занять некоторое время)")
        print()
        
        success, output = utils.run_super_linter(
            repo_root,
            relative_path,
            selected_linters
        )
        
        if not success:
            print(output)
            return 1
        
        # # ВРЕМЕННО: Выводим полный лог
        # print_header("ПОЛНЫЙ ВЫВОД СУПЕР-ЛИНТЕРА (DEBUG)")
        # print(output)
        # print()
        # print("=" * 60)
        # print(f"Длина вывода: {len(output)} символов")
        # print(f"Строк: {len(output.split(chr(10)))}")
        # print("=" * 60)
        # print()
        
        # Парсим и форматируем результаты
        fatal, errors, warnings = utils.parse_linter_output(output)
        formatted_results = utils.format_results(fatal, errors, warnings)
        
        # Вывод результатов
        print_header("Результаты проверки")
        print(formatted_results)
        print()
        
        # Возвращаем код выхода
        if fatal or errors:
            return 1
        else:
            return 0
        
    except KeyboardInterrupt:
        print("\n\n❌ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
