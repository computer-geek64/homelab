#!/usr/bin/python
# wg_gen_config.py

import os
import sys
import psycopg2
from getpass import getpass


WIREGUARD_POSTGRES_PASSWORD = os.environ.get('WIREGUARD_POSTGRES_PASSWORD')
if WIREGUARD_POSTGRES_PASSWORD is None:
    WIREGUARD_POSTGRES_PASSWORD = getpass('Wireguard Postgres password: ')
class HostNotFoundError(LookupError):
    def __init__(self, host: str, *args, **kwargs):
        super().__init__(host, *args, **kwargs)

class WireguardHost:
    def __init__(self, hostname: str):
        self.hostname = hostname

        with psycopg2.connect(host='citadel', dbname='homelab', user='wireguard', password=WIREGUARD_POSTGRES_PASSWORD) as connection:
            cursor = connection.cursor()

            cursor.execute('SELECT wh.private_key, wh.ip, wh.dns, h.description FROM wireguard.hosts AS wh INNER JOIN public.hosts AS h ON wh.hostname = h.hostname WHERE wh.hostname = %s;', (self.hostname,))
            results = cursor.fetchall()
            if len(results) != 1:
                raise HostNotFoundError(self.hostname)
            self.private_key, self.ip, self.dns, self.description = results[0]

            # Server query
            cursor.execute('SELECT wt.client, wh.ip, wh.public_key, h.description FROM wireguard.tunnels AS wt INNER JOIN wireguard.hosts AS wh ON wt.client = wh.hostname INNER JOIN public.hosts AS h ON wt.client = h.hostname WHERE wt.server = %s;', (self.hostname,))
            self.peers = [{'name': client, 'description': description, 'AllowedIPs': f'{ip}/32', 'PublicKey': public_key} for client, ip, public_key, description in cursor.fetchall()]
            self.is_server = bool(self.peers)

            # Client query
            cursor.execute('SELECT wt.server, wt.allowed_ips, wh.public_key, wt.endpoint, h.description FROM wireguard.tunnels AS wt INNER JOIN wireguard.hosts AS wh ON wt.server = wh.hostname INNER JOIN public.hosts AS h ON wt.server = h.hostname WHERE wt.client = %s;', (self.hostname,))
            self.peers += [{'name': server, 'description': description, 'AllowedIPs': allowed_ips, 'PublicKey': public_key, 'Endpoint': endpoint, 'PersistentKeepalive': 25} for server, allowed_ips, public_key, endpoint, description in cursor.fetchall()]

    def write(self):
        print('[Interface]')
        print(f'# {self.hostname}: {self.description}')
        print(f'PrivateKey = {self.private_key}')
        print(f'Address = {self.ip}')
        if self.dns:
            print(f'DNS = {self.dns}')
        if self.is_server:
            print('ListenPort = 51820')

        for peer in self.peers:
            print()
            print('[Peer]')
            print('# ' + peer.pop('name') + ': ' + peer.pop('description'))
            for key, value in peer.items():
                print(f'{key} = {value}')


if __name__ == '__main__':
    wireguard_host = WireguardHost(sys.argv[1])
    wireguard_host.write()

