"""
Hirschmann Switch Discovery Implementation
Handles discovery and information gathering for Hirschmann switches.
"""
import re
import sys
import os
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .BaseDiscovery import BaseDiscovery
from ssh_client import SSHClient
from data_model import SwitchInfo, NeighborInfo


class HirschmannDiscovery(BaseDiscovery):
    """
    Discovery implementation for Hirschmann switches.
    """
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        """Initialize Hirschmann discovery."""
        super().__init__(host, username, password, port)
        self.ssh_client = None
        self.vendor = "hirschmann"
    
    def connect(self) -> bool:
        """
        Establish SSH connection to Hirschmann switch.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.ssh_client = SSHClient(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )
            
            if self.ssh_client.connect():
                # Start shell for interactive commands
                if self.ssh_client.start_shell():
                    # Clear initial prompt
                    self.ssh_client.send_command_to_shell("", 1.0)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Connection failed to {self.host}: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close SSH connection to the switch."""
        if self.ssh_client:
            self.ssh_client.disconnect()
            self.ssh_client = None
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information from Hirschmann switch.
        
        Returns:
            Dict containing parsed system information
        """
        try:
            # Try different variations of the system info command
            commands = ["show system info"]
            
            for command in commands:
                output = self.ssh_client.send_command_to_shell(command, 3.0)
                if output and ("System information" in output or "hirschmann" in output.lower()):
                    return self._parse_hirschmann_system_info(output)
            
            return {"error": "Could not retrieve system information"}
            
        except Exception as e:
            return {"error": f"Failed to get system info: {str(e)}"}
    
    def _parse_hirschmann_system_info(self, output: str) -> Dict[str, Any]:
        """
        Parse Hirschmann 'show system info' output.
        
        Args:
            output: Raw command output
            
        Returns:
            Dict containing parsed system information
        """
        system_info = {
            "vendor": "hirschmann",
            "hostname": None,
            "model": None,
            "os_version": None,
            "serial_number": None,
            "uptime": None,
            "location": None,
            "contact": None,
            "description": None,
            "management_ip": None,
            "management_mac": None
        }
        
        # Parse key-value pairs from the output
        patterns = {
            "description": r"System Description\.+(.+)",
            "hostname": r"System name\.+(.+)",
            "location": r"System location\.+(.+)",
            "contact": r"System contact\.+(.+)",
            "uptime": r"System uptime\.+(.+)",
            "os_version": r"Firmware software release \(RAM\)\.+(.+)",
            "serial_number": r"Serial number\.+(.+)",
            "management_ip": r"IP address \(management\)\.+(.+)",
            "management_mac": r"MAC address \(management\)\.+(.+)",
            "model": r"Device hardware description\.+(.+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                system_info[key] = match.group(1).strip()
        
        # Extract model from description if not found elsewhere
        if not system_info["model"] and system_info["description"]:
            if "BOBCAT" in system_info["description"]:
                system_info["model"] = "BOBCAT"
            elif "BXP" in system_info["description"]:
                system_info["model"] = "BXP"
        
        return system_info
    
    def _parse_hirschmann_version_info(self, output: str) -> Dict[str, Any]:
        """
        Parse Hirschmann version information as fallback.
        
        Args:
            output: Raw command output
            
        Returns:
            Dict containing parsed version information
        """
        system_info = {
            "vendor": "hirschmann",
            "hostname": None,
            "model": "Unknown Hirschmann",
            "os_version": None,
            "serial_number": None,
            "description": "Hirschmann Switch"
        }
        
        # Try to extract version information
        version_match = re.search(r"HiOS[^\s]*\s+([^\s]+)", output)
        if version_match:
            system_info["os_version"] = version_match.group(1)
        
        return system_info
    
    def get_interface_info(self) -> List[Dict[str, Any]]:
        """
        Simplified interface info - not needed for discovery.
        
        Returns:
            Empty list (interfaces not required for discovery)
        """
        return []
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        """
        Get LLDP neighbor information from Hirschmann switch.
        
        Returns:
            List of dictionaries containing neighbor information
        """
        try:
            output = self.ssh_client.send_command_to_shell("show lldp remote", 3.0)
            if output:
                return self._parse_hirschmann_lldp(output)
            return []
            
        except Exception as e:
            print(f"Failed to get neighbor info: {e}")
            return []
    
    def _parse_hirschmann_lldp(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse Hirschmann LLDP neighbor output.
        
        Args:
            output: Raw LLDP output
            
        Returns:
            List of neighbor dictionaries
        """
        neighbors = []
        
        # Parse LLDP output - this would need adjustment based on actual format
        lines = output.split('\n')
        current_neighbor = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for LLDP neighbor entries
            if "Local Interface" in line or "Port ID" in line:
                if current_neighbor:
                    neighbors.append(current_neighbor)
                    current_neighbor = {}
                    
            # Parse individual fields
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                current_neighbor[key] = value
        
        if current_neighbor:
            neighbors.append(current_neighbor)
        
        return neighbors
    
    def get_mac_table(self) -> List[Dict[str, Any]]:
        """
        Simplified MAC table - not needed for discovery.
        
        Returns:
            Empty list (MAC table not required for discovery)
        """
        return []
    
    def get_switch_info(self) -> SwitchInfo:
        """
        Get simplified switch information for network discovery.
        
        Returns:
            SwitchInfo object with essential fields only
        """
        try:
            # First, establish connection
            print(f"Attempting to connect to {self.host} with username: {self.username}")
            if not self.connect():
                print(f"Failed to connect to {self.host}")
                return SwitchInfo(
                    ip=self.host,
                    mac=None,
                    type='hirschmann',
                    neighbors=[]
                )
            
            print(f"Successfully connected to {self.host}")
            
            # Get system info to extract IP, MAC, and switch type
            system_info = self.get_system_info()
            print(f"System info retrieved: {list(system_info.keys()) if system_info else 'None'}")
            
            # Extract essential information
            ip = self.host
            mac = system_info.get('management_mac')
            switch_type = system_info.get('vendor', 'hirschmann')
            
            # Get neighbor information
            print("Getting neighbor information...")
            neighbors = self.get_simplified_neighbors()
            print(f"Found {len(neighbors)} neighbors")
            
            # Disconnect after gathering information
            self.disconnect()
            print(f"Disconnected from {self.host}")
            
            return SwitchInfo(
                ip=ip,
                mac=mac,
                type=switch_type,
                neighbors=neighbors
            )
            
        except Exception as e:
            print(f"Failed to get switch info: {e}")
            # Make sure to disconnect on error
            try:
                self.disconnect()
            except:
                pass
            return SwitchInfo(
                ip=self.host,
                mac=None,
                type='hirschmann',
                neighbors=[]
            )
    
    def get_simplified_neighbors(self) -> List[NeighborInfo]:
        """
        Get simplified neighbor information from LLDP.
        
        Returns:
            List of NeighborInfo objects
        """
        try:
            output = self.ssh_client.send_command_to_shell("show lldp remote-data", 3.0)
            if output:
                return self._parse_simple_lldp(output)
            return []
            
        except Exception as e:
            print(f"Failed to get neighbor info: {e}")
            return []
    
    def _parse_simple_lldp(self, output: str) -> List[NeighborInfo]:
        """
        Parse LLDP output and extract only essential neighbor information.
        
        Args:
            output: Raw LLDP output
            
        Returns:
            List of NeighborInfo objects
        """
        neighbors = []
        
        # Parse Hirschmann LLDP remote-data output format
        lines = output.split('\n')
        current_neighbor = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for IPv4 Management address
            if 'IPv4 Management address' in line:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_neighbor['ip'] = ip_match.group(1)
            
            # Look for Chassis ID (MAC address)
            elif 'Chassis ID' in line:
                mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
                if mac_match:
                    current_neighbor['mac'] = mac_match.group(0)
            
            # Look for System description to determine neighbor type
            elif 'System description' in line:
                line_lower = line.lower()
                if 'hirschmann' in line_lower:
                    current_neighbor['type'] = 'hirschmann'
                elif 'lantech' in line_lower:
                    current_neighbor['type'] = 'lantech'
                elif 'kontron' in line_lower:
                    current_neighbor['type'] = 'kontron'
                elif 'nomad' in line_lower:
                    current_neighbor['type'] = 'nomad'
                else:
                    # Try to guess type from system description
                    current_neighbor['type'] = 'unknown'
            
            # Check if we have a complete neighbor entry and start a new one
            elif line.startswith('Remote data,') and current_neighbor:
                if 'ip' in current_neighbor:
                    neighbor = NeighborInfo(
                        ip=current_neighbor.get('ip'),
                        mac=current_neighbor.get('mac'),
                        type=current_neighbor.get('type', 'unknown')
                    )
                    neighbors.append(neighbor)
                current_neighbor = {}
        
        # Add the last neighbor if we have one
        if current_neighbor and 'ip' in current_neighbor:
            neighbor = NeighborInfo(
                ip=current_neighbor.get('ip'),
                mac=current_neighbor.get('mac'),
                type=current_neighbor.get('type', 'unknown')
            )
            neighbors.append(neighbor)
        
        return neighbors

