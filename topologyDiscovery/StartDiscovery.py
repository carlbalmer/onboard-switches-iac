from topologyDiscovery.KontorDiscovery import KontorDiscovery
from topologyDiscovery.TopologyDiscovery import SystemInterface


def get_system_interface(os_type: str) -> SystemInterface:
    return KontorDiscovery()


# Example usage
if __name__ == "__main__":
    import sys

    # Determine the OS type (for demonstration purposes)
    os_type = platform.system()  # This will return 'Linux', 'Windows', etc.

    # Get the appropriate system interface
    system_interface = get_system_interface(os_type)

    # Use the interface
    print("System Info:", system_interface.getSystemInfo())
    command_output = system_interface.executeCommand("echo Hello, World!")
    print("Command Output:", command_output)
    parsed_output = system_interface.parseOutput(command_output)
    print("Parsed Output:", parsed_output)