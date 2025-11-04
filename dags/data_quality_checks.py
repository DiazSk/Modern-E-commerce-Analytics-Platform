"""
==============================================================================
Data Quality Validation DAG - Great Expectations Integration
==============================================================================
Purpose: Automated data quality checks using Great Expectations

This DAG:
1. Runs Great Expectations checkpoint on fact_orders table
2. Validates data quality against predefined expectations
3. Updates data docs with validation results
4. Sends alerts on validation failures
5. Can block downstream processing if quality checks fail

Schedule: Daily after fact_orders is loaded
Depends on: fact_orders table populated

Expectations Validated:
- Table row count within expected range
- Primary key uniqueness
- Foreign keys not null
- Numeric value ranges
- Categorical value validity
- Business logic correctness

Usage:
- Manual trigger: airflow dags trigger data_quality_validation
- View logs: airflow tasks logs data_quality_validation validate_data_quality <date>
- Test: airflow tasks test data_quality_validation validate_data_quality <date>

Author: Zaid
Date: 2025-11-03
==============================================================================
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import great_expectations as gx
from great_expectations.checkpoint import SimpleCheckpoint
from great_expectations.data_context import BaseDataContext


# =============================================================================
# DAG CONFIGURATION
# =============================================================================

DEFAULT_ARGS = {
    'owner': 'zaid',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 3),
    'email': ['zaid07sk@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# DAG schedule: Run daily at 1 AM (after data loads)
SCHEDULE_INTERVAL = '0 1 * * *'  # Daily at 1 AM

# Great Expectations configuration
GE_DIRECTORY = PROJECT_ROOT / "great_expectations"
CHECKPOINT_NAME = "orders_checkpoint"
SUITE_NAME = "orders_quality_suite"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_great_expectations_context() -> BaseDataContext:
    """
    Load Great Expectations data context.
    
    Returns:
        BaseDataContext: Great Expectations context
        
    Raises:
        Exception: If context cannot be loaded
    """
    try:
        context = gx.get_context()
        return context
    except Exception as e:
        raise Exception(f"Failed to load Great Expectations context: {e}")


def log_validation_summary(results: dict) -> None:
    """
    Log validation results summary.
    
    Args:
        results: Validation results dictionary
    """
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS SUMMARY")
    print("=" * 80)
    
    stats = results.get('statistics', {})
    
    print(f"Success: {results.get('success', False)}")
    print(f"Evaluated Expectations: {stats.get('evaluated_expectations', 0)}")
    print(f"Successful Expectations: {stats.get('successful_expectations', 0)}")
    print(f"Failed Expectations: {stats.get('unsuccessful_expectations', 0)}")
    print(f"Success Rate: {stats.get('success_percent', 0):.2f}%")
    
    if not results.get('success', False):
        print("\n⚠ VALIDATION FAILED - Some expectations did not pass")
        print("\nFailed Expectations:")
        
        for result in results.get('results', []):
            if not result.get('success', True):
                exp_type = result.get('expectation_config', {}).get('expectation_type', 'Unknown')
                column = result.get('expectation_config', {}).get('kwargs', {}).get('column', 'N/A')
                print(f"  - {exp_type} (column: {column})")
    
    print("=" * 80 + "\n")


# =============================================================================
# AIRFLOW TASK FUNCTIONS
# =============================================================================

def validate_data_quality(**context):
    """
    Run Great Expectations checkpoint to validate data quality.
    
    This function:
    1. Loads Great Expectations context
    2. Runs the configured checkpoint
    3. Logs validation results
    4. Raises error if validation fails (blocking downstream tasks)
    
    Args:
        **context: Airflow context (contains execution_date, task_instance, etc.)
        
    Returns:
        dict: Validation results
        
    Raises:
        ValueError: If validation fails
    """
    
    execution_date = context['execution_date']
    task_instance = context['task_instance']
    
    print(f"\n{'=' * 80}")
    print(f"STARTING DATA QUALITY VALIDATION")
    print(f"Execution Date: {execution_date}")
    print(f"{'=' * 80}\n")
    
    try:
        # Load Great Expectations context
        print("Loading Great Expectations context...")
        ge_context = get_great_expectations_context()
        print("✓ Context loaded successfully\n")
        
        # Get checkpoint
        print(f"Loading checkpoint: {CHECKPOINT_NAME}...")
        checkpoint = ge_context.get_checkpoint(name=CHECKPOINT_NAME)
        print("✓ Checkpoint loaded successfully\n")
        
        # Run checkpoint
        print("Running data quality validation...")
        print(f"Suite: {SUITE_NAME}")
        print(f"Table: public.fact_orders")
        print()
        
        checkpoint_result = checkpoint.run(
            run_name=f"airflow_{execution_date.strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Extract results
        validation_result = checkpoint_result.run_results
        
        # Get first (and only) validation result
        first_result_key = list(validation_result.keys())[0]
        result_dict = validation_result[first_result_key]
        
        # Log summary
        log_validation_summary(result_dict)
        
        # Store results in XCom for downstream tasks
        task_instance.xcom_push(key='validation_success', value=result_dict.get('success'))
        task_instance.xcom_push(key='validation_stats', value=result_dict.get('statistics'))
        
        # Check if validation passed
        if not result_dict.get('success', False):
            failed_count = result_dict.get('statistics', {}).get('unsuccessful_expectations', 0)
            
            raise ValueError(
                f"Data quality validation FAILED! "
                f"{failed_count} expectation(s) did not pass. "
                f"Review data docs for details."
            )
        
        print("✓ Data quality validation PASSED!")
        print("✓ All expectations met")
        
        return result_dict
        
    except Exception as e:
        print(f"\n✗ Validation failed with error: {e}")
        raise


def check_validation_status(**context):
    """
    Check validation status from previous task.
    
    This is an optional task that can be used to:
    - Send custom notifications
    - Update monitoring dashboards
    - Trigger remediation workflows
    
    Args:
        **context: Airflow context
    """
    
    task_instance = context['task_instance']
    
    # Pull validation results from XCom
    success = task_instance.xcom_pull(
        task_ids='validate_data_quality',
        key='validation_success'
    )
    
    stats = task_instance.xcom_pull(
        task_ids='validate_data_quality',
        key='validation_stats'
    )
    
    print("\n" + "=" * 80)
    print("VALIDATION STATUS CHECK")
    print("=" * 80)
    
    if success:
        print("✓ Data quality validation: PASSED")
        print(f"✓ Success rate: {stats.get('success_percent', 0):.2f}%")
        print("\nData is ready for downstream processing")
    else:
        print("✗ Data quality validation: FAILED")
        print(f"✗ Failed expectations: {stats.get('unsuccessful_expectations', 0)}")
        print("\n⚠ Review data docs and fix data quality issues")
    
    print("=" * 80 + "\n")


def generate_data_quality_report(**context):
    """
    Generate and store data quality report.
    
    This function creates a summary report of data quality metrics
    that can be:
    - Stored in a database table
    - Sent via email
    - Posted to Slack/Teams
    - Displayed in a dashboard
    
    Args:
        **context: Airflow context
    """
    
    task_instance = context['task_instance']
    execution_date = context['execution_date']
    
    stats = task_instance.xcom_pull(
        task_ids='validate_data_quality',
        key='validation_stats'
    )
    
    report = {
        'execution_date': execution_date.isoformat(),
        'suite_name': SUITE_NAME,
        'table_name': 'public.fact_orders',
        'total_expectations': stats.get('evaluated_expectations', 0),
        'successful_expectations': stats.get('successful_expectations', 0),
        'failed_expectations': stats.get('unsuccessful_expectations', 0),
        'success_rate': stats.get('success_percent', 0),
        'validation_passed': stats.get('unsuccessful_expectations', 0) == 0,
    }
    
    print("\n" + "=" * 80)
    print("DATA QUALITY REPORT")
    print("=" * 80)
    
    for key, value in report.items():
        print(f"{key}: {value}")
    
    print("=" * 80 + "\n")
    
    # Store report in XCom for potential downstream use
    task_instance.xcom_push(key='quality_report', value=report)
    
    return report


# =============================================================================
# DAG DEFINITION
# =============================================================================

with DAG(
    dag_id='data_quality_validation',
    default_args=DEFAULT_ARGS,
    description='Validate data quality using Great Expectations on fact_orders table',
    schedule_interval=SCHEDULE_INTERVAL,
    catchup=False,
    tags=['data-quality', 'great-expectations', 'validation', 'fact-orders'],
    max_active_runs=1,
    doc_md=__doc__,
) as dag:
    
    # =========================================================================
    # TASK GROUP 1: PRE-VALIDATION CHECKS
    # =========================================================================
    
    with TaskGroup(group_id='pre_validation_checks') as pre_checks:
        
        # Check if Great Expectations is configured
        check_ge_config = BashOperator(
            task_id='check_ge_configuration',
            bash_command=f'test -d {GE_DIRECTORY} || exit 1',
            doc_md="""
            Verify Great Expectations directory exists.
            Fails if GE is not initialized.
            """,
        )
        
        # Check if fact_orders table exists
        # Note: This is a placeholder - actual implementation would query database
        check_table_exists = BashOperator(
            task_id='check_table_exists',
            bash_command='echo "Checking if fact_orders table exists..."',
            doc_md="""
            Verify fact_orders table exists in database.
            In production, this would query the database.
            """,
        )
        
        check_ge_config >> check_table_exists
    
    # =========================================================================
    # TASK GROUP 2: RUN VALIDATION
    # =========================================================================
    
    with TaskGroup(group_id='run_validation') as validation:
        
        # Main validation task
        validate_task = PythonOperator(
            task_id='validate_data_quality',
            python_callable=validate_data_quality,
            provide_context=True,
            doc_md="""
            Run Great Expectations checkpoint to validate fact_orders.
            
            Validates:
            - Row count within expected range
            - Primary key uniqueness
            - Foreign keys not null
            - Value ranges for numeric columns
            - Valid enumerations for categorical columns
            """,
        )
        
        # Check validation status
        status_check = PythonOperator(
            task_id='check_validation_status',
            python_callable=check_validation_status,
            provide_context=True,
            doc_md="""
            Review validation results and log status.
            """,
        )
        
        validate_task >> status_check
    
    # =========================================================================
    # TASK GROUP 3: POST-VALIDATION REPORTING
    # =========================================================================
    
    with TaskGroup(group_id='post_validation_reporting') as reporting:
        
        # Generate quality report
        generate_report = PythonOperator(
            task_id='generate_quality_report',
            python_callable=generate_data_quality_report,
            provide_context=True,
            doc_md="""
            Generate data quality report with metrics and statistics.
            """,
        )
        
        # Update data docs (already done by checkpoint, but can trigger refresh)
        update_docs = BashOperator(
            task_id='update_data_docs',
            bash_command='echo "Data docs updated by checkpoint"',
            doc_md="""
            Great Expectations checkpoint automatically updates data docs.
            This task is a placeholder for any additional doc generation.
            """,
        )
        
        generate_report >> update_docs
    
    # =========================================================================
    # TASK DEPENDENCIES
    # =========================================================================
    
    pre_checks >> validation >> reporting


# =============================================================================
# DAG DOCUMENTATION
# =============================================================================

# This will show up in the Airflow UI
dag.doc_md = """
# Data Quality Validation DAG

