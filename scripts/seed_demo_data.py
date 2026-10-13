"""Manually insert the fictional sample batches into the configured database."""
from app import create_app
from demo_data import seed_demo_data


if __name__ == "__main__":
    app = create_app({"SEED_DEMO_DATA": False})
    with app.app_context():
        inserted = seed_demo_data()
        print(f"Demo seed complete. Inserted {inserted} new record(s).")
