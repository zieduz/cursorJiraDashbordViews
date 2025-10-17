from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema(engine) -> None:
    """Ensure critical schema elements exist in the connected database.

    This function is a lightweight guard to add newly introduced nullable columns
    when the table already exists but migrations haven't been applied yet.
    """
    try:
        inspector = inspect(engine)
        ticket_columns = {col["name"] for col in inspector.get_columns("tickets")}
    except Exception:
        # If inspection fails (e.g., no connection), skip silently
        return

    alter_statements = []

    # Add newly introduced nullable columns used by the ORM model.
    # Keep types aligned with models.Ticket definitions and prefer nullable to avoid backfilling.
    # Note: Using generic SQL to remain compatible with Postgres.

    # String/VARCHAR fields
    if "issue_type" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN issue_type VARCHAR(50)")
    if "priority" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN priority VARCHAR(20)")
    if "customer" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN customer VARCHAR(200)")

    # Text fields
    if "labels" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN labels TEXT")
    if "description" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN description TEXT")

    # Numeric fields
    if "story_points" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN story_points INTEGER")
    if "time_estimate" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN time_estimate DOUBLE PRECISION")
    if "time_spent" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN time_spent DOUBLE PRECISION")

    # Timestamps
    if "updated_at" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN updated_at TIMESTAMPTZ")
    if "started_at" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN started_at TIMESTAMPTZ")
    if "resolved_at" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN resolved_at TIMESTAMPTZ")

    # Foreign keys (nullable). We do not enforce FK constraints here to avoid migration complexity.
    if "assignee_id" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN assignee_id INTEGER")
    if "project_id" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN project_id INTEGER")

    if not alter_statements:
        return

    # Apply ALTERs in a single transaction
    with engine.begin() as connection:
        for stmt in alter_statements:
            connection.exec_driver_sql(stmt)