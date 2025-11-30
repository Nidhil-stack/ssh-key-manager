## 🔐 Global Oversight Of Deployed Authorized SSH Settings

This document provides installation instructions and operational guidelines for managing SSH authorized keys across multiple hosts.

---

## 📑 Table of Contents

- [Installation and Configuration](#️-installation-and-configuration)
  - [Installation](#-installation)
  - [First Run and Setup Wizard](#-first-run-and-setup-wizard)
  - [Configuration Files](#-configuration-files)
  - [Thread Limiting](#-thread-limiting-optional)
- [Main Menu Overview](#-main-menu-overview)
- [Core Features](#-core-features)
  - [Fetch and Display SSH Keys](#1-fetch-and-display-ssh-keys)
  - [Fix SSH Key Issues](#2-fix-ssh-key-issues)
  - [Manage Users](#3-manage-users)
  - [Manage Hosts](#4-manage-hosts)
- [Advanced Options](#-advanced-options)
  - [Remote Sync (SFTP)](#-remote-sync-sftp)
  - [GPG Encryption & Signing](#-gpg-encryption--signing)
  - [Multi-File Management](#-multi-file-management)
- [Settings](#️-settings)
- [Non-Interactive Mode](#-non-interactive-mode)
- [Security Best Practices](#️-security-best-practices)
- [Password Configuration (Use with Caution)](#️-optional-password-configuration-use-with-caution)
- [Development & Testing](#-development--testing)
- [Contributing](#-contributing)
- [Roadmap](#️-roadmap--todo)
- [License](#️-license)
- [Contact](#-contact)

---

## ⚙️ Installation and Configuration

### 📥 Installation

1.  **Download the Release File:** Download the latest Wheel file (`.whl`) from the **goodass release page**: [https://github.com/Nidhil-stack/GOODASS/releases](https://github.com/Nidhil-stack/GOODASS/releases)
2.  **Install the Package:** Install the package using **pip** from the location where you downloaded the file (replace `path/to/download` with the actual path):

```bash
pip install path/to/download/goodass-0.3.0_pre.whl
```

### 🚀 First Run and Setup Wizard

The program includes an **interactive Setup Wizard** that handles the initial configuration.

1.  **Run Program:** Execute the main command:
    ```bash
    goodass
    ```
2.  **Wizard Activation:** The program will automatically launch the **Setup Wizard** if the required **`settings.yaml`** file is missing.
3.  **Automatic Configuration:** The wizard allows you to:
      * **Create** the `settings.yaml` file interactively.
      * **Generate a new SSH keypair** for immediate use (if you don't have one).

> **Note:** The Setup Wizard is **automatically skipped** if the `settings.yaml` file is found.

### 📝 Configuration Files

> Note: **No file needs to be created or edited manually, although you can always edit them manually or import them if you find it faster.**

The primary configuration file, **`settings.yaml`**, must be located in the application configuration directory:

| Operating System | Absolute Configuration Path |
| :--- | :--- |
| **Linux/Unix** | `~/.config/goodass/settings.yaml` |
| **Windows** | `%APPDATA%\goodass\settings.yaml` |
| **macOS** | `~/Library/Application Support/goodass/settings.yaml` |

A minimal `settings.yaml` file looks like this:

```yaml
ssh_private_key_path: /absolute/path/to/your/key
```

Additional settings available:

```yaml
ssh_private_key_path: /absolute/path/to/your/key
verbosity: 0                    # Set to 4 for debug mode
gpg_home: ~/.gnupg              # GPG home directory (optional)
config_files:                   # Multiple config files (optional)
  - name: "Main Config"
    path: "/path/to/ssh-config.yaml"
selected_files:                 # Currently selected config files
  - "Main Config"
```

### 🔒 Thread Limiting (Optional)

To prevent overwhelming SSH servers when managing many keys, you can limit concurrent connections per host in `ssh-config.yaml`:

```yaml
max_threads_per_host: 5  # Limit to 5 concurrent connections per host
```

  * Set to a positive integer to limit concurrent threads per host
  * Set to `0` or omit the setting entirely for **no limit** (default behavior)

> **❗ Error Handling Note**
> All program errors, warnings, and log messages are **redirected and saved** in files within the configuration directory (e.g., `~/.config/goodass/`). Set **verbosity to 4** for debug mode to display errors in the terminal.

---

## 📋 Main Menu Overview

When you run `goodass`, you'll see the main menu with 7 options:

```
Welcome to the SSH Key Manager (v0.3.0-pre), please select an option:

    1. Fetch and display all SSH keys
    2. Fix SSH key issues
    3. Manage Users
    4. Manage Hosts
    5. Advanced Options (Sync, GPG, Multi-File)
    6. Edit Settings
    
    7. Exit

Licensed under AGPL-3.0 | https://github.com/Nidhil-stack/GOODASS
```

The **Advanced Options** submenu contains:
```
Advanced Options:

    1. Remote Sync (SFTP)
    2. GPG Encryption & Signing
    3. Manage Config Files

    4. Back to Main Menu
```

---

## 🔧 Core Features

### 1. Fetch and Display SSH Keys

Retrieves and displays all SSH public keys currently deployed on your configured hosts.

**Usage:**
1. Select option `1` from the main menu
2. The program connects to all configured hosts
3. Displays a table showing:
   - Host IP/hostname
   - Username
   - Key type (e.g., ssh-ed25519, ssh-rsa)
   - Key fingerprint (first 10 characters)
   - Key hostname/comment

### 2. Fix SSH Key Issues

Synchronizes your configured keys with all remote hosts, ensuring each user has the correct authorized keys.

**Usage:**
1. Select option `2` from the main menu
2. Review the displayed keys and their status:
   - **MATCHED**: Key is correctly deployed
   - **NOT FOUND**: Key should be added to the server
   - **UNAUTHORIZED**: Key exists on server but not in config (will be removed)
3. Confirm to apply fixes

### 3. Manage Users

Add, remove, and configure users and their SSH keys.

**User Management Menu:**
```
    1. Add User
    2. Add Key(s) to User
    3. Remove Key from User
    4. Remove User
    5. Manage User Key Access
    6. Back to Main Menu
```

**Key Access Management:**
- Configure which hosts/users each key can access
- Admin keys automatically have access to all hosts
- Non-admin keys require explicit access configuration

### 4. Manage Hosts

Add and remove hosts from your configuration.

**Usage:**
- Type `add user@host` to add a new host/user combination
- Type `remove user@host` or `rm user@host` to remove
- Use **Tab** for autocomplete on existing entries

---

## 🚀 Advanced Options

The **Advanced Options** submenu (option 5 from the main menu) provides access to:
- Remote Sync (SFTP) - Sync configs across servers
- GPG Encryption & Signing - Protect your config files
- Manage Config Files - Work with multiple configurations

---

## 🔄 Remote Sync (SFTP)

Synchronize your `ssh-config.yaml` with remote servers via SFTP. This enables configuration sharing and backup across multiple machines.

**Access via:** Main Menu → Advanced Options → Remote Sync (SFTP)

**Remote Sync Menu:**
```
    1. Add Sync Server
    2. Remove Sync Server
    3. Upload Config to All Servers
    4. Download Config from Server
    5. Toggle Autosync on Startup
    6. Back to Main Menu
```

### Adding a Sync Server

1. Select **Advanced Options** from the main menu
2. Select **Remote Sync (SFTP)**
3. Select option `1` (Add Sync Server)
4. Enter the required information:
   - **Hostname or IP**: The server address (e.g., `192.168.1.100` or `myserver.com`)
   - **SSH Username**: The user to connect as (e.g., `admin`)
   - **SSH Port**: Default is `22`
   - **Remote Path**: Where to store the config (default: `~/.config/goodass/ssh-config.yaml`)

**Example:**
```
Enter server hostname or IP: backup.example.com
Enter SSH username: admin
Enter SSH port (default: 22): 22
Enter remote path (default: ~/.config/goodass/ssh-config.yaml): 
```

### Uploading Config to Servers

1. Select option `3` (Upload Config to All Servers)
2. Confirm to upload
3. The config will be uploaded to all configured sync servers

> **Note:** The upload uses your SSH private key configured in settings. Ensure key-based authentication is set up on the remote servers.

### Downloading Config from Server

1. Select option `4` (Download Config from Server)
2. If multiple servers are configured, select which one to download from
3. Confirm to download and overwrite your local config

### Autosync on Startup

Enable automatic synchronization when the program starts:

1. Select option `5` (Toggle Autosync on Startup)
2. When enabled, the program will:
   - **Sync ALL config files** (main config and any additional config files you've added)
   - Upload all config files to **ALL configured sync servers**
   - Keep configurations in sync across all your machines

> **Tip:** Autosync is useful for teams sharing a common configuration. All selected config files are synced to all servers.

---

## 🔐 GPG Encryption & Signing

Protect your configuration files with GPG encryption and cryptographic signatures to prevent unauthorized modifications.

**Access via:** Main Menu → Advanced Options → GPG Encryption & Signing

**GPG Key Management Menu:**
```
    1. Add GPG Public Key (from keyring)
    2. Add GPG Public Key (import from file)
    3. Remove GPG Public Key
    4. List Available Keys in Keyring
    5. Sign & Encrypt Config File
    6. Decrypt & Verify Config File
    7. Sign Config File Only
    8. Verify Config Signature
    9. Back to Main Menu
```

### Managing GPG Public Keys

**Add from Keyring:**
1. Select option `1` to add a key from your GPG keyring
2. Select the key number from the displayed list
3. The key fingerprint is stored in your config

**Import from File:**
1. Select option `2` to import from a `.asc` or `.gpg` file
2. Enter the path to the public key file (use **Tab** for autocomplete)
3. The key is imported to your keyring and added to the config

**Remove Key:**
1. Select option `3` to remove a key
2. Select the key number to remove

### Sign & Encrypt Config File

This provides both **confidentiality** (encryption) and **integrity** (signature).

1. Select option `5` (Sign & Encrypt)
2. Select which private key to sign with
3. Enter your GPG passphrase (if not using gpg-agent)
4. The encrypted file is saved as `ssh-config.yaml.gpg`

**Result:** Only recipients with the corresponding private keys can decrypt, and the signature proves the file hasn't been tampered with.

### Decrypt & Verify Config File

1. Select option `6` (Decrypt & Verify)
2. Enter the path to the encrypted file (default: `ssh-config.yaml.gpg`)
3. Enter your GPG passphrase
4. The file is decrypted and the signature is verified against trusted keys

**Verification outcomes:**
- ✓ **Valid & Trusted**: Signature matches a trusted key
- ⚠ **Valid but Untrusted**: Signature is valid but signer is not in your trusted keys
- ✗ **Failed**: Decryption or verification failed

### Sign Config Only

Create a detached signature without encrypting:

1. Select option `7` (Sign Config Only)
2. Select which private key to sign with
3. Enter your GPG passphrase
4. A `.sig` file is created alongside your config

**Use case:** Share unencrypted config but prove authenticity.

### Verify Config Signature

Verify a detached signature:

1. Select option `8` (Verify Config Signature)
2. The program checks `ssh-config.yaml.sig` against trusted keys
3. Results show whether the signature is valid and from a trusted source

> **Security Note:** Always verify signatures on config files received from remote sources before using them.

---

## 📁 Multi-File Management

Work with multiple `ssh-config.yaml` files simultaneously, useful for managing different environments or projects.

**Access via:** Main Menu → Advanced Options → Manage Config Files

**Config File Management Menu:**
```
    1. Add Config File
    2. Remove Config File
    3. Select Files to Use
    4. Select All Files
    5. View Selected Files
    6. Back to Main Menu
```

### Adding Config Files

1. Select **Advanced Options** from the main menu
2. Select **Manage Config Files**
3. Select option `1` (Add Config File)
4. Enter a display name (e.g., "Production", "Staging")
5. Enter the file path (use **Tab** for autocomplete)
6. If the file doesn't exist, you'll be asked to create it

**Example:**
```
Enter a display name for this config: Production
Enter path to the config file: /home/user/configs/prod-ssh-config.yaml
File /home/user/configs/prod-ssh-config.yaml does not exist. Create it? (y/N): y
Created /home/user/configs/prod-ssh-config.yaml
Config file 'Production' added successfully.
```

### Selecting Files to Use

1. Select option `3` (Select Files to Use)
2. Enter your selection:
   - Type `all` to select all files
   - Type comma-separated numbers (e.g., `1,2,3`)
   - Type `none` to clear selection

**Example:**
```
Configured Config Files:
+---+------------+--------------------------------------+----------+
| # |    Name    |                 Path                 | Selected |
+---+------------+--------------------------------------+----------+
| 1 | Production | /home/user/configs/prod-ssh.yaml     |          |
| 2 | Staging    | /home/user/configs/staging-ssh.yaml  |          |
| 3 | Dev        | /home/user/configs/dev-ssh.yaml      | ✓        |
+---+------------+--------------------------------------+----------+

Select files to use:
  Type 'all' to select all files
  Type file numbers separated by commas (e.g., 1,2,3)
  Type 'none' to clear selection

Your selection: 1,3
Selected 2 file(s).
```

### Working with Multiple Files

When multiple files are selected:
- **Hosts and users are merged** from all selected files
- **Changes are saved** to the first selected file
- The selection is **remembered** across sessions
- **All selected files are synced** when autosync is enabled

**Startup behavior:**
- If you have multiple config files and no prior selection, you'll be prompted to choose
- Your last selection is automatically used on subsequent runs
- When autosync is enabled, ALL selected config files are uploaded to ALL sync servers

---

## ⚙️ Settings

Configure program settings through the Settings menu (option `6`):

```
=== Settings Configuration ===

Current settings:
  1. ssh_private_key_path: /home/user/.ssh/id_rsa
  2. verbosity: 0
  3. max_threads_per_host: (not set)
  4. gpg_home: (not set)

Options:
  Enter 1, 2, 3, or 4 to edit the corresponding setting
  Enter 'done' or 'q' to return to main menu
```

**Settings explained:**

| Setting | Description |
| :--- | :--- |
| `ssh_private_key_path` | Path to SSH private key for connecting to hosts |
| `verbosity` | Log level (0-3 normal, 4 for debug mode) |
| `max_threads_per_host` | Limit concurrent SSH connections per host |
| `gpg_home` | GPG home directory for encryption operations |

---

## 🤖 Non-Interactive Mode

Run key synchronization without user prompts, ideal for cron jobs or automated deployments:

```bash
goodass --fix-keys
```

**Requirements:**
- Configuration files must already exist
- SSH key-based authentication must be set up
- For password-protected hosts, use `passwords.yaml` (see below)

---

## 🛡️ Security Best Practices

  * **Private Keys:** **Never** commit private keys to source control. Store them securely with restricted permissions (`chmod 600`).
  * **GPG Signing:** Use GPG signatures to verify config file integrity, especially when syncing from remote servers.
  * **Trusted Keys:** Only add GPG public keys from sources you trust.
  * **SSH Agent:** Use an SSH agent to avoid storing key passphrases.
  * **Pre-Distribution:** Verify remote server SSH policies (`sshd_config`) before mass-distributing keys.

---

## ⚠️ Optional Password Configuration (Use with Caution)

An optional **`passwords.yaml`** file can be placed in the configuration directory to **skip manual password entry** during bulk host registration.

> **🛑 WARNING: SECURITY RISK**
>
>   * The use of `passwords.yaml` is **strongly discouraged** as it stores credentials in plaintext.
>   * If used, **delete the file immediately** after bulk registration is complete.
>   * **Never** commit this file to any source code repository.

**Example `passwords.yaml`:**
```yaml
hosts:
  - ip: 192.168.1.100
    credentials:
      - user: root
        password: your_password
      - user: admin
        password: another_password
```

---

## 🧑‍💻 Development & Testing

**Running during development:**
```bash
python src/goodass/cli.py
```

**Local Testing:** Test using dedicated **test VMs** or **containers** to avoid impacting production systems.

**Autocomplete compatibility:**
- Requires `readline` module (included by default on Linux/macOS)
- On Windows, falls back to standard input without completion

---

## 🤝 Contributing

  * **Bug Reporting:** Open an issue on **GitHub** with clear reproduction steps.
  * **Improvements:** Submit **pull requests** with focused, well-described changes.

---

## 🗺️ Roadmap / TODO

> Completion of the remaining items will trigger the **Version 1.0.0** release.

  * Implement a **comprehensive logging system** for operational details, warnings, and success messages.
  * ~~**Limit multi-threaded jobs against one host**~~ ✅ **Implemented** - Use `max_threads_per_host` setting.
  * ~~**Synchronize ssh-config.yaml with remote servers via SFTP**~~ ✅ **Implemented** - Use "Manage Remote Sync" menu.
  * ~~**GPG encryption for config files**~~ ✅ **Implemented** - Use "Manage GPG Keys" menu.

> **Future Goal: Version 2.0**
> A **Text User Interface (TUI)** is being considered for Version 2.0.

---

## ⚖️ License

This project is released under the license included in the repository. See the **`LICENSE`** file for details.

---

## 📧 Contact

  * **Author:** `Nidhil-stack`
  * **Contributors:**
    <a href="https://github.com/EddyDevProject"><img src="https://github.com/EddyDevProject.png" width="60px"/><br /></a>

---
