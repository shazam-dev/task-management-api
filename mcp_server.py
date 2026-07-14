"""
MCP Server for Task Management API.

Wraps the Task Management API as MCP tools for LLM integration.
Uses stdio transport (LLM launches this as a subprocess).

Usage:
    python mcp_server.py                    # stdio mode
    mcp dev mcp_server.py                   # MCP Inspector
    mcp run mcp_server.py                   # MCP CLI run
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.models import Base
from src.schemas.auth import LoginRequest, RegisterRequest
from src.schemas.category import CategoryCreate
from src.schemas.share_link import ShareLinkCreate
from src.schemas.status import StatusCreate
from src.schemas.task import TaskCreate, TaskUpdate
from src.schemas.user import UserUpdate
from src.services import auth_service, category_service, share_link_service
from src.services import status_service, task_service, user_service

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def _task_dict(task: Any) -> dict:
    return {
        "id": task.id,
        "userId": task.userId,
        "title": task.title,
        "statusId": task.statusId,
        "categoryId": task.categoryId,
        "description": task.description,
        "priority": task.priority.value if hasattr(task.priority, "value") else str(task.priority),
        "dueDate": str(task.dueDate) if task.dueDate else None,
        "createdAt": str(task.createdAt),
        "updatedAt": str(task.updatedAt),
    }


def _user_dict(user: Any) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "createdAt": str(user.createdAt),
        "updatedAt": str(user.updatedAt),
    }


def _category_dict(cat: Any) -> dict:
    return {
        "id": cat.id,
        "name": cat.name,
        "createdAt": str(cat.createdAt),
        "updatedAt": str(cat.updatedAt),
    }


def _status_dict(st: Any) -> dict:
    return {
        "id": st.id,
        "name": st.name,
        "createdAt": str(st.createdAt),
        "updatedAt": str(st.updatedAt),
    }


def _share_link_dict(link: Any) -> dict:
    return {
        "id": link.id,
        "taskId": link.taskId,
        "token": link.token,
        "expiresAt": str(link.expiresAt),
    }


mcp = FastMCP("Task Management API")


@mcp.tool()
async def register(email: str, password: str, name: str | None = None) -> str:
    """Create a new user account.

    Args:
        email: Email address for the account.
        password: Password for the account.
        name: Optional display name.
    """
    async with async_session() as db:
        result = await auth_service.register_user(db, RegisterRequest(email=email, password=password, name=name))
        return f"Account created successfully. Token: {result['access_token'][:30]}..."


@mcp.tool()
async def login(email: str, password: str) -> str:
    """Log in and get a JWT access token.

    Args:
        email: Email address.
        password: Password.
    """
    async with async_session() as db:
        result = await auth_service.login_user(db, LoginRequest(email=email, password=password))
        return f"Login successful. Token: {result['access_token']}"


@mcp.tool()
async def get_me(token: str) -> str:
    """Get current user profile (requires authentication).

    Args:
        token: JWT access token from login/register.
    """
    async with async_session() as db:
        user = await auth_service.get_user_from_token(db, token)
        return f"User: {_user_dict(user)}"


@mcp.tool()
async def list_users() -> str:
    """List all registered users."""
    async with async_session() as db:
        users = await user_service.get_all_users(db)
        return f"Users: {[_user_dict(u) for u in users]}"


@mcp.tool()
async def get_user(user_id: str) -> str:
    """Get a user by their ID.

    Args:
        user_id: UUID of the user.
    """
    async with async_session() as db:
        user = await user_service.get_user_by_id(db, user_id)
        return f"User: {_user_dict(user)}"


@mcp.tool()
async def update_user(token: str, user_id: str, name: str | None = None, email: str | None = None) -> str:
    """Update a user's name or email (requires authentication).

    Args:
        token: JWT access token.
        user_id: UUID of the user to update.
        name: New display name (optional).
        email: New email address (optional).
    """
    async with async_session() as db:
        user = await user_service.update_user(db, user_id, UserUpdate(name=name, email=email))
        return f"User updated: {_user_dict(user)}"


@mcp.tool()
async def delete_user(token: str, user_id: str) -> str:
    """Delete a user account (requires authentication).

    Args:
        token: JWT access token.
        user_id: UUID of the user to delete.
    """
    async with async_session() as db:
        await user_service.delete_user(db, user_id)
        return f"User {user_id} deleted successfully."


@mcp.tool()
async def list_tasks(user_id: str | None = None) -> str:
    """List all tasks, optionally filtered by user ID.

    Args:
        user_id: Optional UUID of user to filter tasks by.
    """
    async with async_session() as db:
        tasks = await task_service.get_all_tasks(db, user_id)
        return f"Tasks ({len(tasks)}): {[_task_dict(t) for t in tasks]}"


@mcp.tool()
async def get_task(task_id: str) -> str:
    """Get a task by its ID.

    Args:
        task_id: UUID of the task.
    """
    async with async_session() as db:
        task = await task_service.get_task_by_id(db, task_id)
        return f"Task: {_task_dict(task)}"


@mcp.tool()
async def create_task(
    token: str,
    title: str,
    status_id: str,
    category_id: str,
    description: str | None = None,
    priority: str = "medium",
    due_date: str | None = None,
) -> str:
    """Create a new task (requires authentication).

    Args:
        token: JWT access token.
        title: Task title.
        status_id: UUID of the status to assign.
        category_id: UUID of the category to assign.
        description: Optional task description.
        priority: Priority level: low, medium, high, urgent (default: medium).
        due_date: Optional due date in ISO format (e.g., 2026-12-31T23:59:59Z).
    """
    from datetime import datetime, timezone

    user = await _get_user_from_token(token)
    due_dt = datetime.fromisoformat(due_date) if due_date else None
    async with async_session() as db:
        task = await task_service.create_task(
            db,
            user.id,
            TaskCreate(
                title=title,
                statusId=status_id,
                categoryId=category_id,
                description=description,
                priority=priority,
                dueDate=due_dt,
            ),
        )
        return f"Task created: {_task_dict(task)}"


@mcp.tool()
async def update_task(
    token: str,
    task_id: str,
    title: str | None = None,
    status_id: str | None = None,
    category_id: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
) -> str:
    """Update an existing task (requires authentication, must be task owner).

    Args:
        token: JWT access token.
        task_id: UUID of the task to update.
        title: New title (optional).
        status_id: New status UUID (optional).
        category_id: New category UUID (optional).
        description: New description (optional).
        priority: New priority: low, medium, high, urgent (optional).
        due_date: New due date in ISO format (optional).
    """
    from datetime import datetime, timezone

    user = await _get_user_from_token(token)
    due_dt = datetime.fromisoformat(due_date) if due_date else None
    async with async_session() as db:
        task = await task_service.update_task(
            db,
            task_id,
            user.id,
            TaskUpdate(
                title=title,
                statusId=status_id,
                categoryId=category_id,
                description=description,
                priority=priority,
                dueDate=due_dt,
            ),
        )
        return f"Task updated: {_task_dict(task)}"


@mcp.tool()
async def delete_task(token: str, task_id: str) -> str:
    """Delete a task (requires authentication, must be task owner).

    Args:
        token: JWT access token.
        task_id: UUID of the task to delete.
    """
    user = await _get_user_from_token(token)
    async with async_session() as db:
        await task_service.delete_task(db, task_id, user.id)
        return f"Task {task_id} deleted successfully."


@mcp.tool()
async def list_categories() -> str:
    """List all task categories."""
    async with async_session() as db:
        categories = await category_service.get_all_categories(db)
        return f"Categories: {[_category_dict(c) for c in categories]}"


@mcp.tool()
async def create_category(name: str) -> str:
    """Create a new task category.

    Args:
        name: Category name (must be unique).
    """
    async with async_session() as db:
        cat = await category_service.create_category(db, CategoryCreate(name=name))
        return f"Category created: {_category_dict(cat)}"


@mcp.tool()
async def delete_category(category_id: str) -> str:
    """Delete a task category.

    Args:
        category_id: UUID of the category to delete.
    """
    async with async_session() as db:
        await category_service.delete_category(db, category_id)
        return f"Category {category_id} deleted successfully."


@mcp.tool()
async def list_statuses() -> str:
    """List all task statuses."""
    async with async_session() as db:
        statuses = await status_service.get_all_statuses(db)
        return f"Statuses: {[_status_dict(s) for s in statuses]}"


@mcp.tool()
async def create_status(name: str) -> str:
    """Create a new task status.

    Args:
        name: Status name (must be unique).
    """
    async with async_session() as db:
        st = await status_service.create_status(db, StatusCreate(name=name))
        return f"Status created: {_status_dict(st)}"


@mcp.tool()
async def delete_status(status_id: str) -> str:
    """Delete a task status.

    Args:
        status_id: UUID of the status to delete.
    """
    async with async_session() as db:
        await status_service.delete_status(db, status_id)
        return f"Status {status_id} deleted successfully."


@mcp.tool()
async def create_share_link(task_id: str, token: str, expires_at: str) -> str:
    """Create a shareable link for a task.

    Args:
        task_id: UUID of the task to share.
        token: Unique token for the share link.
        expires_at: Expiration date in ISO format (e.g., 2026-12-31T23:59:59Z).
    """
    from datetime import datetime, timezone

    expires_dt = datetime.fromisoformat(expires_at)
    async with async_session() as db:
        link = await share_link_service.create_share_link(
            db,
            ShareLinkCreate(taskId=task_id, token=token, expiresAt=expires_dt),
        )
        return f"Share link created: {_share_link_dict(link)}"


@mcp.tool()
async def get_shared_task(share_token: str) -> str:
    """Get a task via its share link token.

    Args:
        share_token: The share link token.
    """
    async with async_session() as db:
        task = await share_link_service.get_task_by_share_token(db, share_token)
        return f"Shared task: {_task_dict(task)}"


@mcp.tool()
async def delete_share_link(link_id: str) -> str:
    """Delete a share link.

    Args:
        link_id: UUID of the share link to delete.
    """
    async with async_session() as db:
        await share_link_service.delete_share_link(db, link_id)
        return f"Share link {link_id} deleted successfully."


async def _get_user_from_token(token: str):
    async with async_session() as db:
        return await auth_service.get_user_from_token(db, token)


@mcp.resource("task-management://status")
def server_status() -> str:
    """MCP server status and available tools."""
    return "Task Management MCP Server is running. 18 tools available."


if __name__ == "__main__":
    mcp.run()
