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

# Personal packages
from backend.backend import load_env_vars
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
        print(f"[!] IP:\t{ip}\t{local_ip}")
        print("[x] Quitting because private range resolves to 127.0.0.0/24 or a public IP")
        return None


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
                    if ip_obj.is_private and not ip.startswith("127."):
                        # Dynamically calculate the actual network range
                        network = ip_obj.network
                        print(Colors.BOLD_WHITE + f"[+] Found private IP: " + Colors.ORANGE +  f"{ip}" + Colors.BOLD_WHITE + " on interface " + Colors.GREEN + f"{iface}" + Colors.R)
                        return str(network)
                except ValueError:
                    continue  # Skip invalid addresses

    print("[x] No valid private IP address found on this machine.")
    return None

def scan_nmap(scan_dir):
    # Get the private IP range
    #private_ip = get_private_ip()
    #if not private_ip:
    #    return

    #private_range = f"{private_ip}.0/24"
    private_range = get_private_network()
    print(f"[!] Solving to {private_range}")

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


    #print("DB_HOST:", os.getenv("DB_HOST"))
    #print("DB_NAME:", os.getenv("DB_NAME"))
    #print("DB_USER:", os.getenv("DB_USER"))
    #print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))
    #print("DB_PORT:", os.getenv("DB_PORT"))


    #sys.exit(0)
    # Example usage

    if os.name == 'posix':
        project_path = os.getcwd()  # Execute it in the current project path
    elif os.name == 'nt':
        project_path = "C:\\Users\\jesus\\Other\\scan_private" # Hardcoded path

    scan_dir = os.path.join(project_path,"scans/active3")
    scan_result = scan_nmap(scan_dir)
    
    load_data_db(scan_result)
