"""Fictional inventory records used for a fresh demonstration database."""
from datetime import date, timedelta

from database import get_db


def seed_demo_data(today=None):
    """Insert the example batches without overwriting an existing inventory."""
    today = today or date.today()
    rows = [
        ("Demo Paracetamol 500 mg", "DEMO-PARA-001", "Analgesic", "Northstar Labs", 120, 20,
         today - timedelta(days=150), today + timedelta(days=152), "1.25", "Harbor Medical Supply"),
        ("Demo Cetirizine 10 mg", "DEMO-CET-002", "Antihistamine", "Cedar Health", 45, 12,
         today - timedelta(days=90), today + timedelta(days=11), "2.10", "Harbor Medical Supply"),
        ("Demo Vitamin C 500 mg", "DEMO-VITC-003", "Supplement", "Fictional Nutraceuticals", 8, 15,
         today - timedelta(days=280), today + timedelta(days=124), "3.50", "Maple Wholesale"),
    ]
    db = get_db()
    db.executemany(
        """INSERT OR IGNORE INTO medicines
          (name,batch_number,category,manufacturer,quantity,min_stock,manufacturing_date,expiry_date,unit_price,supplier)
          VALUES (?,?,?,?,?,?,?,?,?,?)""",
        [(name, batch, category, manufacturer, quantity, min_stock, made.isoformat(), expires.isoformat(), price, supplier)
         for name, batch, category, manufacturer, quantity, min_stock, made, expires, price, supplier in rows],
    )
    db.commit()
    return db.execute("SELECT changes()").fetchone()[0]
