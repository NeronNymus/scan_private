#!/usr/bin/env python3

import os
import sys
import psycopg2
import asyncio
import asyncpg

# Personal packages

# Database connection parameters using environment variables
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT')

# Create a connection pool
async def create_pool():
    return await asyncpg.create_pool(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

# Updated exec_ifconfig function using save_ifconfig
async def exec_ifconfig(pool, ip, tn, command):
    if command == 'ifconfig':
        if tn:
            output = send_command(tn, command)
            if output:
                print(output)
                # Save ifconfig output to the database asynchronously
                await save_ifconfig(pool, ip, output)
            else:
                print("Failed to execute command.")
            tn.close()
        else:
            print("Failed to connect.")

# Function to save ifconfig data to the database asynchronously
async def save_ifconfig(pool, ip, data):
    async with pool.acquire() as connection:
        async with connection.transaction():
            # Check if the record exists asynchronously
            existing_record = await connection.fetchrow("SELECT * FROM ifconfig_results WHERE ip_address = $1", ip)

            if existing_record is None:
                # Insert data into the table asynchronously
                await connection.execute("INSERT INTO ifconfig_results (ip_address, output) VALUES ($1, $2)", ip, data)
                print("[!] Data saved to the database.")
            else:
                print("[!] Data already exists in the database. Skipped insertion.")

async def main(ip, data):
    pool = await create_pool()

    # Simulate multiple concurrent writes
    tasks = [save_ifconfig(pool, ip, data) for _ in range(100)]
    await asyncio.gather(*tasks)

# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())
