import os
import pytest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("API_KEY", "")
os.environ.setdefault("RATE_LIMIT", "1000/minute")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.models.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def authed_client():
    from app.core.config import Settings
    with patch("app.core.auth.settings", Settings(API_KEY="test-secret", RATE_LIMIT="1000/minute")):
        with TestClient(app, headers={"X-API-Key": "test-secret"}) as c:
            yield c


@pytest.fixture()
def seed_user(db):
    from app.models.user import User
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, name="Test User", email="test@jarvis.local")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
