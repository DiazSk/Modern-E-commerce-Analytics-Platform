"""
Quick Verification Script - PostgreSQL Ingestion DAG
Tests all prerequisites before running the DAG
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_docker_services():
    """Check if required Docker services are running"""
    print("1. Checking Docker services...")
    
    required_services = [
        'ecommerce-postgres-source',
        'ecommerce-airflow-webserver',
        'ecommerce-airflow-scheduler',
        'ecommerce-airflow-worker'
    ]
    
    try:
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], 
                              capture_output=True, text=True)
        running_services = result.stdout.strip().split('\n')
        
        all_running = True
        for service in required_services:
            if service in running_services:
                print(f"   ✅ {service} is running")
            else:
                print(f"   ❌ {service} is NOT running")
                all_running = False
        
        return all_running
        
    except Exception as e:
        print(f"   ❌ Docker check failed: {str(e)}")
        return False

def check_postgres_data():
    """Check if orders exist in PostgreSQL"""
    print("\n2. Checking PostgreSQL data...")
    
    try:
        # Query order count
        cmd = [
            'docker', 'exec', 'ecommerce-postgres-source',
            'psql', '-U', 'ecommerce_user', '-d', 'ecommerce',
            '-t', '-c', 'SELECT COUNT(*) FROM orders;'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        count = int(result.stdout.strip())
        
        if count > 0:
            print(f"   ✅ {count:,} orders found in database")
            
            # Check date range
            cmd = [
                'docker', 'exec', 'ecommerce-postgres-source',
                'psql', '-U', 'ecommerce_user', '-d', 'ecommerce',
                '-t', '-c', "SELECT MIN(DATE(order_date)), MAX(DATE(order_date)) FROM orders;"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            date_range = result.stdout.strip()
            print(f"   📅 Date range: {date_range}")
            
            return True
        else:
            print(f"   ❌ No orders found")
            print(f"   Run: python scripts/load_data.py")
            return False
            
    except Exception as e:
        print(f"   ❌ PostgreSQL check failed: {str(e)}")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print("\n3. Checking AWS credentials...")
    
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket = os.getenv('S3_RAW_BUCKET')
    
    if access_key and secret_key and bucket:
        print(f"   ✅ AWS_ACCESS_KEY_ID: {access_key[:8]}...")
        print(f"   ✅ AWS_SECRET_ACCESS_KEY: {secret_key[:8]}...")
        print(f"   ✅ S3_RAW_BUCKET: {bucket}")
        return True
    else:
        print(f"   ❌ AWS credentials not configured in .env file")
        return False

def check_dag_file():
    """Check if DAG file exists and has no syntax errors"""
    print("\n4. Checking DAG file...")
    
    dag_path = Path('dags/ingest_postgres_orders.py')
    
    if dag_path.exists():
        print(f"   ✅ DAG file exists: {dag_path}")
        
        # Check for syntax errors
        try:
            with open(dag_path, 'r') as f:
                compile(f.read(), dag_path, 'exec')
            print(f"   ✅ No syntax errors")
            return True
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {str(e)}")
            return False
    else:
        print(f"   ❌ DAG file not found: {dag_path}")
        return False

def check_airflow_ui():
    """Check if Airflow UI is accessible"""
    print("\n5. Checking Airflow UI...")
    
    try:
        import requests
        response = requests.get('http://localhost:8081/health', timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ Airflow UI accessible at http://localhost:8081")
            print(f"   📝 Login: admin / admin123")
            return True
        else:
            print(f"   ⚠️ Airflow UI returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Airflow UI not accessible: {str(e)}")
        print(f"   Try: docker restart ecommerce-airflow-webserver")
        return False

def print_next_steps(all_checks_passed):
    """Print next steps based on check results"""
    print("\n" + "=" * 60)
    
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("\n1. Set up Airflow connections:")
        print("   python scripts/setup_airflow_connections.py")
        print("\n2. Open Airflow UI:")
        print("   http://localhost:8081")
        print("   Login: admin / admin123")
        print("\n3. Verify connections:")
        print("   Admin > Connections")
        print("   - postgres_source")
        print("   - aws_default")
        print("\n4. Find and trigger DAG:")
        print("   - Look for 'ingest_postgres_orders'")
        print("   - Click Play button (▶)")
        print("   - Select 'Trigger DAG'")
        print("\n5. Monitor execution:")
        print("   - Click on DAG name")
        print("   - Watch tasks turn green")
        print("   - Check logs for details")
        
    else:
        print("⚠️ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nFix the issues above before proceeding.")
        print("\nCommon fixes:")
        print("- Start Docker: docker-compose up -d")
        print("- Load data: python scripts/load_data.py")
        print("- Check .env file for AWS credentials")
    
    print("=" * 60)

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("PostgreSQL Ingestion DAG - Pre-flight Check")
    print("=" * 60)
    
    checks = [
        check_docker_services(),
        check_postgres_data(),
        check_aws_credentials(),
        check_dag_file(),
        check_airflow_ui()
    ]
    
    all_passed = all(checks)
    
    print_next_steps(all_passed)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
