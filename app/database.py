

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

# SQLite requires a special argument for requests across FastAPI threads.
# PostgreSQL does not use this argument.
connection_options = (
    {"connect_args": {"check_same_thread": False}}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, **connection_options)


# SQLite does not enforce foreign keys unless this is enabled per connection.
# PostgreSQL enforces foreign keys automatically.
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Provide a database session to FastAPI routes; always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create missing tables after model registration (for development)."""
    from app import models  # noqa: F401 - registers tables with Base
    Base.metadata.create_all(bind=engine)
