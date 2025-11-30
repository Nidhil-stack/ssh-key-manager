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
    import utils
    import settingsManager
    import syncManager
    import gpgManager
    import multiFileManager
    import logger as app_logger
else:
    from . import keyManager
    from . import userManager
    from . import hostManager
    from . import utils
    from . import settingsManager
    from . import syncManager
    from . import gpgManager
    from . import multiFileManager
    from . import logger as app_logger
from pathlib import Path
import yaml
import signal
import tempfile


LICENSE_TEXT = "Licensed under AGPL-3.0 | https://github.com/Nidhil-stack/GOODASS"


def advanced_options_cli(config_dir, config_path, ssh_private_key_path, settings):
    """CLI for advanced options submenu (Sync, GPG, Multi-File).

    Parameters:
    - config_dir (str): Path to the configuration directory.
    - config_path (str): Path to the ssh-config.yaml file.
    - ssh_private_key_path (str): Path to the SSH private key.
    - settings (dict): Settings dictionary.

    Returns:
    - dict: Updated settings dictionary.
    """
    advanced_menu = """
Advanced Options:

    1. Remote Sync (SFTP)
    2. GPG Encryption & Signing
    3. Manage Config Files

    4. Back to Main Menu
    """

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(advanced_menu)
        print(f"\n{LICENSE_TEXT}")
        option = input("\nEnter option number: ")
        os.system("cls" if os.name == "nt" else "clear")

        if option == "1":
            syncManager.sync_cli(config_dir, config_path, ssh_private_key_path)
        elif option == "2":
            gpgManager.gpg_cli(config_dir, config_path, settings)
        elif option == "3":
            multiFileManager.multifile_cli(config_dir)
            settings = multiFileManager.load_settings(config_dir)
        elif option == "4" or option.lower() in ["back", "done", "q"]:
            return settings
        else:
            print("Invalid option selected.")
            input("Press Enter to continue...")

    return settings


def main():
    global directory, stderr_file
    stderr_file = None
    directory = None
    if len(sys.argv) > 1 and sys.argv[1] == "--fix-keys":
        non_interactive = True
    else:
        non_interactive = False
    directory = tempfile.mkdtemp(prefix="goodass-")

    # Set directory reference in utils module for cleanup
    utils.directory = directory

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
        _, public_key = utils.generate_ssh_keypair(
            os.path.join(config_dir, "goodass_id_rsa")
        )
        settings = {"ssh_private_key_path": ssh_private_key_path}
        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            yaml.dump(settings, f)
        settings = {"ssh_private_key_path": ssh_private_key_path}
        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            yaml.dump(settings, f)
        if not ssh_private_key_path.strip():
            # Only generate keypair and add to config if no path was provided
            _, public_key = utils.generate_ssh_keypair(
                os.path.join(config_dir, "goodass_id_rsa")
            )
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
        verbosity = settings.get("verbosity", 1)

    # Initialize the logging system
    log = app_logger.init_logger(config_dir, verbosity)
    log.set_gpg_home(settings.get("gpg_home"))
    log.log_program("startup", f"GOODASS starting with verbosity level {verbosity}")
    log.print_debug(f"Configuration directory: {config_dir}")

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
        log.print_debug(f"Loaded {len(pwds)} password entries from passwords.yaml")

    signal.signal(signal.SIGINT, utils.signal_handler)

    # In debug mode (verbosity 3), stderr is NOT redirected so errors are shown
    # directly in the terminal for easier debugging. Otherwise, errors go to log file.
    if verbosity < 3:
        err_log_path = os.path.join(config_dir, "goodass_error_log.txt")
        stderr_file = open(err_log_path, "w")
        sys.stderr = stderr_file

    # Check for multi-file setup and prompt for selection if needed
    settings = multiFileManager.file_selection_prompt(settings, config_dir)

    # Perform autosync if enabled (syncs ALL config files based on selection)
    syncManager.perform_autosync(
        config_path, ssh_private_key_path, settings, non_interactive
    )

    if non_interactive:
        log.log_program("mode", "Running in non-interactive mode (--fix-keys)")
        keyManager.non_interactive_fix_keys(
            pwds,
            config_path,
            ssh_private_key_path=ssh_private_key_path,
            directory=directory,
        )
        utils.exit_gracefully()

    menu = """
Welcome to the SSH Key Manager (v0.3.0-pre), please select an option:

    1. Fetch and display all SSH keys
    2. Fix SSH key issues
    3. Manage Users
    4. Manage Hosts
    5. Advanced Options (Sync, GPG, Multi-File)
    6. Edit Settings
    
    7. Exit
    """

    #### Main CLI Loop ####
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        log.print_minimal(menu)
        log.print_minimal(f"\n{LICENSE_TEXT}")
        log.set_user_typing(True)
        option = input("\nEnter option number: ")
        log.set_user_typing(False)
        os.system("cls" if os.name == "nt" else "clear")
        log.log_program("menu", f"User selected menu option: {option}")
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
            userManager.user_cli(config_path, config_dir=config_dir)
        elif option == "4":
            hostManager.host_cli(config_path, config_dir=config_dir)
        elif option == "5":
            settings = advanced_options_cli(
                config_dir, config_path, ssh_private_key_path, settings
            )
        elif option == "6":
            ssh_private_key_path = settingsManager.settings_cli(config_dir, config_path)
            # Reload settings to get updated gpg_home using consistent function
            settings = multiFileManager.load_settings(config_dir)
            # Update logger settings after verbosity might have changed
            new_verbosity = settings.get("verbosity", 1)
            log.set_verbosity(new_verbosity)
            log.set_gpg_home(settings.get("gpg_home"))
        elif option == "7" or option.lower() == "exit" or option.lower() == "q":
            utils.exit_gracefully()
        else:
            log.print_default("Invalid option selected.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
