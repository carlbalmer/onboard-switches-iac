"""
Minimal data structures for switch discovery information.
Only includes essential fields: IP, MAC, vendor/type, and neighbor information.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class NeighborInfo:
    """
    Minimal LLDP neighbor information.
    """
    ip: Optional[str] = None
    mac: Optional[str] = None
    type: Optional[str] = None  # vendor/switch type


@dataclass
class SwitchInfo:
    """
    Minimal switch information.
    """
    ip: str
    mac: Optional[str] = None
    type: Optional[str] = None  # vendor (hirschmann, lantech, kontron, nomad)
    neighbors: List[NeighborInfo] = None
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = []


@dataclass
class NetworkTopology:
    """
    Minimal network topology representation.
    """
    switches: Dict[str, SwitchInfo] = None  # IP -> SwitchInfo
    discovery_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.switches is None:
            self.switches = {}
    
    def add_switch(self, switch_info: SwitchInfo) -> None:
        """Add a switch to the topology."""
        self.switches[switch_info.ip] = switch_info
    
    def get_switch(self, ip_address: str) -> Optional[SwitchInfo]:
        """Get switch by IP address."""
        return self.switches.get(ip_address)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert topology to dictionary format."""
        return {
            "discovery_timestamp": self.discovery_timestamp.isoformat() if self.discovery_timestamp else None,
            "switches": {
                ip: {
                    "ip": switch.ip,
                    "mac": switch.mac,
                    "type": switch.type,
                    "neighbors": [
                        {
                            "ip": neighbor.ip,
                            "mac": neighbor.mac,
                            "type": neighbor.type
                        }
                        for neighbor in switch.neighbors
                    ]
                }
                for ip, switch in self.switches.items()
            }
        }
