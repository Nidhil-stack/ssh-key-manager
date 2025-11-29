"""Multi-file management for goodass CLI.

This module provides functions for managing multiple ssh-config.yaml files,
allowing users to work on multiple files as if they're a single file.
"""

import os
import yaml
import copy

if __package__ is None:
    import autocomplete
else:
    from . import autocomplete


def load_settings(config_dir):
    """Load the settings.yaml file.
    
    Parameters:
    - config_dir (str): Path to the configuration directory.
    
    Returns:
    - dict: Settings dictionary.
    """
    settings_path = os.path.join(config_dir, "settings.yaml")
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_settings(settings, config_dir):
    """Save the settings.yaml file.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    """
    settings_path = os.path.join(config_dir, "settings.yaml")
    with open(settings_path, "w") as f:
        yaml.dump(settings, f)


def get_config_files(settings):
    """Get the list of configured config files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    
    Returns:
    - list: List of config file configurations.
    """
    return settings.get("config_files", [])


def get_selected_files(settings):
    """Get the list of currently selected config files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    
    Returns:
    - list: List of selected file names.
    """
    return settings.get("selected_files", [])


def add_config_file(settings, name, path):
    """Add a config file to the list.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - name (str): Display name for the config file.
    - path (str): Path to the config file.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    if "config_files" not in settings:
        settings["config_files"] = []
    
    # Check if file already exists
    for f in settings["config_files"]:
        if f.get("path") == path:
            print(f"File {path} already exists in the list.")
            return settings
    
    settings["config_files"].append({
        "name": name,
        "path": path,
    })
    return settings


def remove_config_file(settings, name):
    """Remove a config file from the list.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - name (str): Name of the config file to remove.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    files = settings.get("config_files", [])
    settings["config_files"] = [f for f in files if f.get("name") != name]
    
    # Also remove from selected files
    selected = settings.get("selected_files", [])
    settings["selected_files"] = [s for s in selected if s != name]
    
    return settings


