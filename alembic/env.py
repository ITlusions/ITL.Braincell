"""
Alembic environment configuration for BrainCell.

Supports both sync and async migrations. Reads the database URL from
environment variables or falls back to alembic.ini.
"""
import os
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all cell models so Alembic can detect them
from src.core.models import Base

# Import all cell models to register with Base.metadata
from src.cells.interactions.model import Interaction
from src.cells.conversations.model import Conversation
from src.cells.sessions.model import MemorySession
from src.cells.decisions.model import DesignDecision
from src.cells.architecture_notes.model import ArchitectureNote
from src.cells.snippets.model import CodeSnippet
from src.cells.files_discussed.model import FileDiscussed
from src.cells.notes.model import Note
from src.cells.research_questions.model import ResearchQuestion
from src.cells.tasks.model import Task
from src.cells.errors.model import CellError
from src.cells.persons.model import Person
from src.cells.versions.model import CellVersion
from src.cells.references.model import Reference
from src.cells.iocs.model import IOC
from src.cells.threats.model import ThreatActor
from src.cells.incidents.model import SecurityIncident
from src.cells.intel_reports.model import IntelReport
from src.cells.vuln_patches.model import VulnPatch
from src.cells.runbooks.model import Runbook
from src.cells.dependencies.model import Dependency
from src.cells.api_contracts.model import ApiContract
from src.cells.kill_chains.model import KillChain
from src.cells.vuln_reports.model import VulnReport

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment or config."""
    # Support both full DATABASE_URL and individual components
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Convert postgresql:// to postgresql+asyncpg://
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return db_url
    
    # Fallback to individual components
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "9500")
    db = os.getenv("DATABASE_NAME", "braincell")
    user = os.getenv("DATABASE_USER", "braincell")
    password = os.getenv("DATABASE_PASSWORD", "braincell_dev_password")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL without connecting."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a live connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the database."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
