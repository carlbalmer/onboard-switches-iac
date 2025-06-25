# Network Switch Discovery Tool

A comprehensive Python tool for discovering and mapping network switches across different vendors (Hirschmann, Lantech, Kontron, Nomad).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Discovery Tool                    │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 StartDiscovery.py (Entry Point)             │
│  • Parses command line arguments                            │
│  • Initializes NetworkDiscoveryManager                      │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              NetworkDiscoveryManager                        │
│  • Orchestrates entire discovery process                   │
│  • Manages topology building                               │
│  • Handles recursive discovery                             │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  SwitchDetector                             │
│  • Auto-detects switch vendor/type                         │
│  • Tries different credentials                             │
│  • Validates vendor using command responses                │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│            Vendor-Specific Discovery Classes                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────│
│  │ Hirschmann  │ │   Lantech   │ │   Kontron   │ │  Nomad  │
│  │ Discovery   │ │  Discovery  │ │  Discovery  │ │Discovery│
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────│
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                     SSH Client                              │
│  • Handles SSH connections                                  │
│  • Executes commands                                        │
│  • Manages interactive shell sessions                      │
└─────────────────────────────────────────────────────────────┘
```

## Discovery Process Flow

1. **Auto-Detection Phase**:
   - Try different vendor credentials (Hirschmann, Lantech, Kontron, Nomad)
   - For each successful login, run vendor-specific identification commands
   - Confirm vendor by checking command output patterns

2. **Information Gathering Phase**:
   - Get system information (hostname, model, version, etc.)
   - Retrieve interface status
   - Collect LLDP neighbor information
   - Gather MAC address table

3. **Topology Building Phase**:
   - Extract neighbor IP addresses from LLDP data
   - Create topology nodes and edges
   - Recursively discover connected switches

4. **Output Generation Phase**:
   - Generate network topology JSON
   - Create Ansible inventory file

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test Hirschmann Switch Discovery
```bash
python test_hirschmann.py 192.168.1.31
```

### 3. Discover Entire Network
```bash
python StartDiscovery.py 192.168.1.31
```

### 4. Advanced Usage
```bash
# Use custom credentials file
python StartDiscovery.py 192.168.1.31 --credentials my_creds.yaml

# Specify output directory
python StartDiscovery.py 192.168.1.31 --output-dir /tmp/discovery
```

## Vendor-Specific Commands

### Hirschmann Switches
- **System Info**: `show system info`
- **Interfaces**: `show interface status`
- **LLDP Neighbors**: `show lldp remote`
- **MAC Table**: `show forwarding-table`

### Lantech Switches
- **System Info**: `System configuration`
- **Interfaces**: `Port configuration`
- **LLDP Neighbors**: `show lldp remote`
- **MAC Table**: `show mac-address-table`

### Kontron Switches
- **System Info**: `show version`
- **Interfaces**: `show interface status`
- **LLDP Neighbors**: `show lldp neighbors`
- **MAC Table**: `show mac-address-table`

### Nomad Switches
- **System Info**: `show version`
- **Interfaces**: `show interface`
- **LLDP Neighbors**: `show lldp neighbors`
- **MAC Table**: `show mac-address-table`

## Configuration

### Credentials File (credentials.yaml)
```yaml
credentials:
  hirschmann:
    default_username: "admin"
    default_password: "admin"
    alternative_credentials:
      - username: "admin"
        password: "admin"
      - username: "manager"
        password: "manager"
  
  lantech:
    default_username: "admin"
    default_password: "admin"
    # ... more credentials

ssh_settings:
  port: 22
  timeout: 30
  retry_attempts: 3
  retry_delay: 2
```

## Output Files

### 1. Network Topology (JSON)
```json
{
  "discovery_started": "2025-06-24T10:00:00",
  "discovery_completed": "2025-06-24T10:05:00",
  "nodes": {
    "192.168.1.31": {
      "host": "192.168.1.31",
      "switch_data": {
        "system_info": {
          "hostname": "ITonICE-LAB-4083-1",
          "vendor": "hirschmann",
          "model": "BOBCAT",
          "os_version": "HiOS-2A-10.3.00"
        }
      }
    }
  },
  "edges": [...]
}
```

### 2. Ansible Inventory (YAML)
```yaml
all:
  children:
    switches:
      hosts:
        192.168.1.31:
          ansible_host: 192.168.1.31
          vendor: hirschmann
          model: BOBCAT
          hostname: ITonICE-LAB-4083-1
```

## Key Features

- **Multi-Vendor Support**: Supports Hirschmann, Lantech, Kontron, and Nomad switches
- **Auto-Detection**: Automatically detects switch type using credential and command testing
- **Recursive Discovery**: Discovers entire network topology through LLDP neighbors
- **Robust Error Handling**: Continues discovery even if some switches fail
- **Multiple Output Formats**: JSON topology and Ansible inventory
- **Comprehensive Logging**: Detailed output showing discovery progress

## Extending the Tool

To add support for a new vendor:

1. Create a new discovery class inheriting from `BaseDiscovery`
2. Implement vendor-specific command methods
3. Add vendor credentials to `credentials.yaml`
4. Update the `SwitchDetector` patterns and commands
5. Register the new class in `NetworkDiscoveryManager`

## Example Hirschmann Output

```
🔍 Discovering switch at 192.168.1.31
  Trying hirschmann credentials...
  ✓ Confirmed hirschmann - found 'hirschmann' in output
  ✓ Detected hirschmann switch at 192.168.1.31

📋 Switch Information for 192.168.1.31
==================================================
Hostname: ITonICE-LAB-4083-1
Vendor: hirschmann
Model: BOBCAT
OS Version: HiOS-2A-10.3.00 2025-04-30 12:09
Serial Number: 942334007000001001
Uptime: 0 days, 06:32:42
Location: Hirschmann BXP
Contact: Hirschmann Automation and Control GmbH
Management IP: 192.168.1.31
Management MAC: 74:0B:B0:16:AB:1A
```

## Troubleshooting

- **Connection Issues**: Check credentials in `credentials.yaml`
- **Command Failures**: Verify switch model supports the expected commands
- **Performance**: Use `--verbose` flag for detailed debugging information
