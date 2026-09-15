"""
Create SSH Key Script

Interactive script for creating an SSH key for working with GitHub.
Performs all necessary steps: key generation, adding to ssh-agent,
config setup, and displaying the public key.
"""

import sys
from ssh_manager import SSHManager


def print_separator(char: str = "═", length: int = 60) -> None:
    """Prints a separator."""
    print(char * length)


def print_header(text: str) -> None:
    """Prints a section header."""
    print()
    print_separator()
    print(f"🔑 {text}")
    print_separator()
    print()


def get_user_input(prompt: str, validator=None, error_msg: str = "") -> str:
    """
    Request input from the user with validation.
    
    Args:
        prompt: Prompt text
        validator: Function to validate input (optional)
        error_msg: Error message on failed validation
        
    Returns:
        Validated user input
    """
    while True:
        value = input(prompt).strip()
        
        if not value:
            print("⚠️  Поле не может быть пустым. Попробуйте снова.")
            continue
        
        if validator and not validator(value):
            print(f"❌ {error_msg or 'Некорректный ввод'}. Попробуйте снова.")
            continue
        
        return value


def main() -> int:
    """
    Main SSH key creation function.
    
    Returns:
        Exit code (0 - success, 1 - error)
    """
    try:
        print_header("Создание SSH ключа для GitHub")
        
        # Initialize the manager
        manager = SSHManager()
        
        # Request data from the user
        print("📝 Введите данные для создания SSH ключа:\n")
        
        username = get_user_input(
            "GitHub username (например, annkrq): ",
            validator=manager.validate_username,
            error_msg="Username может содержать только буквы, цифры и дефисы"
        )
        
        print("ℹ️  Введите фамилию и имя слитно (например: KozlovskayaAnna)")
        full_name = get_user_input(
            "Фамилия + Имя (без пробелов): ",
            validator=lambda x: len(x) >= 4 and x.replace(" ", "").isalpha(),
            error_msg="Имя должно содержать минимум 4 буквы и только буквы"
        )
        
        # Remove spaces from the full name
        full_name = full_name.replace(" ", "")
        
        print()
        print(f"✓ Username: {username}")
        print(f"✓ Полное имя: {full_name}")
        print(f"✓ Имя ключа: id_ed25519_{full_name}")
        print()
        
        # Step 1: Generate the SSH key
        print_header("Шаг 1/4: Генерация SSH ключа")
        success, message = manager.generate_ssh_key(username, full_name)
        print(message)
        
        if not success:
            return 1
        
        # Step 2: ssh-agent check
        print_header("Шаг 2/4: Проверка ssh-agent")
        agent_running = manager.check_ssh_agent_running()
        
        if not agent_running:
            print("⚠️  ssh-agent не запущен. Попытка запустить...")
            print()
            
            # Try to start ssh-agent
            success, message = manager.start_ssh_agent_windows()
            print(message)
            print()
            
            # Check again
            agent_running = manager.check_ssh_agent_running()
        else:
            print("✅ ssh-agent уже запущен")
        
        # Step 3: Add the key to ssh-agent (if the agent is available)
        print_header("Шаг 3/4: Добавление ключа в ssh-agent")
        
        if agent_running:
            success, message = manager.add_key_to_agent(full_name)
            print(message)
            
            if not success:
                print("\n💡 Вы можете добавить его позже в Git Bash:")
                print('   eval "$(ssh-agent -s)"')
                print(f'   ssh-add ~/.ssh/id_ed25519_{full_name}')
        else:
            print("⏭️  Пропущено (ssh-agent не доступен)")
            print()
            print("ℹ️  SSH ключи работают и без агента!")
            print("   Агент нужен только для удобства, чтобы не вводить пароль.")
            print()
            print("💡 Если хотите использовать агент, запустите в Git Bash:")
            print('   eval "$(ssh-agent -s)"')
            print(f'   ssh-add ~/.ssh/id_ed25519_{full_name}')
        
        # Step 4: Update SSH config
        print_header("Шаг 4/4: Настройка SSH config")
        success, message = manager.update_ssh_config(full_name)
        print(message)
        
        if not success:
            return 1
        
        # Display the public key
        print_header("🔑 Публичный SSH ключ для GitHub")
        pub_key = manager.get_public_key(full_name)
        
        if pub_key:
            print("📋 Скопируйте этот ключ и добавьте в GitHub:")
            print("   (Settings → SSH and GPG keys → New SSH key)\n")
            print("╔" + "═" * 78 + "╗")
            print("║ " + pub_key.ljust(76) + " ║")
            print("╚" + "═" * 78 + "╝")
            print()
            print(f"💡 Команда для повторного просмотра:")
            print(f"   cat ~/.ssh/id_ed25519_{full_name}.pub")
            print()
        else:
            print("⚠️  Не удалось прочитать публичный ключ")
            print(f"   Вы можете вывести его командой:")
            print(f"   cat ~/.ssh/id_ed25519_{full_name}.pub")
            print()
        
        # Final information
        print_separator("═")
        print("✅ SSH ключ успешно настроен!")
        print_separator("═")
        print()
        print("📌 Следующие шаги:")
        print("  1. Скопируйте публичный ключ (выше)")
        print("  2. Перейдите на GitHub: Settings → SSH and GPG keys")
        print("  3. Нажмите 'New SSH key'")
        print("  4. Вставьте ключ и сохраните")
        print()
        host_name = manager.get_host_name_from_full_name(full_name)
        print(f"  5. Теперь используйте этот Host для клонирования:")
        print(f"     git clone git@{host_name}:{username}/repo-name.git")
        print()
        print("ℹ️  Ключ будет работать автоматически без ssh-agent!")
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
