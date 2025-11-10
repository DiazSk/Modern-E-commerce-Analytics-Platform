#!/usr/bin/env python3
"""
Quick test script to run Great Expectations checkpoint and show detailed results
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import great_expectations as gx


def main():
    print("\n" + "=" * 80)
    print("RUNNING GREAT EXPECTATIONS CHECKPOINT")
    print("=" * 80 + "\n")

    try:
        # Get context
        context = gx.get_context()
        print("✓ Context loaded\n")

        # Run checkpoint
        print("Running checkpoint: orders_checkpoint...")
        result = context.run_checkpoint(checkpoint_name="orders_checkpoint")

        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80 + "\n")

        # Get the validation result
        validation_results = result.run_results
        first_key = list(validation_results.keys())[0]
        validation_result = validation_results[first_key]

        # Print summary
        stats = validation_result.get("statistics", {})
        print(f"Success: {validation_result.get('success')}")
        print(f"Evaluated: {stats.get('evaluated_expectations')}")
        print(f"Successful: {stats.get('successful_expectations')}")
        print(f"Failed: {stats.get('unsuccessful_expectations')}")
        print(f"Success Rate: {stats.get('success_percent')}%")

        # Print failed expectations
        if not validation_result.get("success"):
            print("\n" + "-" * 80)
            print("FAILED EXPECTATIONS:")
            print("-" * 80)

            for result_obj in validation_result.get("results", []):
                if not result_obj.get("success", True):
                    exp_config = result_obj.get("expectation_config", {})
                    exp_type = exp_config.get("expectation_type", "Unknown")
                    kwargs = exp_config.get("kwargs", {})
                    column = kwargs.get("column", "N/A")

                    print(f"\n❌ {exp_type}")
                    print(f"   Column: {column}")

                    # Print specific failure details
                    result_detail = result_obj.get("result", {})
                    if "observed_value" in result_detail:
                        print(f"   Observed: {result_detail['observed_value']}")
                    if "unexpected_count" in result_detail:
                        print(
                            f"   Unexpected Count: {result_detail['unexpected_count']}"
                        )
                    if "unexpected_percent" in result_detail:
                        print(f"   Unexpected %: {result_detail['unexpected_percent']}")

        print("\n" + "=" * 80)
        print("✓ CHECKPOINT COMPLETE!")
        print("=" * 80)

        print(f"\nView data docs at:")
        print(
            f"  {PROJECT_ROOT}/great_expectations/uncommitted/data_docs/local_site/index.html"
        )

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
