import logging
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import User, Consultant, Dermatologist

logger = logging.getLogger("skincare_api")

def sync_database_schema():
    """
    Safely executes database schema alterations to ensure new profile &
    push notification preference columns exist in PostgreSQL, and backfills
    any existing records for users, consultants, and dermatologists.
    """
    try:
        with engine.connect() as conn:
            # Users
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100) DEFAULT '';"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100) DEFAULT '';"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50) DEFAULT '';"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS push_notifications_mobile BOOLEAN DEFAULT TRUE;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS push_notifications_email BOOLEAN DEFAULT TRUE;"))
            conn.execute(text("ALTER TABLE user_reminder_logs ADD COLUMN IF NOT EXISTS courier_request_id VARCHAR(100) DEFAULT NULL;"))

            # Consultants
            conn.execute(text("ALTER TABLE consultants ADD COLUMN IF NOT EXISTS first_name VARCHAR(100) DEFAULT '';"))
            conn.execute(text("ALTER TABLE consultants ADD COLUMN IF NOT EXISTS last_name VARCHAR(100) DEFAULT '';"))
            conn.execute(text("ALTER TABLE consultants ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50) DEFAULT '';"))
            conn.execute(text("ALTER TABLE consultants ADD COLUMN IF NOT EXISTS specialization VARCHAR(255) DEFAULT 'Skincare Specialist';"))

            # Dermatologists
            conn.execute(text("ALTER TABLE dermatologists ADD COLUMN IF NOT EXISTS first_name VARCHAR(100) DEFAULT '';"))
            conn.execute(text("ALTER TABLE dermatologists ADD COLUMN IF NOT EXISTS last_name VARCHAR(100) DEFAULT '';"))
            conn.execute(text("ALTER TABLE dermatologists ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50) DEFAULT '';"))

            conn.commit()
        logger.info("Database schema columns synchronized successfully.")
    except Exception as exc:
        logger.error(f"Error altering table schemas: {exc}")

    # Backfill first_name and last_name from name for existing rows
    try:
        db = SessionLocal()
        # Backfill users
        users = db.query(User).all()
        updated_count = 0
        for u in users:
            changed = False
            if (not u.first_name or not u.first_name.strip()) and u.name and u.name.strip():
                parts = u.name.strip().split(maxsplit=1)
                u.first_name = parts[0]
                u.last_name = parts[1] if len(parts) > 1 else ""
                changed = True
            if u.push_notifications_mobile is None:
                u.push_notifications_mobile = True
                changed = True
            if u.push_notifications_email is None:
                u.push_notifications_email = True
                changed = True
            if changed:
                db.add(u)
                updated_count += 1

        # Backfill consultants
        consultants = db.query(Consultant).all()
        for c in consultants:
            changed = False
            if (not c.first_name or not c.first_name.strip()) and c.name and c.name.strip():
                parts = c.name.strip().split(maxsplit=1)
                c.first_name = parts[0]
                c.last_name = parts[1] if len(parts) > 1 else ""
                changed = True
            if not getattr(c, "specialization", None):
                c.specialization = "Skincare Specialist"
                changed = True
            if changed:
                db.add(c)
                updated_count += 1

        # Backfill dermatologists
        derms = db.query(Dermatologist).all()
        for d in derms:
            changed = False
            if (not d.first_name or not d.first_name.strip()) and d.name and d.name.strip():
                parts = d.name.strip().split(maxsplit=1)
                d.first_name = parts[0]
                d.last_name = parts[1] if len(parts) > 1 else ""
                changed = True
            if changed:
                db.add(d)
                updated_count += 1

        if updated_count > 0:
            db.commit()
            logger.info(f"Backfilled {updated_count} user/consultant/dermatologist profiles.")
        db.close()
    except Exception as exc:
        logger.error(f"Error backfilling existing profiles: {exc}")

if __name__ == "__main__":
    sync_database_schema()
    print("Database sync completed.")