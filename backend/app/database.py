import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """Initializes tables and performs non-destructive schema migrations."""
    # Import all models to ensure they are registered with Base.metadata
    from backend.app.models import (
        project,
        agent_log,
        checkpoint,
        contact_submission,
        command_approval,
        setting,
        chat_message,
        website_page
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # SQLite automatic column migration for projects table
        if "sqlite" in settings.DATABASE_URL:
            try:
                res = await conn.execute(text("PRAGMA table_info(projects)"))
                existing_cols = {row[1] for row in res.fetchall()}

                migrations = [
                    ("website_type", "ALTER TABLE projects ADD COLUMN website_type VARCHAR(30) DEFAULT 'single-page'"),
                    ("selected_pages", "ALTER TABLE projects ADD COLUMN selected_pages JSON"),
                    ("tech_stack", "ALTER TABLE projects ADD COLUMN tech_stack VARCHAR(50) DEFAULT 'react-php'"),
                    ("subdomain", "ALTER TABLE projects ADD COLUMN subdomain VARCHAR(100)"),
                    ("custom_domain", "ALTER TABLE projects ADD COLUMN custom_domain VARCHAR(255)"),
                    ("requirements_spec", "ALTER TABLE projects ADD COLUMN requirements_spec JSON"),
                ]

                for col_name, alter_stmt in migrations:
                    if col_name not in existing_cols:
                        logger.info(f"Applying SQLite migration: {alter_stmt}")
                        await conn.execute(text(alter_stmt))

                res_wp = await conn.execute(text("PRAGMA table_info(website_pages)"))
                existing_wp_cols = {row[1] for row in res_wp.fetchall()}
                if "order_index" not in existing_wp_cols and len(existing_wp_cols) > 0:
                    logger.info("Applying SQLite migration: ALTER TABLE website_pages ADD COLUMN order_index INTEGER DEFAULT 0")
                    await conn.execute(text("ALTER TABLE website_pages ADD COLUMN order_index INTEGER DEFAULT 0"))

            except Exception as e:
                logger.warning(f"Database migration check warning: {e}")
