"""Multi-file management for goodass CLI.

This module provides functions for managing multiple ssh-config.yaml files,
allowing users to work on multiple files as if they're a single file.
Files can be toggled on/off and given custom local names.
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
    """Get the list of currently selected (active) config files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    
    Returns:
    - list: List of selected file names.
    """
    return settings.get("selected_files", [])


def get_sync_selection(settings):
    """Get the sync selection for non-interactive mode.
    
    This is stored in settings and used by non-interactive mode
    to determine which files to sync.
    
    Parameters:
    - settings (dict): Settings dictionary.
    
    Returns:
    - list: List of file names to sync in non-interactive mode.
            If None or empty, uses selected_files.
    """
    return settings.get("sync_selection", [])


def set_sync_selection(settings, file_names):
    """Set the sync selection for non-interactive mode.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - file_names (list): List of file names to sync.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    settings["sync_selection"] = file_names
    return settings


def add_config_file(settings, name, path, active=True):
    """Add a config file to the list.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - name (str): Display name for the config file (local custom name).
    - path (str): Path to the config file.
    - active (bool): Whether the file is active/selected.
    
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
        "active": active,
    })
    
    # Auto-select if active
    if active:
        if "selected_files" not in settings:
            settings["selected_files"] = []
        if name not in settings["selected_files"]:
            settings["selected_files"].append(name)
    
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
    
    # Also remove from sync selection
    sync_sel = settings.get("sync_selection", [])
    settings["sync_selection"] = [s for s in sync_sel if s != name]
    
    return settings


def toggle_file_active(settings, name, active=None):
    """Toggle a file's active status on/off.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - name (str): Name of the config file to toggle.
    - active (bool): If provided, set to this value. Otherwise toggle.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    files = settings.get("config_files", [])
    selected = settings.get("selected_files", [])
    
    for f in files:
        if f.get("name") == name:
            if active is None:
                # Toggle
                f["active"] = not f.get("active", True)
            else:
                f["active"] = active
            
            # Update selected_files list
            if f["active"]:
                if name not in selected:
                    selected.append(name)
            else:
                selected = [s for s in selected if s != name]
            
            settings["selected_files"] = selected
            break
    
    return settings


