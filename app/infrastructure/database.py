import os
from sqlmodel import create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set, e.g. postgresql://user:password@localhost:5432/eshop_db"
    )

# Create the SQLModel engine that connects to PostgreSQL
engine = create_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "false").lower() == "true")


# Dependency function to provide a database session to your FastAPI routes
def get_session():
    with Session(engine) as session:
        yield session
