from ansible.errors import AnsibleFilterError


class FilterModule(object):
    def filters(self):
        return {"parse_vlan_ports_table": self.parse_vlan_ports_table}

    def parse_vlan_ports_table(self, stdout_lines):
        print("Parsing VLAN ports table...")
        print("Input lines:", stdout_lines)
        # Find the header line with port numbers
        port_line = None
        for line in stdout_lines:
            if line.strip().startswith("VLAN ID"):
                port_line = line
                break
        if not port_line:
            raise AnsibleFilterError("Could not find port header in output")

        # Extract port numbers (as string indices)
        # Example: "VLAN ID  Port: 1234567890123456789012345678"
        port_numbers = []
        port_index = port_line.find(":")
        if port_index == -1:
            raise AnsibleFilterError("Malformed port header line")
        port_digits = port_line[port_index + 1 :].strip()
        for i, c in enumerate(port_digits):
            if c.isdigit():
                port_numbers.append(str(i + 1))  # Port numbers are 1-based

        ports_to_vlans = {p: [] for p in port_numbers}
        vlans_to_ports = {}

        # Parse VLAN membership lines
        for line in stdout_lines:
            if line.strip() == "" or not line.strip()[0].isdigit():
                continue
            # Example: "      8        -T-T-----UUUU----------U---T"
            parts = line.split()
            if len(parts) < 2:
                continue
            vlan_id = parts[0]
            membership = parts[-1]
            vlans_to_ports[vlan_id] = []
            for idx, status in enumerate(membership):
                if idx >= len(port_numbers):
                    break
                if status in ("T", "U"):  # Tagged or Untagged
                    port = port_numbers[idx]
                    ports_to_vlans[port].append(vlan_id)
                    vlans_to_ports[vlan_id].append(port)
        return {"ports_to_vlans": ports_to_vlans, "vlans_to_ports": vlans_to_ports}
