"""Sync management for goodass CLI.

This module provides functions for synchronizing ssh-config.yaml files
with remote servers via SFTP, supporting both manual and automatic sync.
"""

import os
import yaml
import paramiko

if __package__ is None:
    import autocomplete
else:
    from . import autocomplete


def get_remote_config_path():
    """Get the default remote path for ssh-config.yaml based on platform.
    
    Returns:
    - str: The default path where ssh-config.yaml would be stored on the remote server.
    """
    # Default to Linux/Unix path as most servers are Linux-based
    return "~/.config/goodass/ssh-config.yaml"


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


def get_remote_servers(config):
    """Get the list of remote sync servers from config.
    
    Parameters:
    - config (dict): Configuration dictionary.
    
    Returns:
    - list: List of remote server configurations.
    """
    return config.get("sync_servers", [])


def add_remote_server(config, host, username, port=22, remote_path=None):
    """Add a remote sync server to the configuration.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - host (str): Remote server hostname or IP.
    - username (str): SSH username for the remote server.
    - port (int): SSH port (default: 22).
    - remote_path (str): Remote path for the config file (default: ~/.config/goodass/ssh-config.yaml).
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    if remote_path is None:
        remote_path = get_remote_config_path()
    
    if "sync_servers" not in config:
        config["sync_servers"] = []
    
    # Check if server already exists
    for server in config["sync_servers"]:
        if server.get("host") == host and server.get("username") == username:
            print(f"Server {username}@{host} already exists.")
            return config
    
    config["sync_servers"].append({
        "host": host,
        "username": username,
        "port": port,
        "remote_path": remote_path,
    })
    return config


def remove_remote_server(config, host, username):
    """Remove a remote sync server from the configuration.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - host (str): Remote server hostname or IP.
    - username (str): SSH username for the remote server.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    servers = config.get("sync_servers", [])
    config["sync_servers"] = [
        s for s in servers 
        if not (s.get("host") == host and s.get("username") == username)
    ]
    return config


def upload_config_to_server(config_path, server, ssh_private_key_path):
    """Upload the ssh-config.yaml to a remote server via SFTP.
    
    Parameters:
    - config_path (str): Local path to the ssh-config.yaml file.
    - server (dict): Server configuration with host, username, port, remote_path.
    - ssh_private_key_path (str): Path to the SSH private key.
    
    Returns:
    - bool: True if successful, False otherwise.
    """
    host = server.get("host")
    username = server.get("username")
    port = server.get("port", 22)
    remote_path = os.path.expanduser(server.get("remote_path", get_remote_config_path()))
    
    try:
        client = paramiko.SSHClient()
        # Note: AutoAddPolicy is used for usability with multiple servers.
        # This is consistent with the project's keyManager.py approach.
        # For high-security environments, consider implementing host key verification.
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            host,
            port=port,
            username=username,
            key_filename=ssh_private_key_path,
        )
        
        sftp = client.open_sftp()
        
        # Ensure remote directory exists using SFTP operations
        remote_dir = os.path.dirname(remote_path)
        if remote_dir:
            try:
                # Try to create parent directories using SFTP
                path_parts = remote_dir.split('/')
                current_path = ""
                for part in path_parts:
                    if not part:
                        continue
                    current_path = current_path + "/" + part
                    try:
                        sftp.stat(current_path)
                    except IOError:
                        try:
                            sftp.mkdir(current_path)
                        except IOError:
                            pass  # Directory might already exist
            except Exception:
                pass
        
        sftp.put(config_path, remote_path)
        sftp.close()
        client.close()
        print(f"Successfully uploaded config to {username}@{host}:{remote_path}")
        return True
    except Exception as e:
        print(f"Failed to upload to {username}@{host}: {e}")
        return False


def download_config_from_server(config_path, server, ssh_private_key_path):
    """Download the ssh-config.yaml from a remote server via SFTP.
    
    Parameters:
    - config_path (str): Local path to save the ssh-config.yaml file.
    - server (dict): Server configuration with host, username, port, remote_path.
    - ssh_private_key_path (str): Path to the SSH private key.
    
    Returns:
    - bool: True if successful, False otherwise.
    """
    host = server.get("host")
    username = server.get("username")
    port = server.get("port", 22)
    remote_path = os.path.expanduser(server.get("remote_path", get_remote_config_path()))
    
    try:
        client = paramiko.SSHClient()
        # Note: AutoAddPolicy is used for usability with multiple servers.
        # This is consistent with the project's keyManager.py approach.
        # For high-security environments, consider implementing host key verification.
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            host,
            port=port,
            username=username,
            key_filename=ssh_private_key_path,
        )
        
        sftp = client.open_sftp()
        sftp.get(remote_path, config_path)
        sftp.close()
        client.close()
        print(f"Successfully downloaded config from {username}@{host}:{remote_path}")
        return True
    except Exception as e:
        print(f"Failed to download from {username}@{host}: {e}")
        return False