def rename_config_file(settings, old_name, new_name):
    """Rename a config file (local name only).
    
    Parameters:
    - settings (dict): Settings dictionary.
    - old_name (str): Current name of the config file.
    - new_name (str): New name for the config file.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    files = settings.get("config_files", [])
    
    # Check if new name already exists
    for f in files:
        if f.get("name") == new_name:
            print(f"Name '{new_name}' already exists.")
            return settings
    
    for f in files:
        if f.get("name") == old_name:
            f["name"] = new_name
            break
    
    # Update selected_files
    selected = settings.get("selected_files", [])
    settings["selected_files"] = [new_name if s == old_name else s for s in selected]
    
    # Update sync_selection
    sync_sel = settings.get("sync_selection", [])
    settings["sync_selection"] = [new_name if s == old_name else s for s in sync_sel]
    
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
    
    # Also update active status
    files = settings.get("config_files", [])
    for f in files:
        f["active"] = f.get("name") in selected_names
    
    return settings


def get_active_config_files(settings):
    """Get list of active (enabled) config files.
    
    Parameters:
    - settings (dict): Settings dictionary.
    
    Returns:
    - list: List of active config file configurations.
    """
    files = settings.get("config_files", [])
    return [f for f in files if f.get("active", True)]


def get_files_for_sync(settings, use_sync_selection=False):
    """Get list of files to sync.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - use_sync_selection (bool): If True, use sync_selection instead of active files.
    
    Returns:
    - list: List of config file configurations to sync.
    """
    if use_sync_selection:
        sync_sel = settings.get("sync_selection", [])
        if sync_sel:
            files = settings.get("config_files", [])
            return [f for f in files if f.get("name") in sync_sel]
    
    # Fall back to active files
    return get_active_config_files(settings)


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
    """Print the list of configured config files with active status.
    
    Parameters:
    - settings (dict): Settings dictionary.
    """
    import prettytable
    
    files = settings.get("config_files", [])
    selected = settings.get("selected_files", [])
    sync_sel = settings.get("sync_selection", [])
    
    table = prettytable.PrettyTable()
    table.field_names = ["#", "Name", "Path", "Active", "Sync"]
    
    if not files:
        print("No additional config files configured.")
        print("Using default: ssh-config.yaml")
        return
    
    for i, f in enumerate(files, 1):
        name = f.get("name", "N/A")
        path = f.get("path", "N/A")
        is_active = "✓" if f.get("active", True) or name in selected else ""
        is_sync = "✓" if name in sync_sel else ""
        table.add_row([i, name, path, is_active, is_sync])
    
    print("Configured Config Files:")
    print(table)
    print("\nActive = File is used in current session")
    print("Sync = File is included in non-interactive sync")


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
    3. Toggle File Active On/Off
    4. Rename Config File (local name)
    5. Set Sync Selection (for non-interactive mode)
    6. Select All Files Active
    7. View Selected Files

    8. Back to Main Menu
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
            settings = toggle_file_cli(settings, config_dir)
        elif option == "4":
            settings = rename_file_cli(settings, config_dir)
        elif option == "5":
            settings = set_sync_selection_cli(settings, config_dir)
        elif option == "6":
            files = settings.get("config_files", [])
            settings["selected_files"] = [f.get("name") for f in files]
            for f in files:
                f["active"] = True
            save_settings(settings, config_dir)
            print("All files set to active.")
            input("Press Enter to continue...")
        elif option == "7":
            view_selected_cli(settings)
        elif option == "8" or option.lower() in ["back", "done", "q"]:
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
            dir_path = os.path.dirname(path)
            if dir_path:  # Only create directory if path has a directory component
                os.makedirs(dir_path, exist_ok=True)
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
    print("=== Currently Active Files ===\n")
    
    selected = settings.get("selected_files", [])
    files = settings.get("config_files", [])
    sync_sel = settings.get("sync_selection", [])
    
    print("Active files (used in current session):")
    if not selected:
        print("  No files selected. Using default ssh-config.yaml")
    else:
        for name in selected:
            for f in files:
                if f.get("name") == name:
                    print(f"  ✓ {name}: {f.get('path', 'N/A')}")
                    break
    
    print("\nSync selection (used in non-interactive mode):")
    if not sync_sel:
        print("  Not set - will use active files")
    else:
        for name in sync_sel:
            for f in files:
                if f.get("name") == name:
                    print(f"  ✓ {name}: {f.get('path', 'N/A')}")
                    break
    
    input("\nPress Enter to continue...")


def toggle_file_cli(settings, config_dir):
    """CLI for toggling a file's active status on/off.
    
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
        print("No config files to toggle.")
        input("Press Enter to continue...")
        return settings
    
    try:
        choice = int(input("\nEnter file number to toggle (or 0 to cancel): ").strip())
        if choice == 0:
            return settings
        if 1 <= choice <= len(files):
            file_entry = files[choice - 1]
            name = file_entry.get("name", "")
            settings = toggle_file_active(settings, name)
            save_settings(settings, config_dir)
            new_status = "ACTIVE" if file_entry.get("active", True) else "INACTIVE"
            print(f"\nFile '{name}' is now {new_status}.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    
    input("Press Enter to continue...")
    return settings


def rename_file_cli(settings, config_dir):
    """CLI for renaming a config file (local name only).
    
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
        print("No config files to rename.")
        input("Press Enter to continue...")
        return settings
    
    try:
        choice = int(input("\nEnter file number to rename (or 0 to cancel): ").strip())
        if choice == 0:
            return settings
        if 1 <= choice <= len(files):
            old_name = files[choice - 1].get("name", "")
            new_name = input(f"Enter new name for '{old_name}': ").strip()
            if not new_name:
                print("Name cannot be empty.")
            else:
                settings = rename_config_file(settings, old_name, new_name)
                save_settings(settings, config_dir)
                print(f"\nFile renamed from '{old_name}' to '{new_name}'.")
                print("Note: This is a local name only. When uploaded, standard naming is used.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    
    input("Press Enter to continue...")
    return settings


def set_sync_selection_cli(settings, config_dir):
    """CLI for setting the sync selection for non-interactive mode.
    
    Parameters:
    - settings (dict): Settings dictionary.
    - config_dir (str): Path to the configuration directory.
    
    Returns:
    - dict: Updated settings dictionary.
    """
    os.system("cls" if os.name == "nt" else "clear")
    config_files_print(settings)
    
    files = settings.get("config_files", [])
    current_sync = settings.get("sync_selection", [])
    
    if not files:
        print("No config files configured.")
        input("Press Enter to continue...")
        return settings
    
    print("\n=== Set Sync Selection for Non-Interactive Mode ===")
    print("\nThis determines which files are synced when running:")
    print("  goodass --fix-keys")
    print("\nCurrent sync selection:", current_sync if current_sync else "(uses active files)")
    
    print("\nOptions:")
    print("  Type 'all' to sync all files")
    print("  Type file numbers separated by commas (e.g., 1,2,3)")
    print("  Type 'active' to use currently active files")
    print("  Type 'clear' to clear sync selection (will use active files)")
    
    user_input = input("\nYour selection: ").strip().lower()
    
    if user_input == "all":
        settings["sync_selection"] = [f.get("name") for f in files]
        print("Sync selection set to all files.")
    elif user_input == "active":
        settings["sync_selection"] = list(settings.get("selected_files", []))
        print("Sync selection set to match current active files.")
    elif user_input == "clear" or user_input == "none":
        settings["sync_selection"] = []
        print("Sync selection cleared. Will use active files.")
    else:
        try:
            indices = [int(x.strip()) for x in user_input.split(",")]
            sync_names = []
            for idx in indices:
                if 1 <= idx <= len(files):
                    sync_names.append(files[idx - 1].get("name"))
            settings["sync_selection"] = sync_names
            print(f"Sync selection set to {len(sync_names)} file(s).")
        except ValueError:
            print("Invalid input.")
    
    save_settings(settings, config_dir)
    input("Press Enter to continue...")
    return settings
