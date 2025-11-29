"""GPG encryption management for goodass CLI.

This module provides functions for managing GPG keys and encrypting/decrypting
the ssh-config.yaml file using GPG encryption.
"""

import os
import yaml
import gnupg
import tempfile

if __package__ is None:
    import autocomplete
else:
    from . import autocomplete


def get_gpg(gpg_home=None):
    """Get a GPG instance.
    
    Parameters:
    - gpg_home (str): Path to the GPG home directory.
    
    Returns:
    - gnupg.GPG: GPG instance.
    """
    if gpg_home:
        return gnupg.GPG(gnupghome=gpg_home)
    return gnupg.GPG()


def load_ssh_config(config_path):
    """Load the ssh-config.yaml file.
    
    Parameters:
    - config_path (str): Path to the ssh-config.yaml file.
    
    Returns:
    - dict: Configuration dictionary.
    """
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_ssh_config(config, config_path):
    """Save the ssh-config.yaml file.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to the ssh-config.yaml file.
    """
    with open(config_path, "w") as f:
        yaml.dump(config, f)


def get_gpg_public_keys(config):
    """Get the list of GPG public keys from config.
    
    Parameters:
    - config (dict): Configuration dictionary.
    
    Returns:
    - list: List of GPG public key configurations.
    """
    return config.get("gpg_public_keys", [])


def add_gpg_public_key(config, key_id, fingerprint, email=None, name=None):
    """Add a GPG public key to the configuration.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - key_id (str): GPG key ID.
    - fingerprint (str): GPG key fingerprint.
    - email (str): Email associated with the key.
    - name (str): Name associated with the key.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    if "gpg_public_keys" not in config:
        config["gpg_public_keys"] = []
    
    # Check if key already exists
    for key in config["gpg_public_keys"]:
        if key.get("fingerprint") == fingerprint:
            print(f"Key with fingerprint {fingerprint[:16]}... already exists.")
            return config
    
    config["gpg_public_keys"].append({
        "key_id": key_id,
        "fingerprint": fingerprint,
        "email": email or "",
        "name": name or "",
    })
    return config


def remove_gpg_public_key(config, fingerprint):
    """Remove a GPG public key from the configuration.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - fingerprint (str): GPG key fingerprint to remove.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    keys = config.get("gpg_public_keys", [])
    config["gpg_public_keys"] = [
        k for k in keys if k.get("fingerprint") != fingerprint
    ]
    return config


def import_gpg_key(gpg, key_data):
    """Import a GPG key.
    
    Parameters:
    - gpg (gnupg.GPG): GPG instance.
    - key_data (str): ASCII-armored GPG key data.
    
    Returns:
    - dict: Import result containing fingerprint and other info.
    """
    result = gpg.import_keys(key_data)
    return result


def encrypt_config(config_path, fingerprints, gpg_home=None):
    """Encrypt the ssh-config.yaml file with GPG.
    
    Parameters:
    - config_path (str): Path to the ssh-config.yaml file.
    - fingerprints (list): List of GPG key fingerprints to encrypt for.
    - gpg_home (str): Path to the GPG home directory.
    
    Returns:
    - bool: True if successful, False otherwise.
    """
    if not fingerprints:
        print("No GPG keys configured for encryption.")
        return False
    
    gpg = get_gpg(gpg_home)
    
    with open(config_path, "r") as f:
        data = f.read()
    
    encrypted = gpg.encrypt(data, fingerprints, armor=True)
    
    if encrypted.ok:
        encrypted_path = config_path + ".gpg"
        with open(encrypted_path, "w") as f:
            f.write(str(encrypted))
        print(f"Config encrypted to {encrypted_path}")
        return True
    else:
        print(f"Encryption failed: {encrypted.status}")
        return False


def decrypt_config(encrypted_path, output_path=None, passphrase=None, gpg_home=None):
    """Decrypt a GPG-encrypted ssh-config.yaml file.
    
    Parameters:
    - encrypted_path (str): Path to the encrypted file.
    - output_path (str): Path to save the decrypted file (default: removes .gpg extension).
    - passphrase (str): Passphrase for the GPG private key.
    - gpg_home (str): Path to the GPG home directory.
    
    Returns:
    - bool: True if successful, False otherwise.
    """
    if output_path is None:
        if encrypted_path.endswith(".gpg"):
            output_path = encrypted_path[:-4]
        else:
            output_path = encrypted_path + ".decrypted"
    
    gpg = get_gpg(gpg_home)
    
    with open(encrypted_path, "r") as f:
        encrypted_data = f.read()
    
    decrypted = gpg.decrypt(encrypted_data, passphrase=passphrase)
    
    if decrypted.ok:
        with open(output_path, "w") as f:
            f.write(str(decrypted))
        print(f"Config decrypted to {output_path}")
        return True
    else:
        print(f"Decryption failed: {decrypted.status}")
        return False


