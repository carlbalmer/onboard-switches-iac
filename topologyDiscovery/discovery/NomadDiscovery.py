"""
Nomad Switch Discovery Implementation (Stub)
TODO: Implement Nomad-specific discovery logic
"""
import sys
import os
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .BaseDiscovery import BaseDiscovery
from ssh_client import SSHClient
from data_model import SwitchInfo


class NomadDiscovery(BaseDiscovery):
    """Stub implementation for Nomad switches."""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        super().__init__(host, username, password, port)
        self.vendor = "nomad"
    
    def connect(self) -> bool:
        """Establish SSH connection to Lantech switch."""
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
        """TODO: Implement Nomad disconnect logic."""
        pass
    
    def get_switch_info(self) -> SwitchInfo:
        """Get simplified switch information for network discovery."""
        return SwitchInfo(ip=self.host, mac=None, type="nomad", neighbors=[])
    
    # Compatibility methods required by BaseDiscovery
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information (backward compatibility)."""
        return {"error": "Nomad discovery not yet implemented"}
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        """Get neighbor information (backward compatibility)."""
        return []

