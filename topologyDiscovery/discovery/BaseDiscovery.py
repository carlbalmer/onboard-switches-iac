"""
Abstract base class for all discovery implementations.
Defines the common interface that all vendor-specific discovery classes must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_model import SwitchInfo, NeighborInfo


class BaseDiscovery(ABC):
    """
    Abstract base class for switch discovery implementations.
    Each vendor-specific discovery class should inherit from this class.
    """
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        """
        Initialize the discovery instance.
        
        Args:
            host: IP address or hostname of the switch
            username: SSH username
            password: SSH password
            port: SSH port (default: 22)
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the switch.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to the switch.
        """
        pass
    
    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get basic system information from the switch.
        
        Returns:
            Dict containing system information like model, version, etc.
        """
        pass
    
    def get_interface_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all interfaces on the switch.
        Default implementation returns empty list (optional for discovery).
        
        Returns:
            List of dictionaries containing interface information
        """
        return []
    
    @abstractmethod
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        """
        Get LLDP neighbor information.
        
        Returns:
            List of dictionaries containing neighbor information
        """
        pass
    
    def get_mac_table(self) -> List[Dict[str, Any]]:
        """
        Get MAC address table from the switch.
        Default implementation returns empty list (optional for discovery).
        
        Returns:
            List of dictionaries containing MAC table entries
        """
        return []
    
    @abstractmethod
    def get_switch_info(self) -> SwitchInfo:
        """
        Get simplified switch information for network discovery.
        This is the main method used by the network discovery manager.
        
        Returns:
            SwitchInfo object with essential fields only (IP, MAC, type, neighbors)
        """
        pass

    def discover(self) -> Dict[str, Any]:
        """
        Main discovery method that orchestrates the discovery process.
        
        Returns:
            Dict containing all discovered information about the switch
        """
        if not self.connect():
            return {"error": f"Failed to connect to {self.host}"}
        
        try:
            discovery_data = {
                "host": self.host,
                "system_info": self.get_system_info(),
                "interfaces": self.get_interface_info(),
                "neighbors": self.get_neighbor_info(),
                "mac_table": self.get_mac_table()
            }
            return discovery_data
        except Exception as e:
            return {"error": f"Discovery failed for {self.host}: {str(e)}"}
        finally:
            self.disconnect()
