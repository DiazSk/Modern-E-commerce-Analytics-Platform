"""
============================================
Airflow Connections Setup Script
============================================

This script creates required Airflow connections for the
data ingestion pipelines.

Connections:
1. postgres_source - PostgreSQL source database
2. aws_default - AWS S3 credentials

Usage:
    python scripts/setup_airflow_connections.py

Note: Run this AFTER Airflow is initialized
============================================
"""

import logging
import os
import subprocess

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_airflow_command(command):
    """Execute airflow CLI command in Docker container"""
    try:
        # Run command in airflow-scheduler container
        docker_cmd = [
            "docker",
            "exec",
            "ecommerce-airflow-scheduler",
            "airflow",
        ] + command

        result = subprocess.run(docker_cmd, capture_output=True, text=True, check=True)

        return result.stdout

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e.stderr}")
        raise


def delete_connection_if_exists(conn_id):
    """Delete existing connection"""
    try:
        logger.info(f"Checking if connection '{conn_id}' exists...")
        run_airflow_command(["connections", "delete", conn_id])
        logger.info(f"✅ Deleted existing connection '{conn_id}'")
    except:
        logger.info(f"   Connection '{conn_id}' doesn't exist (this is fine)")


def create_postgres_connection():
    """Create PostgreSQL source database connection"""
    logger.info("Creating PostgreSQL source connection...")

    # Get credentials from environment
    host = os.getenv("POSTGRES_SOURCE_HOST", "postgres-source")
    port = os.getenv("POSTGRES_SOURCE_PORT", "5432")  # Internal Docker port
    database = os.getenv("POSTGRES_SOURCE_DB", "ecommerce")
    user = os.getenv("POSTGRES_SOURCE_USER", "ecommerce_user")
    password = os.getenv("POSTGRES_SOURCE_PASSWORD", "ecommerce_pass")

    # Connection URI
    # Inside Docker network, use service name 'postgres-source'
    conn_uri = f"postgresql://{user}:{password}@postgres-source:{port}/{database}"

    # Delete if exists
    delete_connection_if_exists("postgres_source")

    # Create connection
    command = [
        "connections",
        "add",
        "postgres_source",
        "--conn-type",
        "postgres",
        "--conn-uri",
        conn_uri,
    ]

    run_airflow_command(command)
    logger.info("✅ PostgreSQL connection created successfully")

    return True


def create_aws_connection():
    """Create AWS S3 connection"""
    logger.info("Creating AWS S3 connection...")

    # Get credentials from environment
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    if not access_key or not secret_key:
        logger.error("❌ AWS credentials not found in .env file")
        return False

    # Delete if exists
    delete_connection_if_exists("aws_default")

    # Create connection using JSON extra
    extra = f'{{"region_name": "{region}"}}'

    command = [
        "connections",
        "add",
        "aws_default",
        "--conn-type",
        "aws",
        "--conn-login",
        access_key,
        "--conn-password",
        secret_key,
        "--conn-extra",
        extra,
    ]

    run_airflow_command(command)
    logger.info("✅ AWS connection created successfully")

    return True


def verify_connections():
    """List all connections to verify"""
    logger.info("\nVerifying connections...")

    try:
        output = run_airflow_command(["connections", "list"])
        logger.info("\nCurrent Airflow Connections:")
        logger.info(output)
        return True
    except Exception as e:
        logger.error(f"Failed to list connections: {str(e)}")
        return False


def test_postgres_connection():
    """Test PostgreSQL connection"""
    logger.info("\nTesting PostgreSQL connection...")

    try:
        # Test using airflow CLI
        output = run_airflow_command(["connections", "get", "postgres_source"])
        logger.info("✅ PostgreSQL connection exists")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection test failed: {str(e)}")
        return False


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("Airflow Connections Setup")
    logger.info("=" * 60)

    try:
        # Create connections
        create_postgres_connection()
        create_aws_connection()

        # Verify
        verify_connections()

        # Test
        test_postgres_connection()

        logger.info("\n" + "=" * 60)
        logger.info("✅ All connections set up successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Open Airflow UI: http://localhost:8081")
        logger.info("2. Check Admin > Connections to verify")
        logger.info("3. Enable and trigger the DAG")

        return True

    except Exception as e:
        logger.error(f"\n❌ Setup failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
