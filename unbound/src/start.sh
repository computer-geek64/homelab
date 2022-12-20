#!/bin/sh
# start.sh

set -e

./update_unbound_dns_records.py

/usr/sbin/unbound "$@"
