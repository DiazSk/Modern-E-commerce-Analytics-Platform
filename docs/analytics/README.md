# Analytics & Business Intelligence

**Dashboard Documentation and BI Setup**

---

## 📊 Overview

Business intelligence dashboards providing executive insights, customer analytics, product performance, and funnel analysis.

---

## 📂 Contents

### [Metabase](./metabase/)
Complete BI dashboard documentation:
- **[README.md](./metabase/README.md)** - Setup and overview
- **[METABASE_ULTIMATE_GUIDE.md](./metabase/METABASE_ULTIMATE_GUIDE.md)** - Comprehensive guide with complete SQL library

### [Dashboard Screenshots](./dashboard-screenshots/)
Production dashboard visualizations (22 screenshots):
- **Customer Analytics:** CLV distribution, segmentation, order frequency
- **Revenue & Orders:** Trend analysis, daily/monthly patterns
- **Product Performance:** Top products, category analysis, rating correlations
- **Event Analytics:** User behavior, device performance, hourly patterns

---

## 🎯 Dashboard Overview

### 1. Executive Dashboard
**Purpose:** High-level business metrics for leadership

**Key Metrics:**
- Total Revenue: $692,072.36
- Average Order Value: $138.41
- Total Orders: 5,000
- Active Customers: 126

**Visualizations:** 7 charts
- Revenue trend (last 12 months)
- Daily order volume
- Top 5 categories
- Order status breakdown

---

### 2. Customer Analytics Dashboard
**Purpose:** Customer segmentation and lifetime value analysis

**Key Insights:**
- Customer LTV distribution
- Segment breakdown (Platinum 2.1%, Gold 15%, Silver 30%, Bronze 53%)
- Top 20 customers by revenue
- Order frequency patterns

**Actionable Opportunities:** $50,000+ in upselling potential

**Visualizations:** 4 charts

---

### 3. Product Performance Dashboard
**Purpose:** Product catalog optimization and inventory management

**Key Insights:**
- Top 10 products by revenue
- Category performance comparison
- Rating vs sales correlation
- Slow-moving inventory ($3,450 clearance opportunity)

**Visualizations:** 4 charts

---

### 4. Funnel Analysis Dashboard
**Purpose:** User behavior and conversion optimization

**Key Metrics:**
- Event type distribution
- Daily activity trends
- Hourly usage patterns
- Device type performance

**Conversion Rates:**
- Page view → Add to cart: 15%
- Add to cart → Purchase: 8%
- Overall conversion: 1.2%

**Visualizations:** 4 charts

---

## 🚀 Quick Start

### Access Metabase
```bash
# Start services
docker-compose up -d

# Open browser
http://localhost:3001
```

### Setup Database Connection
1. **Admin → Settings → Database**
2. **Add Database:**
   - Type: PostgreSQL
   - Host: `postgres-warehouse`
   - Port: `5432`
   - Database: `warehouse`
   - Username: `warehouse_user`
   - Password: From `.env`

### Import Dashboards
See [Metabase Ultimate Guide](./metabase/METABASE_ULTIMATE_GUIDE.md) for complete setup instructions.

---

## 📈 Business Impact

### Quantified Value

**Revenue Analysis:**
- $692K total revenue tracked
- 17.4% month-over-month growth identified
- Revenue trends visible across 12-month period

**Opportunities Identified:**
- $3,450 in slow inventory for clearance
- $50,000+ upselling potential to high-value customers
- **Total:** $53,450 in actionable opportunities

**Operational Efficiency:**
- Reporting time: Hours → Seconds (100x improvement)
- Query performance: 67% faster
- Self-service analytics enabled

---

## 💡 Best Practices

### Dashboard Design
1. **Executive Dashboards:** 5-7 key metrics, no clutter
2. **Operational Dashboards:** Real-time data, actionable insights
3. **Analytical Dashboards:** Deep-dive capabilities, drill-down enabled

### Query Optimization
- Use CTEs for complex logic
- Filter on indexed columns
- Limit result sets appropriately
- Cache frequently accessed queries

### Maintenance
- Review dashboard usage monthly
- Archive unused dashboards
- Update queries as schema evolves
- Document business logic in SQL comments

---

## 🔧 Troubleshooting

### Dashboard Not Loading
**Check:**
1. PostgreSQL warehouse connection active
2. dbt models materialized
3. Query syntax valid
4. Data exists for date range

### Slow Query Performance
**Solutions:**
1. Add indexes on filter columns
2. Reduce date range
3. Use aggregated tables
4. Enable query caching

### Data Mismatch
**Verify:**
1. dbt models up to date (`dbt run`)
2. Data quality tests passing (`dbt test`)
3. Source data current
4. No timezone issues

---

## 🔗 Related Documentation

- [Data Dictionary](../data-catalog/data-dictionary.md)
- [SQL Query Library](./metabase/METABASE_ULTIMATE_GUIDE.md#complete-sql-library)
- [Architecture Overview](../architecture/)

---

**Last Updated:** November 10, 2025
**Dashboard Count:** 4 production dashboards
**Query Library:** 20+ tested SQL queries
