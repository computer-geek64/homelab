#!/usr/bin/python3
# wg_gen_config.py

import os
import sys
import psycopg2
from getpass import getpass


WIREGUARD_ENDPOINT = '205.185.115.161:51820'
DNS = '192.168.2.1'

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres.homelab.net')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'ashish')
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD'] if 'POSTGRES_PASSWORD' in os.environ else getpass('Enter Postgres password for ashish: ')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'homelab')


class HostNotFoundError(LookupError):
    def __init__(self, host: str, *args, **kwargs):
        super().__init__(host, *args, **kwargs)

class WireguardHost:
    def __init__(self, hostname: str):
        self.hostname = hostname

        with psycopg2.connect(host=POSTGRES_HOST, dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD) as connection:
            cursor = connection.cursor()

            cursor.execute('SELECT h.alias, h.description, h.wireguard_ip, h.wireguard_private_key, h.wireguard_public_key FROM host AS h WHERE h.hostname = %s AND h.wireguard_ip IS NOT NULL;', (self.hostname,))
            results = cursor.fetchall()
            if not results:
                raise HostNotFoundError(self.hostname)
            self.alias, self.description, self.ip, self.private_key, self.public_key = results[0]

            # Peers query
            if self.ip == DNS:  # If host is Wireguard server
                self.is_server = True
                cursor.execute('SELECT h.hostname, h.alias, h.description, h.wireguard_ip, h.wireguard_public_key FROM host AS h WHERE h.hostname != %s AND h.wireguard_ip IS NOT NULL;', (self.hostname,))
                self.peers = [{'name': name, 'alias': alias, 'description': description, 'AllowedIPs': f'{ip}/32', 'PublicKey': public_key} for name, alias, description, ip, public_key in cursor.fetchall()]
            else:
                self.is_server = False
                cursor.execute('SELECT h.hostname, h.alias, h.description, h.wireguard_public_key FROM host AS h WHERE h.wireguard_ip = %s;', (DNS,))
                self.peers = [{'name': name, 'alias': alias, 'description': description, 'AllowedIPs': DNS.rsplit('.', 1)[0] + '.0/24', 'PublicKey': public_key, 'Endpoint': WIREGUARD_ENDPOINT, 'PersistentKeepalive': 25} for name, alias, description, public_key in cursor.fetchall()]

    def write(self):
        print('[Interface]')
        print(f'# {self.hostname}' + (f' ({self.alias})' if self.alias is not None else '') + (f': {self.description}' if self.description is not None else ''))
        print(f'PrivateKey = {self.private_key}')
        print(f'Address = {self.ip}')
        if self.is_server:
            print('ListenPort = ' + WIREGUARD_ENDPOINT.rsplit(':', 1)[-1])
        else:
            print(f'DNS = {DNS}')

        for peer in self.peers:
            name = peer.pop('name')
            alias = peer.pop('alias')
            description = peer.pop('description')

            print()
            print('[Peer]')
            print(f'# {name}' + (f' ({alias})' if alias is not None else '') + (f': {description}' if description is not None else ''))
            for key, value in peer.items():
                print(f'{key} = {value}')


if __name__ == '__main__':
    wireguard_host = WireguardHost(sys.argv[1])
    wireguard_host.write()

