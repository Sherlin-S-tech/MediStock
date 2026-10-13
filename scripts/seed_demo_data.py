"""Idempotently insert fictional sample medicine batches."""
from datetime import date, timedelta
from app import create_app
from database import get_db


def seed():
    app = create_app()
    today = date.today()
    rows = [
        ("Paracetamol 500 mg", "DEMO-PARA-01", "Analgesic", "Northstar Labs", 120, 20, today - timedelta(days=150), today + timedelta(days=500), "1.25", "Harbor Medical Supply"),
        ("Cetirizine 10 mg", "DEMO-CET-02", "Antihistamine", "Cedar Health", 45, 12, today - timedelta(days=90), today + timedelta(days=12), "2.10", "Harbor Medical Supply"),
        ("Vitamin C 500 mg", "DEMO-VITC-03", "Supplement", "Fictional Nutraceuticals", 18, 20, today - timedelta(days=280), today + timedelta(days=240), "3.50", "Maple Wholesale"),
        ("Antacid tablets", "DEMO-ANT-04", "Gastrointestinal", "Riverbend Remedies", 8, 15, today - timedelta(days=400), today - timedelta(days=4), "0.85", "Maple Wholesale"),
    ]
    with app.app_context():
        db = get_db()
        db.executemany("""INSERT OR IGNORE INTO medicines
          (name,batch_number,category,manufacturer,quantity,min_stock,manufacturing_date,expiry_date,unit_price,supplier)
          VALUES (?,?,?,?,?,?,?,?,?,?)""", [(n,b,c,m,q,s,man.isoformat(),exp.isoformat(),price,sup) for n,b,c,m,q,s,man,exp,price,sup in rows])
        db.commit()
        print(f"Demo seed complete. Inserted {db.execute('SELECT changes()').fetchone()[0]} new record(s).")


if __name__ == "__main__":
    seed()
