# Git Helper - AI Agent Instructions

## Project Overview

Git Helper - это инструмент автоматизации Git/SSH workflow для студенческих проектов. Центральная точка входа - `git_helper.bat` (Windows batch-файл с меню), который запускает Python-скрипты из папки `src/`.

**Целевая аудитория:** Студенты с множественными GitHub-аккаунтами, работающие над разными курсовыми репозиториями.

## Core Architecture

### Entry Point Pattern

- **Main Menu:** [git_helper.bat](../git_helper.bat) - batch-скрипт, который:
  - Создаёт/активирует Python venv
  - Показывает интерактивное меню (1-7)
  - Вызывает соответствующие Python-модули из `src/`
- **Quick Lint:** [quick_lint.bat](../quick_lint.bat) - минималистичный запуск линтера:
  - Запускается из любой директории (добавить в PATH)
  - Использует текущую директорию как целевую
  - venv всегда из `%SCRIPT_DIR%` (где лежит bat)
  - Синтаксис: `quick_lint` (без аргументов)
  
### Path Convention (КРИТИЧНО!)

Все скрипты парсят специфичный паттерн путей:

```text
C:\Users\...\{ДИСЦИПЛИНА} ({Фамилия})\students\{ФамилияИмя}\...
```

Примеры:

- `WT-AC-2025 (Kozlovskaya)` - корень форка репозитория
- `WT-AC-2025 (Kozlovskaya)\students\KozlovskayaAnna\task_05` - папка с заданием

**Regex паттерн:** `^(.+?)\s*\(([^)]+)\)$` парсит `{repo_name} ({surname})`

### Module Organization

```text
src/
├── ssh_manager.py         # SSHManager class - ядро для всех SSH операций
├── create_ssh_key.py      # CLI обёртка для SSHManager.generate_ssh_key()
├── delete_ssh_key.py      # CLI обёртка для SSHManager.remove_ssh_key()
├── clone_repository.py    # Парсит путь → находит SSH ключ → клонирует
├── sync_upstream.py       # Синхронизация main с upstream (brstu/{discipline})
├── create_branch.py       # Импортирует sync_upstream.py → создаёт ветку
├── git_docker_utils.py    # GitDockerUtils class для линтера
└── run_linter.py          # CLI обёртка для супер-линтера через Docker
```

## Key Design Patterns

### 1. SSHManager Class Pattern

`ssh_manager.py` - единственный модуль, работающий с SSH. Все остальные импортируют его.

**Ключевая конвенция:** SSH host = `github-{ФамилияИмя}`, ключ = `id_ed25519_{ФамилияИмя}`

```python
# Пример использования в других модулях:
from ssh_manager import SSHManager
ssh_mgr = SSHManager()
full_name = ssh_mgr.get_full_name_from_config(surname)  # Kozlovskaya → KozlovskayaAnna
```

### 2. Module Importation Pattern (cross-script calls)

`create_branch.py` ИМПОРТИРУЕТ `sync_upstream.py` динамически через `importlib`:

```python
spec = importlib.util.spec_from_file_location("sync_upstream_module", sync_script)
sync_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_module)
exit_code = sync_module.sync_upstream(repo_path, silent=True)
```

**Почему:** Избегает дублирования логики синхронизации upstream.

### 3. Path Resolution Pattern

Все модули с парсингом путей используют:

```python
def find_repo_folder(path) -> Optional[Tuple[Path, str]]:
    """Поднимается вверх по дереву до паттерна '{repo} ({surname})'"""
    # Используется в: clone_repository.py, sync_upstream.py
```

### 4. Git Root Discovery

`git_docker_utils.py` и другие поднимаются до `.git`:

```python
def find_git_root(start_path) -> Optional[Path]:
    while current != current.parent:
        if (current / ".git").exists():
            return current
```

### 5. Encoding Handling (Windows-specific)

Все subprocess вызовы используют:

```python
import locale
console_encoding = locale.getpreferredencoding()
subprocess.run(..., encoding=console_encoding, errors='replace')
```

**Причина:** Кириллица в путях/именах файлов на Windows.

## Critical Workflows

### Super-Linter Integration

