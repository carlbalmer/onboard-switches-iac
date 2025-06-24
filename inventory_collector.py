#!/usr/bin/env python3

import logging
import random
import socket
import subprocess
import sys
import time
import os
from contextlib import suppress

logger = logging.getLogger(__name__)

ETH_P_ALL = 0x0003


def set_promisc():
    for _, if_name in socket.if_nameindex():
        if if_name == "lo":
            continue

        subprocess.call(["ip", "link", "set", if_name, "promisc", "on"])


def collect_lldp(timeout: float = 30.0):
    raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(ETH_P_ALL))
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    timeout += time.monotonic()
    while time.monotonic() < timeout:
        packet, options = raw_socket.recvfrom(0xffff)
        if_name = options[0]

        offset = 14  # start of data
        vlans = []
        while True:
            # check if ether type is 802.1q
            ether_type = int.from_bytes(packet[offset - 2:offset], "big")
            if ether_type != 0x8100:
                break
            vlans.append(int.from_bytes(packet[offset:offset + 2] & 0x0fff, "big"))
            offset += 4

        if ether_type == 0x88cc:
            chassis_ids = []
            names = []
            mgmt_ips = []
            while offset < len(packet):
                tlv_header = int.from_bytes(packet[offset:offset + 2], "big")
                lldp_type = tlv_header >> 9
                lldp_length = tlv_header & 0x1ff
                lldp_data = packet[offset + 2:offset + 2 + lldp_length]

                if lldp_type in [1]:
                    chassis_ids.append(lldp_data)
                elif lldp_type in [4, 5, 6]:
                    names.append(lldp_data.decode("utf-8", errors="ignore"))
                elif lldp_type in [8]:
                    ip_data = lldp_data[1:1 + lldp_data[0]]
                    mgmt_ips.append((ip_data[0], ip_data[1:]))
                offset += 2 + lldp_length

            yield (if_name, chassis_ids, names, mgmt_ips)

    raw_socket.close()


def check_arp(if_name: str, target_ip: bytes, timeout: float = 5.0) -> bytes | None:
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((if_name, socket.SOCK_RAW))
    own_mac = sock.getsockname()[4]
    packet = (b"\xff\xff\xff\xff\xff\xff" +  # broadcast dst
              own_mac +
              b"\x08\x06" +  # ether type arp
              b"\x00\x01" +  # hw_type: ethernet
              b"\x08\x00" +  # p_type: ipv4
              b"\x06" +  # hw_len: 6
              b"\x04" +  # p_len: 4
              b"\x00\x01" +  # arp op: request
              own_mac +
              b"\x00\x00\x00\x00" +
              b"\x00\x00\x00\x00\x00\x00" + # target mac
              target_ip)
    sock.send(packet)

    timeout += time.monotonic()
    while time.monotonic() < timeout:
        packet, _ = sock.recvfrom(0xffff)
        if packet[0:6] == own_mac and \
           packet[12:14] == b"\x08\x06" and \
           packet[14:22] == b"\x00\x01\x08\x00\x06\x04\x00\x02" and \
           packet[28:32] == target_ip:
            return packet[22:28]
    return None


def main():
    logging.basicConfig(level=logging.INFO)

    found_chassis = set()

    for if_name, chassis_ids, names, mgmt_ips in collect_lldp():
        chassis_id = ":".join(f"{n:02x}" for n in b"".join(sorted(chassis_ids)))
        if chassis_id in found_chassis:
            continue
        found_chassis.add(chassis_id)

        for ip_type, ip_raw in mgmt_ips:
            if ip_type != 1:
                continue

            try:
                ip_parsed = socket.inet_ntop(socket.AF_INET, ip_raw)
            except (KeyError, IndexError):
                continue

            break
        else:
            logger.warning("Found no valid IPv4 for %s", chassis_id)
            continue

        logger.info("Found Switch %s (%s) with IP %s on %s",
                    chassis_id, ";".join(names), ip_parsed, if_name)

        # look for an unused ip in this network
        i = 3
        while i > 0:
            last_octet = random.randint(0, 255)
            own_ip = ip_raw[:3] + bytes([last_octet])
            if check_arp(if_name, own_ip) is None:
                break
            i -= 1
        else:
            logger.warning("Unable to find unused IP-Address in %s/24",
                           ip_parsed)
            continue

        own_ip_parsed = socket.inet_ntop(socket.AF_INET, own_ip)
        logger.info("Will configure %s/24 for %s",
                    own_ip_parsed, if_name)
        subprocess.call(["ip", "addr", "add", f"{own_ip_parsed}/24", "dev", if_name])

        logger.info("Check if we can reach %s using ICMP ping", ip_parsed)
        if subprocess.call(["ping", "-c", "2", ip_parsed], stdout=subprocess.DEVNULL) != 0:
            logger.warning("%s does not respond to ICMP ping", ip_parsed)

        fetch_lldp_data(ip_parsed)


def fetch_lldp_data(ip_addr):
    # TODO build map by lldp
    pass


if __name__ == "__main__":
    if os.geteuid() != 0:
        logger.error("This script requires root privileges to setup networking")
        sys.exit(1)

    set_promisc()

    main()
