"""
Switch Detector - Auto-detects switch vendor/type by trying different credentials and commands.
"""
import yaml
import time
from typing import Dict, List, Optional, Tuple
from ssh_client import SSHClient
from data_model import SystemInfo


class SwitchDetector:
    """
    Detects switch vendor/type by attempting connections with different credentials
    and running vendor-specific identification commands.
    """
    
    def __init__(self, credentials_file: str = "credentials.yaml"):
        """
        Initialize the switch detector.
        
        Args:
            credentials_file: Path to credentials YAML file
        """
        self.credentials = self._load_credentials(credentials_file)
        self.ssh_settings = self.credentials.get('ssh_settings', {})
        
        # Vendor detection commands - ordered by priority
        self.detection_commands = {
            'hirschmann': [
                'show system info'
            ],
            'lantech': [
                'System configuration'
            ],
            'kontron': [
                'show version'
            ],
            'nomad': [
                'show version'
            ]
        }
        
        # Expected response patterns to confirm vendor
        self.vendor_patterns = {
            'hirschmann': ['hirschmann', 'hios', 'bobcat'],
            'lantech': ['lantech', 'tpes'],
            'kontron': ['kontron', 'kswitch', 'istax'],
            'nomad': ['nomad']
        }
    
    def _load_credentials(self, credentials_file: str) -> dict:
        """Load credentials from YAML file."""
        try:
            with open(credentials_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return {}
    
    def detect_switch_type(self, host: str) -> Tuple[Optional[str], Optional[SSHClient], Optional[dict]]:
        """
        Detect switch vendor/type by trying different credentials and commands.
        
        Args:
            host: IP address of the switch
            
        Returns:
            Tuple of (vendor_name, ssh_client, credentials_used)
            Returns (None, None, None) if detection fails
        """
        print(f"Starting auto-detection for switch at {host}")
        
        for vendor, vendor_creds in self.credentials.get('credentials', {}).items():
            print(f"  Trying {vendor} credentials...")
            
            # Try default credentials first
            ssh_client, creds_used = self._try_vendor_credentials(host, vendor, vendor_creds)
            
            if ssh_client:
                # Test if this is actually the right vendor
                if self._confirm_vendor(ssh_client, vendor):
                    print(f"  ✓ Detected {vendor} switch at {host}")
                    return vendor, ssh_client, creds_used
                else:
                    print(f"  ✗ Connected but not a {vendor} switch")
                    ssh_client.disconnect()
        
        print(f"  ✗ Failed to detect switch type for {host}")
        return None, None, None
    
    def _try_vendor_credentials(self, host: str, vendor: str, vendor_creds: dict) -> Tuple[Optional[SSHClient], Optional[dict]]:
        """
        Try to connect using vendor-specific credentials.
        
        Returns:
            Tuple of (ssh_client, credentials_used) or (None, None) if failed
        """
        # Try default credentials
        default_creds = {
            'username': vendor_creds.get('default_username'),
            'password': vendor_creds.get('default_password')
        }
        
        ssh_client = self._attempt_connection(host, default_creds)
        if ssh_client:
            return ssh_client, default_creds
        
        # Try alternative credentials
        for alt_creds in vendor_creds.get('alternative_credentials', []):
            ssh_client = self._attempt_connection(host, alt_creds)
            if ssh_client:
                return ssh_client, alt_creds
        
        return None, None
    
    def _attempt_connection(self, host: str, credentials: dict) -> Optional[SSHClient]:
        """
        Attempt SSH connection with given credentials.
        
        Returns:
            SSHClient if successful, None if failed
        """
        try:
            ssh_client = SSHClient(
                host=host,
                username=credentials['username'],
                password=credentials['password'],
                port=self.ssh_settings.get('port', 22),
                timeout=self.ssh_settings.get('timeout', 30)
            )
            
            if ssh_client.connect():
                return ssh_client
                
        except Exception as e:
            print(f"    Connection failed: {e}")
        
        return None
    
    def _confirm_vendor(self, ssh_client: SSHClient, vendor: str) -> bool:
        """
        Confirm the vendor by running vendor-specific commands and checking output.
        
        Args:
            ssh_client: Connected SSH client
            vendor: Vendor name to confirm
            
        Returns:
            True if vendor confirmed, False otherwise
        """
        commands = self.detection_commands.get(vendor, [])
        patterns = self.vendor_patterns.get(vendor, [])
        
        for command in commands:
            try:
                # Use the new pexpect-based SSH client
                output = ssh_client.send_command_to_shell(command, 5.0)
                
                if output:
                    # Check if output contains vendor-specific patterns
                    output_lower = output.lower()
                    for pattern in patterns:
                        if pattern.lower() in output_lower:
                            print(f"    ✓ Confirmed {vendor} - found '{pattern}' in output")
                            return True
                    
                    # Debug: Show what we got vs what we're looking for
                    print(f"    ✗ Output received but no patterns matched")
                    print(f"    Looking for: {patterns}")
                    print(f"    Output preview: {output[:200]}...")
                
            except Exception as e:
                print(f"    Command '{command}' failed: {e}")
                continue
        
        return False
    
    def get_vendor_commands(self, vendor: str) -> dict:
        """
        Get vendor-specific commands for information gathering.
        
        Args:
            vendor: Vendor name
            
        Returns:
            Dictionary of commands for this vendor
        """
        vendor_commands = {
            'hirschmann': {
                'system_info': 'show system info',
                'interfaces': 'show interface status',
                'lldp_neighbors': 'show lldp remote',
                'mac_table': 'show forwarding-table',
                'version': 'show version'
            },
            'lantech': {
                'system_info': 'System configuration',
                'interfaces': 'Port configuration',
                'lldp_neighbors': 'show lldp remote',
                'mac_table': 'show mac-address-table',
                'version': 'show version'
            },
            'kontron': {
                'system_info': 'show version',
                'interfaces': 'show interface status',
                'lldp_neighbors': 'show lldp neighbors',
                'mac_table': 'show mac-address-table',
                'version': 'show version'
            },
            'nomad': {
                'system_info': 'show version',
                'interfaces': 'show interface',
                'lldp_neighbors': 'show lldp neighbors',
                'mac_table': 'show mac-address-table',
                'version': 'show version'
            }
        }
        
        return vendor_commands.get(vendor, {})


if __name__ == "__main__":
    # Test the detector
    detector = SwitchDetector()
    
    # Test with a sample IP
    test_ip = "192.168.1.31"
    vendor, ssh_client, creds = detector.detect_switch_type(test_ip)
    
    if vendor:
        print(f"Successfully detected {vendor} switch at {test_ip}")
        print(f"Used credentials: {creds}")
        
        # Get vendor commands
        commands = detector.get_vendor_commands(vendor)
        print(f"Available commands: {list(commands.keys())}")
        
        ssh_client.disconnect()
    else:
        print(f"Failed to detect switch type for {test_ip}")
