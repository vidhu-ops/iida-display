"""One-off script to import users from data/user-2-df1419.xlsx into the
configured database (Neon Postgres in production). Idempotent: upserts by id.

Run with the project env loaded:
    set -a && source /vercel/share/.env.project && set +a && python3 scripts/import_users.py
"""
import json
from datetime import datetime

import openpyxl

from app import app, db
from models import User

XLSX_PATH = "data/user-2-df1419.xlsx"

# Columns present on the User model that we care about mapping from the sheet.
# (The sheet has extra columns like is_subscriber / subscription_expiry that
# the current model does not define, so we skip those.)
def parse_dt(value):
    if value in (None, "", "None"):
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    # values look like '"2025-11-22T20:15:49.212Z"'
    try:
        s = json.loads(s)
    except Exception:
        pass
    s = str(s).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).replace(tzinfo=None)
    except Exception:
        return None


def parse_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def main():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb["user"]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() for h in rows[0]]
    idx = {name: i for i, name in enumerate(header)}

    created, updated = 0, 0
    with app.app_context():
        db.create_all()
        for row in rows[1:]:
            if row is None or row[idx["id"]] in (None, ""):
                continue
            uid = int(row[idx["id"]])
            user = db.session.get(User, uid)
            if user is None:
                user = User(id=uid)
                db.session.add(user)
                created += 1
            else:
                updated += 1

            user.username = row[idx["username"]]
            user.email = row[idx["email"]]
            user.password_hash = row[idx["password_hash"]]
            user.credits = int(row[idx["credits"]] or 0)
            user.ai_create_access_paid = parse_bool(row[idx["ai_create_access_paid"]])
            user.created_at = parse_dt(row[idx["created_at"]]) or datetime.utcnow()
            if "pm_access_expiry" in idx:
                user.pm_access_expiry = parse_dt(row[idx["pm_access_expiry"]])

        db.session.commit()

        # Keep the Postgres id sequence ahead of the imported ids so new
        # signups don't collide with the explicit ids we just inserted.
        try:
            from sqlalchemy import text
            bind = db.session.get_bind()
            if bind.dialect.name == "postgresql":
                db.session.execute(
                    text("SELECT setval(pg_get_serial_sequence('\"user\"','id'), "
                         "(SELECT MAX(id) FROM \"user\"))")
                )
                db.session.commit()
        except Exception as e:
            print("Sequence reset skipped:", e)

        total = db.session.query(User).count()

    print(f"Imported users -> created: {created}, updated: {updated}, total in db: {total}")


if __name__ == "__main__":
    main()
