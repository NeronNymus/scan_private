#!/usr/bin/env python3

# Python code for reading of different ways the files

import os
import csv
import pandas as pd

def read_csv(filename):
    with open(filename, 'r') as file:
        #reader = csv.DictReader(file)
        reader = csv.reader(file)
        return list(reader)

def read_large_file(file_path):
    with open(file_path, 'r') as file:
        while True:
            line = file.readline()
            if not line:
                break
            yield line.strip()

def loop_scans():
    hard_scan_dir = os.path.abspath("../../scans/crawling/ips_up_port_23_10.0.0.0_8")

    #print(hard_scan_dir)
    #print(len(os.listdir(hard_scan_dir))) 

    base_names = sorted (os.listdir(hard_scan_dir))

    for base_name in base_names:
        if 'clean' in base_name:
            scan_name = hard_scan_dir + "/" + base_name
            analysis_name = scan_name + ".analysis"
            print(analysis_name)
