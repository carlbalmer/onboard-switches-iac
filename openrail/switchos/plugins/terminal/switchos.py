#
# (c) 2024 OpenRail SwitchOS Collection
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# Python 2.7 compatibility
from ansible.module_utils.six import raise_from

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text, to_bytes
from ansible.plugins.terminal import TerminalBase
from ansible.utils.display import Display

display = Display()


class TerminalModule(TerminalBase):
    """
    Terminal plugin for OpenRail SwitchOS devices
    """

    # Terminal prompt patterns for SwitchOS devices
    terminal_stdout_re = [
        re.compile(br"\(BXP\)>"),
        re.compile(br"\(BXP\)#"),
    ]
    # Error patterns to detect command failures
    terminal_stderr_re = [
        re.compile(br"Error: Invalid command"),
    ]

    def on_open_shell(self):
        """
        Called when the shell is opened. Configure terminal settings for SwitchOS.
        """
        try:
            # Set terminal to non-interactive mode for automation
            self._exec_cli_command(b"terminal length 0")
        except AnsibleConnectionFailure:
            display.display("WARNING: Unable to set terminal length, output may be paginated")

        try:
            # Set terminal width to prevent line wrapping
            self._exec_cli_command(b"terminal width 0")
        except AnsibleConnectionFailure:
            display.display("WARNING: Unable to set terminal width, command responses may be truncated")

        try:
            # Disable terminal prompts and confirmations
            self._exec_cli_command(b"terminal no prompt")
        except AnsibleConnectionFailure:
            display.display("WARNING: Unable to disable prompts, some commands may require confirmation")

    def on_become(self, passwd=None):
        if self._get_prompt().endswith(b'#'):
            return
        
        try:
            self._exec_cli_command(b'enable')
        except AnsibleConnectionFailure as exc:
            raise AnsibleConnectionFailure('unable to become') from exc
    
    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if prompt.strip().endswith(b'(Config)#'):
            self._exec_cli_command(b'exit')

        if prompt.endswith(b'(BXP)#'):
            self._exec_cli_command(b'disable')
        else:
            raise AnsibleConnectionFailure(f'Unexpected prompt: {prompt}')