"""
Normalized data structures for switch discovery information.
Defines standard data models used across all vendor-specific discovery implementations.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class LLDPNeighbor:
    """
    LLDP neighbor information.
    """
    ip_address: str
    mac_address: str
    remote_system_name: Optional[str] = None
    remote_system_description: Optional[str] = None


@dataclass
class SystemInfo:
    """
    Basic system information.
    """
    ip_address: str
    hostname: Optional[str] = None
    model: Optional[str] = None
    vendor: Optional[str] = None
    os_version: Optional[str] = None
    serial_number: Optional[str] = None


@dataclass
class SwitchData:
    """
    Complete normalized switch data structure.
    """
    ip_address: str
    host: str
    discovery_timestamp: datetime
    system_info: SystemInfo
    lldp_neighbors: List[LLDPNeighbor]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert switch data to dictionary format.
        
        Returns:
            Dict representation of the switch data
        """
        return {
            "ip_address": self.ip_address,
            "host": self.host,
            "system_info": {
                "ip_address": self.system_info.ip_address,
                "hostname": self.system_info.hostname,
                "model": self.system_info.model,
                "vendor": self.system_info.vendor,
                "os_version": self.system_info.os_version,
                "serial_number": self.system_info.serial_number,
            },
            "lldp_neighbors": [
                {
                    "ip_address": neighbor.ip_address,
                    "mac_address": neighbor.mac_address,
                    "remote_system_name": neighbor.remote_system_name,
                    "remote_system_description": neighbor.remote_system_description,
                }
                for neighbor in self.lldp_neighbors
            ],
            "errors": self.errors
        }
