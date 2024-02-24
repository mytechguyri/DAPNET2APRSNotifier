#!/usr/bin/python3
# Special thanks to KR0SIV for his DAPNET2APRS program https://github.com/KR0SIV/DAPNET2APRS
# and N8ACL for his DAPNETNotifier program https://github.com/n8acl/DAPNETNotifier
# on both of which this program is based
# Copyright 2023 John Tetreault WA1OKB, released under the Gnu General Public License v3.0
#
import json
import re
import requests
import time
import http.client
import urllib
import sys
import aprslib
import logging
import configparser
from requests.auth import HTTPBasicAuth
from os import system, name
from time import sleep

# Setup logging
logger = logging.getLogger('dapnet2aprs')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/var/log/pi-star/DAPNET2APRS.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Read Config file and set variables
logger.info("Starting DAPNET2APRSNotifier...")
config = configparser.ConfigParser()
read_config = config.read('/etc/dapnet2aprs')
if not read_config:
    logger.error(
        "Failed to read the config file at /etc/dapnet2aprs.  Did you forget to create it?")
    exit(1)
logger.info("Reading configuration file at /etc/dapnet2aprs")
first_run = True
try:
    wait_time = int(config['DEFAULT']['wait_time'])
    log_path = config['DEFAULT']['log_path']
    dapnet_username = config['DAPNET']['username']
    dapnet_password = config['DAPNET']['password']
    dapnet_server = config['DAPNET']['server']
    pager_id = config['DAPNET']['pager_id']
    dapnet_url = (
        f"http://{config['DAPNET']['server']}:8080/calls?ownerName={dapnet_username}")
    aprs_server = config['APRS']['server']
    callsign = config['APRS']['callsign']
    send_to = config['APRS']['send_to']
    db_engine = config['DATABASE']['engine']
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    if db_engine == 'mysql':
        logger.info("MySQL database engine selected")
        import mysql.connector
        from mysql.connector import Error
        mysqlhost = config['MYSQL']['host']
        mysqluser = config['MYSQL']['user']
        mysqlpassword = config['MYSQL']['password']
        db = config['MYSQL']['database']

    else:
        logger.info("SQLite database engine selected")
        import sqlite3 as sql
        from sqlite3 import Error
        import os
        db = (f"{os.path.dirname(os.path.abspath(__file__))}/dapnet.db")
except KeyError as e:
    key = e.args[0]
    logger.error(
        f"Failed to find '{e.args[0]}' value in /etc/dapnet2aprs config file")
    raise

# Define Functions

# Define SQL Functions
def create_connection(db_name):
    if db_engine == 'mysql':
        # Create connection to MySQL/MariaDB Database
        try:
            connection = mysql.connector.connect(
                host=mysqlhost,
                user=mysqluser,
                password=mysqlpassword
            )
            logger.info(
                f"Connected to {mysqlhost} MySQL Database Engine {connection}")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to MySQL database: {e}")
            raise
    else:
        # Creates connection to dapnet.db SQLlite3 Database
        try:
            connection = sql.connect(db_name)
            logger.info(f"Connected to sqlite Database Engine {connection}")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to sqlite database: {e}")
            raise


def check_database_exists(connection, db_name):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to execute 'SHOW DATABASES': {e}")
        raise

    for database in databases:
        if db_name == database[0]:
            logger.info(
                f"Found the {database[0]} database on {mysqlhost}.  Connecting.")
            try:
                connection.database = db_name
                logger.info(
                    f"Successfully connected to the {db_name} database on {mysqlhost} {connection}")
                return True
            except Exception as e:
                logger.error(
                    f"Failed to connect to the {db_name} database on {mysqlhost}: {e}")
                raise

    logger.info(
        f"The {db_name} database was not found on {mysqlhost}, creating it.")
    try:
        cursor.execute(f"CREATE DATABASE {db_name}")
        connection.database = db_name
        create_messages_table = """CREATE TABLE IF NOT EXISTS messages (
            text TEXT,
            timestamp TEXT
        );"""
        cursor.execute(create_messages_table)
        logger.info(f"Created the {db_name} database on {mysqlhost}")
        return True
    except Exception as e:
        logger.error(
            f"Failed to create the {db_name} database on {mysqlhost}: {e}")
        raise


