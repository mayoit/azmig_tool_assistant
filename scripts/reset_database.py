"""
Database reset script - Clean all data and reinitialize schema.
WARNING: This will delete ALL data from the database!
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import from api
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from database import engine, Base, init_db
from models import (
    User, Project, LandingZoneConfig, ServerConfig,
    LZValidationResult, ServerValidationResult,
    ReplicationStatus, FileUpload, ValidationJob,
    ValidationEvent, MigrateProjectValidation, AppLandingZoneValidation
)
from sqlalchemy import text


def reset_database(confirm: bool = False):
    """
    Reset the database by dropping all tables and recreating them.
    
    Args:
        confirm: Set to True to confirm the reset operation
    """
    if not confirm:
        print("⚠️  WARNING: This will DELETE ALL DATA from the database!")
        print("⚠️  This action cannot be undone!")
        print("")
        response = input("Are you sure you want to continue? Type 'yes' to proceed: ")
        
        if response.lower() != 'yes':
            print("❌ Database reset cancelled.")
            return False
    
    try:
        print("\n🗑️  Dropping all tables...")
        
        # Drop all tables in reverse dependency order
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully")
        
        print("\n🔨 Creating fresh database schema...")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema created successfully")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print(f"\n📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"  • {table}")
        
        print("\n✅ Database reset completed successfully!")
        print("🎉 Database is now clean and ready for fresh data")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during database reset: {e}")
        import traceback
        traceback.print_exc()
        return False


def delete_all_data_only():
    """
    Delete all data from tables but keep the schema.
    Faster than full reset if schema hasn't changed.
    """
    try:
        print("\n🗑️  Deleting all data from tables (keeping schema)...")
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Disable foreign key checks temporarily (PostgreSQL)
                conn.execute(text("SET session_replication_role = 'replica'"))
                
                # Delete from all tables
                tables = [
                    'validation_events',
                    'app_landing_zone_validations',
                    'migrate_project_validations',
                    'server_validation_results',
                    'lz_validation_results',
                    'replication_status',
                    'file_uploads',
                    'validation_jobs',
                    'server_configs',
                    'landing_zone_configs',
                    'projects',
                    'users'
                ]
                
                for table in tables:
                    try:
                        result = conn.execute(text(f"DELETE FROM {table}"))
                        print(f"  ✅ Deleted {result.rowcount} rows from {table}")
                    except Exception as e:
                        print(f"  ⚠️  Warning for {table}: {e}")
                
                # Re-enable foreign key checks
                conn.execute(text("SET session_replication_role = 'origin'"))
                
                # Reset sequences
                print("\n🔄 Resetting ID sequences...")
                for table in tables:
                    try:
                        conn.execute(text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1"))
                    except Exception as e:
                        # Some tables might not have sequences
                        pass
                
                # Commit transaction
                trans.commit()
                print("\n✅ All data deleted successfully!")
                return True
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"\n❌ Error during data deletion: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset the database")
    parser.add_argument(
        "--full-reset",
        action="store_true",
        help="Drop and recreate all tables (schema reset)"
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="Delete all data but keep schema (faster)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    if args.full_reset:
        reset_database(confirm=args.yes)
    elif args.data_only:
        if not args.yes:
            print("⚠️  WARNING: This will DELETE ALL DATA from all tables!")
            response = input("Are you sure? Type 'yes' to proceed: ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled.")
                sys.exit(0)
        delete_all_data_only()
    else:
        print("Please specify --full-reset or --data-only")
        print("\nExamples:")
        print("  python scripts/reset_database.py --full-reset      # Drop and recreate schema")
        print("  python scripts/reset_database.py --data-only       # Just delete all data")
        print("  python scripts/reset_database.py --data-only --yes # Skip confirmation")
        sys.exit(1)
