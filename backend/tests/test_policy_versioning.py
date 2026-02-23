"""
Integration tests for policy versioning API.
Verifies snapshots, version increments, and restoration logic.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.models.policy import Policy, PolicyStatus, PolicyType, PolicyVersion, PolicyChunk, PolicyProcessing
from app.models.eligibility import UserEligibilityProfile, EligibilityCheck

# Ensure all models are loaded for Base.metadata
import app.models  # noqa: F401

# --- Test DB Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session
        await session.commit()

fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test and drop them after."""
    async with engine.begin() as conn:
        # Tables are already registered in Base.metadata because we imported models
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Create a test client."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def sample_policy():
    """Create a sample policy in the test database."""
    async with TestingSessionLocal() as db:
        policy = Policy(
            policy_id="pol_test_123",
            title="Original Title",
            description="Original Description",
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            content_type="application/pdf",
            version=1,
            status=PolicyStatus.UPLOADED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy


# --- Tests ---

@pytest.mark.anyio
async def test_patch_policy_creates_snapshot(client, sample_policy):
    """Test that PATCH snapshots the old state and increments version."""
    policy_id = sample_policy.policy_id
    
    # Update title
    response = await client.patch(
        f"/api/v1/policies/{policy_id}",
        json={
            "title": "New Updated Title",
            "change_reason": "Renaming for clarity",
            "changed_by": "test_user"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 2
    assert data["title"] == "New Updated Title"
    
    # Verify history
    history_response = await client.get(f"/api/v1/policies/{policy_id}/versions")
    assert history_response.status_code == 200
    history_data = history_response.json()
    
    assert history_data["total"] == 1
    snapshot = history_data["versions"][0]
    assert snapshot["version_number"] == 1
    assert snapshot["title"] == "Original Title"
    assert snapshot["change_reason"] == "Renaming for clarity"
    assert snapshot["changed_by"] == "test_user"


@pytest.mark.anyio
async def test_multiple_patches_increment_version(client, sample_policy):
    """Test multiple updates accumulate in version history."""
    policy_id = sample_policy.policy_id
    
    # Patch 1 -> v2
    await client.patch(f"/api/v1/policies/{policy_id}", json={"title": "V2 Title"})
    # Patch 2 -> v3
    await client.patch(f"/api/v1/policies/{policy_id}", json={"title": "V3 Title"})
    
    response = await client.get(f"/api/v1/policies/{policy_id}")
    assert response.json()["version"] == 3
    
    history_response = await client.get(f"/api/v1/policies/{policy_id}/versions")
    history_data = history_response.json()
    assert history_data["total"] == 2
    # Should be ordered by version_number desc
    assert history_data["versions"][0]["version_number"] == 2
    assert history_data["versions"][1]["version_number"] == 1


@pytest.mark.anyio
async def test_get_specific_version(client, sample_policy):
    """Test retrieving a specific historical snapshot."""
    policy_id = sample_policy.policy_id
    await client.patch(f"/api/v1/policies/{policy_id}", json={"title": "Updated"})
    
    response = await client.get(f"/api/v1/policies/{policy_id}/versions/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Original Title"
    assert response.json()["version_number"] == 1


@pytest.mark.anyio
async def test_restore_policy_version(client, sample_policy):
    """Test restoring to a past version."""
    policy_id = sample_policy.policy_id
    
    # 1. Update twice to get to v3
    await client.patch(f"/api/v1/policies/{policy_id}", json={"title": "V2 Title"})
    await client.patch(f"/api/v1/policies/{policy_id}", json={"title": "V3 Title"})
    
    # 2. Restore to v1
    restore_response = await client.post(f"/api/v1/policies/{policy_id}/versions/1/restore")
    assert restore_response.status_code == 200
    assert restore_response.json()["title"] == "Original Title"
    assert restore_response.json()["version"] == 4  # v1=orig, v2=patch1, v3=patch2, v4=restored
    
    # 3. Verify history now includes v3 status
    history_response = await client.get(f"/api/v1/policies/{policy_id}/versions")
    history_data = history_response.json()
    assert history_data["total"] == 3 # v1, v2, v3 are now in history
    assert history_data["versions"][0]["version_number"] == 3
    assert "Restored from version 1" in history_data["versions"][0]["change_reason"]


@pytest.mark.anyio
async def test_patch_no_changes_is_noop(client, sample_policy):
    """Test that PATCH with no actual changes doesn't bump version."""
    policy_id = sample_policy.policy_id
    
    response = await client.patch(
        f"/api/v1/policies/{policy_id}",
        json={"title": "Original Title"} # Same as original
    )
    
    assert response.status_code == 200
    assert response.json()["version"] == 1
    
    history_response = await client.get(f"/api/v1/policies/{policy_id}/versions")
    assert history_response.json()["total"] == 0


@pytest.mark.anyio
async def test_version_not_found(client, sample_policy):
    """Test 404 for non-existent version."""
    policy_id = sample_policy.policy_id
    response = await client.get(f"/api/v1/policies/{policy_id}/versions/99")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"].lower()