[run_linter.py](../src/run_linter.py) + [git_docker_utils.py](../src/git_docker_utils.py):

1. **Auto-detection:** Сканирует файлы → определяет расширения → автоматически выбирает линтеры
2. **Docker invocation:** Монтирует корень репозитория в `/tmp/lint`, проверяет только относительный путь
3. **Config:** Ищет `.markdownlint.yaml` в корне репозитория (не в проверяемой папке!)
4. **Dual Mode:** Интерактивный (по умолчанию) + тихий режим (`--silent --path`)

**CLI аргументы:**

```bash
python run_linter.py                    # Интерактивный режим
python run_linter.py --path "C:\..."   # Интерактивный с предзаполненным путём
python run_linter.py --path "C:\..." --silent  # Тихий режим (для quick_lint)
```

**Команда Docker:**

```python
docker run --rm -e RUN_LOCAL=true \
  -e FILTER_REGEX_INCLUDE="students/.*" \
  -e VALIDATE_MARKDOWN=true \
  -v /path/to/repo:/tmp/lint \
  ghcr.io/super-linter/super-linter:v6
```

### Upstream Sync Pattern

`sync_upstream.py` формирует URL: `git@github-{surname}:brstu/{discipline}.git`

- Фамилия из паттерна пути → SSH host
- Дисциплина (например, `WT-AC-2025`) → имя оригинального репозитория

### Branch Creation Flow

1. Импортирует `sync_upstream.py`
2. Синхронизирует main с upstream (brstu)
3. Создаёт ветку от обновлённого main
4. Публикует в origin (форк студента)

## Conventions & Best Practices

### Error Handling

- Все функции возвращают `Tuple[bool, str]` для (успех, сообщение)
- Вывод с эмодзи: ✅ успех, ❌ ошибка, ⚠️ предупреждение, 🔹 инфо

### User Output Style

```python
def print_separator(char: str = "═", length: int = 60) -> None:
def print_header(text: str) -> None:
    print_separator()
    print(f"📦 {text}")
    print_separator()
```

**Используется везде!** Сохраняйте консистентность.

### Validation Pattern

SSHManager содержит regex-валидацию для:

- GitHub username: `^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38})?$`
- Имя/фамилия: `^[a-zA-Zа-яА-ЯёЁ]{2,50}$`

### Config Management

SSH config обновляется атомарно:

```python
def update_ssh_config(full_name: str):
    # 1. Читает весь config
    # 2. Ищет существующую запись для Host github-{full_name}
    # 3. Обновляет или добавляет новую
    # 4. Записывает обратно
```

## External Dependencies

- **Python 3.8+** (проверяется в git_helper.bat)
- **Git** + **Git Bash** (для ssh-agent на Windows)
- **Docker Desktop** (только для супер-линтера, пункт 6)

## Testing & Development

### Run Individual Scripts
Quick Lint Setup

```bash
# Добавить в PATH переменную среды Windows:
C:\Users\kseni\Documents\GitHub\git_helper

# Использование откуда угодно:
cd C:\Projects\MyRepo\task_01
quick_lint  # Проверит текущую директорию

# Внутреннее поведение:
# 1. %SCRIPT_DIR% → C:\Users\kseni\Documents\GitHub\git_helper
# 2. %TARGET_DIR% → %CD% (текущая директория)
# 3. Активирует venv из SCRIPT_DIR
# 4. Вызывает: python run_linter.py --path TARGET_DIR --silent
```

### 
```bash
# Активировать venv
venv\Scripts\activate

# Запустить модуль напрямую
python src\create_ssh_key.py
```

### Path Testing

Используйте тестовые пути формата:

```text
C:\Test\WT-AC-2025 (TestSurname)\students\TestSurnameFirst\task_01
```

## Important Notes

- **НИКОГДА не изменяйте паттерн пути** `{repo} ({surname})` - весь проект завязан на нём
- **SSH keys БЕЗ passphrase** (для автоматизации) - см. `generate_ssh_key()` с `-N ""`
- **Git config настраивается автоматически** при клонировании через `clone_repository.py`
- **Документация живёт в `doc/`**, но README.md в корне - главная точка входа для пользователей