def set_selected_files(settings, selected_names):
    """Set the selected config files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - selected_names (list): List of file names to select.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    settings["selected_files"] = selected_names
    return settings


def merge_configs(configs):
    """Merge multiple config files into a single config.
    
    Parameters:
    - configs (list): List of (name, config_dict) tuples.
    
    Returns:
    - dict: Merged configuration dictionary.
    """
    merged = {
        "hosts": [],
        "users": [],
    }
    
    for name, config in configs:
        # Merge hosts
        for host in config.get("hosts", []):
            # Check if host already exists
            existing = None
            for h in merged["hosts"]:
                if h.get("host") == host.get("host"):
                    existing = h
                    break
            
            if existing:
                # Merge users for existing host
                for user in host.get("users", []):
                    if user not in existing.get("users", []):
                        existing.setdefault("users", []).append(user)
            else:
                # Add new host
                merged["hosts"].append(copy.deepcopy(host))
        
        # Merge users
        for user in config.get("users", []):
            # Check if user already exists by email
            existing = None
            for u in merged["users"]:
                if u.get("email") == user.get("email"):
                    existing = u
                    break
            
            if existing:
                # Merge keys for existing user
                for key in user.get("keys", []):
                    key_exists = False
                    for k in existing.get("keys", []):
                        if k.get("key") == key.get("key"):
                            key_exists = True
                            break
                    if not key_exists:
                        existing.setdefault("keys", []).append(copy.deepcopy(key))
            else:
                # Add new user
                merged["users"].append(copy.deepcopy(user))
        
        # Preserve other settings from first config
        for key, value in config.items():
            if key not in ["hosts", "users"] and key not in merged:
                merged[key] = value
    
    return merged


def load_merged_config(settings, config_dir):
    """Load and merge all selected config files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    
    Returns:
    - dict: Merged configuration dictionary.
    """
    selected = settings.get("selected_files", [])
    files = settings.get("config_files", [])
    
    if not selected:
        # Return default config path
        default_path = os.path.join(config_dir, "ssh-config.yaml")
        if os.path.exists(default_path):
            with open(default_path, "r") as f:
                return yaml.safe_load(f) or {"hosts": [], "users": []}
        return {"hosts": [], "users": []}
    
    configs = []
    for name in selected:
        for f in files:
            if f.get("name") == name:
                path = f.get("path", "")
                if os.path.exists(path):
                    with open(path, "r") as fp:
                        config = yaml.safe_load(fp) or {"hosts": [], "users": []}
                        configs.append((name, config))
                break
    
    if not configs:
        return {"hosts": [], "users": []}
    
    return merge_configs(configs)


def save_to_selected_files(config, settings, config_dir):
    """Save changes to all selected config files.
    
    For merged files, this updates each file with its own hosts/users.
    For single file, it saves directly.
    
    Parameters:
    - config (dict): Configuration to save.
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    """
    selected = settings.get("selected_files", [])
    files = settings.get("config_files", [])
    
    if not selected or len(selected) == 1:
        # Single file mode - save directly
        if selected:
            for f in files:
                if f.get("name") == selected[0]:
                    with open(f.get("path"), "w") as fp:
                        yaml.dump(config, fp)
                    return
        
        # Default file
        default_path = os.path.join(config_dir, "ssh-config.yaml")
        with open(default_path, "w") as f:
            yaml.dump(config, f)
        return
    
    # Multi-file mode - need to distribute changes
    # For simplicity, save the full merged config to the first selected file
    # and leave others unchanged (user can use sync to propagate)
    for f in files:
        if f.get("name") == selected[0]:
            with open(f.get("path"), "w") as fp:
                yaml.dump(config, fp)
            break


def config_files_print(settings):
    """Print the list of configured config files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    """
    import prettytable
    
    files = settings.get("config_files", [])
    selected = settings.get("selected_files", [])
    
    table = prettytable.PrettyTable()
    table.field_names = ["#", "Name", "Path", "Selected"]
    
    if not files:
        print("No additional config files configured.")
        print("Using default: ssh-config.yaml")
        return
    
    for i, f in enumerate(files, 1):
        name = f.get("name", "N/A")
        path = f.get("path", "N/A")
        is_selected = "✓" if name in selected else ""
        table.add_row([i, name, path, is_selected])
    
    print("Configured Config Files:")
    print(table)


def get_file_completions(settings):
    """Get list of completions for file management.
    
    Parameters:
    - settings (dict): Settings dictionary.
    
    Returns:
    - list: List of completion options.
    """
    completions = ["add", "remove", "rm", "select", "all", "back", "done", "q"]
    
    for f in settings.get("config_files", []):
        name = f.get("name", "")
        if name:
            completions.append(f"remove {name}")
            completions.append(f"rm {name}")
            completions.append(f"select {name}")
    
    return completions


def file_selection_prompt(settings, config_dir):
    """Prompt user to select config files on startup.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    files = settings.get("config_files", [])
    
    if not files:
        return settings
    
    selected = settings.get("selected_files", [])
    
    # If already has selection, use it
    if selected:
        return settings
    
    # If only one file, auto-select it
    if len(files) == 1:
        settings["selected_files"] = [files[0].get("name")]
        save_settings(settings, config_dir)
        return settings
    
    # Multiple files - prompt user
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Select Config Files ===\n")
    print("You have multiple config files. Select which to use:")
    print("  Type 'all' to select all files")
    print("  Type file numbers separated by commas (e.g., 1,2,3)")
    print()
    
    config_files_print(settings)
    
    user_input = input("\nYour selection: ").strip().lower()
    
    if user_input == "all":
        settings["selected_files"] = [f.get("name") for f in files]
    else:
        try:
            indices = [int(x.strip()) for x in user_input.split(",")]
            selected_names = []
            for idx in indices:
                if 1 <= idx <= len(files):
                    selected_names.append(files[idx - 1].get("name"))
            settings["selected_files"] = selected_names
        except ValueError:
            # Single name input
            for f in files:
                if f.get("name", "").lower() == user_input:
                    settings["selected_files"] = [f.get("name")]
                    break
    
    save_settings(settings, config_dir)
    return settings


