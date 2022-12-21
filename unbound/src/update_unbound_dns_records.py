#!/usr/bin/python3
# update_unbound_dns_records.py

import os
import psycopg2


def pull_configuration() -> dict[str, str]:
    with psycopg2.connect(host='127.0.0.1', dbname='homelab', user='dns', password=os.environ['DNS_POSTGRES_PASSWORD']) as connection:
        cursor = connection.cursor()

        records = {}

        cursor.execute('SELECT hostname, ip, alias FROM hosts WHERE ip IS NOT NULL;')
        for domain, ip, alias in cursor.fetchall():
            records[domain] = ip
            if alias is not None:
                records[alias] = ip

        cursor.execute('SELECT name, ip FROM domains INNER JOIN hosts ON domains.host = hosts.hostname WHERE ip IS NOT NULL;')
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

