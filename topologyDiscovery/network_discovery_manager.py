"""
Network Discovery Manager - Main orchestrator for switch network discovery.
Handles the complete discovery process from initial switch detection to topology mapping.
"""
import json
import yaml
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from switch_detector import SwitchDetector
from discovery.HirschmannDiscovery import HirschmannDiscovery
from discovery.LantechDiscovery import LantechDiscovery
from discovery.KontorDiscovery import KontorDiscovery
from discovery.NomadDiscovery import NomadDiscovery
from data_model import NetworkTopology, TopologyNode, TopologyEdge, SwitchData, SystemInfo


class NetworkDiscoveryManager:
    """
    Main class that orchestrates the network discovery process.
    """
    
    def __init__(self, credentials_file: str = "credentials.yaml"):
        """
        Initialize the network discovery manager.
        
        Args:
            credentials_file: Path to credentials configuration file
        """
        self.detector = SwitchDetector(credentials_file)
        self.discovered_switches: Set[str] = set()
        self.failed_switches: Set[str] = set()
        self.topology = NetworkTopology()
        self.max_discovery_depth = 5  # Prevent infinite loops
        
        # Vendor to discovery class mapping
        self.discovery_classes = {
            'hirschmann': HirschmannDiscovery,
            'lantech': LantechDiscovery,
            'kontron': KontorDiscovery,
            'nomad': NomadDiscovery
        }
    
    def discover_network(self, seed_ip: str, max_depth: int = None) -> NetworkTopology:
        """
        Discover the entire network starting from a seed IP address.
        
        Args:
            seed_ip: Starting IP address for discovery
            max_depth: Maximum discovery depth (default: 5)
            
        Returns:
            NetworkTopology object containing discovered network
        """
        if max_depth:
            self.max_discovery_depth = max_depth
        
        print(f"🚀 Starting network discovery from seed IP: {seed_ip}")
        print(f"📊 Maximum discovery depth: {self.max_discovery_depth}")
        
        self.topology.discovery_started = datetime.now()
        
        # Start discovery with the seed IP
        self._discover_switch_recursive(seed_ip, depth=0)
        
        self.topology.discovery_completed = datetime.now()
        
        # Print discovery summary
        self._print_discovery_summary()
        
        return self.topology
    
    def _discover_switch_recursive(self, host: str, depth: int = 0) -> Optional[TopologyNode]:
        """
        Recursively discover switches starting from the given host.
        
        Args:
            host: IP address of the switch to discover
            depth: Current discovery depth
            
        Returns:
            TopologyNode if successful, None if failed
        """
        # Check depth limit
        if depth > self.max_discovery_depth:
            print(f"⚠️  Maximum discovery depth ({self.max_discovery_depth}) reached for {host}")
            return None
        
        # Skip if already discovered or failed
        if host in self.discovered_switches:
            print(f"ℹ️  Switch {host} already discovered, skipping...")
            return self.topology.get_node(host)
        
        if host in self.failed_switches:
            print(f"⚠️  Switch {host} previously failed, skipping...")
            return None
        
        print(f"🔍 Discovering switch at {host} (depth: {depth})")
        
        # Step 1: Auto-detect switch type
        vendor, ssh_client, credentials = self.detector.detect_switch_type(host)
        
        if not vendor or not ssh_client:
            print(f"❌ Failed to detect/connect to switch at {host}")
            self.failed_switches.add(host)
            return None
        
        try:
            # Step 2: Create vendor-specific discovery instance
            discovery_class = self.discovery_classes.get(vendor)
            if not discovery_class:
                print(f"❌ No discovery class found for vendor: {vendor}")
                ssh_client.disconnect()
                self.failed_switches.add(host)
                return None
            
            discovery = discovery_class(
                host=host,
                username=credentials['username'],
                password=credentials['password']
            )
            
            # Use the existing connection
            discovery.ssh_client = ssh_client
            
            # Step 3: Gather switch information
            print(f"📋 Gathering information from {vendor} switch at {host}")
            
            system_info = discovery.get_system_info()
            interfaces = discovery.get_interface_info()
            neighbors = discovery.get_neighbor_info()
            mac_table = discovery.get_mac_table()
            
            # Step 4: Create switch data structure
            switch_data = self._create_switch_data(
                host, vendor, system_info, interfaces, neighbors, mac_table
            )
            
            # Step 5: Create topology node
            topology_node = TopologyNode(
                host=host,
                switch_data=switch_data,
                connections=[],
                discovered=True,
                discovery_depth=depth
            )
            
            # Step 6: Add to topology
            self.topology.add_node(topology_node)
            self.discovered_switches.add(host)
            
            # Step 7: Print switch information
            self._print_switch_info(switch_data)
            
            # Step 8: Process LLDP neighbors for recursive discovery
            neighbor_ips = self._extract_neighbor_ips(neighbors)
            topology_node.connections = neighbor_ips
            
            # Step 9: Add edges for discovered neighbors
            for neighbor_info in neighbors:
                neighbor_ip = self._extract_ip_from_neighbor(neighbor_info)
                if neighbor_ip:
                    edge = TopologyEdge(
                        source_host=host,
                        source_interface=neighbor_info.get('local_interface', 'unknown'),
                        target_host=neighbor_ip,
                        target_interface=neighbor_info.get('remote_port_id', 'unknown'),
                        connection_type='lldp'
                    )
                    self.topology.add_edge(edge)
            
            # Step 10: Recursively discover neighbors
            print(f"🔗 Found {len(neighbor_ips)} neighbors for {host}: {neighbor_ips}")
            
            for neighbor_ip in neighbor_ips:
                self._discover_switch_recursive(neighbor_ip, depth + 1)
            
            # Clean up connection
            discovery.disconnect()
            
            return topology_node
            
        except Exception as e:
            print(f"❌ Error during discovery of {host}: {e}")
            if ssh_client:
                ssh_client.disconnect()
            self.failed_switches.add(host)
            return None
    
    def _create_switch_data(self, host: str, vendor: str, system_info: dict, 
                           interfaces: list, neighbors: list, mac_table: list) -> SwitchData:
        """Create a SwitchData object from discovery results."""
        
        # Create SystemInfo object
        sys_info = SystemInfo(
            hostname=system_info.get('hostname'),
            model=system_info.get('model'),
            vendor=vendor,
            os_version=system_info.get('os_version'),
            serial_number=system_info.get('serial_number'),
            uptime=system_info.get('uptime'),
            location=system_info.get('location'),
            contact=system_info.get('contact'),
            description=system_info.get('description')
        )
        
        # Create SwitchData object
        switch_data = SwitchData(
            host=host,
            discovery_timestamp=datetime.now(),
            system_info=sys_info,
            interfaces=[],  # Would convert to SwitchInterface objects
            lldp_neighbors=[],  # Would convert to LLDPNeighbor objects
            mac_table=[],  # Would convert to MacTableEntry objects
            raw_data={
                'system_info': system_info,
                'interfaces': interfaces,
                'neighbors': neighbors,
                'mac_table': mac_table
            }
        )
        
        return switch_data
    
    def _extract_neighbor_ips(self, neighbors: List[Dict[str, Any]]) -> List[str]:
        """Extract IP addresses from neighbor information."""
        ips = []
        
        for neighbor in neighbors:
            ip = self._extract_ip_from_neighbor(neighbor)
            if ip and ip not in ips:
                ips.append(ip)
        
        return ips
    
    def _extract_ip_from_neighbor(self, neighbor: Dict[str, Any]) -> Optional[str]:
        """Extract IP address from a single neighbor entry."""
        # Try different fields where IP might be stored
        ip_fields = [
            'remote_management_address',
            'management_address',
            'remote_ip',
            'ip_address',
            'address'
        ]
        
        for field in ip_fields:
            if field in neighbor and neighbor[field]:
                ip = neighbor[field].strip()
                # Basic IP validation
                if self._is_valid_ip(ip):
                    return ip
        
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Basic IP address validation."""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def _print_switch_info(self, switch_data: SwitchData) -> None:
        """Print formatted switch information."""
        print(f"\n📋 Switch Information for {switch_data.host}")
        print("=" * 50)
        
        sys_info = switch_data.system_info
        if sys_info.hostname:
            print(f"Hostname: {sys_info.hostname}")
        if sys_info.vendor:
            print(f"Vendor: {sys_info.vendor}")
        if sys_info.model:
            print(f"Model: {sys_info.model}")
        if sys_info.os_version:
            print(f"OS Version: {sys_info.os_version}")
        if sys_info.serial_number:
            print(f"Serial Number: {sys_info.serial_number}")
        if sys_info.uptime:
            print(f"Uptime: {sys_info.uptime}")
        if sys_info.location:
            print(f"Location: {sys_info.location}")
        if sys_info.contact:
            print(f"Contact: {sys_info.contact}")
        
        # Print raw data for debugging
        raw_system = switch_data.raw_data.get('system_info', {})
        if 'management_ip' in raw_system:
            print(f"Management IP: {raw_system['management_ip']}")
        if 'management_mac' in raw_system:
            print(f"Management MAC: {raw_system['management_mac']}")
        
        print(f"Interfaces: {len(switch_data.raw_data.get('interfaces', []))}")
        print(f"LLDP Neighbors: {len(switch_data.raw_data.get('neighbors', []))}")
        print(f"MAC Table Entries: {len(switch_data.raw_data.get('mac_table', []))}")
        print()
    
    def _print_discovery_summary(self) -> None:
        """Print discovery summary."""
        print("\n" + "=" * 60)
        print("🎯 NETWORK DISCOVERY SUMMARY")
        print("=" * 60)
        
        duration = self.topology.discovery_completed - self.topology.discovery_started
        
        print(f"Discovery started: {self.topology.discovery_started.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Discovery completed: {self.topology.discovery_completed.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        print(f"Switches discovered: {len(self.discovered_switches)}")
        print(f"Failed switches: {len(self.failed_switches)}")
        print(f"Network connections: {len(self.topology.edges)}")
        
        if self.discovered_switches:
            print(f"\n✅ Successfully discovered switches:")
            for ip in sorted(self.discovered_switches):
                node = self.topology.get_node(ip)
                if node and node.switch_data.system_info.hostname:
                    print(f"  - {ip} ({node.switch_data.system_info.hostname})")
                else:
                    print(f"  - {ip}")
        
        if self.failed_switches:
            print(f"\n❌ Failed to discover switches:")
            for ip in sorted(self.failed_switches):
                print(f"  - {ip}")
        
        print()
    
    def save_topology(self, filename: str = None) -> str:
        """
        Save discovered topology to JSON file.
        
        Args:
            filename: Output filename (default: topology_YYYYMMDD_HHMMSS.json)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/topology_{timestamp}.json"
        
        topology_dict = self.topology.to_dict()
        
        try:
            with open(filename, 'w') as f:
                json.dump(topology_dict, f, indent=2, default=str)
            
            print(f"💾 Topology saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Failed to save topology: {e}")
            return ""
    
    def generate_inventory(self, filename: str = None) -> str:
        """
        Generate Ansible inventory from discovered topology.
        
        Args:
            filename: Output filename (default: output/inventory.yaml)
            
        Returns:
            Path to generated inventory file
        """
        if not filename:
            filename = "output/inventory.yaml"
        
        inventory = {
            'all': {
                'children': {
                    'switches': {
                        'hosts': {},
                        'vars': {
                            'ansible_connection': 'network_cli',
                            'ansible_python_interpreter': '{{ ansible_playbook_python }}'
                        }
                    }
                },
                'vars': {
                    'discovery_timestamp': self.topology.discovery_completed.isoformat() if self.topology.discovery_completed else None,
                    'total_switches_discovered': len(self.discovered_switches),
                    'topology_depth': self.max_discovery_depth
                }
            }
        }
        
        # Add discovered switches to inventory
        for host, node in self.topology.nodes.items():
            sys_info = node.switch_data.system_info
            
            inventory['all']['children']['switches']['hosts'][host] = {
                'ansible_host': host,
                'vendor': sys_info.vendor or 'unknown',
                'model': sys_info.model or 'unknown',
                'hostname': sys_info.hostname or 'unknown',
                'serial_number': sys_info.serial_number or 'unknown',
                'os_version': sys_info.os_version or 'unknown',
                'discovery_depth': node.discovery_depth,
                'neighbor_count': len(node.connections)
            }
        
        try:
            with open(filename, 'w') as f:
                yaml.dump(inventory, f, default_flow_style=False, indent=2)
            
            print(f"📋 Ansible inventory generated: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Failed to generate inventory: {e}")
            return ""


if __name__ == "__main__":
    # Example usage
    discovery_manager = NetworkDiscoveryManager()
    
    # Start discovery from seed IP
    seed_ip = "192.168.1.31"  # Hirschmann switch example
    
    print("🚀 Starting Network Discovery Tool")
    print(f"Seed IP: {seed_ip}")
    
    # Discover the network
    topology = discovery_manager.discover_network(seed_ip, max_depth=3)
    
    # Save results
    discovery_manager.save_topology()
    discovery_manager.generate_inventory()
