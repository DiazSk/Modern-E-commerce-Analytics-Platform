#!/usr/bin/env python3
"""
Create expectations - FIXED for correct schema
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
os.chdir(PROJECT_ROOT)

import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.core.expectation_suite import ExpectationSuite

def main():
    print("\n" + "=" * 80)
    print("CREATING EXPECTATIONS - CORRECT SCHEMA FIX")
    print("=" * 80 + "\n")
    
    try:
        # Get context
        context = gx.get_context()
        print(f"✓ Context loaded from: {context.root_directory}\n")
        
        # Create expectation suite
        suite_name = "orders_quality_suite"
        
        try:
            suite = context.add_or_update_expectation_suite(expectation_suite_name=suite_name)
            print(f"✓ Created/updated suite: {suite_name}\n")
        except:
            suite = ExpectationSuite(expectation_suite_name=suite_name)
            context.save_expectation_suite(expectation_suite=suite)
            print(f"✓ Created suite: {suite_name}\n")
        
        # FIXED: Use correct schema - public_marts_core, not public
        batch_request = RuntimeBatchRequest(
            datasource_name="postgres_datasource",
            data_connector_name="default_runtime_data_connector",
            data_asset_name="fact_orders",
            runtime_parameters={
                "query": "SELECT * FROM public_marts_core.fact_orders LIMIT 10000"
            },
            batch_identifiers={
                "default_identifier_name": "fact_orders_sample"
            }
        )
        
        # Create validator
        validator = context.get_validator(
            batch_request=batch_request,
            expectation_suite_name=suite_name,
        )
        
        print("✓ Validator created\n")
        print("Adding 15 expectations...\n")
        
        # Table-level (2)
        validator.expect_table_row_count_to_be_between(min_value=0, max_value=10000000)
        print("✓ 1/15: Table row count")
        
        validator.expect_table_columns_to_match_set(
            column_set=["order_item_key", "customer_key", "product_key", "date_key",
                       "order_id", "order_date", "quantity", "unit_price",
                       "line_total", "order_status", "payment_method"],
            exact_match=False
        )
        print("✓ 2/15: Table columns")
        
        # Primary key (2)
        validator.expect_column_values_to_be_unique(column="order_item_key")
        print("✓ 3/15: Primary key unique")
        
        validator.expect_column_values_to_not_be_null(column="order_item_key")
        print("✓ 4/15: Primary key not null")
        
        # Foreign keys (3)
        validator.expect_column_values_to_not_be_null(column="customer_key")
        print("✓ 5/15: customer_key not null")
        
        validator.expect_column_values_to_not_be_null(column="product_key")
        print("✓ 6/15: product_key not null")
        
        validator.expect_column_values_to_not_be_null(column="date_key")
        print("✓ 7/15: date_key not null")
        
        # Numeric ranges (4)
        validator.expect_column_values_to_be_between(column="quantity", min_value=1, max_value=100)
        print("✓ 8/15: quantity range")
        
        validator.expect_column_values_to_be_between(column="unit_price", min_value=0.01, max_value=10000.00)
        print("✓ 9/15: unit_price range")
        
        validator.expect_column_values_to_be_between(column="line_total", min_value=0, max_value=None)
        print("✓ 10/15: line_total range")
        
        validator.expect_column_values_to_be_between(column="discount_amount", min_value=0, max_value=None)
        print("✓ 11/15: discount_amount range")
        
        # Categorical (2)
        validator.expect_column_values_to_be_in_set(
            column="order_status",
            value_set=["pending", "processing", "shipped", "delivered", "cancelled"]
        )
        print("✓ 12/15: order_status values")
        
        validator.expect_column_values_to_be_in_set(
            column="payment_method",
            value_set=["credit_card", "debit_card", "paypal", "bank_transfer", "cash"]
        )
        print("✓ 13/15: payment_method values")
        
        # Date/time (2)
        validator.expect_column_values_to_not_be_null(column="order_date")
        print("✓ 14/15: order_date not null")
        
        validator.expect_column_values_to_not_be_null(column="order_timestamp")
        print("✓ 15/15: order_timestamp not null")
        
        # Save
        print("\nSaving expectation suite...")
        validator.save_expectation_suite(discard_failed_expectations=False)
        
        suite = validator.get_expectation_suite()
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS! ALL EXPECTATIONS CREATED!")
        print("=" * 80)
        print(f"\n✓ Suite: {suite_name}")
        print(f"✓ Schema: public_marts_core.fact_orders")
        print(f"✓ Location: gx/expectations/")
        print(f"✓ Total expectations: {len(suite.expectations)}")
        print(f"\n🚀 Ready for Week 5 Day 3-5 completion!\n")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
