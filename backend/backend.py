#!/usr/bin/env python3

import os
import sys
import psycopg2
from psycopg2 import pool
from natsort import natsorted
from subprocess import run, PIPE

# Personal packages
from utils.colors import Colors


# Function to source environment variables from a file
def load_env_vars(filename):
    try:
        with open(filename) as f:
            for line in f:
                # Skip comments and empty lines
                if line.startswith("#") or not line.strip():
                    continue
                # Split the line by '=' and remove whitespace
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
    except FileNotFoundError:
        print(Colors.RED + f"Error: File '{filename}' not found." + Colors.R)
        sys.exit(1)
    except Exception as e:
        print(Colors.RED + f"Error loading environment variables: {e}" + Colors.R)
        sys.exit(1)

load_env_vars('.env')

# Database connection parameters using environment variables
DB_HOST     = os.getenv('DB_HOST')
DB_NAME     = os.getenv('DB_NAME')
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT     = os.getenv('DB_PORT')

# Database connection parameters
def get_db_params():
    return {
        "dbname": os.getenv('DB_NAME'),
        "user": os.getenv('DB_USER'),
        "password": os.getenv('DB_PASSWORD'),
        "host": os.getenv('DB_HOST'),
        "port": os.getenv('DB_PORT')
    }

# Initialize the connection pool
def start_pool(min_connections, max_connections):
    global DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

    connection_pool = psycopg2.pool.SimpleConnectionPool(
        min_connections,  # minimum number of connections
        max_connections,  # maximum number of connections
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )
    return connection_pool


def connect_to_database(connection_pool):
    try:
        conn = connection_pool.getconn()
        
        if conn:
            print(Colors.ORANGE + "[!] Connected to the database.\n" + Colors.R)
            return conn
        else:
            print(Colors.RED + "[#] No available connections in the pool." + Colors.R)
            return None
    except psycopg2.Error as e:
        print(Colors.RED + f"[#] Error connecting to PostgreSQL:\n{e}" + Colors.R)
        return None


# Connect to the database
def conn_simple():
    params = get_db_params()
    try:
        conn = psycopg2.connect(**params)
        print(Colors.GREEN + "[*] Connection successful to database." + Colors.R)
        return conn
    except Exception as e:
        print(Colors.RED + f"Unable to connect to the database: {e}" + Colors.R)
        return None


# Function to query to the database
def query(conn, sql_query):
    
    if not conn:
        return

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)

        rows = cursor.fetchall()
        #rows = natsorted(rows)
        return rows

    except psycopg2.Error as e:
        print(f"[x] Error quering to database.\n{e}")
        sys.exit(1)

    finally:
        if cursor:
            cursor.close()
        #if conn:
        #    print(Colors.GREEN + "[*] Connection to database closed." + Colors.R)
        #    conn.close()
