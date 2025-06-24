from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

class ActionModule(ActionBase):
    """
    Simple hello world action plugin for testing
    """
    
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        
        # Get custom message if provided
        message = self._task.args.get('message', 'Hello World!')
        
        # Display message for debugging
        display.v(f"hello_world plugin executing with message: {message}")
        
        result = {
            "changed": False,
            "msg": message,
            "plugin": "openrail.switchos.hello_world",
            "success": True
        }
        
        return result
