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
from data_model import SystemInfo, SwitchInterface, LLDPNeighbor, MacTableEntry


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
                if output and ("mac" in output.lower() or "hirschmann" in output.lower()):
                    return self._parse_hirschmann_version_info(output)
            
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
        Get interface information from Hirschmann switch.
        
        Returns:
            List of dictionaries containing interface information
        """
        try:
            output = self.ssh_client.send_command_to_shell("show interface status", 3.0)
            if output:
                return self._parse_hirschmann_interfaces(output)
            return []
            
        except Exception as e:
            print(f"Failed to get interface info: {e}")
            return []
    
    def _parse_hirschmann_interfaces(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse Hirschmann interface status output.
        
        Args:
            output: Raw interface status output
            
        Returns:
            List of interface dictionaries
        """
        interfaces = []
        
        # This is a simplified parser - would need to be adjusted based on actual output format
        lines = output.split('\n')
        for line in lines:
            if re.match(r'^\s*(eth|port|interface)', line.lower()):
                parts = line.split()
                if len(parts) >= 3:
                    interface = {
                        "name": parts[0],
                        "admin_status": parts[1] if len(parts) > 1 else "unknown",
                        "oper_status": parts[2] if len(parts) > 2 else "unknown",
                        "speed": None,
                        "duplex": None
                    }
                    interfaces.append(interface)
        
        return interfaces
    
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
        Get MAC address table from Hirschmann switch.
        
        Returns:
            List of dictionaries containing MAC table entries
        """
        try:
            output = self.ssh_client.send_command_to_shell("show forwarding-table", 3.0)
            if output:
                return self._parse_hirschmann_mac_table(output)
            return []
            
        except Exception as e:
            print(f"Failed to get MAC table: {e}")
            return []
    
    def _parse_hirschmann_mac_table(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse Hirschmann MAC address table output.
        
        Args:
            output: Raw MAC table output
            
        Returns:
            List of MAC table entry dictionaries
        """
        mac_entries = []
        
        # Parse MAC table - format would need adjustment based on actual output
        lines = output.split('\n')
        for line in lines:
            # Look for MAC address patterns
            mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
            if mac_match:
                parts = line.split()
                if len(parts) >= 3:
                    entry = {
                        "mac_address": mac_match.group(0),
                        "vlan_id": 1,  # Default VLAN
                        "interface": parts[-1] if parts else "unknown",
                        "entry_type": "dynamic"
                    }
                    mac_entries.append(entry)
        
        return mac_entries

