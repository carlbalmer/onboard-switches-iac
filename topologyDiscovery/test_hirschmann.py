#!/usr/bin/env python3
"""
Test script specifically for Hirschmann switch discovery.
Demonstrates the step-by-step process for a single Hirschmann switch.
"""
import sys
from switch_detector import SwitchDetector
from discovery.HirschmannDiscovery import HirschmannDiscovery


def test_hirschmann_discovery(switch_ip: str):
    """
    Test Hirschmann switch discovery step by step.
    
    Args:
        switch_ip: IP address of the Hirschmann switch
    """
    print("🔍 Hirschmann Switch Discovery Test")
    print("=" * 40)
    print(f"Target Switch IP: {switch_ip}")
    print()
    
    # Step 1: Auto-detect switch type
    print("Step 1: Auto-detecting switch type...")
    detector = SwitchDetector()
    
    vendor, ssh_client, credentials = detector.detect_switch_type(switch_ip)
    
    if not vendor:
        print("❌ Failed to detect switch type")
        return False
    
    if vendor != 'hirschmann':
        print(f"⚠️ Detected {vendor} switch, but this test is for Hirschmann switches")
        if ssh_client:
            ssh_client.disconnect()
        return False
    
    print(f"✅ Detected Hirschmann switch")
    print(f"   Used credentials: {credentials}")
    print()
    
    try:
        # Step 2: Create Hirschmann discovery instance
        print("Step 2: Creating Hirschmann discovery instance...")
        
        discovery = HirschmannDiscovery(
            host=switch_ip,
            username=credentials['username'],
            password=credentials['password']
        )
        
        # Use the existing SSH connection
        discovery.ssh_client = ssh_client
        print("✅ Discovery instance created")
        print()
        
        # Step 3: Get system information
        print("Step 3: Retrieving system information...")
        system_info = discovery.get_system_info()
        
        if 'error' in system_info:
            print(f"❌ Error getting system info: {system_info['error']}")
        else:
            print("✅ System information retrieved:")
            print("   System Information:")
            print("   " + "-" * 30)
            
            for key, value in system_info.items():
                if value:
                    print(f"   {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Step 4: Get interface information
        print("Step 4: Retrieving interface information...")
        interfaces = discovery.get_interface_info()
        
        print(f"✅ Found {len(interfaces)} interfaces:")
        for i, interface in enumerate(interfaces[:5]):  # Show first 5
            print(f"   Interface {i+1}: {interface}")
        if len(interfaces) > 5:
            print(f"   ... and {len(interfaces) - 5} more interfaces")
        print()
        
        # Step 5: Get LLDP neighbor information
        print("Step 5: Retrieving LLDP neighbor information...")
        neighbors = discovery.get_neighbor_info()
        
        print(f"✅ Found {len(neighbors)} LLDP neighbors:")
        for i, neighbor in enumerate(neighbors):
            print(f"   Neighbor {i+1}: {neighbor}")
        print()
        
        # Step 6: Get MAC address table
        print("Step 6: Retrieving MAC address table...")
        mac_table = discovery.get_mac_table()
        
        print(f"✅ Found {len(mac_table)} MAC table entries:")
        for i, entry in enumerate(mac_table[:3]):  # Show first 3
            print(f"   Entry {i+1}: {entry}")
        if len(mac_table) > 3:
            print(f"   ... and {len(mac_table) - 3} more entries")
        print()
        
        # Step 7: Summary
        print("🎉 Discovery completed successfully!")
        print("Summary:")
        print(f"   - Switch Type: Hirschmann")
        print(f"   - Hostname: {system_info.get('hostname', 'Unknown')}")
        print(f"   - Model: {system_info.get('model', 'Unknown')}")
        print(f"   - OS Version: {system_info.get('os_version', 'Unknown')}")
        print(f"   - Serial Number: {system_info.get('serial_number', 'Unknown')}")
        print(f"   - Interfaces: {len(interfaces)}")
        print(f"   - LLDP Neighbors: {len(neighbors)}")
        print(f"   - MAC Table Entries: {len(mac_table)}")
        
        # Step 8: Extract neighbor IPs for further discovery
        if neighbors:
            print("\n🔗 Neighbor IP addresses for further discovery:")
            neighbor_ips = []
            for neighbor in neighbors:
                # Try to extract IP from neighbor info
                for field in ['remote_management_address', 'management_address', 'remote_ip']:
                    if field in neighbor and neighbor[field]:
                        ip = neighbor[field].strip()
                        if is_valid_ip(ip) and ip not in neighbor_ips:
                            neighbor_ips.append(ip)
                            print(f"   - {ip}")
            
            if not neighbor_ips:
                print("   No neighbor IP addresses found in LLDP data")
        
        # Clean up
        discovery.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Error during discovery: {e}")
        if ssh_client:
            ssh_client.disconnect()
        return False


def is_valid_ip(ip: str) -> bool:
    """Basic IP address validation."""
    try:
        parts = ip.split('.')
        return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except:
        return False


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python test_hirschmann.py <switch_ip>")
        print("Example: python test_hirschmann.py 192.168.1.31")
        sys.exit(1)
    
    switch_ip = sys.argv[1]
    
    if not is_valid_ip(switch_ip):
        print(f"❌ Invalid IP address: {switch_ip}")
        sys.exit(1)
    
    success = test_hirschmann_discovery(switch_ip)
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
