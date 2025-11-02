# Staging - Events

## Purpose
Clean and standardize clickstream event data from web analytics.

## Models
- `stg_clickstream_events.sql` - User interaction events with session tracking

## Source
- **Format:** CSV files
- **Location:** S3 raw bucket
- **Ingestion:** Hourly batch via Airflow DAG

## Transformations Applied
1. Column renaming to snake_case convention
2. Timestamp parsing to datetime with timezone
3. User agent parsing (browser, device, OS)
4. Session ID generation from user + timestamp window
5. Event type validation and standardization
6. URL parameter extraction
7. Referrer categorization

## Dependencies
- Source: `raw_clickstream_events` (S3 CSV files)
- Next Layer: `intermediate/user_sessions` or `marts/core`

## Data Quality Checks
- [ ] event_id uniqueness
- [ ] user_id not null for logged-in events
- [ ] timestamp within valid range (not future)
- [ ] event_type in accepted values
- [ ] page_url format validation
- [ ] session_id consistency within time windows

## Event Types
- `page_view` - User viewed a page
- `add_to_cart` - Product added to cart
- `remove_from_cart` - Product removed from cart
- `checkout_start` - Checkout process initiated
- `purchase` - Order completed
- `search` - Search query performed
- `product_click` - Product detail page clicked
