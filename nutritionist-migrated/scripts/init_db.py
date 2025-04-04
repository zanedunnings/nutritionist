import os
import sys
from sqlalchemy.orm import Session
from datetime import datetime
import bcrypt

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from models.database import Base, engine, get_db
from models.user import User
from models.meal_plan import MealPlan, Modification

def init_db():
    # Ensure data directory exists
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

def create_admin_user(db: Session):
    # Check if admin user already exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        return

    # Create admin user
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw("admin".encode(), salt)
    
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hashed_password.decode(),
        is_active=True,
        is_admin=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(admin)
    db.commit()

def main():
    # Initialize database
    init_db()
    
    # Create admin user
    db = next(get_db())
    try:
        create_admin_user(db)
        print("Database initialized successfully!")
        print("Admin user created with credentials:")
        print("Username: admin")
        print("Password: admin")
    finally:
        db.close()

if __name__ == "__main__":
    main() 