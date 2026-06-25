"""CLI to create or update a dashboard user.

Usage (from backend/ directory):
    python -m app.create_user <username> <password>
"""
import sys

from .database import Base, SessionLocal, engine
from .models import User
from .security import hash_password


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m app.create_user <username> <password>")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.hashed_password = hash_password(password)
            print(f"Updated password for existing user '{username}'.")
        else:
            user = User(username=username, hashed_password=hash_password(password))
            db.add(user)
            print(f"Created new user '{username}'.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
