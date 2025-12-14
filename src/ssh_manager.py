"""
SSH Manager Module

Модуль для безопасного управления SSH ключами и конфигурацией.
Поддерживает генерацию ключей, настройку SSH config и управление ssh-agent.
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple


class SSHManager:
    """Менеджер для работы с SSH ключами и конфигурацией."""
    
    def __init__(self):
        """Инициализация менеджера SSH."""
        self.ssh_dir = Path.home() / ".ssh"
        self.config_path = self.ssh_dir / "config"
        
    def ensure_ssh_directory(self) -> None:
        """Создает директорию .ssh если её нет."""
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
    def validate_username(self, username: str) -> bool:
        """
        Проверяет корректность GitHub username.
        
        Args:
            username: GitHub username для проверки
            
        Returns:
            True если username валиден, иначе False
        """
        # GitHub username может содержать только буквы, цифры и дефисы
        # Не может начинаться с дефиса и должен быть от 1 до 39 символов
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38})?$'
        return bool(re.match(pattern, username))
    
    def validate_name(self, name: str) -> bool:
        """
        Проверяет корректность имени/фамилии.
        
        Args:
            name: Имя или фамилия для проверки
            
        Returns:
            True если имя валидно, иначе False
        """
        # Имя должно содержать только буквы (латиница/кириллица)
        # и быть от 2 до 50 символов
        pattern = r'^[a-zA-Zа-яА-ЯёЁ]{2,50}$'
        return bool(re.match(pattern, name))
    
    def generate_ssh_key(self, username: str, full_name: str) -> Tuple[bool, str]:
        """
        Генерирует новый SSH ключ ed25519.
        
        Args:
            username: GitHub username
            full_name: Полное имя (фамилия + имя без пробелов, например KozlovskayaAnna)
            
        Returns:
            Tuple (успех, сообщение)
        """
        try:
            self.ensure_ssh_directory()
            
            # Формируем имена файлов
            key_name = f"id_ed25519_{full_name}"
            key_path = self.ssh_dir / key_name
            
            # Проверяем, не существует ли уже ключ
            if key_path.exists():
                return False, f"⚠️  Ключ {key_name} уже существует!"
            
            # Генерируем ключ
            cmd = [
                "ssh-keygen",
                "-t", "ed25519",
                "-C", username,
                "-f", str(key_path),
                "-N", ""  # Без пароля
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return False, f"❌ Ошибка генерации ключа: {result.stderr}"
            
            # Устанавливаем правильные права доступа
            key_path.chmod(0o600)
            
            return True, f"✅ SSH ключ успешно создан: {key_name}"
            
        except Exception as e:
            return False, f"❌ Ошибка: {str(e)}"
    
    def add_key_to_agent(self, full_name: str) -> Tuple[bool, str]:
        """
        Добавляет SSH ключ в ssh-agent.
        
        Args:
            full_name: Полное имя для идентификации ключа
            
        Returns:
            Tuple (успех, сообщение)
        """
        try:
            key_path = self.ssh_dir / f"id_ed25519_{full_name}"
            
            if not key_path.exists():
                return False, f"❌ Ключ не найден: {key_path}"
            
            # Добавляем ключ в агент
            cmd = ["ssh-add", str(key_path)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                # Возможно ssh-agent не запущен
                return False, (
                    "❌ Не удалось добавить ключ в ssh-agent.\n"
                    "Возможно, ssh-agent не запущен. Запустите:\n"
                    "  eval \"$(ssh-agent -s)\""
                )
            
            return True, "✅ Ключ добавлен в ssh-agent"
            
        except Exception as e:
            return False, f"❌ Ошибка: {str(e)}"
    
    def get_public_key(self, full_name: str) -> Optional[str]:
        """
        Читает содержимое публичного ключа.
        
        Args:
            full_name: Полное имя для идентификации ключа
            
        Returns:
            Содержимое публичного ключа или None при ошибке
        """
        try:
            pub_key_path = self.ssh_dir / f"id_ed25519_{full_name}.pub"
            
            if not pub_key_path.exists():
                return None
            
            return pub_key_path.read_text(encoding='utf-8').strip()
            
        except Exception:
            return None
    
    def extract_surname(self, full_name: str) -> str:
        """
        Извлекает фамилию из полного имени.
        Предполагается формат: ФамилияИмя (например, GritsukPavel -> Gritsuk)
        
        Args:
            full_name: Полное имя (ФамилияИмя)
            
        Returns:
            Фамилия
        """
        # Используем регулярное выражение для разбиения на заглавные буквы
        # Паттерн: ищем последовательность букв, начинающуюся с заглавной
        parts = re.findall(r'[A-ZА-ЯЁ][a-zа-яё]*', full_name)
        
        # Первая часть - это фамилия
        if parts:
            return parts[0]
        
        # Fallback: если не удалось разобрать, возвращаем весь full_name
        return full_name
    
    def update_ssh_config(self, full_name: str) -> Tuple[bool, str]:
        """
        Добавляет или обновляет запись в SSH config.
        
        Args:
            full_name: Полное имя для идентификации ключа (ФамилияИмя)
            
        Returns:
            Tuple (успех, сообщение)
        """
        try:
            self.ensure_ssh_directory()
            
            # Извлекаем фамилию для Host
            surname = self.extract_surname(full_name)
            host_name = f"github-{surname}"
            
            # Полное имя используется для IdentityFile
            key_path = self.ssh_dir / f"id_ed25519_{full_name}"
            
            # Проверяем существование ключа
            if not key_path.exists():
                return False, f"❌ Ключ не найден: {key_path}"
            
            # Формируем новую запись для config
            new_entry = f"""
