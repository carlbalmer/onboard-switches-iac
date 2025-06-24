import subprocess

from topologyDiscovery.TopologyDiscovery import SystemInterface

class HirschmannDiscovery(SystemInterface):
    def getSystemInfo(self):
        return "Hirschmann"

    def executeCommand(self, command: str):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout

    def parseOutput(self, output: str):
        return "output"

