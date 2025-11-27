import os
import threading
import paramiko
import getpass
import prettytable
import yaml


colorRed = "\033[0;31;40m"
colorGreen = "\033[0;32;40m"
colorReset = "\033[0m"

all_keys = []
passwords = {}


def print_keys_table_cli(pwds):
    """Fetch and display all SSH keys from configured hosts.

    This function retrieves SSH key data from the configuration using
    `get_ssh_keys`, updates the local password cache, clears
    the console, prints a table of all discovered keys and waits for
    the user to press Enter before returning.
    """

    servers, all_user_keys, all_keys, passwords = get_ssh_keys("config.yaml", pwds)
    pwds.update(passwords)
    os.system("cls" if os.name == "nt" else "clear")
    print_keys_table(all_keys)
    input("Press Enter to continue...")


def fix_keys_cli(pwds, directory="./tempKeys"):
    """Run a check-and-fix workflow for SSH keys.

    Steps performed:
    - Fetch current key state from `config.yaml`.
    - Run `check_keys` to detect inconsistencies.
    - Display a table of checked keys and, if issues are found,
      allow the user to confirm applying fixes.
    - On confirmation, upload corrected `authorized_keys` files to the
      remote servers using `upload_all_ssh_files`.

    This function updates the shared `pwds` cache with any passwords
    returned from `get_ssh_keys`.
    """

    servers, all_user_keys, all_keys, passwords = get_ssh_keys("config.yaml", pwds)
    pwds.update(passwords)
    checked_keys = check_keys(all_user_keys)
    # if all keys are status 0, then no issues
    os.system("cls" if os.name == "nt" else "clear")
    print_checked_keys_table(checked_keys)
    if all(key["status"] == 0 for key in checked_keys):
        print("All servers are up to date, no issues found.")
        input("Press Enter to continue...")
        return
    print(
        "Issues found with the above keys. Please check them then press Enter to continue."
    )
    fixed_keys = list(filter(lambda k: k["status"] >= 0, checked_keys))
    input("Press Enter to continue...")
    os.system("cls" if os.name == "nt" else "clear")
    print("Fixed Keys:")
    print_checked_keys_table(list(fixed_keys))
    key_tables = {}
    for server in servers:
        for user in server["users"]:
            host = server["host"]
            key_table = list(
                filter(
                    lambda k: k["host"] == host
                    and k["user"] == user
                    and k["status"] >= 0,
                    list(fixed_keys),
                )
            )
            key_tables[f"{user}@{host}"] = key_table
            print(f"Keys table for {user}@{host}...")
            print_checked_keys_table(key_table)
    confirmation = input("Result after fix, continue? [y/N]")
    if confirmation.lower() == "y":
        print("Fixing keys...")
        upload_all_ssh_files(pwds, directory=directory, key_tables=key_tables)
        input("All done! Press Enter to continue...")


def upload_all_ssh_files(pwds, key_tables, console_lock=None, directory="./tempKeys"):
    """Upload multiple `authorized_keys` files to their respective servers concurrently.

    Parameters:
    - pwds (dict): dictionary to store or reuse passwords for user@host pairs.
    - key_tables (dict): mapping of "user@host" -> list of key entries to write and upload.
    - console_lock (threading.Lock|None): optional lock used to synchronize console I/O when
      prompting for passwords across threads.
    - directory (str): local directory where temporary `authorized_keys` files are created.

    The function creates a temporary `authorized_keys` file for each entry in `key_tables`,
    spawns a thread to upload it (using `upload_ssh_file`) and waits for all uploads to finish.
    """
    threads = []
    servers, _ = fetch_config("config.yaml")
    if console_lock is None:
        console_lock = threading.Lock()
    for server in servers:
        host = server["host"]
        for key_table in key_tables.items():
            host_user = key_table[0]
            keys = key_table[1]
            create_ssh_file(host_user, keys, directory=directory)
            thread = threading.Thread(
                target=lambda: upload_ssh_file(
                    host_user.split("@")[1],
                    host_user.split("@")[0],
                    pwds,
                    console_lock,
                    directory,
                )
            )
            threads.append(thread)
            thread.start()
    for thread in threads:
        thread.join()


