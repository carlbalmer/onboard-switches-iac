from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import json

from itertools import chain

from ansible.module_utils._text import to_bytes, to_text
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode

DOCUMENTATION = """
---
name: lantech
short_description: Use lantech cliconf to run command on Lantech BXP platform
description:
  - This lantech plugin provides low level abstraction apis for
    sending and receiving CLI commands from Lantech TPES-6616XT network devices.
"""


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'lantech'

        reply = self.get('System Configuration')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        match = re.search(r'^Name\s+(.+)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    @enable_mode
    def get_config(self, source='running', flags=None, format='text'):
        pass

    @enable_mode
    def edit_config(self, command) -> None:
        pass

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)
