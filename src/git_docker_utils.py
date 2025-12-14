"""
Git Docker Utilities Module

Модуль для работы с Docker и Git репозиториями.
Поддерживает поиск корня репозитория, запуск супер-линтера и обработку результатов.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List


class GitDockerUtils:
    """Утилиты для работы с Git и Docker."""
    
    def __init__(self):
        """Инициализация утилит."""
        self.super_linter_image = "ghcr.io/super-linter/super-linter:v6"
    
    def find_git_root(self, start_path: str) -> Optional[Path]:
        """
        Находит корень Git репозитория, поднимаясь вверх по дереву каталогов.
        
        Args:
            start_path: Путь, от которого начинать поиск
            
        Returns:
            Path к корню репозитория или None если не найден
        """
        current = Path(start_path).resolve()
        
        # Поднимаемся вверх до тех пор, пока не найдем .git
        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.exists():
                return current
            current = current.parent
        
        return None
    
    def get_relative_path(self, full_path: str, repo_root: Path) -> str:
        """
        Вычисляет относительный путь от корня репозитория.
        
        Args:
            full_path: Полный путь к папке
            repo_root: Корень репозитория
            
        Returns:
            Относительный путь в Unix формате
        """
        full = Path(full_path).resolve()
        relative = full.relative_to(repo_root)
        # Преобразуем в Unix формат (для Docker)
        return str(relative).replace("\\", "/")
    
    def check_docker_running(self) -> Tuple[bool, str]:
        """
        Проверяет, запущен ли Docker.
        
        Returns:
            Tuple (успех, сообщение)
        """
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "✅ Docker запущен и доступен"
            else:
                return False, "❌ Docker не отвечает. Убедитесь, что Docker Desktop запущен."
        except subprocess.TimeoutExpired:
            return False, "❌ Docker не отвечает (timeout). Запустите Docker Desktop."
        except FileNotFoundError:
            return False, "❌ Docker не установлен. Установите Docker Desktop."
        except Exception as e:
            return False, f"❌ Ошибка проверки Docker: {str(e)}"
    
    def check_config_exists(self, repo_root: Path, config_name: str = ".markdownlint.yaml") -> bool:
        """
        Проверяет наличие конфигурационного файла в корне репозитория.
        
        Args:
            repo_root: Корень репозитория
            config_name: Имя конфига
            
        Returns:
            True если файл существует
        """
        config_path = repo_root / config_name
        return config_path.exists()
    
    def run_super_linter(
        self,
        repo_root: Path,
        relative_path: str,
        linters: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Запускает супер-линтер через Docker.
        
        Args:
            repo_root: Корень Git репозитория
            relative_path: Относительный путь к проверяемой папке
            linters: Список линтеров для активации (по умолчанию только MARKDOWN)
            
        Returns:
            Tuple (успех, вывод команды)
        """
        try:
            # Формируем команду Docker
            if linters is None:
                linters = ["MARKDOWN"]
            
            # Базовые параметры
            docker_cmd = [
                "docker", "run", "--rm",
                "-e", "RUN_LOCAL=true",
                "-e", "DEFAULT_BRANCH=main",
                "-e", "VALIDATE_ALL_CODEBASE=false",
                # Конфигурация линтеров (как в GitHub Actions)
                "-e", "LINTER_RULES_PATH=.",
                "-e", "MARKDOWN_CONFIG_FILE=.markdownlint.yaml",
            ]
            
            # Добавляем активацию линтеров
            for linter in linters:
                docker_cmd.extend(["-e", f"VALIDATE_{linter}=true"])
            
            # Добавляем фильтр для конкретной папки (regex должен начинаться с .*)
            filter_regex = f".*{relative_path}/.*"
            docker_cmd.extend(["-e", f"FILTER_REGEX_INCLUDE={filter_regex}"])
            
            # Исключаем папки (как в GitHub Actions)
            docker_cmd.extend(["-e", "FILTER_REGEX_EXCLUDE=(node_modules/|tools/ci/out/)"])
            
            # Монтируем корень репозитория
            # Используем абсолютный путь для Windows
            mount_path = str(repo_root).replace("\\", "/")
            docker_cmd.extend(["-v", f"{mount_path}:/tmp/lint"])
            
            # Добавляем образ
            docker_cmd.append(self.super_linter_image)
            
            # Запускаем Docker
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False,
                cwd=str(repo_root),
                shell=False
            )
            
            # Собираем вывод
            output = result.stdout + result.stderr
            
            return True, output
            
        except Exception as e:
            return False, f"❌ Ошибка запуска Docker: {str(e)}"
    
    def parse_linter_output(self, output: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Парсит вывод супер-линтера и группирует по типам.
        Извлекает детальные ошибки из блоков Stderr contents.
        
        Args:
            output: Вывод супер-линтера
            
        Returns:
            Tuple (fatal_errors, errors, warnings)
        """
        fatal_errors = []
        errors = []
        warnings = []
        
        lines = output.split("\n")
        i = 0
        current_linter = None
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Определяем текущий линтер
            if "[INFO]   Linting" in line and "items..." in line:
                # Извлекаем имя: "2025-12-14 11:04:03 [INFO]   Linting MARKDOWN items..."
                parts = line.split("Linting")
                if len(parts) > 1:
                    current_linter = parts[1].replace("items...", "").strip()
            
            # Ищем блок с детальными ошибками "Stderr contents for"
            if "Stderr contents for" in line:
                linter_name = current_linter or "Unknown"
                i += 1
                
                # Пропускаем разделитель "------"
                if i < len(lines) and "------" in lines[i]:
                    i += 1
                
                # Читаем строки до следующего "------"
                while i < len(lines):
                    stderr_line = lines[i].strip()
                    if "------" in stderr_line:
                        break
                    if stderr_line and len(stderr_line) > 5:
                        # Это реальная ошибка линтера
                        errors.append(f"[{linter_name}] {stderr_line}")
                    i += 1
                i += 1
                continue
            
            # Ищем строки с [ERROR] (общие сообщения)
            if "[ERROR]" in line:
                # Пропускаем итоговые/сводные сообщения
                if "Found errors when linting" in line:
                    pass
                elif "Super-linter detected linting errors" in line:
                    pass
                elif "Errors found in" in line:
                    # Например: "Errors found in MARKDOWN" - итоговое сообщение
                    pass
                elif "0 error" not in line.lower():
                    errors.append(line)
            
            # Ищем WARNING (пропускаем технические)
            elif "[WARN]" in line or "[WARNING]" in line:
                if "0 warning" not in line.lower():
                    if "DeprecationWarning" not in line and "chktex" not in line and "punycode" not in line:
                        warnings.append(line)
            
            # Ищем FATAL
            elif "[FATAL]" in line:
                fatal_errors.append(line)
            
            i += 1
        
        return fatal_errors, errors, warnings
    
    def format_results(
        self,
        fatal_errors: List[str],
        errors: List[str],
        warnings: List[str]
    ) -> str:
        """
        Форматирует результаты проверки для вывода пользователю.
        
        Args:
            fatal_errors: Список критических ошибок
            errors: Список ошибок
            warnings: Список предупреждений
            
        Returns:
            Отформатированная строка результатов
        """
        if not fatal_errors and not errors and not warnings:
            return "✅ Проверка завершена успешно, ошибок не обнаружено"
        
        result_lines = []
        
        if fatal_errors:
            result_lines.append("\n🔴 КРИТИЧЕСКИЕ ОШИБКИ:")
            result_lines.append("=" * 60)
            result_lines.extend(fatal_errors)
            result_lines.append("")
        
        if errors:
            result_lines.append("\n❌ ОШИБКИ:")
            result_lines.append("=" * 60)
            result_lines.extend(errors)
            result_lines.append("")
        
        if warnings:
            result_lines.append("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            result_lines.append("=" * 60)
            result_lines.extend(warnings)
            result_lines.append("")
        
        # Статистика
        total = len(fatal_errors) + len(errors) + len(warnings)
        result_lines.append(f"\n📊 Итого: {total} проблем(ы)")
        result_lines.append(f"   🔴 Критических: {len(fatal_errors)}")
        result_lines.append(f"   ❌ Ошибок: {len(errors)}")
        result_lines.append(f"   ⚠️  Предупреждений: {len(warnings)}")
        
        return "\n".join(result_lines)
    
    def get_extension_to_linter_mapping(self) -> dict:
        """
        Возвращает маппинг расширений файлов на линтеры супер-линтера.
        
        Returns:
            Словарь {расширение: список_линтеров}
        """
        return {
            ".md": ["MARKDOWN"],
            ".markdown": ["MARKDOWN"],
            ".js": ["JAVASCRIPT_ES"],
            ".jsx": ["JAVASCRIPT_ES"],
            ".py": ["PYTHON_PYLINT", "PYTHON_FLAKE8"],
            ".html": ["HTML"],
            ".htm": ["HTML"],
            ".css": ["CSS"],
            ".scss": ["CSS"],
            ".json": ["JSON"],
            ".yml": ["YAML"],
            ".yaml": ["YAML"],
            ".sh": ["BASH"],
            ".bash": ["BASH"],
            ".ts": ["TYPESCRIPT_ES"],
            ".tsx": ["TYPESCRIPT_ES"],
            ".xml": ["XML"],
            ".sql": ["SQL"],
            ".dockerfile": ["DOCKERFILE_HADOLINT"],
        }
    
    def scan_directory_for_file_types(self, directory: Path) -> dict:
        """
        Сканирует директорию и определяет все типы файлов.
        Исключает node_modules и tools/ci/out.
        
        Args:
            directory: Путь к директории для сканирования
            
        Returns:
            Словарь {расширение: количество_файлов}
        """
        file_types = {}
        
        # Папки для исключения (как в GitHub Actions)
        excluded_dirs = {'node_modules', 'tools'}
        
        try:
            # Рекурсивно обходим все файлы
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    # Проверяем, находится ли файл в исключенных директориях
                    parts = file_path.relative_to(directory).parts
                    if any(excluded_dir in parts for excluded_dir in excluded_dirs):
                        continue
                    
                    # Получаем расширение (в нижнем регистре)
                    ext = file_path.suffix.lower()
                    
                    # Пропускаем файлы без расширения и скрытые файлы
                    if not ext or file_path.name.startswith("."):
                        continue
                    
                    # Считаем файлы по расширениям
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return file_types
            
        except Exception as e:
            print(f"⚠️  Ошибка сканирования директории: {str(e)}")
            return {}
    
    def detect_linters_from_files(self, directory: Path) -> Tuple[List[str], dict]:
        """
        Автоматически определяет нужные линтеры на основе найденных файлов.
        
        Args:
            directory: Путь к директории для анализа
            
        Returns:
            Tuple (список_линтеров, статистика_файлов)
        """
        # Сканируем директорию
        file_types = self.scan_directory_for_file_types(directory)
        
        if not file_types:
            return [], {}
        
        # Получаем маппинг расширений на линтеры
        ext_to_linters = self.get_extension_to_linter_mapping()
        
        # Собираем уникальные линтеры
        detected_linters = set()
        for ext, count in file_types.items():
            if ext in ext_to_linters:
                detected_linters.update(ext_to_linters[ext])
        
        return sorted(list(detected_linters)), file_types
    
    def get_linter_description(self, linter_code: str) -> str:
        """
        Возвращает описание линтера.
        
        Args:
            linter_code: Код линтера
            
        Returns:
            Описание линтера
        """
        descriptions = {
            "MARKDOWN": "Markdown",
            "JAVASCRIPT_ES": "JavaScript/ES",
            "TYPESCRIPT_ES": "TypeScript",
            "PYTHON_PYLINT": "Python (Pylint)",
            "PYTHON_BLACK": "Python (Black)",
            "PYTHON_FLAKE8": "Python (Flake8)",
            "HTML": "HTML",
            "CSS": "CSS/SCSS",
            "JSON": "JSON",
            "YAML": "YAML",
            "BASH": "Bash",
            "XML": "XML",
            "SQL": "SQL",
            "DOCKERFILE_HADOLINT": "Dockerfile",
        }
        return descriptions.get(linter_code, linter_code)
