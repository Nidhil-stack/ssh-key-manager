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
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

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


def generate_ssh_keypair(path):
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )

    with open(path, "w") as f:
        f.write(private_key.decode())
    os.chmod(path, 0o600)
    with open(f"{path}.pub", "w") as f:
        f.write(f"{public_key.decode()} goodass_key@generated")
    return private_key.decode(), public_key.decode()


def settings_cli(config_dir, config_path):
    """CLI for managing settings.yaml and ssh-config.yaml.
    
    Parameters:
    - config_dir (str): Path to the configuration directory.
    - config_path (str): Path to the ssh-config.yaml file.
    
    Returns:
    - ssh_private_key_path (str): Updated SSH private key path.
    """
    settings_path = os.path.join(config_dir, "settings.yaml")
    
    # Load current settings
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = yaml.safe_load(f) or {}
    else:
        settings = {}
    
    # Load ssh-config for max_threads_per_host
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            ssh_config = yaml.safe_load(f) or {}
    else:
        ssh_config = {}
    
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=== Settings Configuration ===\n")
        print("Current settings (from settings.yaml):")
        print(f"  1. ssh_private_key_path: {settings.get('ssh_private_key_path', '(not set)')}")
        print(f"  2. verbosity: {settings.get('verbosity', '(not set)')}")
        print("\nCurrent settings (from ssh-config.yaml):")
        print(f"  3. max_threads_per_host: {ssh_config.get('max_threads_per_host', '(not set)')}")
        print("\nOptions:")
        print("  Enter 1, 2, or 3 to edit the corresponding setting")
        print("  Enter 'done' or 'q' to return to main menu")
        
        choice = input("\nEnter your choice: ").strip().lower()
        
        if choice in ['done', 'q', 'back']:
            break
        elif choice == '1':
            settings = edit_ssh_private_key_path(settings, config_dir, config_path)
        elif choice == '2':
            settings = edit_verbosity(settings)
        elif choice == '3':
            ssh_config = edit_max_threads_per_host(ssh_config, config_path)
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")
    
    # Save settings
    with open(settings_path, "w") as f:
        yaml.dump(settings, f)
    
    return settings.get('ssh_private_key_path', '')


def edit_ssh_private_key_path(settings, config_dir, config_path):
    """Edit the ssh_private_key_path setting.
    
    Parameters:
    - settings (dict): Current settings dictionary.
    - config_dir (str): Path to the configuration directory.
    - config_path (str): Path to the ssh-config.yaml file.
    
    Returns:
    - settings (dict): Updated settings dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Edit SSH Private Key Path ===\n")
    current_value = settings.get('ssh_private_key_path', '')
    print(f"Current value: {current_value if current_value else '(not set)'}")
    print("\nEnter new path to SSH private key.")
    print("Leave blank to generate a new keypair in the config directory.")
    
    new_path = input("\nNew path (or blank to generate): ").strip()
    
    if not new_path:
        # Generate new keypair
        keypair_path = os.path.join(config_dir, "goodass_id_rsa")
        print(f"\nGenerating new SSH keypair at: {keypair_path}")
        _, public_key = generate_ssh_keypair(keypair_path)
        settings['ssh_private_key_path'] = keypair_path
        print(f"Private key saved to: {keypair_path}")
        print(f"Public key saved to: {keypair_path}.pub")
        
        # Update config with the new key as a user
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {"hosts": [], "users": []}
            
            # Check if goodass_user already exists
            user_exists = False
            for user in config.get("users", []):
                if user.get("username") == "goodass_user":
                    user_exists = True
                    break
            
            if not user_exists:
                # Validate public_key format before using
                key_parts = public_key.split(" ")
                if len(key_parts) >= 2:
                    config.setdefault("users", []).append(
                        {
                            "username": "goodass_user",
                            "keys": [
                                {
                                    "type": key_parts[0],
                                    "key": key_parts[1],
                                    "hostname": "goodass_key@generated",
                                }
                            ],
                        }
                    )
                    with open(config_path, "w") as f:
                        yaml.dump(config, f)
                    print("Added generated key to configuration as 'goodass_user'.")
                else:
                    print("Warning: Generated key has unexpected format, skipping config update.")
    else:
        # Validate the path exists
        if os.path.exists(new_path):
            settings['ssh_private_key_path'] = new_path
            print(f"\nSSH private key path updated to: {new_path}")
        else:
            print(f"\nWarning: Path '{new_path}' does not exist.")
            confirm = input("Save anyway? (y/N): ").strip().lower()
            if confirm == 'y':
                settings['ssh_private_key_path'] = new_path
                print(f"SSH private key path updated to: {new_path}")
            else:
                print("Path not updated.")
    
    input("\nPress Enter to continue...")
    return settings


def edit_verbosity(settings):
    """Edit the verbosity setting.
    
    Parameters:
    - settings (dict): Current settings dictionary.
    
    Returns:
    - settings (dict): Updated settings dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Edit Verbosity ===\n")
    current_value = settings.get('verbosity', '')
    print(f"Current value: {current_value if current_value else '(not set)'}")
    print("\nEnter new verbosity level (e.g., 0, 1, 2).")
    print("Leave blank to clear the setting.")
    
    new_value = input("\nNew value: ").strip()
    
    if not new_value:
        if 'verbosity' in settings:
            del settings['verbosity']
        print("Verbosity setting cleared.")
    else:
        try:
            val = int(new_value)
            if val < 0:
                print("Invalid value. Verbosity must be 0 or greater.")
            else:
                settings['verbosity'] = val
                print(f"Verbosity updated to: {settings['verbosity']}")
        except ValueError:
            print("Invalid value. Please enter a number.")
    
    input("\nPress Enter to continue...")
    return settings


