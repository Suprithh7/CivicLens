"""
Database setup verification script.
Run this after installing PostgreSQL to verify the setup.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import engine, Base
from app.models import policy  # Import models to register them
from sqlalchemy import text


async def verify_connection():
    """Verify database connection."""
    print("🔍 Testing database connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL!")
            print(f"   Version: {version}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def verify_tables():
    """Verify tables exist."""
    print("\n🔍 Checking database tables...")
    try:
        async with engine.connect() as conn:
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            
            if not tables:
                print("⚠️  No tables found. Run migrations first:")
                print("   .\\venv\\Scripts\\alembic upgrade head")
                return False
            
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
            
            # Check for expected tables
            expected = ['policies', 'policy_categories', 'policy_tags', 'policy_processing']
            missing = [t for t in expected if t not in tables]
            
            if missing:
                print(f"\n⚠️  Missing tables: {', '.join(missing)}")
                print("   Run migrations: .\\venv\\Scripts\\alembic upgrade head")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False


async def verify_policy_crud():
    """Test basic CRUD operations."""
    print("\n🔍 Testing CRUD operations...")
    try:
        from app.models.policy import Policy, PolicyStatus
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import sessionmaker
        from datetime import datetime
        
        # Create session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Create test policy
            test_policy = Policy(
                policy_id="test_verification_001",
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                file_size=1024,
                file_hash="test_hash_123",
                content_type="application/pdf",
                status=PolicyStatus.UPLOADED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(test_policy)
            await session.commit()
            print("✅ CREATE: Test policy created")
            
            # Read
            from sqlalchemy import select
            stmt = select(Policy).where(Policy.policy_id == "test_verification_001")
            result = await session.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if policy:
                print(f"✅ READ: Policy retrieved (ID: {policy.id})")
            else:
                print("❌ READ: Failed to retrieve policy")
                return False
            
            # Update
            policy.title = "Test Policy Updated"
            await session.commit()
            print("✅ UPDATE: Policy updated")
            
            # Delete (soft delete)
            policy.deleted_at = datetime.utcnow()
            await session.commit()
            print("✅ DELETE: Policy soft deleted")
            
            # Cleanup - hard delete test record
            await session.delete(policy)
            await session.commit()
            print("✅ CLEANUP: Test record removed")
            
            return True
            
    except Exception as e:
        print(f"❌ CRUD test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all verification checks."""
    print("=" * 60)
    print("CivicLens AI - Database Setup Verification")
    print("=" * 60)
    
    # Check connection
    if not await verify_connection():
        print("\n❌ Setup verification failed!")
        print("\nNext steps:")
        print("1. Install PostgreSQL from https://www.postgresql.org/download/windows/")
        print("2. Create database: psql -U postgres -c \"CREATE DATABASE civiclens_dev;\"")
        print("3. Update .env file with correct DATABASE_URL")
        print("4. Run this script again")
        await engine.dispose()
        return
    
    # Check tables
    tables_ok = await verify_tables()
    
    # Test CRUD if tables exist
    if tables_ok:
        crud_ok = await verify_crud()
        
        if crud_ok:
            print("\n" + "=" * 60)
            print("✅ All verification checks passed!")
            print("=" * 60)
            print("\nYour database is ready to use! 🎉")
            print("\nNext steps:")
            print("1. Start the server: uvicorn app.main:app --reload")
            print("2. Visit http://localhost:8000/docs to test the API")
        else:
            print("\n⚠️  CRUD operations failed. Check error messages above.")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
