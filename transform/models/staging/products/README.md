# Staging - Products

## Purpose
Clean and standardize product catalog data from FakeStore API.

## Models
- `stg_products.sql` - Product master data with standardized attributes

## Source
- **API:** FakeStore API
- **Endpoint:** /products
- **Ingestion:** Daily full refresh via Airflow DAG

## Transformations Applied
1. Column renaming to snake_case convention
2. Price normalization to decimal(10,2)
3. Rating extraction from nested JSON
4. Category standardization
5. Description text cleaning
6. Image URL validation

## Dependencies
- Source: `raw_products` (S3 JSON files)
- Next Layer: `marts/dimensions/dim_products`

## Data Quality Checks
- [ ] product_id uniqueness
- [ ] title not null
- [ ] price > 0
- [ ] category in predefined list
- [ ] rating between 0 and 5
- [ ] image_url format validation
