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
stderr_file = None


def signal_handler(sig, frame):
    print("\nYou pressed Ctrl+C! Exiting gracefully...")
    exit_gracefully()


def exit_gracefully():
    """Cleans up temporary files and exits the program."""
    global stderr_file
    if stderr_file is not None:
        try:
            stderr_file.close()
        except Exception:
            pass
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


def non_interactive_fix_keys(
    pwds, config_dir, config_path, ssh_private_key_path, directory
):
    """Non-interactive function to fix SSH keys."""
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
            _, public_key = generate_ssh_keypair(
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
        verbosity = settings.get("verbosity", "INFO")

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

    # if verbosity != "DEBUG":
    #    global stderr_file
    #    err_log_path = os.path.join(config_dir, "goodass_error_log.txt")
    #    stderr_file = open(err_log_path, "w")
    #    sys.stderr = stderr_file

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
    3. Manage Users
    4. Manage Hosts
    
    5. Exit
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
            userManager.user_cli(config_path)
        elif option == "4":
            hostManager.host_cli(config_path)
        elif option == "5" or option.lower() == "exit" or option.lower() == "q":
            exit_gracefully()
        else:
            print("Invalid option selected.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
