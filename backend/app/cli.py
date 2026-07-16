"""Administrative commands intentionally kept outside the public API."""

import argparse
import asyncio
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionFactory
from app.models import Settings, User


async def create_user(email: str) -> None:
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation or len(password) < 12:
        raise SystemExit("Passwords must match and contain at least 12 characters")
    async with SessionFactory() as session:
        normalized = email.strip().lower()
        if await session.scalar(select(User).where(User.email == normalized)):
            raise SystemExit("User already exists")
        user = User(email=normalized, password_hash=hash_password(password))
        session.add(user)
        await session.flush()
        session.add(Settings(user_id=user.id))
        await session.commit()
        print(f"Created user {normalized}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AdPilot administrative CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-user")
    create.add_argument("--email", required=True)
    args = parser.parse_args()
    if args.command == "create-user":
        asyncio.run(create_user(args.email))


if __name__ == "__main__":
    main()