def sync_all_servers(config_path, ssh_private_key_path, direction="upload"):
    """Sync config with all configured remote servers.
    
    Parameters:
    - config_path (str): Path to the ssh-config.yaml file.
    - ssh_private_key_path (str): Path to the SSH private key.
    - direction (str): Either "upload" or "download".
    
    Returns:
    - int: Number of successful sync operations.
    """
    config = load_ssh_config(config_path)
    servers = get_remote_servers(config)
    
    if not servers:
        print("No remote sync servers configured.")
        return 0
    
    success_count = 0
    for server in servers:
        if direction == "upload":
            if upload_config_to_server(config_path, server, ssh_private_key_path):
                success_count += 1
        elif direction == "download":
            if download_config_from_server(config_path, server, ssh_private_key_path):
                success_count += 1
    
    return success_count


def get_server_completions(config):
    """Get list of completions for server management.
    
    Parameters:
    - config (dict): Configuration dictionary.
    
    Returns:
    - list: List of completion options.
    """
    completions = ["add", "remove", "rm", "back", "done", "q"]
    
    for server in config.get("sync_servers", []):
        host = server.get("host", "")
        username = server.get("username", "")
        if host and username:
            completions.append(f"remove {username}@{host}")
            completions.append(f"rm {username}@{host}")
    
    return completions


def sync_servers_print(config):
    """Print the list of configured sync servers.
    
    Parameters:
    - config (dict): Configuration dictionary.
    """
    import prettytable
    
    servers = config.get("sync_servers", [])
    table = prettytable.PrettyTable()
    table.field_names = ["Username", "Host", "Port", "Remote Path"]
    
    if not servers:
        print("No remote sync servers configured.")
        return
    
    for server in servers:
        table.add_row([
            server.get("username", "N/A"),
            server.get("host", "N/A"),
            server.get("port", 22),
            server.get("remote_path", "N/A"),
        ])
    
    print("Configured Sync Servers:")
    print(table)


def sync_cli(config_dir, config_path, ssh_private_key_path):
    """CLI for managing remote sync servers and syncing configuration.
    
    Parameters:
    - config_dir (str): Path to the configuration directory.
    - config_path (str): Path to the ssh-config.yaml file.
    - ssh_private_key_path (str): Path to the SSH private key.
    """
    config = load_ssh_config(config_path)
    
    sync_menu = """
Sync Management Menu:

    1. Add Sync Server
    2. Remove Sync Server
    3. Upload Config to All Servers
    4. Download Config from Server
    5. Toggle Autosync on Startup

    6. Back to Main Menu
    """
    
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        sync_servers_print(config)
        autosync = config.get("autosync_on_startup", False)
        print(f"\nAutosync on startup: {'Enabled' if autosync else 'Disabled'}")
        print(sync_menu)
        option = input("Enter option number: ")
        os.system("cls" if os.name == "nt" else "clear")
        
        if option == "1":
            config = add_server_cli(config, config_path)
        elif option == "2":
            config = remove_server_cli(config, config_path)
        elif option == "3":
            sync_servers_print(config)
            if config.get("sync_servers"):
                confirm = input("\nUpload config to all servers? (y/N): ").strip().lower()
                if confirm == "y":
                    count = sync_all_servers(config_path, ssh_private_key_path, "upload")
                    print(f"\nSuccessfully synced to {count} server(s).")
                    input("Press Enter to continue...")
            else:
                input("Press Enter to continue...")
        elif option == "4":
            config = download_config_cli(config, config_path, ssh_private_key_path)
        elif option == "5":
            config["autosync_on_startup"] = not config.get("autosync_on_startup", False)
            save_ssh_config(config, config_path)
            status = "enabled" if config["autosync_on_startup"] else "disabled"
            print(f"Autosync on startup {status}.")
            input("Press Enter to continue...")
        elif option == "6" or option.lower() in ["back", "done", "q"]:
            return
        else:
            print("Invalid option selected.")
            input("Press Enter to continue...")


