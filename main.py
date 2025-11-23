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
import libs.userManager as userManager

import signal
def signal_handler(sig, frame):
    print('\nYou pressed Ctrl+C! Exiting gracefully...')
    graceFulExit()
signal.signal(signal.SIGINT, signal_handler)

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

pwds = {}

directory = "./tempKeys"
if not os.path.exists(directory):
    os.makedirs(directory)

menu = """
Welcome to the SSH Key Manager, please select an option:\n
1. Fetch and display all SSH keys\n2. Fix SSH key issues
3. Add User
4. Add Key(s) to User
5. Remove Key from User
6. Remove User
7. Manage User Key Access
8. Exit
"""

#### Main CLI Loop ####
while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    print(menu)
    option = input("Enter option number: ")
    os.system('cls' if os.name == 'nt' else 'clear')
    if option == '1':
        keyManager.print_keys_table_cli(pwds)
    elif option == '2':
        keyManager.fix_keys_cli(pwds, directory=directory)
    elif option == '3':
        userManager.user_add_cli()
    elif option == '4':
        userManager.user_add_key_cli()
    elif option == '5':
        userManager.user_remove_key_cli()
    elif option == '6':
        userManager.user_remove_cli()
    elif option == '7':
        userManager.user_key_access_cli()
    elif option == '8':
        break
    else:
        print("Invalid option selected.")
        input("Press Enter to continue...")



graceFulExit()









