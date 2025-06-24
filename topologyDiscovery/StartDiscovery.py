#!/usr/bin/env python3
"""
Network Discovery Tool - Entry Point
Starts the network discovery process from a seed IP address.
"""
import sys
import argparse
from network_discovery_manager import NetworkDiscoveryManager


def main():
    """Main entry point for the network discovery tool."""
    
    parser = argparse.ArgumentParser(
        description="Network Switch Discovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python StartDiscovery.py 192.168.1.31
  python StartDiscovery.py 192.168.1.31 --depth 5
  python StartDiscovery.py 192.168.1.31 --credentials custom_creds.yaml
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
        import os
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