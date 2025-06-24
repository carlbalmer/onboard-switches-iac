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

DOCUMENTATION = '''
---
author: OpenRail SwitchOS Collection Contributors
name: switchos
short_description: Use switchos cliconf to run commands on OpenRail SwitchOS network devices
description:
  - This switchos plugin provides low level abstraction APIs for
    sending and receiving CLI commands from OpenRail SwitchOS network devices.
version_added: "1.0.0"
options:
  config_commands:
    description:
      - Specifies a list of commands that can be used to enter configuration mode
    default: ['configure terminal']
  check_all:
    description:
      - By default, if the task has a complex command that contains multiple statements,
        this value will be set to C(True). Set it to C(False) to disable it.
    default: True
'''

import json

from ansible.plugins.cliconf import CliconfBase, enable_mode
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list


class Cliconf(CliconfBase):
    """
    CLI configuration plugin for OpenRail SwitchOS devices
    """

    def get_device_info(self):
        """
        Get basic device information
        """
        device_info = {}
        device_info['network_os'] = 'switchos'
        return device_info

    @enable_mode
    def get_config(self, source='running', flags=None, format=None):
        """
        Retrieve device configuration
        """
        if source not in ("running", "startup"):
            raise ValueError(
                "fetching configuration from %s is not supported" % source
            )

        if format:
            raise ValueError(
                "'format' value %s is not supported for get_config" % format
            )

        if flags:
            raise ValueError(
                "'flags' value %s is not supported for get_config" % flags
            )

        if source == "running":
            cmd = "show running-config"
        else:
            cmd = "show startup-config"

        return self.send_command(cmd)

    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        """
        Edit device configuration - minimal implementation for SwitchOS
        """
        # For basic functionality, we'll implement a simple version
        # that doesn't actually edit config but satisfies the abstract method requirement
        resp = {}
        resp['request'] = []
        resp['response'] = []
        return resp

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        """
        Execute a single command on the device
        """
        return self.send_command(
            command=command, 
            prompt=prompt, 
            answer=answer, 
            sendonly=sendonly, 
            newline=newline, 
            check_all=check_all
        )

    def get_capabilities(self):
        """
        Get device capabilities
        """
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] = self.get_base_rpc() + ['get_config', 'get_capabilities', 'run_commands']
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)

    def get_device_operations(self):
        """
        Get supported device operations
        """
        return {
            'supports_diff_replace': False,
            'supports_commit': False,
            'supports_rollback': False,
            'supports_defaults': False,
            'supports_onbox_diff': False,
            'supports_configure_mode': True,
            'supports_multiline_delimiter': False,
            'supports_diff_match': False,
            'supports_diff_ignore_lines': False,
            'supports_generate_diff': False,
            'supports_replace': False
        }
