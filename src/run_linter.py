"""
Run Super Linter Script

Interactive script for running the super-linter via Docker.
Checks code in the specified repository folder.

Supports two modes:
1. Interactive (default) - detailed output and path prompt
2. Quiet mode (--silent) - minimal output, path passed via --path
"""

import sys
import argparse
import threading
import time
from pathlib import Path
from git_docker_utils import GitDockerUtils


class Spinner:
    """Minimal console loading spinner."""
    
    def __init__(self, message: str = "Проверка"):
        """
        Args:
            message: Message to display next to the spinner
        """
        self.message = message
        self.frames = ['|', '/', '-', '\\']
        self.running = False
        self.thread = None
        self._lock = threading.Lock()
    
    def _animate(self):
        """Spinner animation in a separate thread."""
        idx = 0
        while self.running:
            frame = self.frames[idx % len(self.frames)]
            # \r - carriage return, overwrite the line
            sys.stdout.write(f'\r{frame} {self.message}...')
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)
    
    def __enter__(self):
        """Context manager: start the spinner."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: stop the spinner."""
        self.stop()
        return False
    
    def start(self):
        """Starts the spinner."""
        with self._lock:
            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self._animate, daemon=True)
                self.thread.start()
    
    def stop(self):
        """Stops the spinner and clears the line."""
        with self._lock:
            if self.running:
                self.running = False
                if self.thread:
                    self.thread.join(timeout=1.0)
                # Clear the spinner line
                sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
                sys.stdout.flush()


def print_separator(char: str = "═", length: int = 60) -> None:
    """Prints a separator."""
    print(char * length)


def print_header(text: str) -> None:
    """Prints a section header."""
    print()
    print_separator()
    print(f"🔍 {text}")
    print_separator()
    print()


def run_linter_silent(folder_path: str) -> int:
    """
    Run the linter in quiet mode (minimal output).
    
    Args:
        folder_path: Path to the folder to check
        
    Returns:
        Exit code (0 - success, 1 - error)
    """
    try:
        utils = GitDockerUtils()
        
        # Path validation
        folder = Path(folder_path).resolve()
        if not folder.exists():
            print(f"❌ Папка не существует: {folder_path}")
            return 1
        
        if not folder.is_dir():
            print(f"❌ Указанный путь не является папкой: {folder_path}")
            return 1
        
        # Docker check (quiet)
        docker_ok, _ = utils.check_docker_running()
        if not docker_ok:
            print("❌ Docker не запущен. Запустите Docker Desktop.")
            return 1
        
        # Find the repository root
        repo_root = utils.find_git_root(str(folder))
        if not repo_root:
            print(f"❌ Git репозиторий не найден для: {folder.name}")
            return 1
        
        relative_path = utils.get_relative_path(str(folder), repo_root)
        
        # Automatic linter detection
        selected_linters, file_stats = utils.detect_linters_from_files(folder)
        
        if not selected_linters:
            print("⚠️  Нет файлов для проверки")
            return 1
        
        # Brief launch information
        print(f"🔍 Проверка: {folder.name} ({len(file_stats)} типов файлов, {len(selected_linters)} линтеров)")
        
        # Run the linter with a loading indicator
        with Spinner("Проверка кода"):
            success, output = utils.run_super_linter(
                repo_root,
                relative_path,
                selected_linters
            )
        
        if not success:
            print(output)
            return 1
        
        # Show the full super-linter log
        print()
        print(output)
        
        # Determine the exit code based on errors found
        if utils.has_linter_errors(output):
            return 1
        else:
            print("\n✅ Проверка завершена успешно")
            return 0
        
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        return 1
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return 1


