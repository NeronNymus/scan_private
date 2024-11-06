#!/usr/bin/env python3

# This script is intended to run primarily on Windows systems, 
# subtituing scan_private2.sh as nmap caller, that works well on Linux systems,
# but not in Windows.

import os
import nmap
import socket
import datetime
import ipaddress
import subprocess

# Personal packages
from utils.colors import Colors


def get_private_ip():
    # Obtain the local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Verify if it's within a private IP range
    ip = ipaddress.ip_address(local_ip)
    if ip.is_private and not local_ip.startswith("127."):
        private_ip_prefix = '.'.join(local_ip.split('.')[:4])
        return private_ip_prefix
    else:
        print("[x] Quitting because private range resolves to 127.0.0.0/24 or a public IP")
        return None


def get_private_network():
    # Get the local IP and subnet mask
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Check if it's a private IP and calculate network range
    ip = ipaddress.ip_interface(f"{local_ip}/24")  # Temporary mask
    if ip.is_private and not local_ip.startswith("127."):
        # Dynamically calculate the actual network range
        network = ip.network
        return str(network)
    else:
        print("[x] Quitting because private range resolves to 127.0.0.0/24 or a public IP")
        return None


def scan_nmap(scan_dir):
    # Get the private IP range
    private_ip = get_private_ip()
    if not private_ip:
        return

    #private_range = f"{private_ip}.0/24"
    private_range = get_private_network()

    # Create timestamped scan result filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    print(Colors.BOLD_WHITE + f"[!] Start private network scan on " + Colors.ORANGE + f" {private_range} " + Colors.R + "at " + Colors.CYAN + f"{timestamp}" + Colors.R)
    os.makedirs(scan_dir, exist_ok=True)
    scan_result = os.path.join(scan_dir, f"{timestamp}_nmap.xml")

    # Initialize nmap and perform the scan
    nm = nmap.PortScanner()
    nm.scan(hosts=private_range, arguments="-PR -sn --max-retries 5")
    
    # Retrieve the scan results in XML format
    xml_output = nm.get_nmap_last_output().decode()

    # Write the XML output to the file
    with open(scan_result, 'w') as f:
        f.write(xml_output)
    
    print(Colors.GREEN + "\n[!] Nmap scan results saved into:\n" + Colors.ORANGE +  f"{scan_result}" + Colors.R)
    return scan_result


def load_data_db(scan_result):
    # Load data into database using an external Python script
    import_script = os.path.join(project_path, "import_nmap.py")
    subprocess.run(f"python {import_script} -iL {scan_result}", shell=True)

    print(Colors.GREEN + "\n[!] Results saved into the database!" + Colors.R)


if __name__ == "__main__":
    # Example usage
    project_path = os.getcwd()  # Execute it in the current project path
    scan_dir = os.path.join(project_path,"scans\\active3")
    scan_result = scan_nmap(scan_dir)
    
    load_data_db(scan_result)