## Purpose
Automated data quality validation for the `fact_orders` table using Great Expectations.

## Schedule
- **Frequency**: Daily at 1:00 AM
- **Catchup**: Disabled
- **Max Active Runs**: 1

## Validations Performed

### Table-Level Checks
- Row count between 1,000 and 10,000,000
- Required columns exist

### Primary Key Checks
- `order_item_key` is unique
- `order_item_key` is not null

### Foreign Key Checks
- `customer_key` is not null
- `product_key` is not null
- `date_key` is not null

### Data Quality Checks
- `quantity` between 1 and 100
- `unit_price` between $0.01 and $10,000
- `line_total` >= 0
- `discount_amount` >= 0
- `order_status` in valid set
- `payment_method` in valid set
- `order_date` is not null
- `order_timestamp` is not null

## Failure Handling
- **Retries**: 2 attempts with 5-minute delays
- **Email Alerts**: Sent on failure
- **Blocking**: Downstream tasks will not run if validation fails

## Viewing Results
- **Data Docs**: `great_expectations/uncommitted/data_docs/local_site/index.html`
- **Airflow Logs**: Check task logs for detailed validation results
- **XCom**: Results stored for downstream task access

## Manual Trigger
```bash
airflow dags trigger data_quality_validation
```

## Testing
```bash
airflow tasks test data_quality_validation validate_data_quality 2025-11-03
```
"""
