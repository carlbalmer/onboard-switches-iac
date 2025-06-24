#!/usr/bin/env python3

import pexpect
import sys
import time

def connect_and_run_command(host, username, password, command):
    try:
        print(f"Connecting to {username}@{host}...")
        
        # Connect via SSH with explicit options
        ssh_cmd = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {username}@{host}'
        child = pexpect.spawn(ssh_cmd)
        child.timeout = 30
        
        # Handle SSH connection prompts
        print("Waiting for password prompt...")
        i = child.expect(['password:', 'Password:', 'yes/no', pexpect.TIMEOUT, pexpect.EOF])
        
        if i == 2:  # Handle "yes/no" prompt for first connection
            print("Accepting host key...")
            child.sendline('yes')
            child.expect(['password:', 'Password:'])
        elif i == 3:  # Timeout
            print("Connection timeout waiting for password prompt")
            return None
        elif i == 4:  # EOF
            print("Connection closed unexpectedly")
            return None
            
        # Send password
        print("Sending password...")
        child.sendline(password)
        
        # Wait for the initial system information and prompt
        print("Waiting for login to complete...")
        time.sleep(5)  # Give it time to show system info
        
        # Now wait for the actual command prompt
        try:
            child.expect([r'!.*>', pexpect.TIMEOUT], timeout=10)
            print("Found command prompt")
        except pexpect.TIMEOUT:
            print("Timeout waiting for command prompt, continuing anyway...")
        
        print(f"Sending command: {command}")
        
        # Send the command
        child.sendline(command)
        
        # Now collect the actual command output
        output_lines = []
        start_time = time.time()
        
        while time.time() - start_time < 45:  # 45 second timeout for long output
            try:
                # Look for line endings
                i = child.expect(['\r\n', '--More--', r'!.*>', pexpect.TIMEOUT], timeout=3)
                
                if i == 0:  # Regular line
                    line = child.before.decode('utf-8').strip()
                    if line and line != command:  # Don't include the command echo
                        output_lines.append(line)
                        print(f"Got line: {line}")
                        
                elif i == 1:  # More prompt
                    print("Detected 'More' prompt, sending space...")
                    child.send(' ')
                    
                elif i == 2:  # Back to command prompt
                    print("Back at command prompt, command completed")
                    # Get any remaining output
                    remaining = child.before.decode('utf-8').strip()
                    if remaining and remaining != command:
                        output_lines.append(remaining)
                    break
                    
                elif i == 3:  # Timeout
                    # Check if we might be at a prompt
                    print("Timeout - checking for prompt...")
                    continue
                    
            except pexpect.EOF:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Exception during output collection: {e}")
                break
        
        child.close()
        return '\n'.join(output_lines)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: script.py <host> <username> <password> <command>")
        sys.exit(1)
        
    host = sys.argv[1]
    username = sys.argv[2] 
    password = sys.argv[3]
    command = sys.argv[4]
    
    output = connect_and_run_command(host, username, password, command)
    if output:
        print("=== COMMAND OUTPUT ===")
        print(output)
    else:
        print("Failed to get output")
        sys.exit(1)
