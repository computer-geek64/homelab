#!/usr/bin/python3
# update_unbound_dns_records.py

import os
import psycopg2


def pull_configuration() -> dict[str, str]:
    vpn_dns = os.environ.get('VPN_DNS', 'false').lower() == 'true'

    with psycopg2.connect(host=os.environ.get('POSTGRES_HOST', '127.0.0.1'), dbname='homelab', user='dns', password=os.environ['DNS_POSTGRES_PASSWORD']) as connection:
        cursor = connection.cursor()

        records = {}

        if vpn_dns:
            cursor.execute('SELECT lower(wh.hostname), wh.ip, lower(h.alias) FROM wireguard.hosts AS wh INNER JOIN hosts AS h ON wh.hostname = h.hostname;')
        else:
            cursor.execute('SELECT lower(h.hostname), h.ip, lower(h.alias) FROM hosts AS h WHERE h.ip IS NOT NULL;')
        for domain, ip, alias in cursor.fetchall():
            records[domain] = ip
            if alias is not None:
                records[alias] = ip

        if vpn_dns:
            cursor.execute('SELECT lower(d.name), wh.ip FROM domains AS d INNER JOIN wireguard.hosts AS wh ON d.host = wh.hostname;')
        else:
            cursor.execute('SELECT lower(d.name), h.ip FROM domains AS d INNER JOIN hosts AS h ON d.host = h.hostname WHERE h.ip IS NOT NULL;')
        for domain, ip in cursor.fetchall():
            records[domain] = ip

        return records


def update_records(filename: str, records: dict[str, str]) -> None:
    with open(filename, 'w') as records_file:
        for domain, ip in records.items():
            records_file.write(f'local-data: "{domain} A {ip}"\n')
            records_file.write(f'local-data-ptr: "{ip} {domain}"\n')

if __name__ == '__main__':
    records = pull_configuration()
    update_records('/etc/unbound/records.conf', records)

