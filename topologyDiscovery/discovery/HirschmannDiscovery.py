from typing import Dict, List, Any, Optional

from topologyDiscovery.discovery import BaseDiscovery

class HirschmannDiscovery(BaseDiscovery):
    def connect(self) -> bool:
        return "connection"
    
    def disconnect(self) -> bool:
        return "disconnect"

    def get_system_info(self) -> Dict[str, Any]:
        return "Hirschmann"
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        return "neighbors"
