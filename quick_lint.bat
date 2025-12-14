@echo off
REM =====================================================
REM Quick Lint - Минималистичный запуск линтера
REM Использование: quick_lint (из любой директории)
REM =====================================================

REM Определяем директорию, где лежит этот bat файл
set "SCRIPT_DIR=%~dp0"

REM Сохраняем текущую рабочую директорию (откуда запущена команда)
set "TARGET_DIR=%CD%"

REM Активируем виртуальное окружение из директории скрипта
if not exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found in %SCRIPT_DIR%venv
    echo Please run git_helper.bat first to create the environment.
    exit /b 1
)

call "%SCRIPT_DIR%venv\Scripts\activate.bat" >nul 2>&1

REM Запускаем линтер в тихом режиме с текущей директорией
python "%SCRIPT_DIR%src\run_linter.py" --path "%TARGET_DIR%" --silent

REM Сохраняем код выхода
set EXIT_CODE=%ERRORLEVEL%

REM Деактивируем venv
call "%SCRIPT_DIR%venv\Scripts\deactivate.bat" >nul 2>&1

REM Возвращаем код выхода Python скрипта
exit /b %EXIT_CODE%
