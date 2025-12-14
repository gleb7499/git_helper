"""
Delete SSH Key Script

Интерактивный скрипт для удаления SSH ключа.
Удаляет ключ полностью: файлы, запись из config, из ssh-agent.
"""

import sys
from ssh_manager import SSHManager


def print_separator(char: str = "═", length: int = 60) -> None:
    """Печатает разделитель."""
    print(char * length)


def print_header(text: str) -> None:
    """Печатает заголовок раздела."""
    print()
    print_separator()
    print(f"🗑️  {text}")
    print_separator()
    print()


def main() -> int:
    """
    Основная функция удаления SSH ключа.
    
    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        print_header("Удаление SSH ключа")
        
        # Инициализация менеджера
        manager = SSHManager()
        
        # Получаем список ключей
        keys = manager.list_ssh_keys()
        
        if not keys:
            print("❌ SSH ключи не найдены")
            print("\nВ директории ~/.ssh нет ключей формата id_ed25519_*")
            return 1
        
        # Показываем список
        print("📋 Доступные SSH ключи:\n")
        for idx, (full_name, host_name) in enumerate(keys, 1):
            print(f"  {idx}. {host_name}")
            print(f"     Полное имя: {full_name}")
            print(f"     Ключ: id_ed25519_{full_name}")
            print()
        
        # Запрашиваем выбор
        while True:
            try:
                choice = input("Введите номер ключа для удаления (или 'q' для отмены): ").strip()
                
                if choice.lower() == 'q':
                    print("\n❌ Операция отменена")
                    return 1
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(keys):
                    selected_full_name, selected_host = keys[choice_num - 1]
                    break
                else:
                    print(f"⚠️  Введите число от 1 до {len(keys)}")
            except ValueError:
                print("⚠️  Введите корректное число или 'q'")
        
        # Подтверждение
        print()
        print_separator("─")
        print(f"⚠️  ВНИМАНИЕ! Вы собираетесь удалить:")
        print(f"   Host: {selected_host}")
        print(f"   Полное имя: {selected_full_name}")
        print(f"   Файлы: id_ed25519_{selected_full_name}, id_ed25519_{selected_full_name}.pub")
        print_separator("─")
        print()
        
        confirm = input("Подтвердите удаление (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'да']:
            print("\n❌ Операция отменена")
            return 1
        
        # Выполняем удаление
        print_header(f"Удаление ключа {selected_host}")
        
        success, message = manager.remove_ssh_key(selected_full_name)
        
        print(message)
        print()
        
        if success:
            print_separator("═")
            print("✅ Ключ успешно удален из системы!")
            print_separator("═")
            print()
            print("📌 Не забудьте также:")
            print("  1. Удалить ключ из GitHub (Settings → SSH and GPG keys)")
            print(f"  2. Проверить файл ~/.ssh/config")
            print()
            return 0
        else:
            return 1
        
    except KeyboardInterrupt:
        print("\n\n❌ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
