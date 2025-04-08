import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.session import get_db
from src.database.models import Base
from src.main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the database tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user(test_db):
    from src.database.models import User
    from src.core.auth import get_password_hash
    
    # Create a test user
    db = TestingSessionLocal()
    hashed_password = get_password_hash("testpassword")
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    return {"id": str(user.id), "email": user.email, "name": user.name}

@pytest.fixture(scope="function")
def test_token(test_user):
    from src.core.auth import create_access_token
    
    # Create a test token
    access_token = create_access_token(
        data={"sub": test_user["email"]}
    )
    
    return access_token

@pytest.fixture(scope="function")
def authorized_client(test_token):
    # Create an authorized client with the test token
    client.headers = {
        "Authorization": f"Bearer {test_token}"
    }
    
    return client
