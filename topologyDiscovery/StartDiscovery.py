from topologyDiscovery.KontorDiscovery import KontorDiscovery
from topologyDiscovery.TopologyDiscovery import SystemInterface


def get_system_interface(system: str) -> SystemInterface:
    return KontorDiscovery()


# Example usage
if __name__ == "__main__":

    # Get the appropriate system interface
    system_interface = get_system_interface("Kontor")

    # Use the interface
    print("System Info:", system_interface.getSystemInfo())
    command_output = system_interface.executeCommand("echo Hello, World!")
    print("Command Output:", command_output)
    parsed_output = system_interface.parseOutput(command_output)
    print("Parsed Output:", parsed_output)