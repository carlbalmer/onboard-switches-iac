from typing import Dict, List, Any, Optional

from .BaseDiscovery import BaseDiscovery

class NomadDiscovery(BaseDiscovery):
    def connect(self) -> bool:
        return "connection"
    
    def disconnect(self) -> bool:
        return "disconnect"

    def get_system_info(self) -> Dict[str, Any]:
        return "Nomad"
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        return "neighbors"

