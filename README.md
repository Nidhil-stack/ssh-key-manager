## 🔐 Global Oversight Of Deployed Authorized SSH Settings

This document provides installation instructions and operational guidelines for managing SSH authorized keys across multiple hosts.

-----

## ⚙️ Installation and Configuration

### 📥 Installation

Install the package using **pip** from the provided Wheel file:

```bash
pip install download_directory/dist/goodass-0.0.4-py3-none-any.whl
```

### 🚀 First Run and Setup Wizard

The program now includes an **interactive Setup Wizard** that handles the initial configuration.

1.  **Run Program:** Execute the main command:
    ```bash
    goodass
    ```
2.  **Wizard Activation:** The program will automatically launch the **Setup Wizard** if the required **`settings.yaml`** file is missing.
3.  **Automatic Configuration:** The wizard allows you to:
      * **Create** the `settings.yaml` file interactively.
      * **Generate a new SSH keypair** for immediate use (if you don't have one).

> **Note:** Because the Setup Wizard can now create the configuration, the initial configuration is **automatically skipped** if the `settings.yaml` file is found.

### 📝 Configuration Files

The primary configuration file, **`settings.yaml`**, must be located in the application configuration directory.

| Operating System | Absolute Configuration Path |
| :--- | :--- |
| **Linux/Unix** | `~/.config/goodass/settings.yaml` |
| **Windows** | `%APPDATA%\goodass\settings.yaml` |
| **macOS** | `~/Library/Application Support/goodass/settings.yaml` |

A minimal `settings.yaml` file looks like this:

```yaml
ssh_private_key_path: /absolute/path/to/your/key
```

You can always **manually create or edit** this file, or provide a full configuration in the optional **`config.yaml`** file to bypass the initial wizard prompts.

> **❗ Error Handling Note**
> All program errors, warnings, and log messages are output to the terminal in **Interactive Mode**. If running in **Non-Interactive Mode** (e.g., using `--fix-keys`), these messages are **redirected and saved** in files within the same **configuration directory** (e.g., `~/.config/goodass/`). This is essential for debugging and reporting issues in automated runs.

-----

## ⚠️ Optional Password Configuration (Use with Caution)

An optional **`passwords.yaml`** file can be placed in the same configuration directory to **skip manual password entry** during **bulk host registration**.

> **🛑 WARNING: SECURITY RISK**
>
>   * The use of `passwords.yaml` is **strongly discouraged** as it stores credentials in plaintext.
>   * If used, it is **highly recommended to delete the file immediately** after the bulk registration is complete.
>   * **Never** commit this file to any source code repository.

-----

## 🛠️ Typical Workflow

The program can be run in two modes: **Interactive** (default) or **Non-Interactive** (for scripting/automation).

### 🖥️ Interactive Mode (Default)

1.  **Verify Connectivity:** Ensure basic SSH connectivity is working for all target hosts.
2.  **Run Program:**
    ```bash
    goodass
    ```
3.  **Main Operations:** Use the interactive program (or wizard) to:
      * Add **hosts**, **users**, and associated **keys**.
      * Launch the **"fix keys" utility**, which synchronizes your configured keys to the `authorized_keys` file on all added hosts.

### 🤖 Non-Interactive Mode (For Automation)

You can now automatically run the key synchronization utility without any user prompts using the `--fix-keys` argument. This is ideal for cron jobs or automated deployments.

  * **Command:** Execute the key fix operation directly:
    ```bash
    goodass --fix-keys
    ```
    This command will read the existing configuration and immediately synchronize the configured keys across all registered hosts.

-----

## 🔑 Key Management Notes

  * **Private Keys:** **Do not** commit private keys to the source code repository. Store them in a secure location.
  * **Permissions:** Restrict access to private keys using strict file permissions (e.g., `chmod 600 /path/to/private/key`).
  * **Public Keys:** Public keys can be safely included in the **`config.yaml`** for distribution.

-----

## 🛡️ Security Best Practices

  * **Sensitive Data:** **Never** include passwords or private keys directly in **`config.yaml`** or commit them to source control.
  * **Agent Usage:** Utilize an **SSH agent** or rely on the local file paths with restrictive permissions defined in **`settings.yaml`** to prevent accidental exposure.
  * **Pre-Distribution Checks:** Before mass-distributing keys, verify the remote user permissions and the existing SSH policies (`sshd_config`) on the destination servers.

-----

## 🧑‍💻 Development & Testing

  * **Execution:** To run the program during development, launch the entry point script directly:
    ```bash
    python src/goodass/cli.py
    ```
  * **Local Testing:** Test the program locally using a configuration that targets dedicated **test VMs** or **containers** to avoid impacting production systems.

-----

## 🤝 Contributing

  * **Bug Reporting:** Report bugs by opening an issue on **GitHub** and providing clear steps to reproduce the problem.
  * **Improvements:** Submit improvements via **pull requests**. Ensure changes are focused, clearly described, and include tests for new functionality where possible.

-----

## 🗺️ Roadmap / TODO

> Completion of the remaining items in this list will trigger the **Version 1.0.0** release.

  * Implement a **comprehensive logging system** to capture more than just errors, including operational details, warnings, and success messages.
  * **Limit multi-threaded jobs against one host** to prevent unintentionally overwhelming the target server (e.g., avoiding a self-inflicted Distributed Denial of Service, or DDoS).
  * Add functionality to synchronize **`config.yaml`** with a remote server via **SFTP**, enabling configuration collaboration among multiple users.

> **Future Goal: Version 2.0 Consideration**
> The introduction of a small **Text User Interface (TUI)** is being considered, but will be reserved as a major development goal for **Version 2.0**.

-----

## ⚖️ License

This project is released under the license included in the repository. See the **`LICENSE`** file for details.

-----

## 📧 Contact

  * **Author:** `Nidhil-stack`
  * **Contributors:**
    \<a href="[https://github.com/EddyDevProject](https://github.com/EddyDevProject)"\>\<img src="[https://github.com/EddyDevProject.png](https://github.com/EddyDevProject.png)" width="60px"/\>\<br /\>\</a\>

-----
