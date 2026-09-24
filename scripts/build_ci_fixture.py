"""
Rebuild the CI fixture (transform/seeds/ci_fixtures/) from generator output.

Keeps the fixture's existing 40 customers and takes all of their orders and
order items plus their first 400 clickstream events, assigning IDs the way
scripts/load_data.py does when loading into Postgres. products.csv is left
as is (it is a snapshot of the FakeStore API).

Usage:
    python scripts/generate_data.py
    python scripts/build_ci_fixture.py [generated_dir] [fixture_dir]
"""

import sys

import pandas as pd
from generate_data import N_PRODUCTS

GENERATED_DIR = sys.argv[1] if len(sys.argv) > 1 else "data/generated"
FIXTURE_DIR = sys.argv[2] if len(sys.argv) > 2 else "transform/seeds/ci_fixtures"
N_EVENTS = 400

# Load-time values from the database the fixture was first exported from, so
# regenerating only changes rows whose data actually changed. The customer and
# order_item sequences there were not reset before loading (IDs start at 2 and
# 3); orders.order_id is reset to 1 by load_data.py.
CUSTOMER_ID_START = 2
ORDER_ITEM_ID_START = 3
CUSTOMERS_LOADED_AT = "2026-09-24 01:17:15.357854"
ORDERS_LOADED_AT = "2026-09-24 01:17:15.387702"
ORDER_ITEMS_LOADED_AT = "2026-09-24 01:17:15.490293"
# generate_data.py timestamps carry datetime.now() microseconds; pin them.
MICROSECONDS = ".372977"


def pin_microseconds(timestamps):
    return timestamps.str.slice(0, 19) + MICROSECONDS


def main():
    fixture_customers = pd.read_csv(f"{FIXTURE_DIR}/customers.csv")

    customers = pd.read_csv(f"{GENERATED_DIR}/customers.csv")
    customers.insert(
        0,
        "customer_id",
        range(CUSTOMER_ID_START, CUSTOMER_ID_START + len(customers)),
    )
    customers = customers.set_index("customer_id")
    selected = customers.loc[fixture_customers["customer_id"]].reset_index()
    if not (selected["email"] == fixture_customers["email"]).all():
        sys.exit("Generated customers no longer match the fixture's customer_ids")
    selected["is_current"] = True
    selected["created_at"] = selected["updated_at"] = CUSTOMERS_LOADED_AT

    orders = pd.read_csv(f"{GENERATED_DIR}/orders.csv")
    orders.insert(0, "order_id", range(1, len(orders) + 1))
    orders["order_date"] = pin_microseconds(orders["order_date"])
    email_to_id = dict(zip(customers["email"], customers.index))
    orders["customer_id"] = orders["customer_id"].map(email_to_id)
    orders = orders[orders["customer_id"].isin(selected["customer_id"])].copy()
    orders["created_at"] = orders["updated_at"] = ORDERS_LOADED_AT

    items = pd.read_csv(f"{GENERATED_DIR}/order_items.csv")
    items.insert(
        0,
        "order_item_id",
        range(ORDER_ITEM_ID_START, ORDER_ITEM_ID_START + len(items)),
    )
    # Generated column in init_db.sql
    items["line_total"] = (
        items["quantity"] * items["unit_price"] - items["discount_amount"]
    ).round(2)
    items["created_at"] = ORDER_ITEMS_LOADED_AT
    items = items[items["order_id"].isin(orders["order_id"])]

    events = pd.read_csv(f"{GENERATED_DIR}/clickstream_events.csv")
    events["event_timestamp"] = pin_microseconds(events["event_timestamp"])
    events = events[events["user_id"].isin(selected["email"])].head(N_EVENTS).copy()
    events["created_at"] = events["event_timestamp"]

    # Every product_id must exist in products.csv, or fact_orders drops the row
    for name, df in [("order_items", items), ("clickstream_events", events)]:
        if not df["product_id"].between(1, N_PRODUCTS).all():
            sys.exit(f"{name} references product_ids outside 1..{N_PRODUCTS}")

    selected.to_csv(f"{FIXTURE_DIR}/customers.csv", index=False)
    orders.to_csv(f"{FIXTURE_DIR}/orders.csv", index=False)
    items.to_csv(f"{FIXTURE_DIR}/order_items.csv", index=False)
    events.to_csv(f"{FIXTURE_DIR}/clickstream_events.csv", index=False)
    print(
        f"customers={len(selected)} orders={len(orders)} "
        f"order_items={len(items)} clickstream_events={len(events)}"
    )


if __name__ == "__main__":
    main()
