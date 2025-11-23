"""Command-line entry for ssh-key-manager.

This module provides a small interactive CLI that reads `config.yaml`,
displays SSH keys present on configured servers and offers a simple
fix workflow. The interaction is intentionally minimal — the heavy
lifting is implemented in `libs/keyManager.py`.

Functions in this module are light wrappers around keyManager calls
and are documented with short docstrings.
"""

import os
import libs.keyManager as keyManager
import yaml
import prettytable


directory = "./tempKeys"
if not os.path.exists(directory):
    os.makedirs(directory)

pwds = {}


def print_keys_table():
    """Fetch and display all SSH keys from configured hosts.

    This function retrieves SSH key data from the configuration using
    `keyManager.get_ssh_keys`, updates the local password cache, clears
    the console, prints a table of all discovered keys and waits for
    the user to press Enter before returning.
    """

    servers, all_user_keys, all_keys, passwords = keyManager.get_ssh_keys('config.yaml', pwds)
    pwds.update(passwords)
    os.system('cls' if os.name == 'nt' else 'clear')
    keyManager.print_keys_table(all_keys)
    input("Press Enter to continue...")

def fix_keys():
    """Run a check-and-fix workflow for SSH keys.

    Steps performed:
    - Fetch current key state from `config.yaml`.
    - Run `keyManager.check_keys` to detect inconsistencies.
    - Display a table of checked keys and, if issues are found,
      allow the user to confirm applying fixes.
    - On confirmation, upload corrected `authorized_keys` files to the
      remote servers using `keyManager.upload_all_ssh_files`.

    This function updates the shared `pwds` cache with any passwords
    returned from `get_ssh_keys`.
    """

    servers, all_user_keys, all_keys, passwords = keyManager.get_ssh_keys('config.yaml', pwds)
    pwds.update(passwords)
    checked_keys = keyManager.check_keys(all_user_keys)
    # if all keys are status 0, then no issues
    os.system('cls' if os.name == 'nt' else 'clear')
    keyManager.print_checked_keys_table(checked_keys)
    if all(key['status'] == 0 for key in checked_keys):
        print("All servers are up to date, no issues found.")
        input("Press Enter to continue...")
        return
    print("Issues found with the above keys. Please check them then press Enter to continue.")
    fixed_keys = list(filter(lambda k: k['status'] >= 0, checked_keys))
    input("Press Enter to continue...")
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Fixed Keys:")
    keyManager.print_checked_keys_table(list(fixed_keys))
    key_tables = {}
    for server in servers:
        for user in server['users']:
            host = server['host']
            key_table = list(filter(lambda k: k['host'] == host and k['user'] == user and k['status'] >= 0, list(fixed_keys)))
            key_tables[f"{user}@{host}"] = key_table
            print(f"Keys table for {user}@{host}...")
            keyManager.print_checked_keys_table(key_table)
    confirmation = input("Result after fix, continue? [y/N]")
    if confirmation.lower() == 'y':
        print("Fixing keys...")
        keyManager.upload_all_ssh_files(pwds, directory=directory, key_tables=key_tables)
        input("All done! Press Enter to continue...")
    
def graceFulExit():
    """Cleans up temporary files and exits the program."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
    os.rmdir(directory)
    exit()


########### new functions to be moved to libs/userManager.py ###########



def print_user_table(config):
    users = config.get('users', [])
    user_table = prettytable.PrettyTable()
    user_table.field_names = ["Username", "Email", "Keys"]
    for user in users:
        i = 0
        email = user.get('email', 'N/A')
        username = user.get('name', 'N/A')
        keys_info = user.get('keys', [])
        if not keys_info:
            keys = 'N/A'
        else:
            for key in keys_info:
                key_type = key.get('type', 'N/A')
                key_value = key.get('key', 'N/A')
                keys = f"{key_type} {key_value[:5]}..."
                if i == 0:
                    user_table.add_row([username, email, keys])
                else:
                    user_table.add_row(['-', '-', keys])
                i += 1
    print(user_table)

def add_user(config, username, email, keys):
    new_user = {
        'name': username,
        'email': email,
        'keys': [{'type': k['type'], 'key': k['key']} for k in keys]
    }
    for user in config.get('users', []):
        if user['email'] == email:
            print(f"User with email {email} already exists.")
            return config
    config.setdefault('users', []).append(new_user)
    print(f"User {username} added successfully.")
    return config

def load_config(path='config.yaml'):
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def save_config(config, path='config.yaml'):
    with open(path, 'w') as f:
        yaml.dump(config, f)

def add_user_cli(config):
    username = input("Insert new user name: ")
    email = input("Insert new user email: ")
    keys = []
    while True:
        key = input("Insert key or 'done' to finish: ")
        if key.lower() == 'done':
            break
        try: 
            key_type = key.split()[0]
            key_value = key.split()[1]
            key_hostname = key.split()[2] if len(key.split()) > 2 else ''
            keys.append({'type': key_type, 'key': key_value, 'hostname': key_hostname})
        except IndexError:
            print("Invalid key format. Please enter the key in the format: <type> <key> [hostname]")
    config = add_user(config, username, email, keys)
    save_config(config)


def user_add_key(config, email, key):
    users = config.get('users', [])
    for user in users:
        if user['email'] == email:
            key_type = key.split()[0]
            key_value = key.split()[1]
            key_hostname = key.split()[2] if len(key.split()) > 2 else ''
            user.setdefault('keys', []).append({'type': key_type, 'key': key_value, 'hostname': key_hostname})
            return config
    return config

def user_add_key_cli(config):
    email = input("Insert user email to add key: ")
    users = config.get('users', [])
    user_exists = False
    for user in users:
        if user['email'] == email:
            user_exists = True
            break
    if not user_exists:
        print(f"User with email {email} does not exist.")
        return config
    while True:
        key = input("Insert key or 'done' to finish: ")
        if key.lower() == 'done':
            break
        try: 
            key_type = key.split()[0]
            key_value = key.split()[1]
            key_hostname = key.split()[2] if len(key.split()) > 2 else ''
            for user in users:
                if user['email'] == email:
                    user.setdefault('keys', []).append({'type': key_type, 'key': key_value, 'hostname': key_hostname})
                    print(f"Key added to user {user['name']}.")
        except IndexError:
            print("Invalid key format. Please enter the key in the format: <type> <key> [hostname]")
    save_config(config)




###### testing code ###########

config = load_config()

print_user_table(config)

###actual test code###

add_user_cli(config)
user_add_key_cli(config)
###end of actual test code###

config = load_config()

print_user_table(config)

graceFulExit()

########## main interactive loop ###########




while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Welcome to the SSH Key Manager, please select an option:")
    print("1. Fetch and display all SSH keys")
    print("2. Fix SSH key issues")
    print("3. Exit")
    option = input("Enter option number: ")
    os.system('cls' if os.name == 'nt' else 'clear')
    if option == '1':
        print_keys_table()
    elif option == '2':
        fix_keys()
    elif option == '3':
        break
    else:
        print("Invalid option selected.")
        input("Press Enter to continue...")



for filename in os.listdir(directory):
    file_path = os.path.join(directory, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f'Failed to delete {file_path}. Reason: {e}')
os.rmdir(directory)









