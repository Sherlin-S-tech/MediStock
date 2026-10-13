"""Inventory business rules and query helpers."""
from datetime import date, timedelta


def classify_expiry(expiry_date, today, near_days=30):
    expiry = date.fromisoformat(expiry_date) if isinstance(expiry_date, str) else expiry_date
    if expiry < today:
        return "Expired"
    if expiry <= today + timedelta(days=near_days):
        return "Near expiry"
    return "Valid"


def medicine_status(medicine, today, near_days=30):
    expiry = classify_expiry(medicine["expiry_date"], today, near_days)
    low = medicine["quantity"] <= medicine["min_stock"]
    return "Low stock" if low else expiry


def query_medicines(db, today, near_days=30, search="", category="", expiry="", stock="", sort="expiry_date", order="asc", limit=None, attention=False):
    allowed = {"name": "name COLLATE NOCASE", "quantity": "quantity", "expiry_date": "expiry_date", "created_at": "created_at"}
    clauses, args = [], []
    if search:
        clauses.append("(name LIKE ? OR batch_number LIKE ?)")
        args.extend((f"%{search}%", f"%{search}%"))
    if category:
        clauses.append("category = ?")
        args.append(category)
    if stock == "low":
        clauses.append("quantity <= min_stock")
    elif stock == "in-stock":
        clauses.append("quantity > min_stock")
    if expiry in ("Expired", "Near expiry", "Valid"):
        if expiry == "Expired":
            clauses.append("expiry_date < ?")
            args.append(today.isoformat())
        elif expiry == "Near expiry":
            clauses.append("expiry_date >= ? AND expiry_date <= ?")
            args.extend((today.isoformat(), (today + timedelta(days=near_days)).isoformat()))
        else:
            clauses.append("expiry_date > ?")
            args.append((today + timedelta(days=near_days)).isoformat())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    if attention and not where:
        where = " WHERE (expiry_date <= ? OR quantity <= min_stock)"
        args.append((today + timedelta(days=near_days)).isoformat())
    sort_key = allowed.get(sort, "expiry_date")
    direction = "DESC" if order.lower() == "desc" else "ASC"
    tie_direction = "DESC" if sort == "created_at" and direction == "DESC" else "ASC"
    sql = f"SELECT * FROM medicines{where} ORDER BY {sort_key} {direction}, id {tie_direction}"
    if limit:
        sql += " LIMIT ?"
        args.append(limit)
    records = []
    for row in db.execute(sql, args).fetchall():
        item = dict(row)
        item["expiry_status"] = classify_expiry(item["expiry_date"], today, near_days)
        item["stock_status"] = "Low stock" if item["quantity"] <= item["min_stock"] else "In stock"
        item["status"] = "Low stock" if item["stock_status"] == "Low stock" else item["expiry_status"]
        records.append(item)
    return records


def dashboard_stats(db, today, near_days=30):
    all_items = query_medicines(db, today, near_days)
    return {
        "medicine_types": len(all_items),
        "units": sum(i["quantity"] for i in all_items),
        "expired": sum(i["expiry_status"] == "Expired" for i in all_items),
        "near_expiry": sum(i["expiry_status"] == "Near expiry" for i in all_items),
        "low_stock": sum(i["stock_status"] == "Low stock" for i in all_items),
        "expiry_chart": {key: sum(i["expiry_status"] == key for i in all_items) for key in ("Expired", "Near expiry", "Valid")},
    }
