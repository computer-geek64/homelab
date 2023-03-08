#!/usr/bin/python3
# update_unbound_dns_records.py

import os
import psycopg2


def pull_configuration() -> dict[str, str]:
    network = os.environ.get('NETWORK', '')

    with psycopg2.connect(host=os.environ.get('POSTGRES_HOST', '127.0.0.1'), dbname='homelab', user='dns', password=os.environ['POSTGRES_DNS_PASSWORD']) as connection:
        cursor = connection.cursor()

        if network:
            cursor.execute('SELECT d.domain AS domain, h.ip AS ip FROM domain AS d INNER JOIN host AS h ON d.host = h.hostname WHERE h.ip IS NOT NULL AND h.network = %s;', (network,))
        else:
            cursor.execute('SELECT d.domain AS domain, h.wireguard_ip AS ip FROM domain AS d INNER JOIN host AS h ON d.host = h.hostname WHERE h.wireguard_ip IS NOT NULL;')

        return {domain: ip for domain, ip in cursor.fetchall()}


def update_records(filename: str, records: dict[str, str]) -> None:
    with open(filename, 'w') as records_file:
        for domain, ip in records.items():
            records_file.write(f'local-data: "{domain} A {ip}"\n')
            records_file.write(f'local-data-ptr: "{ip} {domain}"\n')

if __name__ == '__main__':
    records = pull_configuration()
    update_records('/etc/unbound/records.conf', records)

