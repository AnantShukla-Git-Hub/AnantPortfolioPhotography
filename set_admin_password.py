"""Change the local admin password (run once, before real use):

    python set_admin_password.py
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sqlmodel import Session, select  # noqa: E402
from app.models import AdminUser, DB_PATH, engine, pwd_context  # noqa: E402


def main():
    if not os.path.exists(DB_PATH):
        sys.exit("portfolio.db not found. Start the server once (uvicorn app.main:app) so it gets created, then run this.")
    pw = getpass.getpass("New admin password (12-72 characters): ")
    if not 12 <= len(pw.encode()) <= 72:
        sys.exit("Password must be 12 to 72 characters.")
    if pw != getpass.getpass("Repeat password: "):
        sys.exit("Passwords did not match.")
    with Session(engine) as session:
        user = session.exec(select(AdminUser)).first()
        if not user:
            sys.exit("No admin user found.")
        user.password_hash = pwd_context.hash(pw)
        session.add(user)
        session.commit()
    print("Admin password updated.")


if __name__ == "__main__":
    main()