def upload_ssh_file(host, username, pwds, console_lock=None, directory="./tempKeys"):
    """Upload a single `authorized_keys` file to a remote user's `.ssh/authorized_keys`.

    Attempts key-based authentication first using a local key file (`./key.pem`). If that
    fails with an authentication error, prompts (with up to 3 attempts) for a password
    (reusing any value present in `pwds`). On success, uploads the local temporary
    `{username}@{host}.authorized_keys` file to `/home/{username}/.ssh/authorized_keys`.

    Parameters:
    - host (str): remote host hostname or IP.
    - username (str): remote username.
    - pwds (dict): shared dictionary of saved passwords keyed by `user@host`.
    - console_lock (threading.Lock|None): optional lock to synchronize password prompts.
    - directory (str): directory holding the temporary `authorized_keys` file.

    Raises exceptions from `paramiko` for non-authentication related failures.
    """
    with open(
        os.path.join(directory, f"{username}@{host}.authorized_keys"), "r"
    ) as key_file:
        print(f"Uploading keys to {username}@{host}")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                host, username=username, password=None, key_filename="./key.pem"
            )
        except Exception as e:
            if "Authentication failed" in str(e):
                if console_lock:
                    console_lock.acquire()
                attempts = 0
                while attempts < 3:
                    try:
                        pwd = pwds.get(f"{username}@{host}")
                        if pwd:
                            password = pwd
                        else:
                            password = getpass.getpass(
                                f"Password for {username}@{host}: "
                            )
                        passwords[f"{username}@{host}"] = password
                        client.connect(host, username=username, password=password)
                        break
                    except Exception as e:
                        if "Authentication failed" in str(e):
                            attempts += 1
                            print("Authentication failed, please try again.")
                        else:
                            raise e
            else:
                raise e
        if console_lock and console_lock.locked():
            console_lock.release()
        sftp = client.open_sftp()
        try:
            if username == "root":
                sftp.put(
                    os.path.join(directory, f"root@{host}.authorized_keys"),
                    "/root/.ssh/authorized_keys",
                )
            else:
                sftp.put(
                    os.path.join(directory, f"{username}@{host}.authorized_keys"),
                    f"/home/{username}/.ssh/authorized_keys",
                )
            sftp.close()
            client.close()
        except Exception as e:
            if console_lock:
                console_lock.acquire()
            if "No such file" in str(e):
                print(
                    f"Remote .ssh directory does not exist for {username}@{host}. Upload failed."
                )
                if console_lock:
                    console_lock.release()
                sftp.close()
                client.close()