def exec_sql(connection, sql):
    # Executes SQL for Updates, inserts and deletes
    try:
        cur = connection.cursor(buffered=True)
        cur.execute(sql)
        connection.commit()
        return ()
    except Excepton as e:
        logger.error(f"Failed to execute SQL query: {e}")
        raise


def select_sql(connection, sql):
    # Executes SQL for Selects
    try:
        cur = connection.cursor(buffered=True)
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        logger.error(f"Failed to execute SQL query: {e}")
        raise

# Get DAPNET API Data
def get_api_data():
    response = requests.get(
        dapnet_url,
        auth=HTTPBasicAuth(
            dapnet_username,
            dapnet_password),
        headers=headers,
        timeout=10).json()
    return response

# Define APRS functions
# Calculate APRS Passcode from callsign function
def aprspass(callsign: str):
    stop_here = callsign.find('-')
    if stop_here != -1:
        callsign = callsign[:stop_here]
    real_call = callsign[:10].upper()
    callsign = real_call
    hash_value = 0x73e2
    for i in range(0, len(real_call), 2):
        hash_value ^= ord(real_call[i]) << 8
        if i + 1 < len(real_call):
            hash_value ^= ord(real_call[i + 1])
    passcode = hash_value & 0x7fff
    logger.info(f"Calculated APRS passcode for {callsign} as {passcode}")
    return passcode

# Send APRS Message function
def send_aprs(msg):
    try:
        if len(msg) > 61:
            split_index = msg.rfind(' ', 0, 61)
            if split_index == -1:  # No space found, split at 61
                split_index = 61
            messages = [msg[:split_index], msg[split_index:].lstrip()]
        else:
            messages = [msg]
        for message in messages:
            logger.info(
                f"Forwarding message for {pager_id} to {send_to}@APRS via {aprs_server}: {message}")
            AIS = aprslib.IS(str(callsign), passwd=str(aprs_passcode), host=str(aprs_server), port=14580)
            AIS.connect()
            AIS.sendall(f"DAPNET>APRS,TCPIP*::{send_to.ljust(9)}:MSG [{message}]")
        return True
    except Exception as e:
        logger.error(f"Failed to send APRS message {msg}: {e}")
        return False

# Main Program

#Call the function to calculate the APRS passcode
aprs_passcode = aprspass(callsign)

# check to see if the database exists. If not create it. Otherwise create
# a connection to it for the rest of the script
connection = create_connection(db)
if db_engine == 'mysql':
    check_database_exists(connection, db)

# Check API and if the last message was not already sent, send it... else
# ignore it.
logger.info(
    f"DAPNET2APRSNotifier Started and polling for incoming DAPNET messages every {wait_time} seconds.")

try:
    while True:
        if first_run:  # If this is the first run, don't send anything
            first_run = False
        else:
            # Wait the check time to not pound the API and get rate Limited
            if wait_time < 60:
                sleep(60)
            else:
                sleep(wait_time)

            # get the data from the API
            data = get_api_data()

            for i in range(0, len(data)):
                text = data[i]['text']
                timestamp = data[i]['timestamp']

                sql = (
                    f"select count(text) as text_cnt from messages where text = '{text}' and timestamp = '{timestamp}';")
                result = select_sql(connection, sql)

                for row in result:
                    text_cnt = row[0]

                if text_cnt == 0:

                    #send the message
                    sent = send_aprs(text)
                    #add to sent messages if successful
                    if sent:
                        sql = (
                            f"insert into messages (text, timestamp) values ('{text}','{timestamp}');")
                        exec_sql(connection, sql)


                    break

except Exception as e:
    logger.error(str(e))
    raise
