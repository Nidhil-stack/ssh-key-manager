# Changelog

## Version 0.3.0-pre

### ✨ New Features

#### Remote Sync via SFTP
- **New `syncManager.py` module**: Synchronize ssh-config.yaml with remote servers via SFTP
  - Add/remove remote sync servers with custom paths
  - Upload config to all configured servers
  - Download config from any configured server
  - **Autosync on startup**: Automatically sync configuration when the program starts
  - Remote path defaults to the standard config location (`~/.config/goodass/ssh-config.yaml`)
  - Sync server configuration is stored in the ssh-config.yaml file itself

#### Multi-File Support
- **New `multiFileManager.py` module**: Work with multiple ssh-config.yaml files simultaneously
  - Add/remove config files with custom names
  - Select which files to use (single, multiple, or all)
  - Merge multiple configs as if they were a single file
  - Remember last selection and use it automatically on startup
  - Prompt for file selection only when multiple files exist and no prior selection is found
  - Quick "all" option to select all files at once

#### GPG Encryption Support
- **New `gpgManager.py` module**: Protect config files with GPG encryption
  - Support for multiple GPG public keys (any one can unlock the file)
  - Add keys from system keyring or import from file
  - Remove GPG public keys from configuration
  - List available keys in system keyring
  - Encrypt/decrypt config files
  - GPG public keys are stored in the ssh-config.yaml file itself

#### Settings Enhancements
- **GPG Home Directory**: New setting for specifying GPG private key location
  - Configurable via Settings menu (option 4)
  - Defaults to system default (~/.gnupg) if not set

### 🎨 UI Changes

#### Updated Main Menu (8 options + exit)
1. Fetch and display all SSH keys
2. Fix SSH key issues
3. Manage Users
4. Manage Hosts
5. Manage Remote Sync (new)
6. Manage GPG Keys (new)
7. Manage Config Files (new)
8. Edit Settings

9. Exit

### 📦 Dependencies
- Added `python-gnupg==0.5.4` for GPG encryption support

### 🔧 Technical Details
- All new features are implemented as separate modules for clean code organization
- Consistent UI patterns matching existing menus (add/remove with tab completion)
- Sync server and GPG key configurations are stored in ssh-config.yaml for portability

---

## Version 0.1.1

### ✨ New Features

#### Tab Autocomplete Support
- **Settings Menu**: Added tab completion for SSH private key path selection with full filesystem navigation
- **Host Management**: Added tab completion for removing hosts with `user@host` format support
- **User Management**: Added tab completion for user email selection in all user management operations
- **Key Access Management**: Added tab completion for removing access entries in the deepest layer of user key access management

### 🔧 Improvements

#### Code Refactoring
- **New `autocomplete.py` module**: Centralized tab-completion functionality with:
  - Path completion for filesystem navigation
  - List-based completion for predefined options
  - Multi-word completion support (e.g., `remove user@host`)
  - Windows compatibility (graceful fallback when readline is unavailable)

- **New `utils.py` module**: Extracted utility functions from cli.py:
  - `signal_handler` - Graceful Ctrl+C handling
  - `exit_gracefully` - Clean temporary file removal on exit
  - `generate_ssh_keypair` - SSH keypair generation

- **New `settingsManager.py` module**: Extracted settings management from cli.py:
  - `settings_cli` - Main settings menu
  - `edit_ssh_private_key_path` - Edit SSH key path with tab completion
  - `edit_verbosity` - Edit verbosity level
  - `edit_max_threads_per_host` - Edit concurrent thread limit

- **Updated `keyManager.py`**: Added `non_interactive_fix_keys()` function

- **Slimmed `cli.py`**: Reduced from ~470 lines to ~190 lines through modularization

### 📝 Usage Notes

#### Autocomplete
- Press `Tab` to cycle through available completions when prompted
- Autocomplete for hosts and key access is only available for **removal** operations (not adding new entries)
- Path completion supports `~` expansion and directory navigation

### 🔄 Compatibility
- Autocomplete requires the `readline` module (included by default on Linux/macOS)
- On Windows, the application gracefully falls back to standard input without completion