Host {host_name}
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile {key_path}
    IdentitiesOnly yes
"""
            
            # Читаем существующий config или создаем новый
            if self.config_path.exists():
                config_content = self.config_path.read_text(encoding='utf-8')
                
                # Проверяем, не существует ли уже запись для этого хоста
                host_pattern = f"Host {host_name}\\s"
                if re.search(host_pattern, config_content):
                    return False, f"⚠️  Запись для {host_name} уже существует в config"
                
                # Добавляем новую запись
                config_content += new_entry
            else:
                config_content = new_entry.lstrip()
            
            # Записываем обновленный config
            self.config_path.write_text(config_content, encoding='utf-8')
            self.config_path.chmod(0o600)
            
            return True, f"✅ SSH config обновлен. Host: {host_name}"
            
        except Exception as e:
            return False, f"❌ Ошибка обновления config: {str(e)}"
    
    def check_ssh_agent_running(self) -> bool:
        """
        Проверяет, запущен ли ssh-agent.
        
        Returns:
            True если ssh-agent запущен, иначе False
        """
        try:
            result = subprocess.run(
                ["ssh-add", "-l"],
                capture_output=True,
                check=False
            )
            # Код возврата 0 или 1 означает, что агент запущен
            # (0 - есть ключи, 1 - нет ключей, но агент работает)
            return result.returncode in [0, 1]
        except Exception:
            return False
    
    def start_ssh_agent_windows(self) -> Tuple[bool, str]:
        """
        Запускает ssh-agent на Windows.
        Пробует несколько методов запуска.
        
        Returns:
            Tuple (успех, сообщение)
        """
        # Метод 1: Попытка запустить службу через sc
        try:
            result = subprocess.run(
                ["sc", "start", "ssh-agent"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 or "уже запущена" in result.stdout.lower() or "running" in result.stdout.lower():
                import time
                time.sleep(1)
                if self.check_ssh_agent_running():
                    return True, "✅ ssh-agent успешно запущен (служба Windows)"
        except Exception:
            pass
        
        # Метод 2: Запуск через net start
        try:
            result = subprocess.run(
                ["net", "start", "ssh-agent"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 or "уже запущена" in result.stdout.lower():
                import time
                time.sleep(1)
                if self.check_ssh_agent_running():
                    return True, "✅ ssh-agent успешно запущен (net start)"
        except Exception:
            pass
        
        # Метод 3: Прямой запуск ssh-agent
        try:
            result = subprocess.run(
                ["ssh-agent"],
                capture_output=True,
                text=True,
                check=False,
                shell=False
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Парсим и устанавливаем переменные окружения
                sock_match = re.search(r'SSH_AUTH_SOCK=([^;]+);', output)
                if sock_match:
                    sock_path = sock_match.group(1)
                    os.environ['SSH_AUTH_SOCK'] = sock_path
                
                pid_match = re.search(r'SSH_AGENT_PID=(\d+);', output)
                if pid_match:
                    os.environ['SSH_AGENT_PID'] = pid_match.group(1)
                
                import time
                time.sleep(0.5)
                
                if self.check_ssh_agent_running():
                    return True, "✅ ssh-agent успешно запущен (прямой запуск)"
        except Exception:
            pass
        
        # Все методы не сработали
        return False, (
            "❌ Не удалось запустить ssh-agent автоматически.\n"
            "   SSH ключи будут работать и без агента, но для удобства\n"
            "   вы можете запустить агент вручную в Git Bash:\n"
            "   eval \"$(ssh-agent -s)\""
        )
    
    def get_host_name_from_full_name(self, full_name: str) -> str:
        """
        Формирует имя хоста на основе полного имени.
        Использует только фамилию (первую часть).
        
        Args:
            full_name: Полное имя пользователя (ФамилияИмя)
            
        Returns:
            Имя хоста для SSH config (github-Фамилия)
        """
        surname = self.extract_surname(full_name)
        return f"github-{surname}"
    
    def list_ssh_keys(self) -> list:
        """
        Возвращает список всех SSH ключей в формате (full_name, host_name).
        
        Returns:
            Список кортежей (полное_имя, host_name)
        """
        keys = []
        
        if not self.ssh_dir.exists():
            return keys
        
        # Ищем все файлы id_ed25519_*
        for key_file in self.ssh_dir.glob("id_ed25519_*"):
            if key_file.suffix != ".pub":  # Только приватные ключи
                # Извлекаем полное имя из имени файла
                full_name = key_file.stem.replace("id_ed25519_", "")
                host_name = self.get_host_name_from_full_name(full_name)
                keys.append((full_name, host_name))
        
        return sorted(keys, key=lambda x: x[1])
    
    def remove_ssh_key(self, full_name: str) -> Tuple[bool, str]:
        """
        Удаляет SSH ключ и все связанные данные:
        - Приватный ключ
        - Публичный ключ
        - Запись из SSH config
        - Ключ из ssh-agent (если загружен)
        
        Args:
            full_name: Полное имя пользователя (ФамилияИмя)
            
        Returns:
            Tuple (успех, сообщение)
        """
        try:
            messages = []
            success_count = 0
            
            # 1. Удаляем приватный ключ
            private_key = self.ssh_dir / f"id_ed25519_{full_name}"
            if private_key.exists():
                private_key.unlink()
                messages.append(f"✅ Удален приватный ключ: {private_key.name}")
                success_count += 1
            else:
                messages.append(f"⚠️  Приватный ключ не найден: {private_key.name}")
            
            # 2. Удаляем публичный ключ
            public_key = self.ssh_dir / f"id_ed25519_{full_name}.pub"
            if public_key.exists():
                public_key.unlink()
                messages.append(f"✅ Удален публичный ключ: {public_key.name}")
                success_count += 1
            else:
                messages.append(f"⚠️  Публичный ключ не найден: {public_key.name}")
            
            # 3. Удаляем из ssh-agent (если агент запущен)
            if self.check_ssh_agent_running():
                result = subprocess.run(
                    ["ssh-add", "-d", str(private_key)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    messages.append("✅ Ключ удален из ssh-agent")
                    success_count += 1
                else:
                    messages.append("⚠️  Ключ не был загружен в ssh-agent")
            else:
                messages.append("⚠️  ssh-agent не запущен (пропуск удаления из агента)")
            
            # 4. Удаляем из SSH config
            success_config, msg_config = self.remove_from_config(full_name)
            if success_config:
                messages.append(msg_config)
                success_count += 1
            else:
                messages.append(msg_config)
            
            # Итоговое сообщение
            if success_count > 0:
                result_msg = "\n".join(messages)
                return True, f"{result_msg}\n\n✅ SSH ключ успешно удален ({success_count} операций)"
            else:
                return False, f"❌ Ничего не удалено. Ключ не найден."
                
        except Exception as e:
            return False, f"❌ Ошибка при удалении ключа: {str(e)}"
    
    def remove_from_config(self, full_name: str) -> Tuple[bool, str]:
        """
        Удаляет запись из SSH config.
        
        Args:
            full_name: Полное имя пользователя
            
        Returns:
            Tuple (успех, сообщение)
        """
        try:
            if not self.config_path.exists():
                return False, "⚠️  Файл config не существует"
            
            # Читаем config
            config_content = self.config_path.read_text(encoding='utf-8')
            
            # Формируем имя хоста для поиска
            host_name = self.get_host_name_from_full_name(full_name)
            
            # Разбиваем на блоки Host
            lines = config_content.split('\n')
            new_lines = []
            skip_block = False
            found = False
            
            for line in lines:
                # Проверяем начало блока Host
                if line.strip().startswith('Host '):
                    # Если это наш блок - пропускаем его
                    if f"Host {host_name}" in line:
                        skip_block = True
                        found = True
                        continue
                    else:
                        skip_block = False
                
                # Если не пропускаем блок, добавляем строку
                if not skip_block:
                    new_lines.append(line)
                elif line.strip().startswith('Host '):
                    # Начался новый блок, перестаем пропускать
                    skip_block = False
                    new_lines.append(line)
            
            if found:
                # Записываем обновленный config
                new_content = '\n'.join(new_lines)
                # Убираем множественные пустые строки
                new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                self.config_path.write_text(new_content, encoding='utf-8')
                return True, f"✅ Удалена запись из config: {host_name}"
            else:
                return False, f"⚠️  Запись {host_name} не найдена в config"
                
        except Exception as e:
            return False, f"❌ Ошибка удаления из config: {str(e)}"