def create_ssh_file(hostname, key_data, directory="./tempKeys"):
    """Create a temporary `authorized_keys` file locally for a given host/user.

    Parameters:
    - hostname (str): used to name the temporary file `{hostname}.authorized_keys`.
    - key_data (list): list of key dictionaries with fields `type`, `key`, `hostname`.
    - directory (str): where to write the file. Directory will be created if missing.

    Returns the path to the created file.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    key_path = os.path.join(directory, f"{hostname}.authorized_keys")
    with open(key_path, "w") as key_file:
        for key in key_data:
            key_file.write(f"{key['type']} {key['key']} {key['hostname']}\n")
    return key_path


def get_ssh_keys(file_path, pwds={}):
    """Retrieve SSH keys from all configured servers in the provided config file.

    Parameters:
    - file_path (str): path to YAML configuration file.
    - pwds (dict): optional dictionary used to store/reuse passwords for `user@host`.

    Returns a tuple: (servers, all_user_keys, all_keys, passwords)
    - servers: list of server entries from the config
    - all_user_keys: list of expected keys derived from users and servers in config
    - all_keys: discovered keys found on the servers (populated by this call)
    - passwords: dictionary of passwords entered during the fetch process

    The function spawns one thread per `user@host` and collects keys concurrently.
    """
    del all_keys[:]
    threads = []
    console_lock = threading.Lock()
    servers, all_user_keys = fetch_config(file_path)
    for server in servers:
        host = server["host"]
        for user in server["users"]:
            print(f"Fetching keys from {user}@{host}")
            thread = threading.Thread(
                target=lambda: fetch_authorized_keys(host, user, console_lock, pwds)
            )
            threads.append(thread)
            thread.start()
    for thread in threads:
        thread.join()
    return servers, all_user_keys, all_keys, passwords


def fetch_config(file_path):
    """Parse the YAML configuration and return servers and expanded user key expectations.

    Parameters:
    - file_path (str): path to YAML configuration file.

    Returns:
    - servers (list): list of server definitions from the config.
    - all_user_keys (list): flattened list of key expectations; each entry contains
      `hostname`, `user`, `type`, `key`, `key_user`, and `email`.
    """
    all_user_keys = []
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    servers = config.get("hosts") or config.get("servers")
    users = config["users"]

    for user in users:
        if user.get("keys") is None or len(user["keys"]) == 0:
            continue
        for key in user["keys"]:
            if not key.get("admin", False):
                if key.get("access") is None or len(key["access"]) == 0:
                    continue
                for server in key["access"]:
                    all_user_keys.append(
                        {
                            "hostname": server["host"],
                            "user": server["username"],
                            "type": key["type"],
                            "key": key["key"],
                            "key_user": key["hostname"],
                            "email": user["email"],
                        }
                    )
            else:
                for server in servers:
                    for server_user in server["users"]:
                        all_user_keys.append(
                            {
                                "hostname": server["host"],
                                "user": server_user,
                                "type": key["type"],
                                "key": key["key"],
                                "key_user": key["hostname"],
                                "email": user["email"],
                            }
                        )
    return servers, all_user_keys


def fetch_authorized_keys(host, username, console_lock, pwds):
    """Connect to a remote host and fetch the `authorized_keys` for a user.

    Parameters:
    - host (str): remote host.
    - username (str): remote username whose `authorized_keys` will be retrieved.
    - console_lock (threading.Lock): lock used to synchronize interactive password prompts.
    - pwds (dict): dictionary to store/use passwords for `user@host`.

    The function downloads the remote `authorized_keys` to a temporary local file,
    parses it with `parse_authorized_keys`, removes the temporary file and updates
    the module-level `all_keys` list with discovered keys.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=username, password=None, key_filename="./key.pem")
    except Exception as e:
        if "Authentication failed" in str(e):
            if console_lock:
                console_lock.acquire()
            print("Using password authentication for", f"{username}@{host}")
            attempts = 0
            while attempts < 3:
                try:
                    pwd = pwds.get(f"{username}@{host}")
                    if pwd:
                        password = pwd
                    else:
                        password = getpass.getpass(f"Password for {username}@{host}: ")
                    passwords[f"{username}@{host}"] = password
                    client.connect(host, username=username, password=password)
                    break
                except Exception as e:
                    if "Authentication failed" in str(e):
                        attempts += 1
                        print("Authentication failed, please try again.")
                    else:
                        print(e)
                        break
        else:
            raise e
    if console_lock and console_lock.locked():
        console_lock.release()
    sftp = client.open_sftp()
    try:
        if username == "root":
            sftp.get(
                "/root/.ssh/authorized_keys",
                f"./tempKeys/authorized_keys_{host}_{username}",
            )
        else:
            sftp.get(
                f"/home/{username}/.ssh/authorized_keys",
                f"./tempKeys/authorized_keys_{host}_{username}",
            )
        keys = parse_authorized_keys(f"./tempKeys/authorized_keys_{host}_{username}")
    except Exception as e:
        if "No such file" in str(e):
            if console_lock:
                console_lock.acquire()
            print(f"No authorized_keys file for {username}@{host}, skipping.")
            keys = []
            open(f"./tempKeys/authorized_keys_{host}_{username}", "w").close()
            if console_lock:
                console_lock.release()
        else:
            raise e

    os.remove(f"./tempKeys/authorized_keys_{host}_{username}")
    sftp.close()
    client.close()
    if not keys:
        return
    for key in keys:  # check if key already exists in all_keys
        if not any(
            existing_key["key"] == key["key"]
            and existing_key["host"] == host
            and existing_key["user"] == username
            for existing_key in all_keys
        ):
            all_keys.append(
                {
                    "host": host,
                    "user": username,
                    "type": key["type"],
                    "key": key["key"],
                    "key_user": key["user"],
                }
            )


