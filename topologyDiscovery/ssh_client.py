"""
Shared SSH utility for connecting to network switches.
Provides common SSH connection functionality used by all discovery classes.
"""
import paramiko
import socket
import time
from typing import Optional, Tuple


class SSHClient:
    """
    SSH client utility for connecting to network switches.
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
        self.client = None
        self.shell = None
    
    def connect(self) -> bool:
        """
        Establish SSH connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            return True
            
        except (paramiko.AuthenticationException, 
                paramiko.SSHException,
                socket.timeout,
                socket.error) as e:
            print(f"SSH connection failed to {self.host}: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """
        Close SSH connection and shell session.
        """
        if self.shell:
            self.shell.close()
            self.shell = None
            
        if self.client:
            self.client.close()
            self.client = None
    
    def execute_command(self, command: str, timeout: int = 10) -> Tuple[str, str, int]:
        """
        Execute a single command via SSH.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if not self.client:
            return "", "No SSH connection", 1
            
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            return stdout_data, stderr_data, exit_code
            
        except Exception as e:
            return "", f"Command execution failed: {str(e)}", 1
    
    def start_shell(self) -> bool:
        """
        Start an interactive shell session.
        
        Returns:
            bool: True if shell started successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            self.shell = self.client.invoke_shell()
            time.sleep(1)  # Wait for shell to initialize
            return True
            
        except Exception as e:
            print(f"Failed to start shell: {str(e)}")
            return False
    
    def send_command_to_shell(self, command: str, wait_time: float = 1.0) -> str:
        """
        Send command to interactive shell and return output.
        
        Args:
            command: Command to send
            wait_time: Time to wait for command completion
            
        Returns:
            str: Command output
        """
        if not self.shell:
            return ""
            
        try:
            # Clear any existing output
            if self.shell.recv_ready():
                self.shell.recv(4096)
            
            # Send command
            self.shell.send(command + '\n')
            time.sleep(wait_time)
            
            # Read output
            output = ""
            while self.shell.recv_ready():
                output += self.shell.recv(4096).decode('utf-8')
                
            return output
            
        except Exception as e:
            print(f"Shell command failed: {str(e)}")
            return ""
    
    def is_connected(self) -> bool:
        """
        Check if SSH connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.client:
            return False
            
        try:
            transport = self.client.get_transport()
            return transport is not None and transport.is_active()
        except:
            return False
