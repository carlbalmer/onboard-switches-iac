from ansible.plugins.terminal import TerminalBase

import re

class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br">"),
    ]

    terminal_stderr_re = [
        re.compile(br"Invalid parameter"),
    ]

    def on_open_shell(self):
        pass

    def on_become(self, passwd=None):
        return None
        
    def on_unbecome(self):
        return None
