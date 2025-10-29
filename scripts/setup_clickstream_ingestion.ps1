# ============================================
# Clickstream Ingestion Setup Script (PowerShell)
# Copies CSV file to Airflow container
# ============================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Clickstream Ingestion - File Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if CSV file exists locally
if (-not (Test-Path "data\generated\clickstream_events.csv")) {
    Write-Host "❌ ERROR: clickstream_events.csv not found" -ForegroundColor Red
    Write-Host "   Expected location: data\generated\clickstream_events.csv"
    Write-Host ""
    Write-Host "   Run data generation first:"
    Write-Host "   python scripts\generate_data.py"
    exit 1
}

Write-Host "✅ Found clickstream_events.csv locally" -ForegroundColor Green
Write-Host ""

# Check if Docker container is running
$container = docker ps | Select-String "ecommerce-airflow-webserver"
if (-not $container) {
    Write-Host "❌ ERROR: Airflow webserver container not running" -ForegroundColor Red
    Write-Host "   Start services first:"
    Write-Host "   docker-compose up -d"
    exit 1
}

Write-Host "✅ Airflow container is running" -ForegroundColor Green
Write-Host ""

# Create directory in container
Write-Host "📁 Creating directory in container..." -ForegroundColor Yellow
docker exec -it ecommerce-airflow-webserver mkdir -p /opt/airflow/data/generated

# Copy file to container
Write-Host "📤 Copying CSV file to container..." -ForegroundColor Yellow
docker cp data\generated\clickstream_events.csv ecommerce-airflow-webserver:/opt/airflow/data/generated/

# Verify file copied
Write-Host "🔍 Verifying file..." -ForegroundColor Yellow
$fileInfo = docker exec -it ecommerce-airflow-webserver ls -lh /opt/airflow/data/generated/clickstream_events.csv

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "File copied to: /opt/airflow/data/generated/clickstream_events.csv"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open Airflow UI: http://localhost:8081"
Write-Host "  2. Find DAG: ingest_clickstream_events"
Write-Host "  3. Trigger manually"
Write-Host "  4. Wait ~1-2 minutes for 50K events to process"
Write-Host "==================================================" -ForegroundColor Green
