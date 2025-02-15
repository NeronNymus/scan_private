#!/usr/bin/env python3

# This script is intended to run primarily on Windows and Linux systems, avoiding the use of nmap

import os
import time
import psutil
import socket
import getpass
import psycopg2
import ipaddress
from datetime import datetime
from scapy.all import ARP, Ether, srp

# Database Configuration (Move these to the top)
DB_HOST = "34.204.78.186"
DB_PORT = 2356
DB_NAME = "scan_private"
DB_USER = "networker"
DB_PASSWORD = "4etv1RybgDk3"

def get_private_ip():
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
    interfaces = psutil.net_if_addrs()
    
    for iface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address
                try:
                    ip_obj = ipaddress.ip_interface(f"{ip}/24")
                    if ip_obj.is_private and not ip.startswith("127.") and not ip.startswith("172."):
                        network = ip_obj.network
                        print(f"[+] Found private IP: {ip} on interface {iface}")
                        return str(network)
                except ValueError:
                    continue

    print("[x] No valid private IP address found on this machine.")
    return None

def scan_network():
    private_range = get_private_network()
    if not private_range:
        return None

    print(f"[!] Scanning {private_range}")
    active_hosts = []
    try:
        arp = ARP(pdst=private_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        result = srp(packet, timeout=2, verbose=False)[0]

        for sent, received in result:
            active_hosts.append((received.psrc, received.hwsrc))


    except Exception as e:
        print(f"[x] Error occurred while scanning the network: {e}")
        return None

    return active_hosts  # Ensure scan results are returned


# Function for getting the alias and mac_vendor from the 'mac_aliases' table
def get_mac_alias(conn, mac_address):
    if not conn:
        return None, None  # Ensure both values are always returned

    query = """
        SELECT alias, mac_vendor
        FROM mac_aliases
        WHERE mac_address = %s;
    """
    cursor = conn.cursor()
    cursor.execute(query, (mac_address,))
    result = cursor.fetchone()
    cursor.close()

    return result if result else (None, None)  # Ensure return values

# Function for loading scan results into the database
def load_data_db(scan_results):
    if not scan_results:
        print("[x] No scan results to load.")
        return
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        scanned_by = getpass.getuser()
        execution_date = datetime.now()

        insert_query = """
        INSERT INTO scan_results (ipv4_address, mac_address, mac_vendor, alias, scanned_by, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        for ip, mac in scan_results:
            mac = mac.upper()  # Standardize MAC format
            alias, mac_vendor = get_mac_alias(conn, mac)
            print(f"{ip}\t{mac}\t{mac_vendor}\t{alias}\t{scanned_by}\t{execution_date}\n")
            
            cursor.execute(insert_query, (ip, mac, mac_vendor, alias, scanned_by, execution_date))

        conn.commit()
        cursor.close()
        conn.close()
        print("[+] Scan results successfully imported into the database.")

    except psycopg2.Error as e:
        print(f"[x] Database error: {e}")



if __name__ == "__main__":

    while True:
        scan_results = scan_network()

        if scan_results:
            load_data_db(scan_results)
        time.sleep(60)