def list_available_keys(gpg_home=None):
    """List available GPG keys in the system.
    
    Parameters:
    - gpg_home (str): Path to the GPG home directory.
    
    Returns:
    - list: List of available public keys.
    """
    gpg = get_gpg(gpg_home)
    keys = gpg.list_keys()
    return keys


def get_key_completions(config):
    """Get list of completions for GPG key management.
    
    Parameters:
    - config (dict): Configuration dictionary.
    
    Returns:
    - list: List of completion options.
    """
    completions = ["add", "remove", "rm", "back", "done", "q"]
    
    for key in config.get("gpg_public_keys", []):
        fingerprint = key.get("fingerprint", "")
        if fingerprint:
            short_fp = fingerprint[-16:] if len(fingerprint) > 16 else fingerprint
            completions.append(f"remove {short_fp}")
            completions.append(f"rm {short_fp}")
    
    return completions


def gpg_keys_print(config):
    """Print the list of configured GPG public keys.
    
    Parameters:
    - config (dict): Configuration dictionary.
    """
    import prettytable
    
    keys = config.get("gpg_public_keys", [])
    table = prettytable.PrettyTable()
    table.field_names = ["#", "Key ID", "Fingerprint (last 16)", "Email", "Name"]
    
    if not keys:
        print("No GPG public keys configured.")
        return
    
    for i, key in enumerate(keys, 1):
        fingerprint = key.get("fingerprint", "N/A")
        short_fp = fingerprint[-16:] if len(fingerprint) > 16 else fingerprint
        table.add_row([
            i,
            key.get("key_id", "N/A"),
            short_fp,
            key.get("email", "N/A"),
            key.get("name", "N/A"),
        ])
    
    print("Configured GPG Public Keys:")
    print(table)


def gpg_cli(config_dir, config_path, settings):
    """CLI for managing GPG keys and encryption.
    
    Parameters:
    - config_dir (str): Path to the configuration directory.
    - config_path (str): Path to the ssh-config.yaml file.
    - settings (dict): Settings dictionary containing gpg_private_key_path.
    """
    config = load_ssh_config(config_path)
    gpg_home = settings.get("gpg_home")
    
    gpg_menu = """
GPG Key Management Menu:

    1. Add GPG Public Key (from keyring)
    2. Add GPG Public Key (import from file)
    3. Remove GPG Public Key
    4. List Available Keys in Keyring
    5. Encrypt Config File
    6. Decrypt Config File

    7. Back to Main Menu
    """
    
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        gpg_keys_print(config)
        print(gpg_menu)
        option = input("Enter option number: ")
        os.system("cls" if os.name == "nt" else "clear")
        
        if option == "1":
            config = add_key_from_keyring_cli(config, config_path, gpg_home)
        elif option == "2":
            config = import_key_cli(config, config_path, gpg_home)
        elif option == "3":
            config = remove_key_cli(config, config_path)
        elif option == "4":
            list_keyring_cli(gpg_home)
        elif option == "5":
            encrypt_config_cli(config, config_path, gpg_home)
        elif option == "6":
            decrypt_config_cli(config_path, gpg_home)
        elif option == "7" or option.lower() in ["back", "done", "q"]:
            return
        else:
            print("Invalid option selected.")
            input("Press Enter to continue...")


