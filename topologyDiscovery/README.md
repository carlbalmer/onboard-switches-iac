# Network Switch Discovery Tool

This tool performs automated network discovery of switches using SSH connections and LLDP neighbor information.

## Features

- **Multi-vendor support**: Hirschmann, Lantech, Kontron, and Nomad switches
- **Automatic switch detection**: Identifies switch type by testing credentials and vendor-specific commands
- **Network topology discovery**: Uses LLDP to discover neighboring switches
- **Structured logging**: Configurable debug and info logging with timestamps
- **Output formats**: JSON topology and YAML inventory files

## Project Structure

```
switch_discovery/
├── discovery/                        # All discovery logic per vendor
│   ├── __init__.py
│   ├── HirschmannDiscovery.py
│   ├── LantechDiscovery.py
│   ├── KontronDiscovery.py
│   ├── NomadDiscovery.py
│   └── BaseDiscovery.py             # Abstract base class for all discovery types
│
├── StartDiscovery.py                # Entry point to launch from seed IP
├── switch_detector.py               # Auto-detects switch vendor/type
├── ssh_client.py                    # Shared SSH utility
├── ssh_command.py                   # Simple SSH command executor
├── logging_config.py                # Logging configuration
├── credentials.yaml                 # Default credentials per vendor
├── data_model.py                    # Normalized switch data structure
├── test_logging.py                  # Logging functionality test
├── README.md
└── output/
    └── inventory.yaml               # Output file with discovered switches
```

## Logging

The tool now uses structured logging instead of print statements:

- **DEBUG**: Detailed information for troubleshooting (connection attempts, command execution, etc.)
- **INFO**: General information about the discovery process (successful connections, summary statistics)
- **WARNING**: Non-critical issues (failed vendor detection, missing credentials)
- **ERROR**: Errors that don't stop the process (connection failures, command errors)
- **CRITICAL**: Serious errors that may stop the process

### Logging Configuration

Use the `--verbose` flag to enable DEBUG level logging:

```bash
python StartDiscovery.py --seed-ip 192.168.1.31 --verbose
```

Default logging level is INFO.

## Usage

```bash
python StartDiscovery.py --seed-ip <starting_ip> [--credentials credentials.yaml] [--output-dir output] [--verbose]
```

### Examples

```bash
# Basic discovery with default settings
python StartDiscovery.py --seed-ip 192.168.1.31

# Verbose logging for debugging
python StartDiscovery.py --seed-ip 192.168.1.31 --verbose

# Custom credentials and output directory
python StartDiscovery.py --seed-ip 192.168.1.31 --credentials my_creds.yaml --output-dir /tmp/results
```

## Testing

TBD