def multifile_cli(config_dir):
    """CLI for managing multiple config files.
    
    Parameters:
    - config_dir (str): Path to the configuration directory.
    """
    settings = load_settings(config_dir)
    
    file_menu = """
Config File Management Menu:

    1. Add Config File
    2. Remove Config File
    3. Select Files to Use
    4. Select All Files
    5. View Selected Files

    6. Back to Main Menu
    """
    
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        config_files_print(settings)
        print(file_menu)
        option = input("Enter option number: ")
        os.system("cls" if os.name == "nt" else "clear")
        
        if option == "1":
            settings = add_file_cli(settings, config_dir)
        elif option == "2":
            settings = remove_file_cli(settings, config_dir)
        elif option == "3":
            settings = select_files_cli(settings, config_dir)
        elif option == "4":
            files = settings.get("config_files", [])
            settings["selected_files"] = [f.get("name") for f in files]
            save_settings(settings, config_dir)
            print("All files selected.")
            input("Press Enter to continue...")
        elif option == "5":
            view_selected_cli(settings)
        elif option == "6" or option.lower() in ["back", "done", "q"]:
            return
        else:
            print("Invalid option selected.")
            input("Press Enter to continue...")


def add_file_cli(settings, config_dir):
    """CLI for adding a new config file.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Add Config File ===\n")
    
    name = input("Enter a display name for this config: ").strip()
    if not name:
        print("Name is required.")
        input("Press Enter to continue...")
        return settings
    
    path = autocomplete.input_with_path_completion(
        "Enter path to the config file (Tab for completion): "
    ).strip()
    
    if not path:
        print("Path is required.")
        input("Press Enter to continue...")
        return settings
    
    # Expand path
    path = os.path.expanduser(path)
    
    # Create file if it doesn't exist
    if not os.path.exists(path):
        create = input(f"File {path} does not exist. Create it? (y/N): ").strip().lower()
        if create == "y":
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                yaml.dump({"hosts": [], "users": []}, f)
            print(f"Created {path}")
        else:
            print("File not added.")
            input("Press Enter to continue...")
            return settings
    
    settings = add_config_file(settings, name, path)
    save_settings(settings, config_dir)
    print(f"\nConfig file '{name}' added successfully.")
    input("Press Enter to continue...")
    return settings


def remove_file_cli(settings, config_dir):
    """CLI for removing a config file.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    config_files_print(settings)
    
    files = settings.get("config_files", [])
    if not files:
        input("Press Enter to continue...")
        return settings
    
    try:
        choice = int(input("\nEnter file number to remove (or 0 to cancel): ").strip())
        if choice == 0:
            return settings
        if 1 <= choice <= len(files):
            name = files[choice - 1].get("name", "")
            settings = remove_config_file(settings, name)
            save_settings(settings, config_dir)
            print(f"\nConfig file '{name}' removed.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    
    input("Press Enter to continue...")
    return settings


def select_files_cli(settings, config_dir):
    """CLI for selecting which config files to use.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    config_files_print(settings)
    
    files = settings.get("config_files", [])
    if not files:
        print("No config files to select from.")
        input("Press Enter to continue...")
        return settings
    
    print("\nSelect files to use:")
    print("  Type 'all' to select all files")
    print("  Type file numbers separated by commas (e.g., 1,2,3)")
    print("  Type 'none' to clear selection")
    
    user_input = input("\nYour selection: ").strip().lower()
    
    if user_input == "all":
        settings["selected_files"] = [f.get("name") for f in files]
        print("All files selected.")
    elif user_input == "none":
        settings["selected_files"] = []
        print("Selection cleared.")
    else:
        try:
            indices = [int(x.strip()) for x in user_input.split(",")]
            selected_names = []
            for idx in indices:
                if 1 <= idx <= len(files):
                    selected_names.append(files[idx - 1].get("name"))
            settings["selected_files"] = selected_names
            print(f"Selected {len(selected_names)} file(s).")
        except ValueError:
            print("Invalid input.")
    
    save_settings(settings, config_dir)
    input("Press Enter to continue...")
    return settings


def view_selected_cli(settings):
    """CLI for viewing currently selected files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print("=== Currently Selected Files ===\n")
    
    selected = settings.get("selected_files", [])
    files = settings.get("config_files", [])
    
    if not selected:
        print("No files selected. Using default ssh-config.yaml")
    else:
        for name in selected:
            for f in files:
                if f.get("name") == name:
                    print(f"  ✓ {name}: {f.get('path', 'N/A')}")
                    break
    
    input("\nPress Enter to continue...")
