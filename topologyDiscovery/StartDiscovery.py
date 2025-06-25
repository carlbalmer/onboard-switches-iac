#!/usr/bin/env python3
"""
Simplified Network Discovery Tool - Entry Point
Combines NetworkDiscoveryManager and StartDiscovery into a single file.
Starts the network discovery process from a seed IP address.
"""
import sys
import os
import json
import yaml
import argparse
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass

# Import existing modules
from switch_detector import SwitchDetector
from discovery.HirschmannDiscovery import HirschmannDiscovery
from discovery.LantechDiscovery import LantechDiscovery
from discovery.KontronDiscovery import KontronDiscovery
from discovery.NomadDiscovery import NomadDiscovery
from data_model import NetworkTopology, SwitchInfo, NeighborInfo


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
            'kontron': KontronDiscovery,
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
        
        self.topology.discovery_timestamp = datetime.now()
        
        # Start discovery with the seed IP
        #self._discover_switch_recursive(seed_ip, depth=0)
        self._discover_switches_iterative(seed_ip)
        
        # Print discovery summary
        self._print_discovery_summary()
        
        return self.topology
    
    def _discover_switch_recursive(self, host: str, depth: int = 0) -> Optional[SwitchInfo]:
        """
        Recursively discover switches starting from the given host.
        
        Args:
            host: IP address of the switch to discover
            depth: Current discovery depth
            
        Returns:
            SwitchInfo object if discovery successful, None otherwise
        """
        # Check if we've already processed this switch
        if host in self.discovered_switches or host in self.failed_switches:
            return self.topology.get_switch(host)
        
        # Check depth limit
        if depth >= self.max_discovery_depth:
            print(f"⚠️  Maximum discovery depth ({self.max_discovery_depth}) reached for {host}")
            return None
        
        print(f"{'  ' * depth}🔍 Discovering switch at {host} (depth: {depth})")
        
        try:
            # Detect switch vendor
            vendor, ssh_client, credentials = self.detector.detect_switch_type(host)
            if ssh_client:
                ssh_client.disconnect()  # Close the detection connection
                
            if not vendor:
                print(f"{'  ' * depth}❌ Failed to detect vendor for {host}")
                self.failed_switches.add(host)
                return None
            
            if not credentials:
                print(f"{'  ' * depth}❌ No credentials returned for {vendor}")
                self.failed_switches.add(host)
                return None
            
            print(f"{'  ' * depth}✅ Detected {vendor} switch at {host}")
            print(f"{'  ' * depth}   Using credentials: {credentials.get('username', 'unknown')}")
            
            # Get appropriate discovery class
            discovery_class = self.discovery_classes.get(vendor)
            if not discovery_class:
                print(f"{'  ' * depth}❌ No discovery implementation for {vendor}")
                self.failed_switches.add(host)
                return None
            
            # Create discovery instance with detected credentials
            discovery = discovery_class(
                host=host,
                username=credentials['username'],
                password=credentials['password']
            )
            
            # Get switch information
            switch_info = discovery.get_switch_info()
            
            # Add to topology
            self.topology.add_switch(switch_info)
            self.discovered_switches.add(host)
            
            print(f"{'  ' * depth}📝 Added switch {host} to topology")
            print(f"{'  ' * depth}   MAC: {switch_info.mac}")
            print(f"{'  ' * depth}   Type: {switch_info.type}")
            print(f"{'  ' * depth}   Neighbors: {len(switch_info.neighbors)}")
            
            # Discover neighbors recursively
            for neighbor in switch_info.neighbors:
                if neighbor.ip and neighbor.ip not in self.discovered_switches:
                    print(f"{'  ' * depth}🔗 Found neighbor: {neighbor.ip} ({neighbor.type})")
                    self._discover_switch_recursive(neighbor.ip, depth + 1)
            
            return switch_info
            
        except Exception as e:
            print(f"{'  ' * depth}❌ Discovery failed for {host}: {str(e)}")
            self.failed_switches.add(host)
            return None
    
    def _discover_switches_iterative(self, seed_ip: str):
        print(f"gotten seed_ip {seed_ip}")
        seen_switches: Set[str] = set()
        failed_switches: Set[str] = set()
        candidate_switches: Set[str] = set()
        candidate_switches.add(seed_ip)
        print("Start looping candidates")
        counter: int = 1
        while candidate_switches:
            is_ok = True
            current_ip = candidate_switches.pop()
            seen_switches.add(current_ip)
            print("-----------------------------------------------------------------")
            print(f"looking at {current_ip}")
            print("-----------------------------------------------------------------")
            try:
                vendor, ssh_client, credentials = self.detector.detect_switch_type(current_ip)
                if ssh_client:
                    ssh_client.disconnect()  # Close the detection connection
                    
                if not credentials:
                    print(f"No credentials returned for {vendor}")
                    self.failed_switches.add(current_ip)
                    is_ok = False
                
                if not vendor:
                    print(f"Failed to detect vendor for {current_ip}")
                    self.failed_switches.add(current_ip)
                    is_ok = False

                if is_ok:
                    discovery_class = self.discovery_classes.get(vendor)
                    switch_instance = discovery_class(
                        host=current_ip,
                        username=credentials['username'],
                        password=credentials['password']
                    )
                    switch_info = switch_instance.get_switch_info()
                    self.topology.add_switch(switch_info)
                    self.discovered_switches.add(switch_info.ip)
                    for neighbor in switch_info.neighbors:
                        neighbor_ip = neighbor.ip
                        if neighbor_ip not in seen_switches:
                            candidate_switches.add(neighbor_ip)
            except Exception as e:
                print(f"Discovery failed for {current_ip}: {str(e)}")
                self.failed_switches.add(current_ip)
            counter += 1
            print("-----------------------------------------------------------------")
            print(F"<<<<looked at {counter} switches>>>>>>>>>>>>>>>>>>>>>>")
            print("-----------------------------------------------------------------")
        print(F"<<<<looked at {counter} switches")




    

    def _print_discovery_summary(self) -> None:
        """Print a summary of the discovery process."""
        print("\n" + "="*60)
        print("📊 NETWORK DISCOVERY SUMMARY")
        print("="*60)
        print(f"✅ Successfully discovered: {len(self.discovered_switches)} switches")
        print(f"❌ Failed to discover: {len(self.failed_switches)} switches")
        print(f"🕒 Discovery timestamp: {self.topology.discovery_timestamp}")
        
        if self.discovered_switches:
            print(f"\n📋 Discovered switches:")
            for ip in sorted(self.discovered_switches):
                switch = self.topology.get_switch(ip)
                if switch:
                    print(f"   {ip} - {switch.type} ({len(switch.neighbors)} neighbors)")
        
        if self.failed_switches:
            print(f"\n⚠️  Failed switches:")
            for ip in sorted(self.failed_switches):
                print(f"   {ip}")
        
        print("="*60)
    
    def save_to_file(self, filename: str, format: str = 'json') -> None:
        """
        Save topology to file.
        
        Args:
            filename: Output filename
            format: Output format ('json' or 'yaml')
        """
        topology_dict = self.topology.to_dict()
        
        try:
            with open(filename, 'w') as f:
                if format.lower() == 'yaml':
                    yaml.dump(topology_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(topology_dict, f, indent=2, default=str)
            
            print(f"💾 Topology saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save topology: {str(e)}")
    
    def get_topology_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the discovered topology.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_switches': len(self.topology.switches),
            'switch_types': {},
            'total_neighbors': 0,
            'discovery_timestamp': self.topology.discovery_timestamp,
            'discovered_ips': list(self.discovered_switches),
            'failed_ips': list(self.failed_switches)
        }
        
        # Count switch types and neighbors
        for switch in self.topology.switches.values():
            switch_type = switch.type or 'unknown'
            stats['switch_types'][switch_type] = stats['switch_types'].get(switch_type, 0) + 1
            stats['total_neighbors'] += len(switch.neighbors)
        
        return stats