def add_key_from_keyring_cli(config, config_path, gpg_home=None):
    """CLI for adding a GPG public key from the system keyring.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to save the configuration.
    - gpg_home (str): Path to the GPG home directory.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Add GPG Public Key from Keyring ===\n")
    
    keys = list_available_keys(gpg_home)
    if not keys:
        print("No keys found in keyring.")
        input("Press Enter to continue...")
        return config
    
    print("Available keys in keyring:")
    for i, key in enumerate(keys, 1):
        uids = key.get("uids", ["Unknown"])
        print(f"  {i}. {key.get('keyid', 'N/A')} - {uids[0] if uids else 'N/A'}")
    
    try:
        choice = int(input("\nEnter key number to add: ").strip())
        if 1 <= choice <= len(keys):
            key = keys[choice - 1]
            fingerprint = key.get("fingerprint", "")
            key_id = key.get("keyid", "")
            uids = key.get("uids", [])
            email = ""
            name = ""
            if uids:
                uid = uids[0]
                # Parse email from uid (format: "Name <email>")
                if "<" in uid and ">" in uid:
                    name = uid.split("<")[0].strip()
                    email = uid.split("<")[1].split(">")[0]
                else:
                    name = uid
            
            config = add_gpg_public_key(config, key_id, fingerprint, email, name)
            save_ssh_config(config, config_path)
            print(f"\nKey {key_id} added successfully.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    
    input("Press Enter to continue...")
    return config


def import_key_cli(config, config_path, gpg_home=None):
    """CLI for importing a GPG public key from a file.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to save the configuration.
    - gpg_home (str): Path to the GPG home directory.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Import GPG Public Key from File ===\n")
    
    key_path = autocomplete.input_with_path_completion(
        "Enter path to the public key file (Tab for completion): "
    ).strip()
    
    if not key_path or not os.path.exists(key_path):
        print("Invalid path or file not found.")
        input("Press Enter to continue...")
        return config
    
    gpg = get_gpg(gpg_home)
    
    with open(key_path, "r") as f:
        key_data = f.read()
    
    result = import_gpg_key(gpg, key_data)
    
    if result.count > 0:
        for fingerprint in result.fingerprints:
            # Get key details
            keys = gpg.list_keys(keys=[fingerprint])
            if keys:
                key = keys[0]
                key_id = key.get("keyid", fingerprint[-8:])
                uids = key.get("uids", [])
                email = ""
                name = ""
                if uids:
                    uid = uids[0]
                    if "<" in uid and ">" in uid:
                        name = uid.split("<")[0].strip()
                        email = uid.split("<")[1].split(">")[0]
                    else:
                        name = uid
                
                config = add_gpg_public_key(config, key_id, fingerprint, email, name)
        
        save_ssh_config(config, config_path)
        print(f"\n{result.count} key(s) imported successfully.")
    else:
        print("No keys were imported.")
    
    input("Press Enter to continue...")
    return config


def remove_key_cli(config, config_path):
    """CLI for removing a GPG public key.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to save the configuration.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    gpg_keys_print(config)
    
    keys = config.get("gpg_public_keys", [])
    if not keys:
        input("Press Enter to continue...")
        return config
    
    try:
        choice = int(input("\nEnter key number to remove (or 0 to cancel): ").strip())
        if choice == 0:
            return config
        if 1 <= choice <= len(keys):
            key = keys[choice - 1]
            fingerprint = key.get("fingerprint", "")
            config = remove_gpg_public_key(config, fingerprint)
            save_ssh_config(config, config_path)
            print(f"\nKey removed successfully.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    
    input("Press Enter to continue...")
    return config


def list_keyring_cli(gpg_home=None):
    """CLI for listing available keys in the keyring.
    
    Parameters:
    - gpg_home (str): Path to the GPG home directory.
    """
    import prettytable
    
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Available Keys in Keyring ===\n")
    
    keys = list_available_keys(gpg_home)
    if not keys:
        print("No keys found in keyring.")
        input("Press Enter to continue...")
        return
    
    table = prettytable.PrettyTable()
    table.field_names = ["Key ID", "Type", "Length", "Creation", "UIDs"]
    
    for key in keys:
        uids = key.get("uids", ["Unknown"])
        table.add_row([
            key.get("keyid", "N/A"),
            key.get("type", "N/A"),
            key.get("length", "N/A"),
            key.get("date", "N/A"),
            uids[0] if uids else "N/A",
        ])
    
    print(table)
    input("\nPress Enter to continue...")


def encrypt_config_cli(config, config_path, gpg_home=None):
    """CLI for encrypting the config file.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to the ssh-config.yaml file.
    - gpg_home (str): Path to the GPG home directory.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Encrypt Config File ===\n")
    
    keys = config.get("gpg_public_keys", [])
    if not keys:
        print("No GPG public keys configured. Add keys first.")
        input("Press Enter to continue...")
        return
    
    gpg_keys_print(config)
    
    fingerprints = [k.get("fingerprint") for k in keys if k.get("fingerprint")]
    
    print(f"\nThe config will be encrypted for {len(fingerprints)} key(s).")
    confirm = input("Proceed with encryption? (y/N): ").strip().lower()
    
    if confirm == "y":
        encrypt_config(config_path, fingerprints, gpg_home)
    
    input("Press Enter to continue...")


def decrypt_config_cli(config_path, gpg_home=None):
    """CLI for decrypting the config file.
    
    Parameters:
    - config_path (str): Path to the ssh-config.yaml file.
    - gpg_home (str): Path to the GPG home directory.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Decrypt Config File ===\n")
    
    encrypted_path = config_path + ".gpg"
    if not os.path.exists(encrypted_path):
        encrypted_path = autocomplete.input_with_path_completion(
            "Enter path to encrypted file (Tab for completion): "
        ).strip()
    
    if not os.path.exists(encrypted_path):
        print("Encrypted file not found.")
        input("Press Enter to continue...")
        return
    
    import getpass
    passphrase = getpass.getpass("Enter GPG passphrase (or leave blank if using agent): ")
    passphrase = passphrase if passphrase else None
    
    decrypt_config(encrypted_path, config_path, passphrase, gpg_home)
    input("Press Enter to continue...")
