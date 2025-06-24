from ansible.plugins.terminal import TerminalBase

class HirschmannTerminal(TerminalBase):
    def __init__(self, connection):
        super().__init__(connection)

