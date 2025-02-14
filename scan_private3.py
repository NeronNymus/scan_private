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
from dotenv import load_dotenv


if __name__ == "__main__":

    # Load environment variables from .env file
    load_dotenv()

    # Example usage
    if os.name == 'posix':
        project_path = os.getcwd()  # Execute it in the current project path
    elif os.name == 'nt':
        project_path = "C:\\Users\\jesus\\Other\\scan_private" # Hardcoded path
        os.makedirs(project_path, exist_ok=True)

        # Get the parent of the parent directory
        if project_path not in sys.path:
            sys.path.append(project_path)

    # Personal packages after successull checking parameters in Windows
    #from backend.backend import load_env_vars
    #from utils.colors import Colors

    # Log test
    test_dir = os.path.join(project_path,"scans/active3")
    test_path = os.path.join(test_dir,"test1")

    execution_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(test_path, 'a') as file:
        print(f"Logged: {execution_date}\tinto {test_path}")
        file.write(f"{execution_date}\t{__file__}\n")


    #scan_dir = os.path.join(project_path,"scans/active3")
    #scan_result = scan_nmap(scan_dir)
    
    #load_data_db(scan_result)
