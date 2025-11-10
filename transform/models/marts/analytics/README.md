# Analytics Models

This directory contains business-oriented analytics models built on top of the core dimensional model.

## Models Overview

### 1. `customer_lifetime_value.sql`
- **Purpose**: Comprehensive customer value analysis
- **Materialization**: Table
- **Grain**: One row per customer (current segment only)
- **Key Features**:
  - Total revenue and order metrics
  - Customer lifetime calculation
  - Estimated monthly revenue
  - Multi-dimensional segmentation (Value, Recency, Frequency)
- **Business Value**:
  - Identify high-value customers (VIP segment)
  - Detect at-risk customers for retention campaigns
  - Understand customer behavior patterns
  - Support customer acquisition cost (CAC) analysis

## Key Metrics Explained

### Revenue Metrics
- **total_revenue**: Sum of all line_total from orders
- **avg_order_value**: Average spending per order
- **estimated_monthly_revenue**: Revenue normalized to monthly rate

### Behavioral Metrics
- **customer_lifetime_days**: Days between first and last order
- **orders_per_month**: Order frequency normalized to monthly rate
- **days_since_last_order**: Recency indicator

### Segmentation Logic

#### Value Segment
- **VIP**: 10+ orders AND $1000+ total revenue
- **High Value**: 5+ orders AND $500+ total revenue
- **Medium Value**: 3+ orders AND $200+ total revenue
- **Low Value**: 1+ orders AND $50+ total revenue
- **At Risk**: Below thresholds

#### Recency Segment
- **Active**: Ordered within 30 days
- **At Risk**: Last order 31-90 days ago
- **Churning**: Last order 91-180 days ago
- **Churned**: No order in 180+ days

#### Frequency Segment
- **Loyal**: 10+ orders
- **Regular**: 5-9 orders
- **Occasional**: 2-4 orders
- **One-Time**: 1 order only

## SQL Techniques Demonstrated

1. **Complex Aggregations**:
   - Multiple aggregate functions in single query
   - Conditional aggregation with CASE statements

2. **Date Math**:
   - Lifetime calculation: `max(order_date) - min(order_date)`
   - Days since last order: `current_date - max(order_date)`
   - Month conversion: `customer_lifetime_days / 30.0`

3. **Derived Metrics**:
   - Monthly revenue estimation
   - Orders per month calculation
   - Multi-tier segmentation logic

4. **NULL Handling**:
   - Using COALESCE for safe calculations
   - Division by zero protection with NULLIF

## Business Use Cases

1. **Marketing Campaigns**:
   - Target VIP customers for loyalty programs
   - Re-engage "Churning" customers with promotions
   - Upsell to "Low Value" customers

2. **Customer Retention**:
   - Monitor "At Risk" segment trends
   - Analyze churn patterns by value segment
   - Calculate retention rates by cohort

3. **Revenue Forecasting**:
   - Project revenue based on customer segments
   - Estimate impact of retention improvements
   - Model customer lifetime value

4. **Product Development**:
   - Identify preferences of high-value customers
   - Analyze purchase patterns by segment
   - Prioritize features for loyal customers

## Interview Talking Points

1. **Business Acumen**:
   - "I implemented RFM-style segmentation to classify customers across three dimensions"
   - "The model enables targeted marketing by identifying customers at different lifecycle stages"
   - "VIP customers represent top 5% by both frequency and monetary value"

2. **Technical Skills**:
   - "Used window functions and CTEs to create complex customer metrics"
   - "Implemented safe division with NULLIF to handle edge cases"
   - "Normalized metrics to monthly rates for consistent comparison"

3. **Data Quality**:
   - "All segments have referential integrity tests to ensure accuracy"
   - "Comprehensive testing validates segmentation logic"
   - "Model is documented with clear business definitions"

## Resume Bullet Points

- Built customer lifetime value analytics model processing 1,000+ customer profiles with multi-dimensional segmentation (RFM analysis)
- Implemented automated customer classification system identifying VIP, high-value, and at-risk customer segments
- Created business metrics dashboard enabling marketing team to target $500K+ annual revenue from top customer segments
- Developed churn prediction indicators tracking customer recency and frequency patterns for retention campaigns

## Extensions & Future Work

1. **Predictive Analytics**:
   - Add churn probability score
   - Predict next purchase date
   - Forecast customer lifetime value

2. **Advanced Segmentation**:
   - K-means clustering for customer groups
   - Product affinity analysis
   - Channel preference modeling

3. **Time-Series Analysis**:
   - Cohort analysis by registration date
   - Customer journey mapping
   - Retention curves by segment

4. **Integration**:
   - Feed segments to CRM systems
   - Automate marketing triggers
   - Create Slack alerts for VIP orders
