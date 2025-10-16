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

    # Add 'customer' column if missing; nullable matches ORM default
    if "customer" not in ticket_columns:
        alter_statements.append("ALTER TABLE tickets ADD COLUMN customer VARCHAR(200)")

    if not alter_statements:
        return

    # Apply ALTERs in a single transaction
    with engine.begin() as connection:
        for stmt in alter_statements:
            connection.exec_driver_sql(stmt)