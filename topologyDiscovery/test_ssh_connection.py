#!/usr/bin/env python3
"""
Quick test script to test SSH connection to Hirschmann switch
Tests connection to 192.168.1.31 with admin/admin credentials
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ssh_client import SSHClient

def test_hirschmann_ssh():
    """Test SSH connection to Hirschmann switch and run 'show system info'"""
    
    # Connection parameters
    host = "192.168.1.31"
    username = "admin"
    password = "admin"
    
    print(f"🔗 Testing SSH connection to Hirschmann switch")
    print(f"   Host: {host}")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password)}")
    print("=" * 60)
    
    ssh_client = None
    try:
        # Create SSH client
        print("📡 Creating SSH client...")
        ssh_client = SSHClient(host, username, password, timeout=15)
        
        # Test connection
        print("🔌 Attempting SSH connection...")
        if ssh_client.connect():
            print("✅ SSH connection successful!")
            
            # Test single command execution
            print("\n📋 Executing: 'show system info'")
            print("-" * 50)
            
            stdout, stderr, exit_code = ssh_client.execute_command("show system info", timeout=10)
            
            if exit_code == 0 and stdout:
                print("✅ Command executed successfully!")
                print(f"Exit code: {exit_code}")
                print("\n📄 Command Output:")
                print("=" * 60)
                print(stdout)
                print("=" * 60)
                
                # Check if it's a Hirschmann switch
                output_lower = stdout.lower()
                if any(keyword in output_lower for keyword in ['hirschmann', 'hios', 'bobcat', 'system information']):
                    print("\n🎯 SUCCESS: Confirmed Hirschmann switch detected!")
                    print("   Found Hirschmann-specific keywords in output")
                else:
                    print("\n❓ Output received but no Hirschmann keywords found")
                    
            else:
                print(f"❌ Command failed!")
                print(f"   Exit code: {exit_code}")
                if stderr:
                    print(f"   Error: {stderr}")
                if stdout:
                    print(f"   Stdout: {stdout}")
                
                # Try alternative commands
                print("\n🔄 Trying alternative commands...")
                alternative_commands = [
                    "show version",
                    "system info", 
                    "show system",
                    "help"
                ]
                
                for cmd in alternative_commands:
                    print(f"\n   Testing: '{cmd}'")
                    alt_stdout, alt_stderr, alt_exit = ssh_client.execute_command(cmd, timeout=5)
                    
                    if alt_exit == 0 and alt_stdout:
                        print(f"   ✅ '{cmd}' succeeded!")
                        print(f"   Output preview: {alt_stdout[:150]}...")
                        break
                    else:
                        print(f"   ❌ '{cmd}' failed (exit: {alt_exit})")
            
            # Test interactive shell mode
            print("\n🐚 Testing interactive shell mode...")
            if ssh_client.start_shell():
                print("✅ Interactive shell started")
                
                # Send command via shell
                shell_output = ssh_client.send_command_to_shell("show system info", 3.0)
                
                if shell_output:
                    print("✅ Shell command executed!")
                    print(f"Shell output preview: {shell_output[:200]}...")
                else:
                    print("❌ No output from shell command")
            else:
                print("❌ Failed to start interactive shell")
                
        else:
            print("❌ SSH connection failed!")
            print("   Check if:")
            print("   - Switch IP is reachable")
            print("   - Credentials are correct")
            print("   - SSH is enabled on the switch")
            
    except Exception as e:
        print(f"🚨 Exception during SSH test: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        
    finally:
        # Clean up connection
        if ssh_client:
            print("\n🔌 Closing SSH connection...")
            ssh_client.disconnect()
            print("✅ Connection closed")

if __name__ == "__main__":
    print("🧪 SSH Client Test - Hirschmann Switch")
    print("🎯 Target: 192.168.1.31 (admin/admin)")
    print("📋 Command: show system info")
    print()
    
    test_hirschmann_ssh()
    
    print("\n✨ SSH test completed!")
