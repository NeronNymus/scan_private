#!/usr/bin/env python3

# Script for importing nmap xml results into the database.
# Execution example:
# python3 import_nmap.py -iL /home/archenemy/Bash/scan_private/scans/active/2024-06-21-12:43:53_nmap.xml -t 1

import os
import gc
import sys
import getpass
import argparse
import psycopg2
import xml.etree.ElementTree as ET
from datetime import datetime
from natsort import natsorted

# Personal packages
#from backend.backend import start_pool, connect_to_database, query, conn_simple
from backend.backend import query, conn_simple, load_env_vars
from utils.colors import Colors


# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Script for loading the scan_private results into the database.")
    parser.add_argument("-iL", "--ip_list", help="\t\tPath to a file containing the nmap results to import in xml format.")
    parser.add_argument("-xB", "--xml_bulk", help="\t\tPath to a file containing the paths to nmap results to import in xml format.")
    parser.add_argument("-t", "--threads", type=int, help="\t\tNumber of threads for concurrent connection to the database.")
    return parser.parse_args()


def exit_gracefully():
    print("\n\n[!] Exiting gracefully...")

    # If there are active connections, close it
    gc.collect()
    sys.exit(0)


insert_list = []   # Global list for tracking the data to be inserted

def load_file(conn, file_name, cont, insert_sql):
    global insert_list

    scanned_by = getpass.getuser() # Get the current user

    timestamp = os.path.getmtime(file_name)
    # Convert the timestamp to a datetime object
    dt_object = datetime.fromtimestamp(timestamp)

    # Format the datetime object to the desired string format (without seconds)
    formatted_timestamp = dt_object.strftime('%Y-%m-%d %H:%M:%S')
    print(Colors.CYAN+ f"[{cont}] Database timestamp: " + Colors.ORANGE + f"{formatted_timestamp}\n" + Colors.R)

    # Return known hosts from database
    hosts = known_hosts(conn)

    # Return known alias from the database
    #alias_dict = known_alias(conn)

    
    check_exists_sql = """
    SELECT 1 FROM scan_results
    WHERE ipv4_address = %(ipv4_address)s
      AND mac_address = %(mac_address)s
      AND timestamp = %(timestamp)s::timestamp;
    """

    # Process XML formatted data
    tree = ET.parse(file_name)
    root = tree.getroot()


    for host in root.findall('host'):
        ipv4_address = host.find('address[@addrtype="ipv4"]').attrib['addr']
        mac_address_elem = host.find('address[@addrtype="mac"]')

        if mac_address_elem is not None:
            mac_address = mac_address_elem.attrib.get('addr', '')
            mac_vendor = mac_address_elem.attrib.get('vendor', '')
        else:
            mac_address = ''
            mac_vendor = ''

        status = host.find('status').attrib['state']
        reason = host.find('status').attrib.get('reason', '')
        srtt_elem = host.find('times')
        srtt = int(srtt_elem.attrib.get('srtt', 0)) if srtt_elem is not None else 0
        rttvar = int(srtt_elem.attrib.get('rttvar', 0)) if srtt_elem is not None else 0

        # Retrieve the alias from the database
        alias = ""
        mac_vendor_fetched = ""
        result = get_mac_alias(conn, mac_address)

        if result is not None:
            alias, mac_vendor_fetched = result

        # If not mac vendor, try to fetch it from the 
        if mac_vendor == '':
            mac_vendor = mac_vendor_fetched

        data_to_insert = {
            "ipv4_address": ipv4_address,
            "mac_address": mac_address,
            "mac_vendor": mac_vendor,
            "status": status,
            "reason": reason,
            "srtt": srtt,
            "rttvar": rttvar,
            "timestamp": formatted_timestamp,
            "alias": alias,
            "scanned_by": scanned_by
        }

        if not record_exists(conn, check_exists_sql, data_to_insert):
            insert_list.append(data_to_insert)
            print(f"[{len(insert_list)}] insertion appended.")
            #print(data_to_insert)
        else:
            #print(Colors.BOLD_WHITE + f"[{cont}] Record for {ipv4_address} with MAC {mac_address} already exists, skipping..." + Colors.R)
            print(Colors.BOLD_WHITE + f"[{cont}] Skipping..." + Colors.R)

        cont += 1



# Function to check if a record already exists
def record_exists(conn, check_sql, data):
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute(check_sql, data)
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


# Function to determine known hosts
def known_hosts(conn):
    if not conn:
        return

    # This query creates a dictionary
    dict_query = f"""SELECT DISTINCT ON (ipv4_address) ipv4_address, mac_address, mac_vendor
                FROM scan_results
                ORDER BY ipv4_address, id;
                """

    # Retrieve the dictionary
    dictionary = query(conn, dict_query)
    dictionary = natsorted(dictionary)

    return dictionary


