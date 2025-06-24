

from discovery.HirschmannDiscovery import HirschmannDiscovery
from discovery.KontorDiscovery import KontorDiscovery
from discovery.LantechDiscovery import LantechDiscovery
from discovery.NomadDiscovery import NomadDiscovery
from discovery.BaseDiscovery import BaseDiscovery


def get_system_interface(system: str = 'unknown') -> BaseDiscovery:
    if system == "hirschmann":
        return HirschmannDiscovery("192.168.1.31", "admin", "admin", 22)
    elif system == "kontor":
        return KontorDiscovery()
    elif system == "lantech":
        return LantechDiscovery()
    elif system == "nomad":
        return NomadDiscovery()
    else:
        return discoverSystem()    
    


def discoverSystem() -> BaseDiscovery:
    # try connect first vendor repeat until success
    # try system info commands until success
    # parse ystem info -> get_system_interface
    print("Info")
    


# Example usage
if __name__ == "__main__":

    # Get the appropriate system interface
    system_interface = get_system_interface("hirschmann")

    # Use the interface
    print("System Info:", system_interface.get_system_info())
    system_interface.connect()
    #command_output = system_interface.executeCommand("echo Hello, World!")
    #print("Command Output:", command_output)
    #parsed_output = system_interface.parseOutput(command_output)
    #print("Parsed Output:", parsed_output)