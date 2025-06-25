"""
Nomad Switch Discovery Implementation
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
from logging_config import get_logger


class NomadDiscovery(BaseDiscovery):
    """Nomad switch discovery implementation."""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        super().__init__(host, username, password, port)
        self.ssh_client = None
        self.vendor = "nomad"
        self.logger = get_logger(__name__)  # Initialize logger
    
    def connect(self) -> bool:
        """Establish SSH connection to Nomad switch."""
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
            self.logger.error(f"Connection failed to {self.host}: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close SSH connection to the switch."""
        if self.ssh_client:
            self.ssh_client.disconnect()
            self.ssh_client = None
    
    def get_basic_info(self) -> Dict[str, Any]:
        """Get essential system information: vendor, IP, and MAC address."""
        try:
            output = self.ssh_client.send_command_to_shell("show version", 3.0)
            if output and ("lantech" in output or "tpes" in output.lower()):
                return self._parse_basic_info(output)
            
            return {"vendor": "lantech", "ip": self.host, "mac": None}
            
        except Exception:
            return {"vendor": "lantech", "ip": self.host, "mac": None}
    
    def _parse_basic_info(self, output: str) -> Dict[str, Any]:
        """Parse essential information from system info output."""
        info = {"vendor": "lantech", "ip": self.host, "mac": None}
        
        # Extract MAC address
        mac_match = re.search(r"MAC address\.+(.+)", output, re.IGNORECASE)
        if mac_match:
            info["mac"] = mac_match.group(1).strip()
        
        return info

    def get_neighbors(self) -> List[NeighborInfo]:
        """Get neighbor information from LLDP."""
        try:
            output = self.ssh_client.send_command_to_shell("show lldp remote-data", 3.0)
            if output:
                return self._parse_lldp_neighbors(output)
            return []
            
        except Exception as e:
            print(f"Failed to get neighbor info: {e}")
            return []

    # Compatibility methods required by BaseDiscovery
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information (backward compatibility)."""
        return {"error": "Nomad discovery not yet implemented"}
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        """Get neighbor information (backward compatibility)."""
        return []

