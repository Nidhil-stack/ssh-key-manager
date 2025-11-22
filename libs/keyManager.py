import os
import threading
import paramiko
import getpass
import prettytable
import yaml


colorRed = "\033[0;31;40m"
colorGreen = "\033[0;32;40m"
colorReset  = "\033[0m"

all_keys = []
passwords = {}

def upload_all_ssh_files(pwds, key_tables, console_lock = None, directory='./tempKeys'):
    threads = []
    servers, _ = fetch_config('config.yaml')
    if console_lock is None:
        console_lock = threading.Lock()
    for server in servers:
        host = server['host']
        for key_table in key_tables.items():
            host_user = key_table[0]
            keys = key_table[1]
            create_ssh_file(host_user, keys, directory=directory)
            thread = threading.Thread(target=lambda: upload_ssh_file(host_user.split('@')[1], host_user.split('@')[0], pwds, console_lock, directory))
            threads.append(thread)
            thread.start()
    for thread in threads:
        thread.join()

def upload_ssh_file(host, username, pwds, console_lock = None, directory='./tempKeys'):
    with open(os.path.join(directory, f'{username}@{host}.authorized_keys'), 'r') as key_file:
        print(f"Uploading keys to {username}@{host}")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(host, username=username, password=None, key_filename='./key.pem')
        except Exception as e:
            if 'Authentication failed' in str(e):
                #check that the console lock exists
                if console_lock:
                    console_lock.acquire()
                #allow password auth if key auth fails, 3 attempts
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
                        if console_lock:
                            console_lock.release()
                        break
                    except Exception as e:
                        if 'Authentication failed' in str(e):
                            attempts += 1
                            print("Authentication failed, please try again.")
                        else:
                            raise e
            else:
                raise e
        sftp = client.open_sftp()
        sftp.put(os.path.join(directory, f'{username}@{host}.authorized_keys'), f'/home/{username}/.ssh/authorized_keys')
        sftp.close()
        client.close()
            
            

def create_ssh_file(hostname, key_data, directory='./tempKeys'):
    if not os.path.exists(directory):
        os.makedirs(directory)
    key_path = os.path.join(directory, f'{hostname}.authorized_keys')
    with open(key_path, 'w') as key_file:
        for key in key_data:
            key_file.write(f"{key['type']} {key['key']} {key['hostname']}\n")
    return key_path

def get_ssh_keys(file_path, pwds = {}):
    del all_keys[:]
    threads = []
    console_lock = threading.Lock()
    servers, all_user_keys = fetch_config(file_path)
    for server in servers:
        host = server['host']
        for user in server['users']:
            print(f"Fetching keys from {user}@{host}")
            thread = threading.Thread(target=lambda: fetch_authorized_keys(host, user, console_lock, pwds))
            threads.append(thread)
            thread.start()
    for thread in threads:
        thread.join()
    return servers, all_user_keys, all_keys, passwords


def fetch_config(file_path):
    all_user_keys = []
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    servers = config['servers']
    users = config['users']
    
    for user in users:
        for key in user['keys']:
            if not key.get('admin', False):
                for server in key['access']:
                    all_user_keys.append({'hostname': server['host'], 'user': server['username'], 'type': key['type'], 'key': key['key'], 'key_user': key['hostname'],'email': user['email'],})
            else:
                for server in servers:
                    for server_user in server['users']:
                        all_user_keys.append({'hostname': server['host'], 'user': server_user, 'type': key['type'], 'key': key['key'], 'key_user': key['hostname'],'email': user['email'],})
    return servers, all_user_keys

def fetch_authorized_keys(host, username, console_lock, pwds):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=username, password=None, key_filename='./key.pem')
    except Exception as e:
        if 'Authentication failed' in str(e):
            #check that the console lock exists
            if console_lock:
                console_lock.acquire()
            #allow password auth if key auth fails, 3 attempts
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
                    if console_lock:
                        console_lock.release()
                    break
                except Exception as e:
                    if 'Authentication failed' in str(e):
                        attempts += 1
                        print("Authentication failed, please try again.")
                    else:
                        raise e
        else:
            raise e
    sftp = client.open_sftp()
    sftp.get(f'/home/{username}/.ssh/authorized_keys', f'./tempKeys/authorized_keys_{host}_{username}')
    keys = parse_authorized_keys(f'./tempKeys/authorized_keys_{host}_{username}')
    os.remove(f'./tempKeys/authorized_keys_{host}_{username}')
    sftp.close()
    client.close()
    for key in keys:#check if key already exists in all_keys
        if not any(existing_key['key'] == key['key'] and existing_key['host'] == host and existing_key['user'] == username for existing_key in all_keys):
            all_keys.append({'host': host, 'user': username, 'type': key['type'], 'key': key['key'], 'key_user': key['user']})

def parse_authorized_keys(file_path): #store the key and user info
    with open(file_path, 'r') as file:
        keys = []
        lines = file.readlines()
        for line in lines:
            if line.strip() == '' or line.startswith('#'):
                continue
            type = line.split(' ')[0]
            key = line.split(' ')[1]
            user = line.split(' ')[2].strip() if len(line.split(' ')) > 2 else 'unknown'
            keys.append({'type': type, 'key': key, 'user': user})
    return keys


def print_keys_table(keys):
    table = prettytable.PrettyTable()
    table.field_names = ["Host", "User", "Key Type", "Key (first 10 chars)", "HostName/User"]
    for key in all_keys:
        table.add_row([key['host'], key['user'], key['type'], key['key'][:10] + '...', key['key_user']])
    print(table)


def print_user_keys_table(keys):
    table = prettytable.PrettyTable()
    table.field_names = ["Host", "User", "Key Type", "Key (first 10 chars)", "HostName/User", "Email"]
    for key in keys:
        table.add_row([key['hostname'], key['user'], key['type'], key['key'][:10] + '...', key['key_user'], key['email']])
    print(table)


def print_checked_keys_table(checked_keys):
    table = prettytable.PrettyTable()
    table.field_names = ["User", "Host", "Key Type", "Key (first 10 chars)", "HostName/User", "Status"]
    for key in checked_keys:
        status_str = "MATCHED" if key['status'] == 0 else (colorGreen + "NOT FOUND" + colorReset if key['status'] == 1 else colorRed + "UNAUTHORIZED" + colorReset)
        table.add_row([key['user'], key['host'], key['type'], key['key'][:10] + '...', key['hostname'], status_str])
    print(table)


def check_keys(all_user_keys):

    checked_keys =  []

    for user_key in all_user_keys:
        matched = False
        for authorized_key in all_keys:
            if user_key['key'] == authorized_key['key'] and user_key['hostname'] == authorized_key['host'] and user_key['user'] == authorized_key['user']:
                checked_keys.append({'user': user_key['user'], 'host': authorized_key['host'], 'type': user_key['type'], 'key': user_key['key'], 'hostname': user_key['key_user'], 'status': 0})
                matched = True
        if not matched:
            checked_keys.append({'user': user_key['user'], 'host': user_key['hostname'], 'type': user_key['type'], 'key': user_key['key'], 'hostname': user_key['key_user'], 'status': 1})

    for key in all_keys:
        for user_key in all_user_keys:
            if key['key'] == user_key['key'] and key['host'] == user_key['hostname'] and key['user'] == user_key['user']:
                break
        else:
            checked_keys.append({'user': key['user'], 'host': key['host'], 'type': key['type'], 'key': key['key'], 'hostname': key['key_user'], 'status': -1})

    return checked_keys
