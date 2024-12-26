#!/usr/bin/env python3

# This script is intended to run primarily on Windows systems, 
# subtituing scan_private2.sh as nmap caller, that works well on Linux systems,
# but not in Windows.

import os
import sys
import nmap
import socket
import psutil
import datetime
import ipaddress
import subprocess
from datetime import datetime

# Personal packages
from backend.backend import load_env_vars
from utils.colors import Colors


def get_private_ip():
    # Obtain the local IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        private_ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        print(f"Error occurred: {e}")
        private_ip = None

    return private_ip

def get_private_network():
    # Get all network interfaces and their addresses
    interfaces = psutil.net_if_addrs()
    
    for iface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # Only consider IPv4 addresses
                ip = addr.address
                try:
                    # Check if it's a private IP and not a loopback
                    ip_obj = ipaddress.ip_interface(f"{ip}/24")  # Temporary mask
                    if ip_obj.is_private and not ip.startswith("127.") and not ip.startswith("172."):
                        # Dynamically calculate the actual network range
                        network = ip_obj.network
                        print(Colors.BOLD_WHITE + f"[+] Found private IP: " + Colors.ORANGE +  f"{ip}" + Colors.BOLD_WHITE + " on interface " + Colors.GREEN + f"{iface}" + Colors.R)
                        return str(network)
                except ValueError:
                    continue

    print("[x] No valid private IP address found on this machine.")
    return None

def scan_nmap(scan_dir):
    # Get the private IP range
    #private_ip = get_private_ip()
    #if not private_ip:
    #    return

    #private_range = f"{private_ip}.0/24"
    private_range = get_private_network()
    print(Colors.GREEN + f"[!] Solving to {private_range}" + Colors.R)

    # Create timestamped scan result filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
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

    filename = "exports2"
    load_env_vars(filename)

    # Example usage
    if os.name == 'posix':
        project_path = os.getcwd()  # Execute it in the current project path
    elif os.name == 'nt':
        project_path = "C:\\Users\\jesus\\Other\\scan_private" # Hardcoded path
        #project_path = "C:\\Users\\Public\\Other\\scan_private" # Hardcoded path
        os.makedirs(project_path, exist_ok=True)

    test_dir = os.path.join(project_path,"scans/active3")
    test_path = os.path.join(test_dir,"test1")

    execution_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(test_path, 'a') as file:
        print(f"Logged: {execution_date}\tinto {test_path}")
        file.write(f"{execution_date}\n")

    #scan_dir = os.path.join(project_path,"scans/active3")
    #scan_result = scan_nmap(scan_dir)
    
    #load_data_db(scan_result)
