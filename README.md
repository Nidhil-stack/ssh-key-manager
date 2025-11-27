## 🚧 WIP: Global Oversight of Deployed Authorized SSH Settings (Main Branch)

-----

### ⚠️ **WORK IN PROGRESS**

This branch is under active development. **No stable installation procedure exists.** Do not use this code in production.
### ❗**I'm close to a first readily usable release, if you want to try it go to the "wip_pip-packaging" branch"**

-----

### 🚀 **Goal**

To provide a CLI utility for standardized management and deployment of SSH `authorized_keys` across multiple hosts.

### ⚙️ **Intended Configuration**

| File | Purpose | Location Example (Linux) |
| :--- | :--- | :--- |
| **`settings.yaml`** | Local private key path (`ssh_private_key_path: ...`) | `~/.config/goodass/` |
| **`config.yaml`** | Hosts, Users, and Public Keys for distribution | `~/.config/goodass/` |

### 🛡️ **Security**

  * **No Committing:** **Never** include private keys or passwords in `config.yaml` or source control.
  * **Permissions:** Private keys must have strict file permissions (`chmod 600`).

### 🧑‍💻 **Development Run**

Test the current state:

```bash
python main.py
```

### 🗺️ **Roadmap / TODO**

  * Non-interactive mode.
  * Configuration TUI.
  * SFTP synchronization for `config.yaml`.
  * WIP pip packaging and standardization of files locations

-----

### 📧 **Contact**
- **Author:** `Nidhil-stack`
- **Contributors:**
  <a href="https://github.com/EddyDevProject"><img src="https://github.com/EddyDevProject.png" width="60px"/><br /></a>

---
