"""Settings management for goodass CLI.

This module provides functions for managing settings.yaml and ssh-config.yaml,
including path completion for SSH private key selection.
"""

import os
import yaml

if __package__ is None:
    import autocomplete
    import utils
else:
    from . import autocomplete
    from . import utils


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
        print("Current settings:")
        print(
            f"  1. ssh_private_key_path: {settings.get('ssh_private_key_path', '(not set)')}"
        )
        print(f"  2. verbosity: {settings.get('verbosity', '(not set)')}")
        print(
            f"  3. max_threads_per_host: {ssh_config.get('max_threads_per_host', '(not set)')}"
        )
        print("\nOptions:")
        print("  Enter 1, 2, or 3 to edit the corresponding setting")
        print("  Enter 'done' or 'q' to return to main menu")

        choice = input("\nEnter your choice: ").strip().lower()

        if choice in ["done", "q", "back"]:
            break
        elif choice == "1":
            settings = edit_ssh_private_key_path(settings, config_dir, config_path)
        elif choice == "2":
            settings = edit_verbosity(settings)
        elif choice == "3":
            ssh_config = edit_max_threads_per_host(ssh_config, config_path)
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

    # Save settings
    with open(settings_path, "w") as f:
        yaml.dump(settings, f)

    return settings.get("ssh_private_key_path", "")


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
    current_value = settings.get("ssh_private_key_path", "")
    print(f"Current value: {current_value if current_value else '(not set)'}")
    print("\nEnter new path to SSH private key.")
    print("Leave blank to generate a new keypair in the config directory.")
    print("(Use Tab for path completion)")

    new_path = autocomplete.input_with_path_completion(
        "\nNew path (or blank to generate): "
    ).strip()

    if not new_path:
        # Generate new keypair
        keypair_path = os.path.join(config_dir, "goodass_id_rsa")
        print(f"\nGenerating new SSH keypair at: {keypair_path}")
        _, public_key = utils.generate_ssh_keypair(keypair_path)
        settings["ssh_private_key_path"] = keypair_path
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
                    print(
                        "Warning: Generated key has unexpected format, skipping config update."
                    )
    else:
        # Validate the path exists
        if os.path.exists(new_path):
            settings["ssh_private_key_path"] = new_path
            print(f"\nSSH private key path updated to: {new_path}")
        else:
            print(f"\nWarning: Path '{new_path}' does not exist.")
            confirm = input("Save anyway? (y/N): ").strip().lower()
            if confirm == "y":
                settings["ssh_private_key_path"] = new_path
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
    current_value = settings.get("verbosity", "")
    print(f"Current value: {current_value if current_value else '(not set)'}")
    print("\nEnter new verbosity level (e.g., 0, 1, 2).")
    print("Leave blank to clear the setting.")

    new_value = input("\nNew value: ").strip()

    if not new_value:
        if "verbosity" in settings:
            del settings["verbosity"]
        print("Verbosity setting cleared.")
    else:
        try:
            val = int(new_value)
            if val < 0:
                print("Invalid value. Verbosity must be 0 or greater.")
            else:
                settings["verbosity"] = val
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
    current_value = ssh_config.get("max_threads_per_host", "")
    print(f"Current value: {current_value if current_value else '(not set)'}")
    print("\nEnter the maximum number of threads per host.")
    print("Leave blank to clear the setting.")

    new_value = input("\nNew value: ").strip()

    if not new_value:
        if "max_threads_per_host" in ssh_config:
            del ssh_config["max_threads_per_host"]
        print("max_threads_per_host setting cleared.")
    else:
        try:
            val = int(new_value)
            if val <= 0:
                print("Invalid value. max_threads_per_host must be greater than 0.")
            else:
                ssh_config["max_threads_per_host"] = val
                print(
                    f"max_threads_per_host updated to: {ssh_config['max_threads_per_host']}"
                )
        except ValueError:
            print("Invalid value. Please enter a number.")

    # Save ssh-config
    with open(config_path, "w") as f:
        yaml.dump(ssh_config, f)

    input("\nPress Enter to continue...")
    return ssh_config
