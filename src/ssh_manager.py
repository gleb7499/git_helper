"""
SSH Manager Module

Module for secure management of SSH keys and configuration.
Supports key generation, SSH config setup, and ssh-agent management.
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple


class SSHManager:
    """Manager for working with SSH keys and configuration."""
    
    def __init__(self):
        """Initialize the SSH manager."""
        self.ssh_dir = Path.home() / ".ssh"
        self.config_path = self.ssh_dir / "config"
        
    def ensure_ssh_directory(self) -> None:
        """Creates the .ssh directory if it does not exist."""
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
    def validate_username(self, username: str) -> bool:
        """
        Check that the GitHub username is valid.
        
        Args:
            username: GitHub username to check
            
        Returns:
            True if the username is valid, otherwise False
        """
        # GitHub username may contain only letters, digits, and hyphens
        # Cannot start with a hyphen and must be 1 to 39 characters
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38})?$'
        return bool(re.match(pattern, username))
    
    def validate_name(self, name: str) -> bool:
        """
        Check that the first name/surname is valid.
        
        Args:
            name: First name or surname to check
            
        Returns:
            True if the name is valid, otherwise False
        """
        # The name must contain only letters (Latin/Cyrillic)
        # and be 2 to 50 characters
        pattern = r'^[a-zA-Zа-яА-ЯёЁ]{2,50}$'
        return bool(re.match(pattern, name))
    
    def generate_ssh_key(self, username: str, full_name: str) -> Tuple[bool, str]:
        """
        Generate a new ed25519 SSH key.
        
        Args:
            username: GitHub username
            full_name: Full name (surname + first name without spaces, e.g., KozlovskayaAnna)
            
        Returns:
            Tuple (success, message)
        """
        try:
            self.ensure_ssh_directory()
            
            # Build the file names
            key_name = f"id_ed25519_{full_name}"
            key_path = self.ssh_dir / key_name
            
            # Check that the key does not already exist
            if key_path.exists():
                return False, f"⚠️  Ключ {key_name} уже существует!"
            
            # Generate the key
            cmd = [
                "ssh-keygen",
                "-t", "ed25519",
                "-C", username,
                "-f", str(key_path),
                "-N", ""  # No passphrase
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return False, f"❌ Ошибка генерации ключа: {result.stderr}"
            
            # Set proper file permissions
            key_path.chmod(0o600)
            
            return True, f"✅ SSH ключ успешно создан: {key_name}"
            
        except Exception as e:
            return False, f"❌ Ошибка: {str(e)}"
    
    def add_key_to_agent(self, full_name: str) -> Tuple[bool, str]:
        """
        Add an SSH key to ssh-agent.
        
        Args:
            full_name: Full name identifying the key
            
        Returns:
            Tuple (success, message)
        """
        try:
            key_path = self.ssh_dir / f"id_ed25519_{full_name}"
            
            if not key_path.exists():
                return False, f"❌ Ключ не найден: {key_path}"
            
            # Add the key to the agent
            cmd = ["ssh-add", str(key_path)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                # ssh-agent is probably not running
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
        Read the contents of the public key.
        
        Args:
            full_name: Full name identifying the key
            
        Returns:
            Public key contents or None on error
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
        Extract the surname from the full name.
        Expected format: SurnameFirstName (e.g., GritsukPavel -> Gritsuk)
        
        Args:
            full_name: Full name (SurnameFirstName)
            
        Returns:
            Surname
        """
        # Use a regular expression to split on capital letters
        # Pattern: look for a sequence of letters starting with a capital
        parts = re.findall(r'[A-ZА-ЯЁ][a-zа-яё]*', full_name)
        
        # The first part is the surname
        if parts:
            return parts[0]
        
        # Fallback: if parsing failed, return the whole full_name
        return full_name
    
    def update_ssh_config(self, full_name: str) -> Tuple[bool, str]:
        """
        Add or update an entry in the SSH config.
        
        Args:
            full_name: Full name identifying the key (SurnameFirstName)
            
        Returns:
            Tuple (success, message)
        """
        try:
            self.ensure_ssh_directory()
            
            # Extract the surname for the Host
            surname = self.extract_surname(full_name)
            host_name = f"github-{surname}"
            
            # The full name is used for IdentityFile
            key_path = self.ssh_dir / f"id_ed25519_{full_name}"
            
            # Check the key
            if not key_path.exists():
                return False, f"❌ Ключ не найден: {key_path}"
            
            # Build the new config entry
            new_entry = f"""
Host {host_name}
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile {key_path}
    IdentitiesOnly yes
"""
            
            # Read the existing config or create a new one
            if self.config_path.exists():
                config_content = self.config_path.read_text(encoding='utf-8')
                
                # Check that an entry for this host does not already exist
                host_pattern = f"Host {host_name}\\s"
                if re.search(host_pattern, config_content):
                    return False, f"⚠️  Запись для {host_name} уже существует в config"
                
                # Add the new entry
                config_content += new_entry
            else:
                config_content = new_entry.lstrip()
            
            # Write the updated config
            self.config_path.write_text(config_content, encoding='utf-8')
            self.config_path.chmod(0o600)
            
            return True, f"✅ SSH config обновлен. Host: {host_name}"
            
        except Exception as e:
            return False, f"❌ Ошибка обновления config: {str(e)}"
    
    def check_ssh_agent_running(self) -> bool:
        """
        Check whether ssh-agent is running.
        
        Returns:
            True if ssh-agent is running, otherwise False
        """
        try:
            result = subprocess.run(
                ["ssh-add", "-l"],
                capture_output=True,
                check=False
            )
            # Return code 0 or 1 means the agent is running
            # (0 - keys present, 1 - no keys, but agent running)
            return result.returncode in [0, 1]
        except Exception:
            return False
    
    def start_ssh_agent_windows(self) -> Tuple[bool, str]:
        """
        Start ssh-agent on Windows.
        Tries several startup methods.
        
        Returns:
            Tuple (success, message)
        """
        # Method 1: Try to start the service via sc
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
        
        # Method 2: Start via net start
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
        
        # Method 3: Direct ssh-agent start
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
                
                # Parse and set environment variables
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
        
        # All methods failed
        return False, (
            "❌ Не удалось запустить ssh-agent автоматически.\n"
            "   SSH ключи будут работать и без агента, но для удобства\n"
            "   вы можете запустить агент вручную в Git Bash:\n"
            "   eval \"$(ssh-agent -s)\""
        )
    
    def get_host_name_from_full_name(self, full_name: str) -> str:
        """
        Build the host name based on the full name.
        Uses only the surname (the first part).
        
        Args:
            full_name: User full name (SurnameFirstName)
            
        Returns:
            Host name for SSH config (github-Surname)
        """
        surname = self.extract_surname(full_name)
        return f"github-{surname}"
    
    def list_ssh_keys(self) -> list:
        """
        Return the list of all SSH keys in (full_name, host_name) format.
        
        Returns:
            List of tuples (full_name, host_name)
        """
        keys = []
        
        if not self.ssh_dir.exists():
            return keys
        
        # Find all id_ed25519_* files
        for key_file in self.ssh_dir.glob("id_ed25519_*"):
            if key_file.suffix != ".pub":  # Private keys only
                # Extract the full name from the file name
                full_name = key_file.stem.replace("id_ed25519_", "")
                host_name = self.get_host_name_from_full_name(full_name)
                keys.append((full_name, host_name))
        
        return sorted(keys, key=lambda x: x[1])
    
    def remove_ssh_key(self, full_name: str) -> Tuple[bool, str]:
        """
        Delete an SSH key and all related data:
        - Private key
        - Public key
        - SSH config entry
        - Key from ssh-agent (if loaded)
        
        Args:
            full_name: User full name (SurnameFirstName)
            
        Returns:
            Tuple (success, message)
        """
        try:
            messages = []
            success_count = 0
            
            # 1. Delete the private key
            private_key = self.ssh_dir / f"id_ed25519_{full_name}"
            if private_key.exists():
                private_key.unlink()
                messages.append(f"✅ Удален приватный ключ: {private_key.name}")
                success_count += 1
            else:
                messages.append(f"⚠️  Приватный ключ не найден: {private_key.name}")
            
            # 2. Delete the public key
            public_key = self.ssh_dir / f"id_ed25519_{full_name}.pub"
            if public_key.exists():
                public_key.unlink()
                messages.append(f"✅ Удален публичный ключ: {public_key.name}")
                success_count += 1
            else:
                messages.append(f"⚠️  Публичный ключ не найден: {public_key.name}")
            
            # 3. Remove from ssh-agent (if the agent is running)
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
            
            # 4. Remove from SSH config
            success_config, msg_config = self.remove_from_config(full_name)
            if success_config:
                messages.append(msg_config)
                success_count += 1
            else:
                messages.append(msg_config)
            
            # Final message
            if success_count > 0:
                result_msg = "\n".join(messages)
                return True, f"{result_msg}\n\n✅ SSH ключ успешно удален ({success_count} операций)"
            else:
                return False, f"❌ Ничего не удалено. Ключ не найден."
                
        except Exception as e:
            return False, f"❌ Ошибка при удалении ключа: {str(e)}"
    
    def remove_from_config(self, full_name: str) -> Tuple[bool, str]:
        """
        Delete an entry from the SSH config.
        
        Args:
            full_name: User full name
            
        Returns:
            Tuple (success, message)
        """
        try:
            if not self.config_path.exists():
                return False, "⚠️  Файл config не существует"
            
            # Read the config
            config_content = self.config_path.read_text(encoding='utf-8')
            
            # Build the host name to search for
            host_name = self.get_host_name_from_full_name(full_name)
            
            # Split into Host blocks
            lines = config_content.split('\n')
            new_lines = []
            skip_block = False
            found = False
            
            for line in lines:
                # Check for the start of a Host block
                if line.strip().startswith('Host '):
                    # If this is our block - skip it
                    if f"Host {host_name}" in line:
                        skip_block = True
                        found = True
                        continue
                    else:
                        skip_block = False
                
                # If not skipping the block, add the line
                if not skip_block:
                    new_lines.append(line)
                elif line.strip().startswith('Host '):
                    # A new block started, stop skipping
                    skip_block = False
                    new_lines.append(line)
            
            if found:
                # Write the updated config
                new_content = '\n'.join(new_lines)
                # Remove multiple consecutive empty lines
                new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                self.config_path.write_text(new_content, encoding='utf-8')
                return True, f"✅ Удалена запись из config: {host_name}"
            else:
                return False, f"⚠️  Запись {host_name} не найдена в config"
                
        except Exception as e:
            return False, f"❌ Ошибка удаления из config: {str(e)}"
