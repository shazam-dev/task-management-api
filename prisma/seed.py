import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

import bcrypt as _bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.models import Category, Priority, ShareLink, Status, Task, User

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def hash_password(password: str) -> str:
    salt = _bcrypt.gensalt(rounds=12)
    return _bcrypt.hashpw(password.encode(), salt).decode()


async def seed_users(db: AsyncSession):
    print("Seeding users...")
    hashed_demo = hash_password("demo123")
    hashed_admin = hash_password("admin123")

    result = await db.execute(select(User).where(User.email == "demo@example.com"))
    demo_user = result.scalar_one_or_none()
    if not demo_user:
        demo_user = User(email="demo@example.com", password=hashed_demo, name="Demo User")
        db.add(demo_user)

    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    admin_user = result.scalar_one_or_none()
    if not admin_user:
        admin_user = User(email="admin@example.com", password=hashed_admin, name="Admin User")
        db.add(admin_user)

    await db.commit()
    await db.refresh(demo_user)
    await db.refresh(admin_user)
    return {"demoUser": demo_user, "adminUser": admin_user}


async def seed_categories(db: AsyncSession):
    print("Seeding categories...")
    categories = {}
    for name in ["Work", "Personal", "Learning", "Health"]:
        result = await db.execute(select(Category).where(Category.name == name))
        cat = result.scalar_one_or_none()
        if not cat:
            cat = Category(name=name)
            db.add(cat)
            await db.flush()
        categories[name.lower()] = cat
    await db.commit()
    return categories


async def seed_statuses(db: AsyncSession):
    print("Seeding statuses...")
    statuses = {}
    for name in ["Todo", "In Progress", "In Review", "Completed", "Blocked"]:
        result = await db.execute(select(Status).where(Status.name == name))
        st = result.scalar_one_or_none()
        if not st:
            st = Status(name=name)
            db.add(st)
            await db.flush()
        statuses[name.lower().replace(" ", "_")] = st
    await db.commit()
    return statuses


async def seed_tasks(db: AsyncSession, users: dict, categories: dict, statuses: dict):
    print("Seeding tasks...")
    now = datetime.now(timezone.utc)
    next_week = now + timedelta(days=7)
    next_month = now + timedelta(days=30)

    tasks_data = [
        {
            "title": "Complete project proposal",
            "description": "Write and submit the Q2 project proposal for the new task management feature",
            "userId": users["demoUser"].id,
            "categoryId": categories["work"].id,
            "statusId": statuses["in_progress"].id,
            "priority": Priority.HIGH,
            "dueDate": next_week,
        },
        {
            "title": "Review code documentation",
            "description": "Go through the API documentation and update outdated sections",
            "userId": users["demoUser"].id,
            "categoryId": categories["work"].id,
            "statusId": statuses["todo"].id,
            "priority": Priority.MEDIUM,
            "dueDate": next_month,
        },
        {
            "title": "Learn TypeScript advanced patterns",
            "description": "Study advanced TypeScript patterns like conditional types and mapped types",
            "userId": users["demoUser"].id,
            "categoryId": categories["learning"].id,
            "statusId": statuses["in_progress"].id,
            "priority": Priority.MEDIUM,
        },
        {
            "title": "Schedule annual health checkup",
            "description": "Book appointment with primary care physician for yearly physical",
            "userId": users["demoUser"].id,
            "categoryId": categories["health"].id,
            "statusId": statuses["todo"].id,
            "priority": Priority.LOW,
            "dueDate": next_month,
        },
        {
            "title": "Organize home office space",
            "description": "Clean and reorganize desk area, set up proper lighting and ergonomics",
            "userId": users["demoUser"].id,
            "categoryId": categories["personal"].id,
            "statusId": statuses["completed"].id,
            "priority": Priority.LOW,
        },
        {
            "title": "Security audit implementation",
            "description": "Implement security recommendations from the latest audit report",
            "userId": users["adminUser"].id,
            "categoryId": categories["work"].id,
            "statusId": statuses["in_review"].id,
            "priority": Priority.URGENT,
            "dueDate": next_week,
        },
        {
            "title": "Database optimization",
            "description": "Optimize slow-running queries identified in the performance monitoring",
            "userId": users["adminUser"].id,
            "categoryId": categories["work"].id,
            "statusId": statuses["in_progress"].id,
            "priority": Priority.HIGH,
        },
        {
            "title": "Team meeting preparation",
            "description": "Prepare agenda and materials for quarterly team retrospective",
            "userId": users["adminUser"].id,
            "categoryId": categories["work"].id,
            "statusId": statuses["blocked"].id,
            "priority": Priority.MEDIUM,
            "dueDate": next_week,
        },
    ]

    created_tasks = []
    for tdata in tasks_data:
        task = Task(**tdata)
        db.add(task)
        await db.flush()
        created_tasks.append(task)

    await db.commit()
    return created_tasks


async def seed_share_links(db: AsyncSession, tasks: list):
    print("Seeding share links...")
    one_week = datetime.now(timezone.utc) + timedelta(days=7)
    one_month = datetime.now(timezone.utc) + timedelta(days=30)

    if len(tasks) > 0:
        result = await db.execute(
            select(ShareLink).where(ShareLink.token == "demo-task-link-token-123")
        )
        if not result.scalar_one_or_none():
            db.add(
                ShareLink(
                    taskId=tasks[0].id,
                    token="demo-task-link-token-123",
                    expiresAt=one_month,
                )
            )

    urgent_task = next((t for t in tasks if t.title == "Security audit implementation"), None)
    if urgent_task:
        result = await db.execute(
            select(ShareLink).where(ShareLink.token == "urgent-security-task-456")
        )
        if not result.scalar_one_or_none():
            db.add(
                ShareLink(
                    taskId=urgent_task.id,
                    token="urgent-security-task-456",
                    expiresAt=one_week,
                )
            )

    await db.commit()


async def execute_seeding():
    print("Starting database seeding process...")
    async with async_session_factory() as db:
        try:
            users = await seed_users(db)
            categories = await seed_categories(db)
            statuses = await seed_statuses(db)
            tasks = await seed_tasks(db, users, categories, statuses)
            await seed_share_links(db, tasks)

            print("Database seeding completed successfully!")
            print(f"Created {len(users)} users")
            print(f"Created {len(categories)} categories")
            print(f"Created {len(statuses)} statuses")
            print(f"Created {len(tasks)} tasks")
            print("Created 2 share links")
        except Exception as e:
            print(f"Error during database seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(execute_seeding())
