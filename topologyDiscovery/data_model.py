"""
Normalized data structures for switch discovery information.
Defines standard data models used across all vendor-specific discovery implementations.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class SwitchInterface:
    """
    Normalized interface information.
    """
    name: str
    description: Optional[str] = None
    admin_status: str = "unknown"  # up, down, testing
    oper_status: str = "unknown"   # up, down, testing, unknown, dormant, notPresent, lowerLayerDown
    speed: Optional[int] = None    # In Mbps
    duplex: Optional[str] = None   # full, half, auto
    mtu: Optional[int] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    vlan_id: Optional[int] = None
    port_type: Optional[str] = None  # access, trunk, hybrid


@dataclass
class LLDPNeighbor:
    """
    LLDP neighbor information.
    """
    local_interface: str
    remote_chassis_id: str
    remote_port_id: str
    remote_system_name: Optional[str] = None
    remote_system_description: Optional[str] = None
    remote_port_description: Optional[str] = None
    remote_management_address: Optional[str] = None
    capabilities: Optional[List[str]] = None


@dataclass
class MacTableEntry:
    """
    MAC address table entry.
    """
    mac_address: str
    vlan_id: int
    interface: str
    entry_type: str = "dynamic"  # dynamic, static, secure


@dataclass
class SystemInfo:
    """
    Basic system information.
    """
    hostname: Optional[str] = None
    model: Optional[str] = None
    vendor: Optional[str] = None
    os_version: Optional[str] = None
    serial_number: Optional[str] = None
    uptime: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None
    description: Optional[str] = None


@dataclass
class SwitchData:
    """
    Complete normalized switch data structure.
    """
    host: str
    discovery_timestamp: datetime
    system_info: SystemInfo
    interfaces: List[SwitchInterface]
    lldp_neighbors: List[LLDPNeighbor]
    mac_table: List[MacTableEntry]
    raw_data: Optional[Dict[str, Any]] = None  # Store vendor-specific raw data
    errors: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert switch data to dictionary format.
        
        Returns:
            Dict representation of the switch data
        """
        return {
            "host": self.host,
            "discovery_timestamp": self.discovery_timestamp.isoformat(),
            "system_info": {
                "hostname": self.system_info.hostname,
                "model": self.system_info.model,
                "vendor": self.system_info.vendor,
                "os_version": self.system_info.os_version,
                "serial_number": self.system_info.serial_number,
                "uptime": self.system_info.uptime,
                "location": self.system_info.location,
                "contact": self.system_info.contact,
                "description": self.system_info.description
            },
            "interfaces": [
                {
                    "name": iface.name,
                    "description": iface.description,
                    "admin_status": iface.admin_status,
                    "oper_status": iface.oper_status,
                    "speed": iface.speed,
                    "duplex": iface.duplex,
                    "mtu": iface.mtu,
                    "mac_address": iface.mac_address,
                    "ip_address": iface.ip_address,
                    "vlan_id": iface.vlan_id,
                    "port_type": iface.port_type
                }
                for iface in self.interfaces
            ],
            "lldp_neighbors": [
                {
                    "local_interface": neighbor.local_interface,
                    "remote_chassis_id": neighbor.remote_chassis_id,
                    "remote_port_id": neighbor.remote_port_id,
                    "remote_system_name": neighbor.remote_system_name,
                    "remote_system_description": neighbor.remote_system_description,
                    "remote_port_description": neighbor.remote_port_description,
                    "remote_management_address": neighbor.remote_management_address,
                    "capabilities": neighbor.capabilities
                }
                for neighbor in self.lldp_neighbors
            ],
            "mac_table": [
                {
                    "mac_address": entry.mac_address,
                    "vlan_id": entry.vlan_id,
                    "interface": entry.interface,
                    "entry_type": entry.entry_type
                }
                for entry in self.mac_table
            ],
            "raw_data": self.raw_data,
            "errors": self.errors
        }


@dataclass
class TopologyNode:
    """
    Represents a node in the network topology.
    """
    host: str
    switch_data: SwitchData
    connections: List[str]  # List of connected host IPs
    discovered: bool = False
    discovery_depth: int = 0


@dataclass
class TopologyEdge:
    """
    Represents a connection between two topology nodes.
    """
    source_host: str
    source_interface: str
    target_host: str  
    target_interface: str
    connection_type: str = "lldp"  # lldp, mac_based, manual


class NetworkTopology:
    """
    Complete network topology representation.
    """
    
    def __init__(self):
        self.nodes: Dict[str, TopologyNode] = {}
        self.edges: List[TopologyEdge] = []
        self.discovery_started: Optional[datetime] = None
        self.discovery_completed: Optional[datetime] = None
    
    def add_node(self, node: TopologyNode) -> None:
        """Add a node to the topology."""
        self.nodes[node.host] = node
    
    def add_edge(self, edge: TopologyEdge) -> None:
        """Add an edge to the topology."""
        self.edges.append(edge)
    
    def get_node(self, host: str) -> Optional[TopologyNode]:
        """Get a node by host IP."""
        return self.nodes.get(host)
    
    def get_neighbors(self, host: str) -> List[str]:
        """Get all neighbor hosts for a given host."""
        neighbors = []
        for edge in self.edges:
            if edge.source_host == host:
                neighbors.append(edge.target_host)
            elif edge.target_host == host:
                neighbors.append(edge.source_host)
        return list(set(neighbors))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert topology to dictionary format."""
        return {
            "discovery_started": self.discovery_started.isoformat() if self.discovery_started else None,
            "discovery_completed": self.discovery_completed.isoformat() if self.discovery_completed else None,
            "nodes": {
                host: {
                    "host": node.host,
                    "switch_data": node.switch_data.to_dict(),
                    "connections": node.connections,
                    "discovered": node.discovered,
                    "discovery_depth": node.discovery_depth
                }
                for host, node in self.nodes.items()
            },
            "edges": [
                {
                    "source_host": edge.source_host,
                    "source_interface": edge.source_interface,
                    "target_host": edge.target_host,
                    "target_interface": edge.target_interface,
                    "connection_type": edge.connection_type
                }
                for edge in self.edges
            ]
        }
