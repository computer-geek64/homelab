#!/usr/bin/python3
# update_unbound_dns_records.py

import os
import psycopg2


def pull_configuration() -> tuple[dict[str, str], dict[str, str]]:
    with psycopg2.connect(host='127.0.0.1', dbname='homelab', user='dns', password=os.environ['DNS_POSTGRES_PASSWORD']) as connection:
        cursor = connection.cursor()

        cursor.execute('SELECT hostname, ip FROM hosts WHERE ip IS NOT NULL;')
        A_records = {host: ip for host, ip in cursor.fetchall()}

        cursor.execute('SELECT cname, host FROM connections WHERE cname IS NOT NULL;')
        CNAME_records = {cname: host for cname, host in cursor.fetchall()}

        return A_records, CNAME_records


def update_records(filename: str, A_records: dict[str, str], CNAME_records: dict[str, str]) -> None:
    with open(filename, 'w') as records_file:
        for host, ip in A_records.items():
            records_file.write(f'local-data: "{host} A {ip}"\n')
            records_file.write(f'local-data-ptr: "{ip} {host}"\n')
        for cname, host in CNAME_records.items():
            records_file.write(f'local-data: "{cname} CNAME {host}"\n')


if __name__ == '__main__':
    A_records, CNAME_records = pull_configuration()
    update_records('/etc/unbound/records.conf', A_records, CNAME_records)

