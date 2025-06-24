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
        re.compile(br"[\r\n]?[\w\+\-\.:\/\[\]]+(?:\([^\)]+\)){0,3}(?:[>#\$]) ?$")
    ]

    # Error patterns to detect command failures
    terminal_stderr_re = [
        re.compile(br"% ?Error"),
        re.compile(br"^% \w+", re.M),
        re.compile(br"% ?Invalid command"),
        re.compile(br"% ?Unknown command"),
        re.compile(br"[\r\n%] Bad passwords"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found"),
        re.compile(br"'[^']' +returned error code: ?\d+"),
        re.compile(br"Bad mask", re.I),
        re.compile(br"% ?(\S+) ?overlaps with ?(\S+)", re.I),
        re.compile(br"[%\S] ?Error: ?[\s]+", re.I),
        re.compile(br"[%\S] ?Warning: ?[\s]+", re.I),
        re.compile(br"Command authorization failed"),
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
        """
        Handle privilege escalation to enable mode
        """
        cmd = {u"command": u"enable"}
        if passwd:
            cmd[u"prompt"] = to_text(
                r"[\r\n]?(?:.*)?[Pp]assword: ?$", errors="surrogate_or_strict"
            )
            cmd[u"answer"] = passwd
            cmd[u"prompt_retry_check"] = True
        
        try:
            self._exec_cli_command(
                to_bytes(json.dumps(cmd), errors="surrogate_or_strict")
            )
            prompt = self._get_prompt()
            if prompt is None or not prompt.endswith(b"#"):
                raise AnsibleConnectionFailure(
                    "failed to elevate privilege to enable mode, still at prompt [%s]"
                    % prompt
                )
        except AnsibleConnectionFailure as e:
            prompt = self._get_prompt()
            raise_from(AnsibleConnectionFailure(
                "unable to elevate privilege to enable mode, at prompt [%s] with error: %s"
                % (prompt, e.message if hasattr(e, 'message') else str(e))
            ), e)

    def on_unbecome(self):
        """
        Handle dropping privileges from enable mode
        """
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if b"(config" in prompt:
            # Exit configuration mode first
            self._exec_cli_command(b"end")
            self._exec_cli_command(b"disable")
        elif prompt.endswith(b"#"):
            # Exit enable mode
            self._exec_cli_command(b"disable")
