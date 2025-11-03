"""
Seed database with initial test data.

Run with: docker compose exec api python seed_data.py
"""
import sys
from datetime import datetime

from database import SessionLocal
from models import User, Project, UserRole, ProjectStatus
from utils.security import get_password_hash


def seed_users(db):
    """Create test users with different roles."""
    users = [
        {
            "email": "admin@example.com",
            "full_name": "Admin User",
            "password": "admin123",  # Change in production!
            "role": UserRole.ADMIN,
            "is_active": True
        },
        {
            "email": "operator@example.com",
            "full_name": "Operator User",
            "password": "operator123",
            "role": UserRole.OPERATOR,
            "is_active": True
        },
        {
            "email": "viewer@example.com",
            "full_name": "Viewer User",
            "password": "viewer123",
            "role": UserRole.VIEWER,
            "is_active": True
        }
    ]
    
    created_users = []
    for user_data in users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"⚠️  User {user_data['email']} already exists, skipping")
            created_users.append(existing_user)
            continue
        
        # Create new user
        password = user_data.pop("password")
        user = User(**user_data, hashed_password=get_password_hash(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        created_users.append(user)
        print(f"✅ Created user: {user.email} ({user.role.value})")
    
    return created_users


def seed_projects(db, users):
    """Create test projects."""
    admin_user = next(u for u in users if u.role == UserRole.ADMIN)
    operator_user = next(u for u in users if u.role == UserRole.OPERATOR)
    
    projects = [
        {
            "name": "Production Migration - Phase 1",
            "description": "Migrate 50 production servers from on-premises to Azure East US",
            "azure_subscription_id": "12345678-1234-1234-1234-123456789012",
            "owner_id": admin_user.id,
            "status": ProjectStatus.ACTIVE,
            "metadata_json": {
                "target_region": "East US",
                "server_count": 50,
                "migration_start": "2024-01-15"
            }
        },
        {
            "name": "Dev/Test Environment",
            "description": "Development and testing environment for Azure migration",
            "azure_subscription_id": "87654321-4321-4321-4321-210987654321",
            "owner_id": operator_user.id,
            "status": ProjectStatus.ACTIVE,
            "metadata_json": {
                "target_region": "West US 2",
                "server_count": 10,
                "environment": "development"
            }
        },
        {
            "name": "DR Site Migration",
            "description": "Disaster recovery site migration - in progress",
            "azure_subscription_id": "11111111-2222-3333-4444-555555555555",
            "owner_id": admin_user.id,
            "status": ProjectStatus.IN_PROGRESS,
            "metadata_json": {
                "target_region": "Central US",
                "server_count": 25,
                "priority": "medium"
            }
        }
    ]
    
    created_projects = []
    for project_data in projects:
        # Check if project already exists
        existing_project = db.query(Project).filter(
            Project.name == project_data["name"]
        ).first()
        if existing_project:
            print(f"⚠️  Project '{project_data['name']}' already exists, skipping")
            created_projects.append(existing_project)
            continue
        
        # Create new project
        project = Project(**project_data)
        db.add(project)
        db.commit()
        db.refresh(project)
        created_projects.append(project)
        print(f"✅ Created project: {project.name} (owner: {project.owner.email})")
    
    return created_projects


def main():
    """Seed database with test data."""
    db = SessionLocal()
    try:
        print("\n🌱 Seeding database with test data...\n")
        
        # Create users
        print("👥 Creating users...")
        users = seed_users(db)
        print()
        
        # Create projects
        print("📁 Creating projects...")
        projects = seed_projects(db, users)
        print()
        
        # Summary
        print("=" * 60)
        print("✅ Database seeding complete!\n")
        print(f"Total users: {len(users)}")
        print(f"Total projects: {len(projects)}\n")
        
        print("Test credentials:")
        print("-" * 60)
        print("Admin:    admin@example.com / admin123")
        print("Operator: operator@example.com / operator123")
        print("Viewer:   viewer@example.com / viewer123")
        print("=" * 60)
        print("\n🔐 Don't forget to change passwords in production!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}", file=sys.stderr)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
