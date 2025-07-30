# Advanced Botnet Implementation

**Warning: This is malware for educational purposes only. Do not use illegally.**

## Description
This repository contains a proof-of-concept botnet with advanced features for educational and research purposes in cybersecurity.

## Features

### Client Malware
- Persistence mechanisms
- Privilege escalation
- Anti-analysis techniques
- Encrypted C2 communication
- Extensive surveillance capabilities
- Credential theft
- Network attack tools
- Self-propagation

### C2 Server
- Multi-client management
- Interactive shell for each bot
- Broadcast commands
- Encrypted communication

## Setup Instructions

1. **Server Setup**
   - Run `server.py` on your C2 server
   - Listens on 0.0.0.0:4444 by default

2. **Client Setup**
   - Modify the hardcoded IP in `client.py` to your C2 server
   - Run `client.py` on target machines

## Command Reference

### Server Commands
- `targets` - List connected bots
- `session [n]` - Connect to session n
- `sendall [cmd]` - Send command to all bots
- `quit` - Shutdown server
- `help` - Show help

### Bot Commands
- **System**
  - `check_priv` - Check privileges
  - `reboot` - Reboot system
  - `turn_off` - Shutdown system
  
- **Surveillance**
  - `start_keylogger`/`stop_keylogger`
  - `steal_clipboard`
  - `steal_info`
  - `network_info`
  
- **Credential Theft**
  - `steal_creds` - Extract browser passwords
  
- **File Operations**
  - `download [file]`
  - `upload [file]`
  - `encrypt_dir [dir]`
  - `decrypt_dir [dir]`
  
- **Network Attacks**
  - `syn_flood [ip] [port]`
  - `stop_syn_flood`
  - `port_scan [ip] [start] [end]`
  - `scan_network [range]`
  - `spread [range]`

## Security Warning
This malware is for educational purposes only. Unauthorized use against systems you don't own is illegal. The authors assume no liability for misuse.

## Legal Disclaimer
This software is provided "as is" without warranty of any kind. Use at your own risk. The developers are not responsible for any damages caused by this software.