def edit_max_threads_per_host(ssh_config, config_path):
    """Edit the max_threads_per_host setting in ssh-config.yaml.
    
    Parameters:
    - ssh_config (dict): Current ssh-config dictionary.
    - config_path (str): Path to the ssh-config.yaml file.
    
    Returns:
    - ssh_config (dict): Updated ssh-config dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Edit Max Threads Per Host ===\n")
    current_value = ssh_config.get('max_threads_per_host', '')
    print(f"Current value: {current_value if current_value else '(not set)'}")
    print("\nEnter the maximum number of threads per host.")
    print("Leave blank to clear the setting.")
    
    new_value = input("\nNew value: ").strip()
    
    if not new_value:
        if 'max_threads_per_host' in ssh_config:
            del ssh_config['max_threads_per_host']
        print("max_threads_per_host setting cleared.")
    else:
        try:
            val = int(new_value)
            if val <= 0:
                print("Invalid value. max_threads_per_host must be greater than 0.")
            else:
                ssh_config['max_threads_per_host'] = val
                print(f"max_threads_per_host updated to: {ssh_config['max_threads_per_host']}")
        except ValueError:
            print("Invalid value. Please enter a number.")
    
    # Save ssh-config
    with open(config_path, "w") as f:
        yaml.dump(ssh_config, f)
    
    input("\nPress Enter to continue...")
    return ssh_config


def non_interactive_fix_keys(
    pwds, config_dir, config_path, ssh_private_key_path, directory
):
    """Non-interactive function to fix SSH keys."""
    err_log_path = os.path.join(config_dir, "goodass_error_log.txt")
    sys.stderr = open(err_log_path, "w")
    keyManager.fix_keys_cli(
        pwds,
        config_path,
        ssh_private_key_path=ssh_private_key_path,
        directory=directory,
        interactive=False,
    )


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--fix-keys":
        non_interactive = True
    else:
        non_interactive = False
    directory = tempfile.mkdtemp(prefix="goodass-")
    if not os.path.exists(directory):
        os.makedirs(directory)
    pwds = {}

    config_dir = platformdirs.user_config_dir("goodass")

    config_path = os.path.join(config_dir, "ssh-config.yaml")

    if not os.path.exists(config_dir):
        if non_interactive:
            print(
                "Configuration directory does not exist. Please run the program interactively first to set up configuration."
            )
            sys.exit(1)
        Path(config_dir).mkdir(parents=True, exist_ok=True)

    if not os.path.exists(config_path):
        if non_interactive:
            print(
                "Configuration file does not exist. Please run the program interactively first to set up configuration."
            )
            sys.exit(1)
        default_config = {"hosts": [], "users": []}
        with open(config_path, "w") as f:
            yaml.dump(default_config, f)
    if not os.path.exists(os.path.join(config_dir, "settings.yaml")):
        if non_interactive:
            print(
                "Settings file does not exist. Please run the program interactively first to set up configuration."
            )
            sys.exit(1)
        ssh_private_key_path = input(
            "Enter path to the program's SSH private key (leave blank to generate a new id_rsa keypair): "
        )
        _, public_key = generate_ssh_keypair(os.path.join(config_dir, "goodass_id_rsa"))
        settings = {"ssh_private_key_path": ssh_private_key_path}
        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            yaml.dump(settings, f)
        settings = {"ssh_private_key_path": ssh_private_key_path}
        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            yaml.dump(settings, f)
        if not ssh_private_key_path.strip():
            # Only generate keypair and add to config if no path was provided
            _, public_key = generate_ssh_keypair(os.path.join(config_dir, "goodass_id_rsa"))
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                config["users"].append(
                    {
                        "username": "goodass_user",
                        "keys": [
                            {
                                "type": public_key.split(" ")[0],
                                "key": public_key.split(" ")[1],
                                "hostname": "goodass_key@generated",
                            }
                        ],
                    }
                )
            with open(config_path, "w") as f:
                yaml.dump(config, f)
    with open(os.path.join(config_dir, "settings.yaml"), "r") as f:
        settings = yaml.safe_load(f)
        ssh_private_key_path = settings.get("ssh_private_key_path", "")

    if os.path.exists(os.path.join(config_dir, "passwords.yaml")):
        with open(os.path.join(config_dir, "passwords.yaml"), "r") as f:
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

    if non_interactive:
        non_interactive_fix_keys(
            pwds,
            config_dir,
            config_path,
            ssh_private_key_path=ssh_private_key_path,
            directory=directory,
        )
        exit_gracefully()

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
    9. Edit Settings
    
    10. Exit
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
            ssh_private_key_path = settings_cli(config_dir, config_path)
        elif option == "10" or option.lower() == "exit" or option.lower() == "q":
            exit_gracefully()
        else:
            print("Invalid option selected.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
