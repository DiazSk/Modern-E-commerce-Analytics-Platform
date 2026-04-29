"""
==============================================================================
Data Quality Validation DAG - Great Expectations Integration
==============================================================================
Purpose: Automated data quality checks using Great Expectations

This DAG:
1. Verifies the GE configuration directory exists
2. Confirms the fact_orders table exists in the database (via information_schema)
3. Runs the GE checkpoint against fact_orders via GreatExpectationsOperator

The GreatExpectationsOperator natively handles logging, data docs updates,
and raises an AirflowException if any expectation fails — no custom Python
reporting code needed.

Schedule: Daily after fact_orders is loaded (1 AM UTC)
==============================================================================
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.sensors.sql import SqlSensor
from airflow.utils.task_group import TaskGroup
from great_expectations_provider.operators.great_expectations import (
    GreatExpectationsOperator,
)

# =============================================================================
# DAG CONFIGURATION
# =============================================================================

DEFAULT_ARGS = {
    "owner": "zaid",
    "depends_on_past": False,
    "start_date": datetime(2025, 11, 3),
    "email": ["zaid07sk@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}

PROJECT_ROOT = Path(__file__).parent.parent
GE_DIRECTORY = PROJECT_ROOT / "gx"
CHECKPOINT_NAME = "orders_checkpoint"

# =============================================================================
# DAG DEFINITION
# =============================================================================

with DAG(
    dag_id="data_quality_validation",
    default_args=DEFAULT_ARGS,
    description="Validate data quality using Great Expectations on fact_orders table",
    schedule_interval="0 1 * * *",
    catchup=False,
    tags=["data-quality", "great-expectations", "validation", "fact-orders"],
    max_active_runs=1,
    doc_md=__doc__,
) as dag:

    # =========================================================================
    # TASK GROUP 1: PRE-VALIDATION CHECKS
    # =========================================================================

    with TaskGroup(group_id="pre_validation_checks") as pre_checks:
        # Verify GE config directory exists on the worker filesystem
        check_ge_config = BashOperator(
            task_id="check_ge_configuration",
            bash_command=f"test -d {GE_DIRECTORY} || (echo 'GE directory not found: {GE_DIRECTORY}' && exit 1)",
        )

        # Confirm fact_orders table exists by querying information_schema —
        # replaces the previous no-op echo command.
        check_table_exists = SqlSensor(
            task_id="check_table_exists",
            conn_id="postgres_source",
            sql="""
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'fact_orders'
            """,
            mode="poke",
            poke_interval=30,
            timeout=300,
        )

        check_ge_config >> check_table_exists

    # =========================================================================
    # TASK GROUP 2: RUN VALIDATION
    # =========================================================================

    with TaskGroup(group_id="run_validation") as validation:
        # GreatExpectationsOperator replaces the 100+ lines of custom Python
        # that manually loaded the context, fetched the checkpoint, and ran it.
        # It natively:
        #   - Runs the named checkpoint
        #   - Updates data docs
        #   - Raises AirflowException (blocking downstream) if validation fails
        validate_task = GreatExpectationsOperator(
            task_id="validate_data_quality",
            data_context_root_dir=str(GE_DIRECTORY),
            checkpoint_name=CHECKPOINT_NAME,
            fail_task_on_validation_error=True,
        )

    # =========================================================================
    # TASK DEPENDENCIES
    # =========================================================================

    pre_checks >> validation
