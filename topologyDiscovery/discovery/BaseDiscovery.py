"""
Simplified Abstract base class for switch discovery implementations.
Focuses only on essential discovery functionality.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_model import SwitchInfo


class BaseDiscovery(ABC):
    """
    Simplified abstract base class for switch discovery implementations.
    Only defines essential methods needed for network topology discovery.
    """
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        """Initialize the discovery instance with connection parameters."""
        self.host = host
        self.username = username
        self.password = password
        self.port = port
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the switch."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the switch."""
        pass
    
    @abstractmethod
    def get_switch_info(self) -> SwitchInfo:
        """
        Get essential switch information for network discovery.
        This is the main method used by the network discovery manager.
        
        Returns:
            SwitchInfo object with essential fields: IP, MAC, type, neighbors
        """
        pass

    # The following methods are kept for backward compatibility only
    # They are required by some discovery implementations but not used by the main discovery process
    
    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information (backward compatibility)."""
        pass
    
    @abstractmethod 
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        """Get neighbor information (backward compatibility)."""
        pass
