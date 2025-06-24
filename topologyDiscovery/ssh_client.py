"""
SSH utility using pexpect for connecting to network switches.
Based on the working ssh_command.py implementation.
"""
import pexpect
import time
import re
from typing import Optional, Tuple, Dict, Any


class SSHClient:
    """
    SSH client utility using pexpect for network switches.
    Optimized for interactive switch sessions with prompts and paging.
    """
    
    def __init__(self, host: str, username: str, password: str, port: int = 22, timeout: int = 30):
        """
        Initialize SSH client.
        
        Args:
            host: IP address or hostname
            username: SSH username
            password: SSH password  
            port: SSH port (default: 22)
            timeout: Connection timeout in seconds (default: 30)
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.session = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """
        Establish SSH connection using pexpect.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            print(f"Connecting to {self.username}@{self.host}...")
            
            # Connect via SSH with explicit options
            ssh_cmd = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {self.port} {self.username}@{self.host}'
            self.session = pexpect.spawn(ssh_cmd)
            self.session.timeout = self.timeout
            
            # Handle SSH connection prompts
            print("Waiting for password prompt...")
            i = self.session.expect(['password:', 'Password:', 'yes/no', pexpect.TIMEOUT, pexpect.EOF])
            
            if i == 2:  # Handle "yes/no" prompt for first connection
                print("Accepting host key...")
                self.session.sendline('yes')
                self.session.expect(['password:', 'Password:'])
            elif i == 3:  # Timeout
                print("Connection timeout waiting for password prompt")
                return False
            elif i == 4:  # EOF
                print("Connection closed unexpectedly")
                return False
                
            # Send password
            print("Sending password...")
            self.session.sendline(self.password)
            
            # Wait for the initial system information and prompt
            print("Waiting for login to complete...")
            time.sleep(3)  # Give it time to show system info
            
            # Now wait for the actual command prompt
            try:
                self.session.expect([r'!.*>', r'.*>', r'.*#', r'.*\$', pexpect.TIMEOUT], timeout=10)
                print("Found command prompt")
                self.is_connected = True
                return True
            except pexpect.TIMEOUT:
                print("Timeout waiting for command prompt, but continuing...")
                self.is_connected = True
                return True
                
        except Exception as e:
            print(f"SSH connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close SSH connection."""
        if self.session:
            try:
                self.session.close()
            except:
                pass
            self.session = None
            self.is_connected = False
    
    def execute_command(self, command: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Execute a command using pexpect (returns dict for compatibility).
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Dict with 'success', 'output', 'error' keys
        """
        if not self.is_connected or not self.session:
            return {
                'success': False,
                'output': '',
                'error': 'No SSH connection'
            }
        
        try:
            output = self.send_command_to_shell(command, timeout)
            return {
                'success': True,
                'output': output,
                'error': ''
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def send_command_to_shell(self, command: str, wait_time: float = 3.0) -> str:
        """
        Send command to interactive shell and return output.
        Based on the working ssh_command.py implementation.
        
        Args:
            command: Command to send
            wait_time: Time to wait for command completion
            
        Returns:
            str: Command output
        """
        if not self.is_connected or not self.session:
            return ""
        
        try:
            print(f"Sending command: {command}")
            
            # Send the command
            self.session.sendline(command)
            
            # Collect the command output
            output_lines = []
            start_time = time.time()
            max_wait = max(wait_time * 10, 30)  # At least 30 seconds for long outputs
            
            while time.time() - start_time < max_wait:
                try:
                    # Look for different patterns
                    i = self.session.expect([
                        '\r\n',           # 0: Regular line
                        '--More--',       # 1: More prompt
                        pexpect.TIMEOUT   # 6: Timeout
                    ], timeout=3)
                    
                    if i == 0:  # Regular line
                        line = self.session.before.decode('utf-8', errors='ignore').strip()
                        if line and line != command and not line.startswith(command):
                            output_lines.append(line)
                            print(f"Got line: {line[:80]}...")  # Show first 80 chars
                            
                    elif i == 1:  # More prompt
                        print("Detected 'More' prompt, sending space...")
                        self.session.send(' ')
                        
                    elif i in [2, 3, 4, 5]:  # Back to command prompt
                        print("Back at command prompt, command completed")
                        # Get any remaining output
                        remaining = self.session.before.decode('utf-8', errors='ignore').strip()
                        if remaining and remaining != command and not remaining.startswith(command):
                            output_lines.append(remaining)
                        break
                        
                    elif i == 6:  # Timeout
                        # Check if we have accumulated enough output
                        if output_lines:
                            print("Timeout but got output, continuing...")
                            continue
                        else:
                            print("Timeout with no output")
                            break
                            
                except pexpect.EOF:
                    print("Connection closed during command execution")
                    break
                except Exception as e:
                    print(f"Exception during command execution: {e}")
                    break
            
            # Join all output lines
            full_output = '\n'.join(output_lines)
            print(f"Command completed, got {len(full_output)} characters of output")
            return full_output
            
        except Exception as e:
            print(f"Failed to execute command '{command}': {e}")
            return ""
    
    def start_shell(self) -> bool:
        """
        Start shell (compatibility method - pexpect is already shell-based).
        
        Returns:
            bool: True if shell is ready
        """
        return self.is_connected
    
    def is_connected_check(self) -> bool:
        """
        Check if SSH connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.is_connected and self.session and self.session.isalive()
