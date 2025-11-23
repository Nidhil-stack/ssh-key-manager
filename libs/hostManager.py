import os
import yaml
import prettytable

def load_config(path='config.yaml'):
    """Loads the configuration from a YAML file.
    Parameters:
    - path (str): Path to the configuration file.
    Returns:
    - config (dict): Configuration dictionary.
    """
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{path}' not found.")
        print("Please create a config.yaml file with your server and user configuration.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse configuration file '{path}'.")
        print(f"YAML parsing error: {e}")
        exit(1)
    except PermissionError:
        print(f"Error: Permission denied when trying to read '{path}'.")
        print("Please check file permissions.")
        exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading '{path}': {e}")
        exit(1)

def hosts_print(config):
    """Prints the loaded hosts for verification."""
    print("Loaded Hosts:")
    table = prettytable.PrettyTable()
    table.field_names = ["Host", "User"]
    for host in config.get('hosts', []):
        i = 0
        if not host.get('users') or len(host.get('users')) == 0:
            table.add_row([host.get('host', 'N/A'), 'N/A'])
            continue
        for user in host.get('users', []):
            if i == 0:
                table.add_row([host.get('host', 'N/A'), user])
            else:
                table.add_row(['', user])
            i += 1
    print(table)

def save_config(config, path='config.yaml'):
    """Saves the configuration to a YAML file.
    Parameters:
    - config (dict): Configuration dictionary.
    - path (str): Path to the configuration file.
    """
    try:
        with open(path, 'w') as f:
            yaml.dump(config, f)
    except PermissionError:
        print(f"Error: Permission denied when trying to write to '{path}'.")
        print("Please check file permissions.")
        exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred while saving '{path}': {e}")
        exit(1)

def hosts_add(config, host, user):
    """Adds a host and its users to the configuration."""
    if 'hosts' not in config:
        config['hosts'] = []
    for h in config['hosts']:
        if h['host'] == host:
            if not user:
                print(f"Host {host} already exists in configuration.")
                input("Press Enter to continue...")
                return config
            if user in h['users']:
                print(f"User {user} already exists for host {host} in configuration.")
                input("Press Enter to continue...")
                return config
            h['users'].append(user)
            return config
    config['hosts'].append({'host': host, 'users': [user]})
    return config

def hosts_remove(config, host, user=None):
    """Removes a host from the configuration."""
    if 'hosts' not in config:
        print("No hosts found in configuration.")
        return config
    for i, h in enumerate(config['hosts']):
        if h['host'] == host:
            print(user)
            if user is None:
                del config['hosts'][i]
                return config
            if user in h['users']:
                h['users'].remove(user)
                if len(h['users']) == 0:
                    del config['hosts'][i]
                return config
    print(f"Host {host} not found in configuration.")
    input("Press Enter to continue...")

def host_cli(config = 'config.yaml'):
    """CLI for managing hosts in the configuration."""
    if isinstance(config, str):
        config = load_config(config)
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        hosts_print(config)
        user_input = input("Type 'add' to add host, 'remove' to remove host, followed by the host you intend to edit in the format username@host (type 'back', 'done' or 'q to finish): \n").strip()
        if user_input.lower() in ['back', 'done', 'q']:
            return
        parts = user_input.split()
        if len(parts) != 2:
            print("Invalid input format. Please try again.")
            input("Press Enter to continue...")
            continue
        action = parts[0]
        host = parts[1].split('@')[1] if '@' in parts[1] else parts[1]
        user = parts[1].split('@')[0] if '@' in parts[1] else None
        if action.lower() == 'add':
            config = hosts_add(config, host, user)
            save_config(config, 'config.yaml')
            print(f"Host {host} added.")
        elif action.lower() == 'remove' or action.lower() == 'rm':
            config = hosts_remove(config, host, user)
            save_config(config, 'config.yaml')
        else:
            print("Invalid action. Please try again.")