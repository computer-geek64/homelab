--DROP DATABASE IF EXISTS homelab;
DROP TABLE IF EXISTS network CASCADE;
DROP TABLE IF EXISTS host CASCADE;
DROP TABLE IF EXISTS service CASCADE;
DROP TABLE IF EXISTS service_port CASCADE;
DROP TYPE IF EXISTS storage_type CASCADE;
DROP TABLE IF EXISTS service_data CASCADE;
DROP TABLE IF EXISTS service_dependency CASCADE;
DROP VIEW IF EXISTS service_discovery CASCADE;
DROP VIEW IF EXISTS domain CASCADE;
DROP VIEW IF EXISTS backup CASCADE;

--CREATE DATABASE homelab;

CREATE TABLE network (
    name varchar PRIMARY KEY,
    dns varchar,
    location varchar NOT NULL
);

CREATE TABLE host (
    hostname varchar PRIMARY KEY,
    alias varchar UNIQUE,
    description varchar,
    ip varchar(15),
    mac char(17) UNIQUE,
    network varchar REFERENCES network (name),
    service_user varchar,
    wireguard_ip varchar(15),
    wireguard_private_key varchar,
    wireguard_public_key varchar
);

CREATE TABLE service (
    name varchar PRIMARY KEY,
    host varchar NOT NULL REFERENCES host (hostname) ON UPDATE CASCADE ON DELETE CASCADE,
    source varchar,
    config jsonb
);

CREATE TABLE service_port (
    service varchar REFERENCES service (name) ON UPDATE CASCADE ON DELETE CASCADE,
    port integer,
    domain varchar,
    reverse_proxy varchar REFERENCES service (name) ON UPDATE CASCADE ON DELETE CASCADE,
    reverse_proxy_port integer,
    PRIMARY KEY (service, port)
);

CREATE TYPE storage_type AS ENUM (
    'docker',
    'path',
    'database'
);

CREATE TABLE service_data (
    service varchar REFERENCES service (name) ON UPDATE CASCADE ON DELETE CASCADE,
    data_name varchar,
    storage_type storage_type NOT NULL,
    source varchar NOT NULL,
    PRIMARY KEY (service, data_name)
);

CREATE TABLE service_dependency (
    service varchar REFERENCES service (name) ON UPDATE CASCADE ON DELETE CASCADE,
    dependency varchar REFERENCES service (name) ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (service, dependency)
);

-- Service discovery view
CREATE VIEW service_discovery AS
SELECT s.name AS service, sp.port AS service_port, CASE WHEN sp.domain IS NULL THEN concat(replace(replace(s.name, '_', '-'), '.', '-'), '.homelab.net') ELSE sp.domain END AS domain, CASE WHEN sp.reverse_proxy_port IS NULL THEN sp.port ELSE sp.reverse_proxy_port END AS port
FROM service AS s
INNER JOIN service_port AS sp
ON s.name = sp.service;

-- Domain view
CREATE VIEW domain AS
SELECT DISTINCT lower(CASE WHEN sp.domain IS NULL THEN concat(replace(replace(s.name, '_', '-'), '.', '-'), '.homelab.net') ELSE sp.domain END) AS domain, CASE WHEN sp.reverse_proxy IS NULL THEN s.host ELSE rp.host END AS host
FROM service AS s
INNER JOIN service_port AS sp
ON s.name = sp.service
LEFT JOIN service AS rp
ON sp.reverse_proxy = rp.name UNION
SELECT lower(h.alias) AS domain, h.hostname AS host
FROM host AS h
WHERE h.alias IS NOT NULL;

-- Backup view
CREATE VIEW backup AS
SELECT concat(s.name, '_', sd.data_name) AS name, s.host, sd.storage_type, sd.source
FROM service AS s
INNER JOIN service_data AS sd
ON s.name = sd.service;