# Function to retrieve the aliases from 'mac_aliases' table
def known_alias(conn):
    if not conn:
        return

    # This query creates a dictionary from 'mac_aliases'
    dict_query = f"""SELECT DISTINCT ON (mac_address) mac_address, alias
                FROM mac_aliases
                ORDER BY mac_address;
                """

    # Retrieve the dictionary
    dictionary = query(conn, dict_query)
    dictionary = natsorted(dictionary)

    return dictionary


# Function for getting the alias from the 'mac_aliases' table
def get_mac_alias(conn, mac_address):
    if not conn:
        return

    # This query creates a dictionary from 'mac_aliases'
    dict_query = """
        SELECT alias, mac_vendor
        FROM mac_aliases
        WHERE mac_address = %s;
    """
    cursor = conn.cursor()
    cursor.execute(dict_query, (mac_address,))
    result = cursor.fetchone()
    cursor.close()
    return result



# Function that returns an index
def find_index_by_ipv4(hosts, ipv4_address):
    for index, host in enumerate(hosts):
        if host[0] == ipv4_address:
            return index
    return None


# Inserting bulk of data into the database
def insert_bulk(conn, insert_list, insert_sql):
    cursor = None
    try:
        # Create a cursor
        cursor = conn.cursor()

        # Loop through the list and execute all insert statements
        cont = 1
        for data_to_insert in insert_list:
            cursor.execute(insert_sql, data_to_insert)

            print(f"[{cont}] Data inserted:\t"
                  f"ipv4_address: {data_to_insert['ipv4_address']}\t"
                  f"mac_address: {data_to_insert['mac_address']}\t"
                  f"mac_vendor: {data_to_insert['mac_vendor']}\t"
                  f"alias: {data_to_insert['alias']}\t"
                  f"scanned_by: {data_to_insert['scanned_by']}")
            cont += 1

        # Commit the transaction after all inserts are done
        conn.commit()

    except psycopg2.Error as e:
        # If there is an error, roll back the transaction
        conn.rollback()
        print(f"[x] Error inserting records: \n{e}")
        sys.exit(1)

    finally:
        # Close the cursor
        if cursor:
            cursor.close()


# Function to load a registry
def insert_registry(conn, data_to_insert, insert_sql, cont):

    cursor = None
    try:
        # Create a cursor
        cursor = conn.cursor()

        # Execute the insert statement
        cursor.execute(insert_sql, data_to_insert)

        # Commit the transaction
        conn.commit()
        
        print(f"[{cont}] Data inserted:\t"
              f"ipv4_address: {data_to_insert['ipv4_address']}\t"
              f"mac_address: {data_to_insert['mac_address']}\t"
              f"mac_vendor: {data_to_insert['mac_vendor']}\t"
              f"alias: {data_to_insert['alias']}")
        cont += 1

    except psycopg2.Error as e:
        print(f"[x] Error inserting record: \n{e}")
        sys.exit(1)

    finally:
        # Close the cursor and connection
        cursor.close()


if __name__ == "__main__":

    # Receive the arguments
    args = parse_arguments()

    insert_sql = """
    INSERT INTO scan_results 
    (ipv4_address, mac_address, mac_vendor, status, reason, srtt, rttvar, timestamp, alias, scanned_by) 
    VALUES 
    (%(ipv4_address)s, %(mac_address)s, %(mac_vendor)s, %(status)s, %(reason)s, %(srtt)s, %(rttvar)s, %(timestamp)s::timestamp, %(alias)s, %(scanned_by)s);
    """

    filename = "exports3.sh"
    load_env_vars(filename)

    # Start a connection to database
    conn = conn_simple()

    # Receive the number of threads if there exists
    if args.threads:
        threads = int(args.threads)

    # Handle the bulk case
    if args.xml_bulk:

        xml_paths = args.xml_bulk
        if os.path.exists(xml_paths) is False:
            print("[*] Write a valid path for the XML file.")
            sys.exit(0)

        cont = 1
        with open(xml_paths, 'r') as file:
            for file_name in file:
                file_name = file_name.rstrip('\n')

                print(Colors.CYAN + f"\n[{cont}] Processing:" + Colors.ORANGE + f"\t{file_name}" + Colors.R)
                load_file(conn, file_name, cont, insert_sql)
                cont += 1

    # Handle single cases
    if args.ip_list:
        file_name = args.ip_list

        if os.path.exists(file_name) is False:
            print("[*] Write a valid path for the XML file.")
            sys.exit(0)

        # Load single file
        load_file(conn, file_name, 1, insert_sql)

    # Insert all insertions collected in insert_list
    print(Colors.GREEN + "\n[*] Trying to insert the bulk of data." + Colors.R)
    insert_bulk(conn, insert_list, insert_sql)

    # Close connection
    if conn:
        print(Colors.GREEN + f"[*] Connection to database closed." + Colors.R)
        conn.close()

    # Force garbage collection
    gc.collect()
