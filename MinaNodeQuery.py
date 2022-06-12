import subprocess
import sys
import os
import json
import logging
import socket
import datetime
import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

logging.getLogger(__name__).addHandler(logging.StreamHandler(sys.stdout))
logging.basicConfig( format = '%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    level = logging.INFO )

load_dotenv()  # take environment variables from .env.

hostname = os.getenv('HOSTNAME')
current_time = datetime.datetime.now()

class MinaNodeQuery:

    def __init__( self ):
        '''constructor'''
        self.mode = os.getenv('RUN_MODE')
        logging.info( f"Mina Node Query for {hostname} for Mode {self.mode}")

        if self.mode == 'docker':
            self.command = ['docker', 'exec', '-it', os.getenv('DOCKER_CONTAINER'), 'mina', 'advanced', 'node-status', '-daemon-peers']
        else:
            self.command = ['mina', 'advanced', 'node-status', '-daemon-peers']

        # connect to the database
        self.conn = self.connect_db( {
            'database':  os.getenv('DATABASE'),
            'host': os.getenv('DATABASE_HOST'),
            'port': os.getenv('DATABASE_PORT'),
            'user': os.getenv('DATABASE_USER'),
            'password': os.getenv('DATABASE_PASSWORD'),
        } )

        # remove previous entries from the host
        self.drop_host_entries()

        # query and add entries
        self.execute()

    def execute( self ):
        '''perform the query and insert into the database'''
        logging.info( f"Collecting Daemon Data" )
        # execute the command and obtain the result from the daemon
        p = subprocess.check_output(self.command, shell=False)
        result = filter(None, p.decode('utf-8').split('\r\n'))
        ip_list = []

        # collect the ip addresses 
        for item in result:
            node_data = json.loads( item )
            # direct node peer ip
            ip_list.append( node_data['node_ip_addr'] )
            # collect peers
            for peer in node_data['peers']:
                ip_list.append( peer['host'] )

        # sort and obtain unique
        ip_list = sorted(list(set(ip_list)))
        logging.info(f"Collected {len(ip_list)} Unique IP Addresses")

        # insert into the database
        for ip_address in ip_list:
            data = ( ip_address, current_time, hostname )
            logging.debug( f"Inserting {data}" )
            self.insert_ip_address( data )

        logging.info( f"Data Inserted into Database. Exiting..." )

    def connect_db( self, info ):
        '''establish the postgres'''
        logging.info( f"Connecting to {info[ 'database' ]} at {info[ 'host' ]}:{info[ 'port' ]}")
        # connect
        conn = psycopg2.connect(
            database =  info[ 'database' ],
            user =      info[ 'user' ],
            password =  info[ 'password' ],
            host =      info[ 'host' ],
            port =      info[ 'port' ] )
            
        # set isolation level
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT);
        return conn

    def insert_ip_address( self, data ):
        '''insert the ip address'''
        cmd = """INSERT INTO node_data (
            ip_address, 
            date,
            origin
            ) VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING"""
        self.conn.cursor().execute( cmd, data )

    def drop_host_entries( self ):
        '''drop entries from the host'''
        logging.info( f"Dropping Old Entries for {hostname}" )
        cmd = """
            DELETE FROM node_data
            WHERE origin = '%s';
        """ % hostname
        self.conn.cursor().execute( cmd )

# run the class
MinaNodeQuery()
