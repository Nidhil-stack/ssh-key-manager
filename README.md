# ssh-key-manager

A lightweight utility to distribute and manage SSH keys across multiple servers in a secure and repeatable way.

Purpose: automate adding public keys to remote users and manage SSH permissions from a single CLI tool.

Status: initial release / CLI utility.

Table of Contents

- Description
- Features
- Requirements
- Installation
- Configuration
- Usage
- Security Notes
- Development & Testing
- Contributing
- License

Description

`ssh-key-manager` is a Python script that simplifies distributing SSH public keys to multiple hosts. It reads a YAML configuration (based on `config.yaml.example`) and applies the keys and permissions defined for remote users.

Main features

- Add public keys to remote users' `authorized_keys`
- Support using a local private key for authentication
- Interactive (wizard) mode for step-by-step operations
- Central configuration via `config.yaml`

Requirements

- Python 3.8+ (Python 3.10+ recommended)
- Dependencies listed in `requirements.txt`
- Valid SSH access to target hosts (via password or private key)

Installation

1. Clone the repository or copy the files to your machine:

```
git clone https://github.com/Nidhil-stack/ssh-key-manager.git
cd ssh-key-manager
```

2. Create a virtual environment and install dependencies:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Verify `main.py` and `libs/keyManager.py` are present.

Configuration

- Copy the example configuration and edit it:

```
cp config.yaml.example config.yaml
```

- Open `config.yaml` and define the following (see `config.yaml.example` for full format):

- `hosts`: list of hosts/addresses to operate on
- `users`: remote users to which keys should be added
- `keys`: public keys (or local file paths) to distribute

Minimal example (illustrative only):

```
hosts:
	- host: server1.example.com
		port: 22
		user: root
users:
	- name: deploy
		public_key: |
			ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy...
```

If you prefer to use a private key to connect, place the private key file (for example, `id_rsa`) in the same folder as `main.py` or specify its path in the configuration.

Usage

- Run the script in interactive (wizard) mode:

```
python main.py
```

- For non-interactive or automated runs, ensure `config.yaml` is valid and SSH access is available without password prompts (e.g., via ssh-agent or pre-authorized keys).

Typical workflow

- Prepare `config.yaml` with hosts and keys
- Verify SSH connectivity to each host
- Run `python main.py` and follow the wizard

Key management notes

- Do not commit private keys to the repository.
- Store private keys in a secure location and restrict permissions (`chmod 600`).
- Public keys can be included in the configuration for distribution.

Security

- Never include passwords or private keys in `config.yaml` or commit them to source control.
- Use an SSH agent or local file paths with restrictive permissions to prevent accidental exposure.
- Verify remote user permissions and the SSH policies on destination servers before mass-distribution.

Development & testing

- Test locally using a config that targets test VMs or containers.
- Add debug prints to `libs/keyManager.py` or run the script with a verbosity flag if provided.

Contributing

- Report bugs by opening an issue on GitHub with reproduction steps.
- Submit improvements via pull requests with focused changes and a clear description.
- Keep changes minimal and include tests for new functionality where possible.

Roadmap / TODO

- Allow specifying the path to the private key externally
- Add detached/daemon mode for automation
- Add a small TUI for quick configuration (?)
- Add generation/editing of `config.yaml` from within the tool

License

This project is released under the license included in the repository (see `LICENSE`).

Contact

- **Author:** `Nidhil-stack`
- **Contributors:**

  <a href="https://github.com/EddyDevProject"><img src="https://github.com/EddyDevProject.png" width="60px"/><br /></a>

---
