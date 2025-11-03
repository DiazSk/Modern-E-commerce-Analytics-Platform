"""
Load Products from S3 JSON to PostgreSQL
"""
import boto3
import psycopg2
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
S3_BUCKET = os.getenv('S3_RAW_BUCKET', 'ecommerce-raw-data-bnf5etbn')
S3_PREFIX = 'raw/products/'

# PostgreSQL Configuration
PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ecommerce',
    'user': 'ecommerce_user',
    'password': 'ecommerce_pass'
}

def create_products_table():
    """Create products table if not exists"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        title VARCHAR(500),
        price DECIMAL(10,2),
        category VARCHAR(100),
        description TEXT,
        image VARCHAR(500),
        rating_rate DECIMAL(3,2),
        rating_count INTEGER,
        ingestion_timestamp TIMESTAMP,
        ingestion_date DATE,
        data_source VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
    CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
    """
    
    cur.execute(create_table_sql)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Products table created successfully")


def load_products_from_s3():
    """Load products from S3 JSON files to PostgreSQL"""
    s3 = boto3.client('s3')
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # List all product files in S3
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
    
    if 'Contents' not in response:
        print("❌ No products found in S3")
        return
    
    total_products = 0
    processed_files = 0
    
    for obj in response['Contents']:
        if obj['Key'].endswith('.json'):
            print(f"Processing: {obj['Key']}")
            
            # Download JSON from S3
            file_obj = s3.get_object(Bucket=S3_BUCKET, Key=obj['Key'])
            json_content = file_obj['Body'].read().decode('utf-8')
            products = json.loads(json_content)
            
            # Insert each product
            for product in products:
                insert_sql = """
                INSERT INTO products (
                    product_id, title, price, category, description, image,
                    rating_rate, rating_count, ingestion_timestamp, 
                    ingestion_date, data_source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    price = EXCLUDED.price,
                    category = EXCLUDED.category,
                    description = EXCLUDED.description,
                    image = EXCLUDED.image,
                    rating_rate = EXCLUDED.rating_rate,
                    rating_count = EXCLUDED.rating_count;
                """
                
                rating = product.get('rating', {})
                
                cur.execute(insert_sql, (
                    product['id'],
                    product['title'],
                    product['price'],
                    product['category'],
                    product['description'],
                    product['image'],
                    rating.get('rate', 0),
                    rating.get('count', 0),
                    product.get('ingestion_timestamp'),
                    product.get('ingestion_date'),
                    product.get('data_source', 'fakestoreapi')
                ))
                total_products += 1
            
            processed_files += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Processed {processed_files} files")
    print(f"✅ Loaded {total_products} products to PostgreSQL")


if __name__ == "__main__":
    print("=" * 60)
    print("Starting products data load from S3 to PostgreSQL...")
    print("=" * 60)
    create_products_table()
    load_products_from_s3()
    print("=" * 60)
    print("Products load complete! 🎉")
    print("=" * 60)
