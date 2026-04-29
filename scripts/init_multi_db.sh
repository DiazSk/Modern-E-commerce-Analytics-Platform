#!/bin/bash
# ============================================================
# Multi-Database Initialization Script
# ============================================================
# Runs at first container startup via docker-entrypoint-initdb.d
# Creates separate logical databases for Airflow and Metabase
# so all three services share one PostgreSQL container.
# ============================================================
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE airflow_db;
    CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
    GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;

    CREATE DATABASE metabase_db;
    CREATE USER metabase_user WITH PASSWORD 'metabase_pass';
    GRANT ALL PRIVILEGES ON DATABASE metabase_db TO metabase_user;
EOSQL

echo "Multi-database initialization complete: airflow_db, metabase_db created."
