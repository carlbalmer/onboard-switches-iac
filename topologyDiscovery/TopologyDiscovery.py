from abc import ABC, abstractmethod
# Interface Class that defines the must have methods for all implementations
class SystemInterface(ABC):
    @abstractmethod
    def getSystemInfo(self):
        pass

    @abstractmethod
    def discoverNeighbors(self, command: str):
        pass

    @abstractmethod
    def parseOutput(self, output: str):
        pass