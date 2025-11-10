#!/bin/bash
# ============================================
# Clickstream Ingestion Setup Script
# Copies CSV file to Airflow container
# ============================================

echo "=================================================="
echo "Clickstream Ingestion - File Setup"
echo "=================================================="
echo ""

# Check if CSV file exists locally
if [ ! -f "data/generated/clickstream_events.csv" ]; then
    echo "❌ ERROR: clickstream_events.csv not found"
    echo "   Expected location: data/generated/clickstream_events.csv"
    echo ""
    echo "   Run data generation first:"
    echo "   python scripts/generate_data.py"
    exit 1
fi

echo "✅ Found clickstream_events.csv locally"
echo ""

# Check if Docker container is running
if ! docker ps | grep -q "ecommerce-airflow-webserver"; then
    echo "❌ ERROR: Airflow webserver container not running"
    echo "   Start services first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "✅ Airflow container is running"
echo ""

# Create directory in container
echo "📁 Creating directory in container..."
docker exec -it ecommerce-airflow-webserver mkdir -p /opt/airflow/data/generated

# Copy file to container
echo "📤 Copying CSV file to container..."
docker cp data/generated/clickstream_events.csv ecommerce-airflow-webserver:/opt/airflow/data/generated/

# Verify file copied
echo "🔍 Verifying file..."
FILE_SIZE=$(docker exec -it ecommerce-airflow-webserver ls -lh /opt/airflow/data/generated/clickstream_events.csv | awk '{print $5}')

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo "File copied to: /opt/airflow/data/generated/clickstream_events.csv"
echo "File size: $FILE_SIZE"
echo ""
echo "Next steps:"
echo "  1. Open Airflow UI: http://localhost:8081"
echo "  2. Find DAG: ingest_clickstream_events"
echo "  3. Trigger manually"
echo "  4. Wait ~1-2 minutes for 50K events to process"
echo "=================================================="
