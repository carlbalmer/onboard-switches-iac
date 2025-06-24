from typing import Dict, List, Any, Optional

import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .BaseDiscovery import BaseDiscovery
from ssh_client import SSHClient

class HirschmannDiscovery(BaseDiscovery):

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
        print("trying to establish connection >>>>>>")
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
                    print("Connection established >>>>>>>")
                    return True
                    
            return False
        
        except Exception as e:
            print(f"Connection failed to {self.host}: {e}")
            return False
    
    def disconnect(self) -> bool:
        return "disconnect"

    def get_system_info(self) -> Dict[str, Any]:
        self.ssh_client.execute_command("show system info", 10)
        return "Hirschmann"
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        return "neighbors"
