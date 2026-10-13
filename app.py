"""Medicine Stock and Expiry Tracking System."""
from __future__ import annotations

import csv
import io
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, Response, abort, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from database import get_db, init_app as init_database
from demo_data import seed_demo_data
from services import classify_expiry, dashboard_stats, medicine_status, query_medicines

csrf = CSRFProtect()
FIELDS = ("name", "batch_number", "category", "manufacturer", "quantity", "min_stock", "manufacturing_date", "expiry_date", "unit_price", "supplier")
REQUIRED = ("name", "batch_number", "category", "quantity", "min_stock", "manufacturing_date", "expiry_date", "unit_price")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key-change-me"),
        DATABASE=os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "data", "medicines.db")),
        NEAR_EXPIRY_DAYS=int(os.environ.get("NEAR_EXPIRY_DAYS", "30")),
        SEED_DEMO_DATA=os.environ.get("SEED_DEMO_DATA", "true").strip().lower() not in {"0", "false", "no", "off"},
        TESTING=False,
    )
    if test_config:
        app.config.update(test_config)
    csrf.init_app(app)

    init_database(app)
    if app.config["SEED_DEMO_DATA"] and not app.config["TESTING"]:
        with app.app_context():
            db = get_db()
            if db.execute("SELECT 1 FROM medicines LIMIT 1").fetchone() is None:
                seed_demo_data()

    def today():
        return date.fromisoformat(app.config["TODAY"]) if app.config.get("TODAY") else date.today()

    def validated_form():
        values = {key: request.form.get(key, "").strip() for key in FIELDS}
        errors = []
        for key in REQUIRED:
            if not values[key]:
                errors.append(f"{key.replace('_', ' ').capitalize()} is required.")
        for key in ("manufacturing_date", "expiry_date"):
            if values[key]:
                try:
                    date.fromisoformat(values[key])
                except ValueError:
                    errors.append(f"{key.replace('_', ' ').capitalize()} must be a valid date.")
        for key in ("quantity", "min_stock"):
            try:
                values[key] = int(values[key])
                if values[key] < 0:
                    errors.append(f"{key.replace('_', ' ').capitalize()} cannot be negative.")
            except (ValueError, TypeError):
                if values[key] != "":
                    errors.append(f"{key.replace('_', ' ').capitalize()} must be a whole number.")
        try:
            price = Decimal(values["unit_price"])
            if not price.is_finite() or price < 0:
                raise InvalidOperation
            values["unit_price"] = format(price.quantize(Decimal("0.01")), "f")
        except (InvalidOperation, ValueError):
            errors.append("Unit price must be a valid non-negative amount.")
        if values["manufacturing_date"] and values["expiry_date"]:
            try:
                if date.fromisoformat(values["manufacturing_date"]) > date.fromisoformat(values["expiry_date"]):
                    errors.append("Manufacturing date cannot be later than expiry date.")
            except ValueError:
                pass
        return values, errors

    def find_medicine(medicine_id):
        item = get_db().execute("SELECT * FROM medicines WHERE id = ?", (medicine_id,)).fetchone()
        if not item:
            abort(404)
        return dict(item)

    @app.context_processor
    def common_context():
        return {"today": today(), "near_expiry_days": app.config["NEAR_EXPIRY_DAYS"]}

    @app.route("/")
    def dashboard():
        db = get_db()
        stats = dashboard_stats(db, today(), app.config["NEAR_EXPIRY_DAYS"])
        recent = query_medicines(db, today(), app.config["NEAR_EXPIRY_DAYS"], sort="created_at", order="desc", limit=6)
        attention = query_medicines(db, today(), app.config["NEAR_EXPIRY_DAYS"], attention=True, limit=8)
        return render_template("dashboard.html", stats=stats, recent=recent, attention=attention)

    @app.route("/inventory")
    def inventory():
        db = get_db()
        categories = [r[0] for r in db.execute("SELECT DISTINCT category FROM medicines WHERE category != '' ORDER BY category")]
        items = query_medicines(db, today(), app.config["NEAR_EXPIRY_DAYS"], search=request.args.get("q", "").strip(), category=request.args.get("category", ""), expiry=request.args.get("expiry", ""), stock=request.args.get("stock", ""), sort=request.args.get("sort", "expiry_date"), order=request.args.get("order", "asc"))
        return render_template("inventory.html", medicines=items, categories=categories)

    @app.route("/medicines/new", methods=["GET", "POST"])
    @app.route("/medicines/<int:medicine_id>/edit", methods=["GET", "POST"])
    def medicine_form(medicine_id=None):
        existing = find_medicine(medicine_id) if medicine_id else None
        values = existing or {key: "" for key in FIELDS}
        errors = []
        if request.method == "POST":
            values, errors = validated_form()
            if not errors:
                try:
                    db = get_db()
                    if existing:
                        db.execute("UPDATE medicines SET name=:name,batch_number=:batch_number,category=:category,manufacturer=:manufacturer,quantity=:quantity,min_stock=:min_stock,manufacturing_date=:manufacturing_date,expiry_date=:expiry_date,unit_price=:unit_price,supplier=:supplier,updated_at=CURRENT_TIMESTAMP WHERE id=:id", {**values, "id": medicine_id})
                    else:
                        db.execute("INSERT INTO medicines (name,batch_number,category,manufacturer,quantity,min_stock,manufacturing_date,expiry_date,unit_price,supplier) VALUES (:name,:batch_number,:category,:manufacturer,:quantity,:min_stock,:manufacturing_date,:expiry_date,:unit_price,:supplier)", values)
                    db.commit()
                    flash("Medicine updated." if existing else "Medicine added.", "success")
                    return redirect(url_for("medicine_detail", medicine_id=medicine_id) if existing else url_for("inventory"))
                except Exception as exc:
                    if "UNIQUE constraint failed" in str(exc):
                        errors.append("That batch number already exists.")
                    else:
                        app.logger.exception("Unable to save medicine")
                        errors.append("The medicine could not be saved. Please try again.")
        return render_template("medicine_form.html", medicine=values, errors=errors, editing=bool(existing))

    @app.route("/medicines/<int:medicine_id>")
    def medicine_detail(medicine_id):
        item = find_medicine(medicine_id)
        item["status"] = medicine_status(item, today(), app.config["NEAR_EXPIRY_DAYS"])
        return render_template("medicine_details.html", medicine=item)

    @app.route("/medicines/<int:medicine_id>/delete", methods=["POST"])
    def delete_medicine(medicine_id):
        find_medicine(medicine_id)
        db = get_db()
        db.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
        db.commit()
        flash("Medicine record deleted.", "success")
        return redirect(url_for("inventory"))

    @app.route("/expiry")
    def expiry():
        items = query_medicines(get_db(), today(), app.config["NEAR_EXPIRY_DAYS"])
        groups = {key: [] for key in ("Expired", "Near expiry", "Valid")}
        for item in items:
            groups[classify_expiry(item["expiry_date"], today(), app.config["NEAR_EXPIRY_DAYS"])].append(item)
        return render_template("expiry.html", groups=groups)

    @app.route("/low-stock")
    def low_stock():
        items = query_medicines(get_db(), today(), app.config["NEAR_EXPIRY_DAYS"], stock="low")
        return render_template("low_stock.html", medicines=items)

    @app.route("/reports")
    def reports():
        return render_template("reports.html")

    @app.route("/reports/<report_type>.csv")
    def export_report(report_type):
        if report_type not in ("inventory", "expired", "near-expiry", "low-stock"):
            abort(404)
        items = query_medicines(get_db(), today(), app.config["NEAR_EXPIRY_DAYS"])
        if report_type == "expired":
            items = [i for i in items if i["expiry_status"] == "Expired"]
        elif report_type == "near-expiry":
            items = [i for i in items if i["expiry_status"] == "Near expiry"]
        elif report_type == "low-stock":
            items = [i for i in items if i["stock_status"] == "Low stock"]
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        columns = ("name", "batch_number", "category", "manufacturer", "quantity", "min_stock", "manufacturing_date", "expiry_date", "unit_price", "supplier", "expiry_status", "stock_status")
        writer.writerow([c.replace("_", " ").title() for c in columns])
        for item in items:
            writer.writerow([item[c] for c in columns])
        return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename=medicine-{report_type}-report.csv"})

    @app.route("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "ok"}, 200

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="The page or medicine record could not be found."), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("error.html", code=500, message="Something went wrong. Please try again."), 500

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
