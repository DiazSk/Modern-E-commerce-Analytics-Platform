"""
Airflow Connection Tester
Tests PostgreSQL and AWS S3 connections before running DAGs
"""

import sys
import os

def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("\n" + "="*50)
    print("Testing PostgreSQL Connection")
    print("="*50)
    
    try:
        import psycopg2
        
        # Try to connect
        conn = psycopg2.connect(
            host='localhost',  # External connection for testing
            port=5433,  # External port
            database='ecommerce',
            user='ecommerce_user',
            password='ecommerce_pass'
        )
        
        # Test query
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders;")
        count = cur.fetchone()[0]
        
        cur.execute("SELECT MAX(DATE(order_date)) FROM orders;")
        max_date = cur.fetchone()[0]
        
        print(f"✅ PostgreSQL connection successful!")
        print(f"   Total orders: {count:,}")
        print(f"   Latest order date: {max_date}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check if Docker container is running: docker ps")
        print("  2. Verify port 5433 is exposed")
        print("  3. Check credentials in .env file")
        return False


def test_aws_connection():
    """Test AWS S3 connection"""
    print("\n" + "="*50)
    print("Testing AWS S3 Connection")
    print("="*50)
    
    try:
        import boto3
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Get bucket name
        bucket_name = os.getenv('S3_RAW_BUCKET')
        
        if not bucket_name:
            print("❌ S3_RAW_BUCKET not set in .env file")
            return False
        
        # Create S3 client
        s3 = boto3.client('s3')
        
        # Test by listing bucket
        try:
            response = s3.head_bucket(Bucket=bucket_name)
            print(f"✅ AWS S3 connection successful!")
            print(f"   Bucket: {bucket_name}")
            print(f"   Region: {response['ResponseMetadata']['HTTPHeaders'].get('x-amz-bucket-region', 'us-east-1')}")
            
            # Try to list objects
            objects = s3.list_objects_v2(Bucket=bucket_name, Prefix='raw/orders/', MaxKeys=5)
            
            if 'Contents' in objects:
                print(f"   Existing files: {len(objects['Contents'])}")
            else:
                print(f"   No existing files (this is OK for first run)")
            
            return True
            
        except s3.exceptions.NoSuchBucket:
            print(f"❌ Bucket '{bucket_name}' does not exist")
            print("   Create it with: terraform apply")
            return False
            
    except Exception as e:
        print(f"❌ AWS S3 connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check AWS credentials in .env file")
        print("  2. Verify IAM permissions for S3")
        print("  3. Ensure bucket exists: aws s3 ls")
        return False


def test_airflow_reachable():
    """Test if Airflow UI is accessible"""
    print("\n" + "="*50)
    print("Testing Airflow Web UI")
    print("="*50)
    
    try:
        import requests
        
        url = "http://localhost:8081/health"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print("✅ Airflow Web UI is accessible")
            print("   URL: http://localhost:8081")
            print("   Login: admin / admin123")
            return True
        else:
            print(f"⚠️ Airflow returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot reach Airflow Web UI")
        print("\nTroubleshooting:")
        print("  1. Check if Airflow is running: docker ps | grep airflow")
        print("  2. Start services: docker-compose up -d")
        print("  3. Wait 30 seconds for initialization")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def check_dag_file():
    """Check if DAG file exists and is valid"""
    print("\n" + "="*50)
    print("Checking DAG File")
    print("="*50)
    
    dag_file = "dags/ingest_postgres_orders.py"
    
    if not os.path.exists(dag_file):
        print(f"❌ DAG file not found: {dag_file}")
        return False
    
    try:
        # Try to import and check syntax
        with open(dag_file, 'r', encoding='utf-8') as f:
            code = f.read()
            compile(code, dag_file, 'exec')
        
        print(f"✅ DAG file exists and syntax is valid")
        print(f"   Location: {dag_file}")
        print(f"   Size: {len(code)} bytes")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in DAG file: {str(e)}")
        return False
    except UnicodeDecodeError as e:
        print(f"❌ Encoding error in DAG file: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Airflow Connection Test Suite")
    print("Modern E-Commerce Analytics Platform")
    print("="*60)
    
    results = {
        "PostgreSQL": test_postgres_connection(),
        "AWS S3": test_aws_connection(),
        "Airflow UI": test_airflow_reachable(),
        "DAG File": check_dag_file(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed! Ready to run Airflow DAGs.")
        print("\nNext steps:")
        print("  1. Open Airflow UI: http://localhost:8081")
        print("  2. Create Airflow connections (see airflow-setup-guide.md)")
        print("  3. Trigger DAG: ingest_postgres_orders")
    else:
        print("\n⚠️ Some tests failed. Fix issues before running DAGs.")
        print("   See troubleshooting in each section above.")
    
    print()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
