"""Command-line entry for ssh-key-manager.

This module provides a small interactive CLI that reads `config.yaml`,
displays SSH keys present on configured servers and offers a simple
fix workflow. The interaction is intentionally minimal — the heavy
lifting is implemented in `libs/keyManager.py`.

Functions in this module are light wrappers around keyManager calls
and are documented with short docstrings.
"""

import os
import sys
import platformdirs


if __package__ is None:
    import keyManager
    import userManager
    import hostManager
else:
    from . import keyManager
    from . import userManager
    from . import hostManager
from pathlib import Path
import yaml
import signal
import tempfile

directory = None


def signal_handler(sig, frame):
    print("\nYou pressed Ctrl+C! Exiting gracefully...")
    exit_gracefully()


def exit_gracefully():
    """Cleans up temporary files and exits the program."""
    if directory is not None and os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
        try:
            os.rmdir(directory)
        except OSError as e:
            print(f"Failed to remove directory {directory}. Reason: {e}")
    sys.exit()


def main():
    directory = tempfile.mkdtemp(prefix="goodass-")
    if not os.path.exists(directory):
        os.makedirs(directory)
    pwds = {}

    config_dir = platformdirs.user_config_dir("goodass")

    config_path = os.path.join(config_dir, "ssh-config.yaml")

    if not os.path.exists(config_dir):
        Path(config_dir).mkdir(parents=True, exist_ok=True)

    if not os.path.exists(config_path):
        default_config = {"hosts": [], "users": []}
        with open(config_path, "w") as f:
            yaml.dump(default_config, f)
    if not os.path.exists(os.path.join(config_dir, "settings.yaml")):
        default_settings = {
            "ssh_private_key_path": "",
        }
        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            yaml.dump(default_settings, f)

    with open(os.path.join(config_dir, "settings.yaml"), "r") as f:
        settings = yaml.safe_load(f)
        ssh_private_key_path = settings.get("ssh_private_key_path", "")

    directory = platformdirs.user_config_dir("goodass")
    if os.path.exists(os.path.join(directory, "passwords.yaml")):
        with open(os.path.join(directory, "passwords.yaml"), "r") as f:
            pass_file = yaml.safe_load(f)
            for host_entry in pass_file.get("hosts", []):
                for c in host_entry.get("credentials", []):
                    host = host_entry.get("ip")
                    user = c.get("user")
                    password = c.get("password")
                    if host and password:
                        pwds[f"{user}@{host}"] = password
        print(pwds)

    signal.signal(signal.SIGINT, signal_handler)

    menu = """
Welcome to the SSH Key Manager, please select an option:\n
    1. Fetch and display all SSH keys
    2. Fix SSH key issues
    3. Add User
    4. Add Key(s) to User
    5. Remove Key from User
    6. Remove User
    7. Manage User Key Access
    8. Manage Hosts
    
    9. Exit
    """

    #### Main CLI Loop ####
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(menu)
        option = input("Enter option number: ")
        os.system("cls" if os.name == "nt" else "clear")
        if option == "1":
            keyManager.print_keys_table_cli(
                pwds,
                config_path,
                ssh_private_key_path=ssh_private_key_path,
                directory=directory,
            )
        elif option == "2":
            keyManager.fix_keys_cli(
                pwds,
                config_path,
                ssh_private_key_path=ssh_private_key_path,
                directory=directory,
            )
        elif option == "3":
            userManager.user_add_cli(config_path)
        elif option == "4":
            userManager.user_add_key_cli(config_path)
        elif option == "5":
            userManager.user_remove_key_cli(config_path)
        elif option == "6":
            userManager.user_remove_cli(config_path)
        elif option == "7":
            userManager.user_key_access_cli(config_path)
        elif option == "8":
            hostManager.host_cli(config_path)
        elif option == "9":
            exit_gracefully()
        else:
            print("Invalid option selected.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