def main() -> int:
    """
    Main super-linter launch function.
    
    Supports command-line arguments:
        --path PATH    : Path to the folder to check
        --silent       : Quiet mode (minimal output)
    
    Returns:
        Exit code (0 - success, 1 - error)
    """
    # Command-line argument parsing
    parser = argparse.ArgumentParser(
        description='Запуск супер-линтера для проверки кода',
        add_help=True
    )
    parser.add_argument(
        '--path',
        type=str,
        help='Путь к папке для проверки (по умолчанию - запрос в интерактивном режиме)'
    )
    parser.add_argument(
        '--silent',
        action='store_true',
        help='Тихий режим - минимальный вывод'
    )
    
    args = parser.parse_args()
    
    # Quiet mode with path
    if args.silent and args.path:
        return run_linter_silent(args.path)
    
    # If only --silent is given without a path - error
    if args.silent and not args.path:
        print("❌ В тихом режиме необходимо указать --path")
        return 1
    
    # Interactive mode (original behavior)
    try:
        print_header("Запуск супер-линтера")
        
        # Initialize the utilities
        utils = GitDockerUtils()
        
        # Step 1: Docker check
        print("🔹 Шаг 1/6: Проверка Docker")
        docker_ok, docker_msg = utils.check_docker_running()
        print(docker_msg)
        
        if not docker_ok:
            print("\n💡 Запустите Docker Desktop и попробуйте снова")
            return 1
        
        print()
        
        # Step 2: Get the folder path
        print("🔹 Шаг 2/6: Укажите путь к папке для проверки")
        print()
        print("Пример:")
        print("  C:\\Users\\...\\WT-AC-2025 (Kotkovets)\\students\\KotkovetsKirill\\task_05")
        print()
        
        # If the path is passed via argument, use it
        if args.path:
            folder_path = args.path
            print(f"Используется путь из аргумента: {folder_path}")
        else:
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
        
        # Step 3: Find the repository root
        print("🔹 Шаг 3/6: Поиск корня Git репозитория")
        
        repo_root = utils.find_git_root(str(folder))
        
        if not repo_root:
            print(f"\n❌ Не удалось найти корень Git репозитория")
            print(f"   Убедитесь, что папка находится внутри Git репозитория")
            return 1
        
        print(f"✅ Корень репозитория: {repo_root}")
        
        # Compute the relative path
        relative_path = utils.get_relative_path(str(folder), repo_root)
        print(f"✅ Относительный путь: {relative_path}")
        print()
        
        # Step 4: Configuration check
        print("🔹 Шаг 4/6: Проверка конфигурации")
        
        has_config = utils.check_config_exists(repo_root, ".markdownlint.yaml")
        if has_config:
            print("✅ Конфигурация .markdownlint.yaml найдена в корне репозитория")
        else:
            print("⚠️  Конфигурация .markdownlint.yaml не найдена в корне")
            print("   Супер-линтер будет использовать настройки по умолчанию")
        
        print()
        
        # Step 5: Automatic linter detection
        print("🔹 Шаг 5/6: Анализ файлов и выбор линтеров")
        print()
        print("⏳ Сканирование файлов в папке...")
        
        selected_linters, file_stats = utils.detect_linters_from_files(folder)
        
        if not selected_linters:
            print("\n⚠️  Не найдено файлов для проверки")
            print("   Убедитесь, что в папке есть файлы с поддерживаемыми расширениями")
            return 1
        
        # Show the found files statistics
        print()
        print("📊 Статистика файлов:")
        for ext, count in sorted(file_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ext:15s} — {count} файл(ов)")
        
        # Show the automatically selected linters
        print()
        print(f"🔍 Автоматически выбрано линтеров: {len(selected_linters)}")
        for linter in selected_linters:
            desc = utils.get_linter_description(linter)
            print(f"   ✓ {desc}")
        
        print()
        
        # Show the launch parameters
        print_separator("─")
        print("📋 Параметры запуска:")
        print(f"   Репозиторий: {repo_root}")
        print(f"   Проверяемая папка: {relative_path}")
        print(f"   Типов файлов: {len(file_stats)}")
        print(f"   Линтеров: {len(selected_linters)}")
        print_separator("─")
        print()
        
        # Step 6: Run the linter
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
        
        # Show the full super-linter log
        print_header("Результаты проверки")
        print(output)
        print()
        
        # Return the exit code
        if utils.has_linter_errors(output):
            return 1
        else:
            print("✅ Проверка завершена успешно")
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