def main():
    """Main entry point for the network discovery tool."""
    
    parser = argparse.ArgumentParser(
        description="Network Switch Discovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python StartDiscovery_Simple.py 192.168.1.31
  python StartDiscovery_Simple.py 192.168.1.31 --depth 5
  python StartDiscovery_Simple.py 192.168.1.31 --credentials custom_creds.yaml
        """
    )
    
    parser.add_argument(
        'seed_ip',
        help='Starting IP address for network discovery'
    )
    
    parser.add_argument(
        '--depth',
        type=int,
        default=5,
        help='Maximum discovery depth (default: 5)'
    )
    
    parser.add_argument(
        '--credentials',
        default='credentials.yaml',
        help='Path to credentials file (default: credentials.yaml)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for results (default: output)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    print("🌐 Network Switch Discovery Tool")
    print("=" * 40)
    print(f"Seed IP: {args.seed_ip}")
    print(f"Max Depth: {args.depth}")
    print(f"Credentials: {args.credentials}")
    print(f"Output Directory: {args.output_dir}")
    print()
    
    try:
        # Initialize discovery manager
        discovery_manager = NetworkDiscoveryManager(args.credentials)
        
        # Start network discovery
        topology = discovery_manager.discover_network(
            seed_ip=args.seed_ip,
            max_depth=args.depth
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Save results
        topology_filename = f"{args.output_dir}/topology_{args.seed_ip.replace('.', '_')}.json"
        inventory_filename = f"{args.output_dir}/inventory.yaml"
        
        discovery_manager.save_to_file(topology_filename, 'json')
        discovery_manager.save_to_file(inventory_filename, 'yaml')
        
        # Print statistics
        stats = discovery_manager.get_topology_stats()
        
        print("🎉 Discovery completed successfully!")
        print(f"Results saved to:")
        print(f"  - Topology (JSON): {topology_filename}")
        print(f"  - Inventory (YAML): {inventory_filename}")
        print(f"\n📊 Discovery Statistics:")
        print(f"  - Total switches discovered: {stats['total_switches']}")
        print(f"  - Switch types: {stats['switch_types']}")
        print(f"  - Total neighbor connections: {stats['total_neighbors']}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Discovery interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
