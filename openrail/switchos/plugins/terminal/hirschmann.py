from ansible.plugins.terminal import TerminalBase

class TerminalModule(TerminalBase):
    def __init__(self, connection):
        super().__init__(connection)