def parse_authorized_keys(file_path):
    """Parse an `authorized_keys` file and return a list of key dictionaries.

    Parameters:
    - file_path (str): path to a local `authorized_keys` file.

    Returns a list of dicts: `{'type': <key-type>, 'key': <key-data>, 'user': <comment/hostname>}`.
    Lines that are empty or start with `#` are ignored.
    """
    with open(file_path, "r") as file:
        keys = []
        lines = file.readlines()
        for line in lines:
            if line.strip() == "" or line.startswith("#"):
                continue
            type = line.split(" ")[0]
            key = line.split(" ")[1]
            user = line.split(" ")[2].strip() if len(line.split(" ")) > 2 else "unknown"
            keys.append({"type": type, "key": key, "user": user})
    return keys


def print_keys_table(keys):
    """Print a summary table of discovered keys (`all_keys`).

    The `keys` parameter is unused: the function prints the module-level
    `all_keys` list in a pretty table for human inspection.
    """
    table = prettytable.PrettyTable()
    table.field_names = [
        "Host",
        "User",
        "Key Type",
        "Key (first 10 chars)",
        "HostName/User",
    ]
    for key in all_keys:
        table.add_row(
            [
                key["host"],
                key["user"],
                key["type"],
                key["key"][:10] + "...",
                key["key_user"],
            ]
        )
    print(table)


def print_user_keys_table(keys):
    """Pretty-print a list of user key expectations derived from the config.

    Parameters:
    - keys (list): each entry should contain `hostname`, `user`, `type`, `key`, `key_user`, `email`.
    """
    table = prettytable.PrettyTable()
    table.field_names = [
        "Host",
        "User",
        "Key Type",
        "Key (first 10 chars)",
        "HostName/User",
        "Email",
    ]
    for key in keys:
        table.add_row(
            [
                key["hostname"],
                key["user"],
                key["type"],
                key["key"][:10] + "...",
                key["key_user"],
                key["email"],
            ]
        )
    print(table)


def print_checked_keys_table(checked_keys):
    """Print the results of `check_keys` in a readable table.

    Each entry in `checked_keys` is expected to have `user`, `host`, `type`, `key`, `hostname`, and `status`.
    Status values are mapped to human-readable strings and colored output.
    """
    table = prettytable.PrettyTable()
    table.field_names = [
        "User",
        "Host",
        "Key Type",
        "Key (first 10 chars)",
        "HostName/User",
        "Status",
    ]
    for key in checked_keys:
        status_str = (
            "MATCHED"
            if key["status"] == 0
            else (
                colorGreen + "NOT FOUND" + colorReset
                if key["status"] == 1
                else colorRed + "UNAUTHORIZED" + colorReset
            )
        )
        table.add_row(
            [
                key["user"],
                key["host"],
                key["type"],
                key["key"][:10] + "...",
                key["hostname"],
                status_str,
            ]
        )
    print(table)


def check_keys(all_user_keys):
    """Compare expected user keys from the config with discovered keys on servers.

    Parameters:
    - all_user_keys (list): expectations derived from `fetch_config`.

    Returns:
    - checked_keys (list): Each entry contains `user`, `host`, `type`, `key`, `hostname`, and `status`.
      Status codes: 0 = matched (key found and authorized), 1 = not found (expected but missing), -1 = unauthorized (found on server but not present in config).
    """

    checked_keys = []

    for user_key in all_user_keys:
        matched = False
        for authorized_key in all_keys:
            if (
                user_key["key"] == authorized_key["key"]
                and user_key["hostname"] == authorized_key["host"]
                and user_key["user"] == authorized_key["user"]
            ):
                checked_keys.append(
                    {
                        "user": user_key["user"],
                        "host": authorized_key["host"],
                        "type": user_key["type"],
                        "key": user_key["key"],
                        "hostname": user_key["key_user"],
                        "status": 0,
                    }
                )
                matched = True
        if not matched:
            checked_keys.append(
                {
                    "user": user_key["user"],
                    "host": user_key["hostname"],
                    "type": user_key["type"],
                    "key": user_key["key"],
                    "hostname": user_key["key_user"],
                    "status": 1,
                }
            )

    for key in all_keys:
        for user_key in all_user_keys:
            if (
                key["key"] == user_key["key"]
                and key["host"] == user_key["hostname"]
                and key["user"] == user_key["user"]
            ):
                break
        else:
            checked_keys.append(
                {
                    "user": key["user"],
                    "host": key["host"],
                    "type": key["type"],
                    "key": key["key"],
                    "hostname": key["key_user"],
                    "status": -1,
                }
            )

    return checked_keys