def add_server_cli(config, config_path):
    """CLI for adding a new sync server.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to save the configuration.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Add Sync Server ===\n")
    
    host = input("Enter server hostname or IP: ").strip()
    if not host:
        print("Host is required.")
        input("Press Enter to continue...")
        return config
    
    username = input("Enter SSH username: ").strip()
    if not username:
        print("Username is required.")
        input("Press Enter to continue...")
        return config
    
    port_str = input("Enter SSH port (default: 22): ").strip()
    port = 22
    if port_str:
        try:
            port = int(port_str)
        except ValueError:
            print("Invalid port number. Using default port 22.")
    
    default_path = get_remote_config_path()
    remote_path = input(f"Enter remote path (default: {default_path}): ").strip()
    if not remote_path:
        remote_path = default_path
    
    config = add_remote_server(config, host, username, port, remote_path)
    save_ssh_config(config, config_path)
    print(f"\nServer {username}@{host} added successfully.")
    input("Press Enter to continue...")
    return config


def remove_server_cli(config, config_path):
    """CLI for removing a sync server.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to save the configuration.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    sync_servers_print(config)
    
    if not config.get("sync_servers"):
        input("Press Enter to continue...")
        return config
    
    completions = get_server_completions(config)
    user_input = autocomplete.input_with_list_completion(
        "\nType 'remove username@host' to remove a server\n"
        "(type 'back' or 'done' to finish, Tab for completion): ",
        completions,
        allow_spaces=True,
    ).strip()
    
    if user_input.lower() in ["back", "done", "q"]:
        return config
    
    parts = user_input.split()
    if len(parts) != 2:
        print("Invalid input format.")
        input("Press Enter to continue...")
        return config
    
    action = parts[0].lower()
    if action not in ["remove", "rm"]:
        print("Invalid action.")
        input("Press Enter to continue...")
        return config
    
    target = parts[1]
    if "@" not in target:
        print("Invalid format. Use username@host.")
        input("Press Enter to continue...")
        return config
    
    username, host = target.split("@", 1)
    config = remove_remote_server(config, host, username)
    save_ssh_config(config, config_path)
    print(f"\nServer {username}@{host} removed.")
    input("Press Enter to continue...")
    return config


def download_config_cli(config, config_path, ssh_private_key_path):
    """CLI for downloading config from a specific server.
    
    Parameters:
    - config (dict): Configuration dictionary.
    - config_path (str): Path to save the configuration.
    - ssh_private_key_path (str): Path to the SSH private key.
    
    Returns:
    - dict: Updated configuration dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    sync_servers_print(config)
    
    servers = config.get("sync_servers", [])
    if not servers:
        input("Press Enter to continue...")
        return config
    
    if len(servers) == 1:
        server = servers[0]
        confirm = input(f"\nDownload config from {server['username']}@{server['host']}? (y/N): ").strip().lower()
        if confirm == "y":
            download_config_from_server(config_path, server, ssh_private_key_path)
            config = load_ssh_config(config_path)
        input("Press Enter to continue...")
        return config
    
    print("\nSelect a server to download from:")
    for i, server in enumerate(servers, 1):
        print(f"  {i}. {server['username']}@{server['host']}")
    
    try:
        choice = int(input("\nEnter server number: ").strip())
        if 1 <= choice <= len(servers):
            server = servers[choice - 1]
            confirm = input(f"\nDownload config from {server['username']}@{server['host']}? (y/N): ").strip().lower()
            if confirm == "y":
                download_config_from_server(config_path, server, ssh_private_key_path)
                config = load_ssh_config(config_path)
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    
    input("Press Enter to continue...")
    return config


def perform_autosync(config_path, ssh_private_key_path, config_files=None):
    """Perform autosync if enabled for all config files.
    
    Called on startup to sync ALL configuration files with remote servers.
    
    Parameters:
    - config_path (str): Path to the main ssh-config.yaml file.
    - ssh_private_key_path (str): Path to the SSH private key.
    - config_files (list): List of additional config file paths to sync.
    
    Returns:
    - bool: True if autosync was performed, False otherwise.
    """
    config = load_ssh_config(config_path)
    
    if not config.get("autosync_on_startup", False):
        return False
    
    servers = config.get("sync_servers", [])
    if not servers:
        return False
    
    print("Performing autosync for all config files...")
    
    # Collect all config file paths to sync
    all_config_paths = [config_path]
    if config_files:
        for cf in config_files:
            path = cf.get("path", "")
            if path and path != config_path and os.path.exists(path):
                all_config_paths.append(path)
    
    # Sync each config file with all servers
    for cfg_path in all_config_paths:
        print(f"  Syncing {os.path.basename(cfg_path)}...")
        # Upload to ALL servers (bidirectional sync)
        for server in servers:
            upload_config_to_server(cfg_path, server, ssh_private_key_path)
    
    return True
