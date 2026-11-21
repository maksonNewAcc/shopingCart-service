from sqlmodel import create_engine, Session

DATABASE_URL = "postgresql://postgres:advbalksdbv@localhost:5432/eshop_db"

# Create the SQLModel engine that connects to PostgreSQL
engine = create_engine(DATABASE_URL, echo=True)

# Dependency function to provide a database session to your FastAPI routes
def get_session():
    with Session(engine) as session:
        yield session