"""
Create SSH Key Script

Interactive script for creating an SSH key for working with GitHub.
Generates the key, adds it to the SSH config, copies the public key
to the clipboard, and opens the GitHub page where it has to be added.
"""

import subprocess
import sys
import webbrowser
from ssh_manager import SSHManager

GITHUB_KEYS_URL = "https://github.com/settings/keys"


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


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to the Windows clipboard using clip.

    Args:
        text: Text to copy (a public key, ASCII only)

    Returns:
        True if the text was copied
    """
    try:
        result = subprocess.run(
            ["clip"],
            input=text.encode("utf-8"),
            capture_output=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def open_browser(url: str) -> None:
    """Open a link in the browser; silently continue on failure."""
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> int:
    """
    Main SSH key creation function.

    Returns:
        Exit code (0 - success, 1 - error)
    """
    try:
        manager = SSHManager()

        username = get_user_input(
            "GitHub username (например, annkrq): ",
            validator=manager.validate_username,
            error_msg="Username может содержать только буквы, цифры и дефисы"
        )

        full_name = get_user_input(
            "Фамилия + Имя слитно (например, KozlovskayaAnna): ",
            validator=lambda x: len(x) >= 4 and x.replace(" ", "").isalpha(),
            error_msg="Имя должно содержать минимум 4 буквы и только буквы"
        ).replace(" ", "")

        print()

        success, message = manager.generate_ssh_key(username, full_name)
        if not success:
            print(message)
            return 1

        success, message = manager.update_ssh_config(full_name)
        if not success:
            print(message)
            return 1

        key_name = f"id_ed25519_{full_name}"
        host_name = manager.get_host_name_from_full_name(full_name)
        print(f"✅ Ключ создан: {key_name} (host: {host_name})")
        print()

        pub_key = manager.get_public_key(full_name)
        if not pub_key:
            print(f"⚠️  Не удалось прочитать публичный ключ: ~/.ssh/{key_name}.pub")
            return 1

        print(pub_key)
        print()

        if copy_to_clipboard(pub_key):
            print(f"📋 Ключ скопирован в буфер обмена. Вставьте его на сайте: {GITHUB_KEYS_URL}")
        else:
            print(f"Скопируйте ключ выше и вставьте его на сайте: {GITHUB_KEYS_URL}")

        open_browser(GITHUB_KEYS_URL)

        return 0

    except KeyboardInterrupt:
        print("\n\n❌ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
