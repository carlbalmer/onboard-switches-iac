"""
Kontron Switch Discovery Implementation
Focuses on essential data: vendor, IP, MAC, and neighbor info only.
"""
import re
import sys
import os
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .BaseDiscovery import BaseDiscovery
from ssh_client import SSHClient
from data_model import SwitchInfo, NeighborInfo


class KontronDiscovery(BaseDiscovery):
    """Discovery implementation for Kontron switches."""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        super().__init__(host, username, password, port)
        self.ssh_client = None
        self.vendor = "kontron"
    
    def connect(self) -> bool:
        """Establish SSH connection to Kontron switch."""
        try:
            self.ssh_client = SSHClient(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )
            
            if self.ssh_client.connect() and self.ssh_client.start_shell():
                self.ssh_client.send_command_to_shell("", 1.0)  # Clear initial prompt
                self.ssh_client.send_command_to_shell("terminal length 0", 1.0) # disable interactive prompt
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
    
    def get_basic_info(self) -> Dict[str, Any]:
        """Get essential system information: vendor, IP, and MAC address."""
        try:
            # Send the command and handle potential pager
            output = self._send_command_with_pager("show version", 5.0)
            if output and ("kontron" in output.lower() or "istax" in output.lower() or "kswitch" in output.lower()):
                return self._parse_basic_info(output)
            
            return {"vendor": "kontron", "ip": self.host, "mac": None}
            
        except Exception:
            return {"vendor": "kontron", "ip": self.host, "mac": None}
    
    def _parse_basic_info(self, output: str) -> Dict[str, Any]:
        """Parse essential information from show version output."""
        info = {"vendor": "kontron", "ip": self.host, "mac": None}
        
        # Extract MAC address
        mac_match = re.search(r"MAC Address\s*:\s*([0-9a-fA-F-]{17})", output)
        if mac_match:
            info["mac"] = mac_match.group(1).strip()
        
        # Verify it's a Kontron switch by checking for identifying strings
        output_lower = output.lower()
        if any(identifier in output_lower for identifier in ['kontron kswitch', 'microchip istax', 'istax switch']):
            info["vendor"] = "kontron"
        
        return info
    
    def get_neighbors(self) -> List[NeighborInfo]:
        """Get neighbor information from LLDP."""
        try:
            output = self._send_command_with_pager("show lldp neighbors", 5.0)
            if output:
                return self._parse_lldp_neighbors(output)
            return []
            
        except Exception as e:
            print(f"Failed to get neighbor info: {e}")
            return []
    
    def _parse_lldp_neighbors(self, output: str) -> List[NeighborInfo]:
        """Parse LLDP output and extract essential neighbor information."""
        neighbors = []
        lines = output.split('\n')
        current_neighbor = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Start of a new neighbor entry
            if line.startswith('Local Interface'):
                # Process previous neighbor if exists
                if current_neighbor and 'ip' in current_neighbor:
                    neighbors.append(NeighborInfo(
                        ip=current_neighbor.get('ip'),
                        mac=current_neighbor.get('mac'),
                        type=current_neighbor.get('type', 'unknown')
                    ))
                current_neighbor = {}
            
            # Extract Management Address (IPv4)
            elif 'Management Address' in line and 'IPv4' in line:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_neighbor['ip'] = ip_match.group(1)
            
            # Extract Chassis ID (MAC address)
            elif line.startswith('Chassis ID'):
                parts = line.split(':')
                if len(parts) > 1:
                    chassis_id = parts[1].strip()
                    # Check if it's a MAC address format
                    if re.match(r'^[0-9a-fA-F-]{17}$', chassis_id):
                        current_neighbor['mac'] = chassis_id
            
            # Determine neighbor type from System Description
            elif line.startswith('System Description'):
                parts = line.split(':')
                if len(parts) > 1:
                    description = parts[1].strip().lower()
                    if 'hirschmann' in description or 'hios' in description or 'bobcat' in description:
                        current_neighbor['type'] = 'hirschmann'
                    elif 'lantech' in description or 'tpes' in description:
                        current_neighbor['type'] = 'lantech'
                    elif 'kontron' in description or 'istax' in description or 'kswitch' in description:
                        current_neighbor['type'] = 'kontron'
                    elif 'nomad' in description:
                        current_neighbor['type'] = 'nomad'
                    else:
                        current_neighbor['type'] = 'unknown'
        
        # Add the last neighbor if exists
        if current_neighbor and 'ip' in current_neighbor:
            neighbors.append(NeighborInfo(
                ip=current_neighbor.get('ip'),
                mac=current_neighbor.get('mac'),
                type=current_neighbor.get('type', 'unknown')
            ))
        
        return neighbors
    
    def get_switch_info(self) -> SwitchInfo:
        """Get essential switch information for network discovery."""
        try:
            print(f"Attempting to connect to {self.host} with username: {self.username}")
            if not self.connect():
                print(f"Failed to connect to {self.host}")
                return SwitchInfo(ip=self.host, mac=None, type='kontron', neighbors=[])
            
            print(f"Successfully connected to {self.host}")
            
            # Get basic info (vendor, IP, MAC)
            basic_info = self.get_basic_info()
            print(f"System info retrieved: {list(basic_info.keys()) if basic_info else 'None'}")
            
            # Get neighbor information
            print("Getting neighbor information...")
            neighbors = self.get_neighbors()
            print(f"Found {len(neighbors)} neighbors")
            
            self.disconnect()
            print(f"Disconnected from {self.host}")
            
            return SwitchInfo(
                ip=basic_info.get('ip', self.host),
                mac=basic_info.get('mac'),
                type=basic_info.get('vendor', 'kontron'),
                neighbors=neighbors
            )
            
        except Exception as e:
            print(f"Failed to get switch info: {e}")
            try:
                self.disconnect()
            except:
                pass
            return SwitchInfo(ip=self.host, mac=None, type='kontron', neighbors=[])
    
    def _send_command_with_pager(self, command: str, timeout: float) -> str:
        """
        Send command and handle potential pager (more/less) interaction.
        Kontron switches use pager for long outputs like 'show version'.
        """
        try:
            # Send the initial command
            output = self.ssh_client.send_command_to_shell(command, timeout)
            
            # Check if there's a pager prompt (-- more --)
            if output and ("-- more --" in output.lower() or "next page: space" in output.lower()):
                full_output = output
                
                # Keep sending spaces to get more content until no more pager prompts
                max_pages = 10  # Safety limit to avoid infinite loops
                page_count = 0
                
                while ("-- more --" in full_output.lower() or "next page: space" in full_output.lower()) and page_count < max_pages:
                    # Send space to continue
                    additional_output = self.ssh_client.send_command_to_shell(" ", timeout)
                    if additional_output:
                        full_output += "\n" + additional_output
                    page_count += 1
                
                return full_output
            
            return output
            
        except Exception as e:
            print(f"Error sending command with pager handling: {e}")
            return ""
    
    # Compatibility methods required by BaseDiscovery
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information (backward compatibility)."""
        return self.get_basic_info()
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        """Get neighbor information (backward compatibility)."""
        neighbors = self.get_neighbors()
        return [{"ip": n.ip, "mac": n.mac, "type": n.type} for n in neighbors]

