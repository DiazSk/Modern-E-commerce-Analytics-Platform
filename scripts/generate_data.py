"""
============================================
Modern E-Commerce Analytics Platform
Synthetic Data Generation Script
============================================

This script generates realistic e-commerce data for the analytics platform:
- Customers (with SCD Type 2 segments)
- Orders (with realistic patterns)
- Order Items (line items)
- Clickstream Events (user behavior)

Usage:
    python scripts/generate_data.py

Output:
    - CSV files in data/ directory
    - Direct PostgreSQL insertion (optional)
    
Author: Zaid Shaikh
Date: October 2025
============================================
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os
import logging
from pathlib import Path

# ============================================
# CONFIGURATION
# ============================================

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)

fake = Faker()

# Data generation parameters
N_CUSTOMERS = 1000
N_ORDERS = 5000
N_PRODUCTS = 200  # Product catalog size
N_CLICKSTREAM_EVENTS = 50000

# Date ranges
# Generate data up to yesterday to ensure we have complete daily batches
START_DATE = datetime.now() - timedelta(days=730)  # 2 years ago
END_DATE = datetime.now() - timedelta(days=1)  # Up to yesterday

# Output directory
OUTPUT_DIR = Path('data/generated')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# HELPER FUNCTIONS
# ============================================

def weighted_choice(choices, weights):
    """Select item from choices based on weights"""
    return random.choices(choices, weights=weights, k=1)[0]

def generate_realistic_date(start_date, end_date, peak_hours=None):
    """Generate date with realistic business patterns"""
    # Random date in range
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randint(0, days_between)
    random_date = start_date + timedelta(days=random_days)
    
    # Add realistic hour patterns if specified
    if peak_hours:
        hour = weighted_choice(
            range(24),
            [peak_hours.get(h, 1) for h in range(24)]
        )
    else:
        hour = random.randint(0, 23)
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return random_date.replace(hour=hour, minute=minute, second=second)

# ============================================
# CUSTOMER DATA GENERATION
# ============================================

def generate_customers(n=N_CUSTOMERS):
    """
    Generate synthetic customer data with SCD Type 2 fields
    
    Returns:
        pd.DataFrame: Customer data
    """
    logger.info(f"Generating {n} customers...")
    
    customers = []
    
    # Customer segments with realistic distribution
    segments = ['bronze', 'silver', 'gold', 'platinum']
    segment_weights = [0.50, 0.30, 0.15, 0.05]  # Most customers are bronze
    
    for i in range(n):
        registration_date = fake.date_between(start_date='-2y', end_date='today')
        
        # Segment assignment (current segment)
        current_segment = weighted_choice(segments, segment_weights)
        
        # Segment start date (could be different from registration)
        # Some customers upgrade/downgrade over time
        if random.random() < 0.3:  # 30% have changed segment
            segment_start = fake.date_between(
                start_date=registration_date,
                end_date='today'
            )
        else:
            segment_start = registration_date
        
        customer = {
            'email': fake.unique.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'phone': fake.phone_number()[:20],  # Limit length
            'registration_date': registration_date,
            'customer_segment': current_segment,
            'segment_start_date': segment_start,
            'segment_end_date': None,  # Current segment
            'is_current': True
        }
        
        customers.append(customer)
    
    df = pd.DataFrame(customers)
    
    logger.info(f"✅ Generated {len(df)} customers")
    logger.info(f"   Segment distribution: {df['customer_segment'].value_counts().to_dict()}")
    
    return df

# ============================================
# ORDER DATA GENERATION
# ============================================

def generate_orders(customers_df, n=N_ORDERS):
    """
    Generate synthetic order data with realistic patterns
    
    Args:
        customers_df: Customer DataFrame with customer_id
        n: Number of orders to generate
        
    Returns:
        pd.DataFrame: Order data
    """
    logger.info(f"Generating {n} orders...")
    
    orders = []
    
    # Payment method distribution (realistic for 2025)
    payment_methods = ['credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay']
    payment_weights = [0.40, 0.25, 0.20, 0.10, 0.05]
    
    # Order status distribution
    statuses = ['completed', 'pending', 'processing', 'cancelled', 'returned']
    status_weights = [0.75, 0.10, 0.08, 0.05, 0.02]
    
    # Peak shopping hours (higher weights = more orders)
    peak_hours = {
        9: 2, 10: 3, 11: 4, 12: 5,  # Morning peak
        13: 4, 14: 3,
        19: 4, 20: 5, 21: 6, 22: 4  # Evening peak
    }
    
    # Customer purchase frequency (Pareto principle: 20% generate 80% of orders)
    frequent_customers = customers_df.sample(n=int(len(customers_df) * 0.2))
    occasional_customers = customers_df[~customers_df.index.isin(frequent_customers.index)]
    
    for i in range(n):
        # 80% of orders from 20% of customers
        if random.random() < 0.8 and len(frequent_customers) > 0:
            customer = frequent_customers.sample(n=1).iloc[0]
        else:
            customer = occasional_customers.sample(n=1).iloc[0]
        
        order_date = generate_realistic_date(START_DATE, END_DATE, peak_hours)
        
        # Order total influenced by customer segment
        segment = customer['customer_segment']
        if segment == 'platinum':
            order_total = round(random.uniform(150, 800), 2)
        elif segment == 'gold':
            order_total = round(random.uniform(80, 400), 2)
        elif segment == 'silver':
            order_total = round(random.uniform(40, 200), 2)
        else:  # bronze
            order_total = round(random.uniform(20, 150), 2)
        
        order = {
            'customer_id': customer['email'],  # Will map to actual ID later
            'order_date': order_date,
            'order_total': order_total,
            'payment_method': weighted_choice(payment_methods, payment_weights),
            'shipping_address': fake.address().replace('\n', ', '),
            'order_status': weighted_choice(statuses, status_weights)
        }
        
        orders.append(order)
    
    df = pd.DataFrame(orders)
    
    # Sort by date for realistic incremental loading
    df = df.sort_values('order_date').reset_index(drop=True)
    
    logger.info(f"✅ Generated {len(df)} orders")
    logger.info(f"   Status distribution: {df['order_status'].value_counts().to_dict()}")
    logger.info(f"   Date range: {df['order_date'].min()} to {df['order_date'].max()}")
    
    return df

# ============================================
# ORDER ITEMS GENERATION
# ============================================

def generate_order_items(orders_df):
    """
    Generate order line items for each order
    
    Args:
        orders_df: Orders DataFrame
        
    Returns:
        pd.DataFrame: Order items data
    """
    logger.info(f"Generating order items for {len(orders_df)} orders...")
    
    order_items = []
    
    for idx, order in orders_df.iterrows():
        order_id = idx + 1  # Assuming sequential IDs
        order_total = order['order_total']
        
        # Number of items per order (1-5 items, weighted toward 1-2)
        n_items = weighted_choice([1, 2, 3, 4, 5], [0.40, 0.35, 0.15, 0.07, 0.03])
        
        # Distribute order total across items
        remaining_total = order_total
        
        for i in range(n_items):
            # Product ID (1 to N_PRODUCTS)
            product_id = random.randint(1, N_PRODUCTS)
            
            # Quantity (most orders have quantity 1-2)
            quantity = weighted_choice([1, 2, 3, 4, 5], [0.60, 0.25, 0.10, 0.03, 0.02])
            
            # Unit price
            if i == n_items - 1:  # Last item gets remaining amount
                unit_price = round(remaining_total / quantity, 2)
            else:
                # Allocate portion of order total
                max_price = remaining_total / (n_items - i)
                unit_price = round(random.uniform(5, min(max_price, 200)) / quantity, 2)
            
            # Discount (20% of orders have discount)
            if random.random() < 0.20:
                max_discount = unit_price * quantity * 0.3  # Max 30% discount
                discount_amount = round(random.uniform(1, max_discount), 2)
            else:
                discount_amount = 0.00
            
            line_total = quantity * unit_price - discount_amount
            remaining_total -= line_total
            
            item = {
                'order_id': order_id,
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price,
                'discount_amount': discount_amount
            }
            
            order_items.append(item)
    
    df = pd.DataFrame(order_items)
    
    logger.info(f"✅ Generated {len(df)} order items")
    logger.info(f"   Average items per order: {len(df) / len(orders_df):.2f}")
    logger.info(f"   Products referenced: {df['product_id'].nunique()}")
    
    return df

# ============================================
# CLICKSTREAM EVENTS GENERATION
# ============================================

def generate_clickstream_events(customers_df, n=N_CLICKSTREAM_EVENTS):
    """
    Generate synthetic clickstream/user behavior events
    
    Args:
        customers_df: Customer DataFrame
        n: Number of events to generate
        
    Returns:
        pd.DataFrame: Clickstream events
    """
    logger.info(f"Generating {n} clickstream events...")
    
    events = []
    
    # Event types with realistic distribution
    event_types = ['page_view', 'add_to_cart', 'remove_from_cart', 'purchase', 'search']
    event_weights = [0.60, 0.15, 0.05, 0.08, 0.12]
    
    # Device types (mobile-first in 2025)
    devices = ['mobile', 'desktop', 'tablet']
    device_weights = [0.65, 0.30, 0.05]
    
    # Browsers
    browsers = ['chrome', 'safari', 'firefox', 'edge']
    browser_weights = [0.50, 0.30, 0.15, 0.05]
    
    # Peak browsing hours
    peak_hours = {
        8: 2, 9: 3, 10: 3, 11: 4, 12: 5,  # Morning
        13: 4, 14: 3, 15: 3,
        19: 5, 20: 6, 21: 7, 22: 6, 23: 4  # Evening peak
    }
    
    for i in range(n):
        # Random customer (user_id references customer email for now)
        customer = customers_df.sample(n=1).iloc[0]
        
        # Event timestamp
        event_timestamp = generate_realistic_date(
            START_DATE - timedelta(days=30),  # Last 30 days more events
            END_DATE,
            peak_hours
        )
        
        event = {
            'event_id': fake.uuid4(),
            'session_id': fake.uuid4(),
            'user_id': customer['email'],
            'event_timestamp': event_timestamp,
            'event_type': weighted_choice(event_types, event_weights),
            'product_id': random.randint(1, N_PRODUCTS),
            'page_url': fake.uri_path(),
            'device_type': weighted_choice(devices, device_weights),
            'browser': weighted_choice(browsers, browser_weights)
        }
        
        events.append(event)
    
    df = pd.DataFrame(events)
    
    # Sort by timestamp
    df = df.sort_values('event_timestamp').reset_index(drop=True)
    
    logger.info(f"✅ Generated {len(df)} clickstream events")
    logger.info(f"   Event type distribution: {df['event_type'].value_counts().to_dict()}")
    logger.info(f"   Device distribution: {df['device_type'].value_counts().to_dict()}")
    
    return df

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main execution function"""
    logger.info("=" * 50)
    logger.info("Starting Data Generation Process")
    logger.info("=" * 50)
    
    try:
        # Generate customers
        customers_df = generate_customers(N_CUSTOMERS)
        customers_df.to_csv(OUTPUT_DIR / 'customers.csv', index=False)
        logger.info(f"💾 Saved: {OUTPUT_DIR / 'customers.csv'}")
        
        # Generate orders
        orders_df = generate_orders(customers_df, N_ORDERS)
        orders_df.to_csv(OUTPUT_DIR / 'orders.csv', index=False)
        logger.info(f"💾 Saved: {OUTPUT_DIR / 'orders.csv'}")
        
        # Generate order items
        order_items_df = generate_order_items(orders_df)
        order_items_df.to_csv(OUTPUT_DIR / 'order_items.csv', index=False)
        logger.info(f"💾 Saved: {OUTPUT_DIR / 'order_items.csv'}")
        
        # Generate clickstream events
        clickstream_df = generate_clickstream_events(customers_df, N_CLICKSTREAM_EVENTS)
        clickstream_df.to_csv(OUTPUT_DIR / 'clickstream_events.csv', index=False)
        logger.info(f"💾 Saved: {OUTPUT_DIR / 'clickstream_events.csv'}")
        
        # Summary statistics
        logger.info("\n" + "=" * 50)
        logger.info("DATA GENERATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"✅ Customers: {len(customers_df):,}")
        logger.info(f"✅ Orders: {len(orders_df):,}")
        logger.info(f"✅ Order Items: {len(order_items_df):,}")
        logger.info(f"✅ Clickstream Events: {len(clickstream_df):,}")
        logger.info(f"📁 Output Directory: {OUTPUT_DIR.absolute()}")
        logger.info("=" * 50)
        
        # Data quality checks
        logger.info("\nDATA QUALITY CHECKS:")
        logger.info(f"✓ Unique customer emails: {customers_df['email'].is_unique}")
        logger.info(f"✓ All orders have positive totals: {(orders_df['order_total'] > 0).all()}")
        logger.info(f"✓ All order items have positive quantities: {(order_items_df['quantity'] > 0).all()}")
        logger.info(f"✓ No null values in customers: {customers_df.isnull().sum().sum() == 0}")
        
        logger.info("\n🎉 Data generation completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during data generation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)